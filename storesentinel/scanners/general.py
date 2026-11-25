"""General (cross-platform) checks."""

from __future__ import annotations

from pathlib import Path

from ..fsutil import find_file
from ..models import Finding, Rule, ScanResult, SEVERITY_INFO

PRIVACY_FILENAMES = {
    "PRIVACY.md", "PRIVACY_POLICY.md", "PrivacyPolicy.md", "privacy.md",
    "privacy-policy.md", "PRIVACY.txt",
}

RULE_PRIVACY_DOC = Rule(
    "GEN001", SEVERITY_INFO,
    "No privacy policy document in repository",
    "App Store Connect and Google Play both require a privacy policy URL "
    "at listing time. Keeping one in the repository makes review-day "
    "surprises unlikely.",
    "Add a PRIVACY.md describing data collection, storage and sharing.",
    "general",
)


def scan(root: Path, result: ScanResult) -> None:
    """Run general rules against the project rooted at *root*."""
    skip = {".git", "node_modules", "build", "Pods"}
    found = any(find_file(root, name, skip_dirs=skip) is not None
                for name in PRIVACY_FILENAMES)
    if not found:
        result.findings.append(Finding(
            RULE_PRIVACY_DOC,
            "No PRIVACY.md / privacy policy file found in project root", ""))
