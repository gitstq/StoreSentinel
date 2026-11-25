"""Unit tests for StoreSentinel scanning engine and CLI."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storesentinel.cli import main
from storesentinel.engine import detect_platforms, run_scan
from storesentinel.models import ScanResult

FIXTURES = Path(__file__).parent / "fixtures"


def rule_ids(result: ScanResult):
    return [f.rule.rule_id for f in result.findings]


class TestIOSFixture(unittest.TestCase):
    def setUp(self):
        self.result = run_scan(FIXTURES / "ios_app")

    def test_platform_detected(self):
        self.assertIn("ios", self.result.platforms_detected)

    def test_missing_encryption_key(self):
        self.assertIn("IOS001", rule_ids(self.result))

    def test_missing_privacy_manifest(self):
        self.assertIn("IOS002", rule_ids(self.result))

    def test_ats_arbitrary_loads(self):
        self.assertIn("IOS003", rule_ids(self.result))

    def test_missing_launch_screen(self):
        self.assertIn("IOS004", rule_ids(self.result))

    def test_location_api_without_purpose_string(self):
        ids = rule_ids(self.result)
        self.assertIn("IOS005", ids)
        finding = next(f for f in self.result.findings
                       if f.rule.rule_id == "IOS005")
        self.assertIn("ViewController.swift", finding.file_path)
        self.assertIsNotNone(finding.line)

    def test_camera_purpose_present_no_camera_finding(self):
        # Camera usage is declared, so IOS005 should fire only once
        # (for the location key).
        ios005 = [f for f in self.result.findings
                  if f.rule.rule_id == "IOS005"]
        self.assertEqual(len(ios005), 1)

    def test_score_matches_severity_weights(self):
        # 3 errors * 10 + 2 warns * 3 = 36 penalty -> 64
        self.assertEqual(self.result.score, 64)


class TestAndroidFixture(unittest.TestCase):
    def setUp(self):
        self.result = run_scan(FIXTURES / "android_app")

    def test_platform_detected(self):
        self.assertIn("android", self.result.platforms_detected)

    def test_debuggable(self):
        self.assertIn("AND001", rule_ids(self.result))

    def test_cleartext(self):
        self.assertIn("AND002", rule_ids(self.result))

    def test_dangerous_permission(self):
        self.assertIn("AND003", rule_ids(self.result))

    def test_target_sdk(self):
        self.assertIn("AND004", rule_ids(self.result))

    def test_exported_missing(self):
        self.assertIn("AND005", rule_ids(self.result))

    def test_placeholder_package(self):
        self.assertIn("AND006", rule_ids(self.result))

    def test_version_present_no_finding(self):
        self.assertNotIn("AND007", rule_ids(self.result))


class TestFlutterFixture(unittest.TestCase):
    def setUp(self):
        self.result = run_scan(FIXTURES / "flutter_app")

    def test_flutter_and_ios_detected(self):
        self.assertIn("flutter", self.result.platforms_detected)
        self.assertIn("ios", self.result.platforms_detected)

    def test_pubspec_missing_version(self):
        self.assertIn("FLT001", rule_ids(self.result))

    def test_description_present_no_finding(self):
        self.assertNotIn("FLT002", rule_ids(self.result))

    def test_good_ios_plist_still_flags_privacy_manifest(self):
        # Valid plist keys but no PrivacyInfo.xcprivacy anywhere.
        self.assertIn("IOS002", rule_ids(self.result))
        self.assertNotIn("IOS001", rule_ids(self.result))


class TestCleanProject(unittest.TestCase):
    def test_perfect_project_only_general_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app" / "Info.plist").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<plist version="1.0"><dict>'
                '<key>CFBundleIdentifier</key><string>io.demo.clean</string>'
                '<key>ITSAppUsesNonExemptEncryption</key><false/>'
                '<key>UILaunchScreen</key><dict/>'
                '</dict></plist>')
            (root / "PRIVACY.md").write_text("# Privacy Policy\n")
            result = run_scan(root, platforms=["ios"])
            ids = rule_ids(result)
            # Valid plist keys, privacy doc present, but no privacy manifest.
            self.assertNotIn("IOS001", ids)
            self.assertNotIn("IOS004", ids)
            self.assertNotIn("GEN001", ids)
            self.assertIn("IOS002", ids)
            self.assertEqual(result.score, 90)


class TestCLI(unittest.TestCase):
    def test_exit_code_zero_without_flag(self):
        self.assertEqual(main([str(FIXTURES / "android_app")]), 0)

    def test_fail_on_error(self):
        self.assertEqual(
            main(["--fail-on-error", str(FIXTURES / "android_app")]), 1)

    def test_missing_path_exit_2(self):
        self.assertEqual(main(["/nonexistent/path/xyz"]), 2)

    def test_json_format_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            main(["-f", "json", "-o", str(out),
                  str(FIXTURES / "flutter_app")])
            data = json.loads(out.read_text())
            self.assertIn("score", data)
            self.assertIn("findings", data)
            self.assertTrue(any(f["rule_id"] == "FLT001"
                                for f in data["findings"]))

    def test_sarif_format_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.sarif"
            main(["-f", "sarif", "-o", str(out),
                  str(FIXTURES / "android_app")])
            data = json.loads(out.read_text())
            self.assertEqual(data["version"], "2.1.0")
            self.assertTrue(data["runs"][0]["results"])

    def test_list_rules(self):
        self.assertEqual(main(["--list-rules"]), 0)


if __name__ == "__main__":
    unittest.main()
