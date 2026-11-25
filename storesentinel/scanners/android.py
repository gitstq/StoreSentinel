"""Android scanner: AndroidManifest.xml + Gradle build files."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from ..fsutil import find_file, read_text
from ..models import (Finding, Rule, ScanResult, SEVERITY_ERROR,
                      SEVERITY_INFO, SEVERITY_WARN)

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

DANGEROUS_PERMISSIONS = {
    "android.permission.CAMERA",
    "android.permission.RECORD_AUDIO",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.ACCESS_BACKGROUND_LOCATION",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.READ_MEDIA_IMAGES",
    "android.permission.READ_CONTACTS",
    "android.permission.READ_PHONE_STATE",
}

RULE_DEBUGGABLE = Rule(
    "AND001", SEVERITY_ERROR,
    "android:debuggable enabled",
    "The application is marked android:debuggable=\"true\". Debuggable "
    "builds are rejected by Google Play and expose app data to attackers.",
    "Remove android:debuggable from AndroidManifest.xml; rely on build "
    "type configuration instead.",
    "android",
)

RULE_CLEARTEXT = Rule(
    "AND002", SEVERITY_WARN,
    "Cleartext traffic allowed globally",
    "android:usesCleartextTraffic=\"true\" permits plain HTTP, a common "
    "store-rejection and security-review flag.",
    "Enable cleartext only for specific domains via a network security "
    "config XML.",
    "android",
)

RULE_DANGEROUS = Rule(
    "AND003", SEVERITY_INFO,
    "Dangerous permission declared",
    "A runtime-sensitive permission is declared in the manifest. Both "
    "stores expect a clear user-facing justification and a privacy policy "
    "entry for each such permission.",
    "Ensure runtime request flows, a privacy policy, and Play Data Safety "
    "declarations cover every dangerous permission.",
    "android",
)

RULE_TARGET_SDK = Rule(
    "AND004", SEVERITY_ERROR,
    "targetSdkVersion below store minimum",
    "Google Play requires new apps and updates to target a recent Android "
    "API level (34+ as of 2025 policy).",
    "Bump targetSdk in app/build.gradle and retest permission flows.",
    "android",
)

RULE_EXPORTED = Rule(
    "AND005", SEVERITY_WARN,
    "Component with intent-filter missing android:exported",
    "Android 12+ requires every activity / service / receiver that has an "
    "intent-filter to declare android:exported explicitly. Uploads fail "
    "the manifest check otherwise.",
    "Add android:exported=\"false\" (or \"true\" where intentional) to "
    "components with intent-filters.",
    "android",
)

RULE_PACKAGE_NAME = Rule(
    "AND006", SEVERITY_WARN,
    "Placeholder package name",
    "The applicationId / package still uses the com.example placeholder, "
    "which Google Play rejects.",
    "Choose a unique applicationId before the first release.",
    "android",
)

RULE_VERSION = Rule(
    "AND007", SEVERITY_ERROR,
    "Missing versionCode / versionName",
    "No versionCode or versionName found in manifest or Gradle config; "
    "release uploads cannot proceed without them.",
    "Set versionCode and versionName in app/build.gradle defaultConfig.",
    "android",
)


def scan(root: Path, result: ScanResult,
         target_sdk_min: int = 34) -> None:
    """Run all Android rules against the project rooted at *root*."""
    manifest_path = find_file(root, "AndroidManifest.xml")
    gradle_text = _read_gradle(root)

    # AND004 targetSdk (Gradle-first, manifest fallback)
    target_sdk = _extract_target_sdk(gradle_text)
    if manifest_path is None:
        # Without a manifest we can still run the Gradle-only rules.
        _check_gradle_only(root, gradle_text, result, target_sdk,
                           target_sdk_min)
        return

    tree = _parse_manifest(manifest_path)
    if tree is None:
        _check_gradle_only(root, gradle_text, result, target_sdk,
                           target_sdk_min)
        return

    ns_root = tree.getroot()
    app_el = ns_root.find("application")
    rel = str(manifest_path.relative_to(root))

    # AND001 debuggable
    if app_el is not None and app_el.get(ANDROID_NS + "debuggable") == "true":
        result.findings.append(Finding(
            RULE_DEBUGGABLE, "android:debuggable=\"true\" in manifest", rel))

    # AND002 cleartext
    if app_el is not None and \
            app_el.get(ANDROID_NS + "usesCleartextTraffic") == "true":
        result.findings.append(Finding(
            RULE_CLEARTEXT, "usesCleartextTraffic=\"true\" in manifest", rel))

    # AND003 dangerous permissions
    for perm in ns_root.iter("uses-permission"):
        name = perm.get(ANDROID_NS + "name", "")
        if name in DANGEROUS_PERMISSIONS:
            result.findings.append(Finding(
                RULE_DANGEROUS, f"Dangerous permission declared: {name}",
                rel))

    # AND005 exported attr on intent-filter components
    for tag in ("activity", "activity-alias", "service", "receiver",
                "provider"):
        for comp in ns_root.iter(tag):
            if comp.find("intent-filter") is None:
                continue
            if ANDROID_NS + "exported" not in comp.attrib:
                result.findings.append(Finding(
                    RULE_EXPORTED,
                    f"<{tag}> {comp.get(ANDROID_NS + 'name', '')} has an "
                    "intent-filter but no android:exported attribute",
                    rel))
                break  # one finding is enough

    # AND007 version presence (manifest attribute or gradle)
    has_version = app_el is not None and (
        ANDROID_NS + "versionCode" in app_el.attrib
        or ANDROID_NS + "versionName" in app_el.attrib)
    gradle_version = re.search(r"versionCode\s+|versionName\s+", gradle_text) \
        if gradle_text else None
    if not has_version and not gradle_version:
        result.findings.append(Finding(
            RULE_VERSION, "No versionCode/versionName in manifest or gradle",
            rel))

    # AND004 / AND006 via gradle + manifest package attr
    _check_gradle_only(root, gradle_text, result, target_sdk,
                       target_sdk_min,
                       package_attr=app_el.get("package")
                       if app_el is not None else None)


def _check_gradle_only(root: Path, gradle_text: str, result: ScanResult,
                       target_sdk: Optional[int], target_sdk_min: int,
                       package_attr: Optional[str] = None) -> None:
    if target_sdk is not None and target_sdk < target_sdk_min:
        result.findings.append(Finding(
            RULE_TARGET_SDK,
            f"targetSdkVersion {target_sdk} is below the store minimum "
            f"{target_sdk_min}", ""))
    pkg = package_attr or _extract_application_id(gradle_text)
    if pkg and pkg.startswith("com.example"):
        result.findings.append(Finding(
            RULE_PACKAGE_NAME, f"Placeholder applicationId: {pkg}", ""))


def _read_gradle(root: Path) -> str:
    for name in ("build.gradle", "build.gradle.kts"):
        p = find_file(root, name, skip_dirs={
            ".git", ".gradle", "build", "node_modules"})
        if p is not None:
            return read_text(p)
    return ""


def _parse_manifest(path: Path) -> Optional[ET.ElementTree]:
    try:
        return ET.parse(path)
    except ET.ParseError:
        return None
    except OSError:
        return None


def _extract_target_sdk(gradle_text: str) -> Optional[int]:
    if not gradle_text:
        return None
    m = re.search(r"targetSdk(?:Version)?\s+(?:=|setup)\s+(\d+)", gradle_text)
    if m:
        return int(m.group(1))
    m = re.search(r"targetSdk(?:Version)?\s+['\"]?(\d+)['\"]?", gradle_text)
    return int(m.group(1)) if m else None


def _extract_application_id(gradle_text: str) -> Optional[str]:
    if not gradle_text:
        return None
    m = re.search(r"""(?:applicationId|namespace)\s+["']([^"']+)["']""",
                  gradle_text)
    return m.group(1) if m else None
