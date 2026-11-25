"""iOS scanner: Info.plist / privacy manifest / purpose strings."""

from __future__ import annotations

import plistlib
from pathlib import Path
from typing import Optional

from ..fsutil import find_file, iter_files, read_text
from ..models import Finding, Rule, ScanResult, SEVERITY_ERROR, SEVERITY_WARN

# API symbols that imply a permission usage, mapped to the required
# Info.plist purpose-string key. Used by rule IOS005.
API_USAGE_MAP = {
    "NSCameraUsageDescription": [
        "AVCaptureDevice", "AVCaptureSession", "AVCapturePhotoOutput",
        "imagePickerController(sourceType: .camera", "cameraDevice",
    ],
    "NSLocationWhenInUseUsageDescription": [
        "CLLocationManager", "requestWhenInUseAuthorization",
        "kCLAuthorizationStatus",
    ],
    "NSPhotoLibraryUsageDescription": [
        "PHPickerViewController", "UIImagePickerPhotosLibraryMode",
        "NSManagedObjectModelPhoto", "PHPhotoLibrary",
    ],
    "NSMicrophoneUsageDescription": [
        "AVAudioRecorder", "requestRecordPermission", "AVAudioSession(record",
    ],
    "NSUserTrackingUsageDescription": [
        "ATTrackingManager", "requestTrackingAuthorization",
    ],
}

RULE_ENCRYPTION = Rule(
    "IOS001", SEVERITY_ERROR,
    "Missing ITSAppUsesNonExemptEncryption key",
    "Info.plist does not declare ITSAppUsesNonExemptEncryption. Without it "
    "the review team may stall on export-compliance questions, and uploads "
    "require manual compliance confirmation each release.",
    "Add <key>ITSAppUsesNonExemptEncryption</key><false/> to Info.plist "
    "(use true if you ship non-exempt cryptography).",
    "ios",
)

RULE_PRIVACY_MANIFEST = Rule(
    "IOS002", SEVERITY_ERROR,
    "Missing PrivacyInfo.xcprivacy privacy manifest",
    "No PrivacyInfo.xcprivacy found. Apple requires privacy manifests for "
    "apps and third-party SDKs that use declared required-reason APIs.",
    "Create a PrivacyInfo.xcprivacy resource declaring required-reason API "
    "categories and collected data types.",
    "ios",
)

RULE_ATS = Rule(
    "IOS003", SEVERITY_WARN,
    "App Transport Security disabled globally",
    "NSAppTransportSecurity / NSAllowsArbitraryLoads is enabled, which is a "
    "common rejection reason and a security smell.",
    "Restrict exceptions per domain with NSExceptionDomains, or remove "
    "NSAllowsArbitraryLoads entirely.",
    "ios",
)

RULE_LAUNCH = Rule(
    "IOS004", SEVERITY_WARN,
    "No launch screen configured",
    "Info.plist has neither UILaunchScreen nor UILaunchStoryboardName. "
    "iPhone apps must provide a launch screen for modern device sizes.",
    "Add UILaunchScreen (empty dict is fine) or a launch storyboard to "
    "Info.plist.",
    "ios",
)

RULE_PURPOSE = Rule(
    "IOS005", SEVERITY_ERROR,
    "Permission API used without purpose string",
    "Source code references a privacy-sensitive API but the matching "
    "usage-description key is missing from Info.plist — a guaranteed "
    "rejection for apps using camera / location / photo / microphone / "
    "tracking APIs.",
    "Add the missing NS*UsageDescription key with a user-facing "
    "explanation of why the permission is needed.",
    "ios",
)


def _load_plist(path: Path) -> Optional[dict]:
    try:
        with open(path, "rb") as fh:
            data = plistlib.load(fh)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def scan(root: Path, result: ScanResult) -> None:
    """Run all iOS rules against the project rooted at *root*."""
    plist_path = _find_info_plist(root)
    if plist_path is not None:
        plist = _load_plist(plist_path) or {}
        rel = str(plist_path.relative_to(root))

        # IOS001 export compliance
        if "ITSAppUsesNonExemptEncryption" not in plist:
            result.findings.append(Finding(
                RULE_ENCRYPTION,
                "ITSAppUsesNonExemptEncryption is not set in Info.plist",
                rel))
        # IOS004 launch screen (empty dict is a valid UILaunchScreen value)
        if plist.get("UILaunchScreen") is None and \
                not plist.get("UILaunchStoryboardName"):
            result.findings.append(Finding(
                RULE_LAUNCH,
                "Neither UILaunchScreen nor UILaunchStoryboardName found",
                rel))
        # IOS003 ATS
        ats = plist.get("NSAppTransportSecurity") or {}
        if ats.get("NSAllowsArbitraryLoads") is True:
            result.findings.append(Finding(
                RULE_ATS,
                "NSAllowsArbitraryLoads is enabled in Info.plist",
                rel))
        # IOS005 purpose strings vs source usage
        _check_purpose_strings(root, plist, result)

    # IOS002 privacy manifest
    if find_file(root, "PrivacyInfo.xcprivacy") is None:
        result.findings.append(Finding(
            RULE_PRIVACY_MANIFEST,
            "No PrivacyInfo.xcprivacy found anywhere in the project",
            ""))


def _find_info_plist(root: Path) -> Optional[Path]:
    """Locate the app's Info.plist (not framework/pod internal ones)."""
    candidates: list = []
    for p in iter_files(root, names={"Info.plist"}):
        # Skip XCTest bundles etc. (Xcode convention: *Tests directories).
        if any(seg.endswith("Tests") for seg in p.parts):
            continue
        try:
            with open(p, "rb") as fh:
                data = plistlib.load(fh)
        except Exception:
            continue
        if isinstance(data, dict) and (
                "CFBundleIdentifier" in data or "CFBundleShortVersionString" in data):
            candidates.append(p)
    candidates.sort(key=lambda x: len(x.parts))
    return candidates[0] if candidates else None


def _check_purpose_strings(root: Path, plist: dict, result: ScanResult) -> None:
    """Flag APIs referenced in Swift/ObjC/m/Dart sources whose purpose
    string is absent (rule IOS005)."""
    for key, symbols in API_USAGE_MAP.items():
        if key in plist:
            continue
        hit_file, hit_line = _find_symbol_usage(root, symbols)
        if hit_file is not None:
            result.findings.append(Finding(
                RULE_PURPOSE,
                f"Source uses an API that requires <{key}> but the key is "
                f"missing from Info.plist",
                hit_file, hit_line))


def _find_symbol_usage(root: Path, symbols: list):
    for p in iter_files(root, suffixes={".swift", ".m", ".h", ".mm", ".dart"}):
        text = read_text(p)
        if not text:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for sym in symbols:
                if sym in line:
                    try:
                        rel = str(p.relative_to(root))
                    except ValueError:
                        rel = str(p)
                    return rel, lineno
    return None, None
