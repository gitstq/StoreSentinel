"""Scan engine: platform detection + scanner orchestration."""

from __future__ import annotations

import os
from pathlib import Path

from . import scanners
from .fsutil import SKIP_DIRS, find_file, read_text
from .models import ScanResult
from .registry import ALL_RULES


def detect_platforms(root: Path) -> list:
    """Detect which app platforms the project targets."""
    found = []

    # iOS: Xcode project/workspace/podfile anywhere (shallow-ish walk).
    has_xcode = find_file(root, "Podfile") is not None or _find_xcodeproj(root)
    has_info = find_file(root, "Info.plist") is not None
    if has_xcode or has_info:
        found.append("ios")

    # Android
    if find_file(root, "AndroidManifest.xml") is not None \
            or find_file(root, "build.gradle") is not None \
            or find_file(root, "build.gradle.kts") is not None:
        found.append("android")

    # Flutter (pubspec.yaml with flutter dependency section)
    pubspec = find_file(root, "pubspec.yaml")
    if pubspec is not None and "flutter" in read_text(pubspec):
        found.append("flutter")

    # React Native (package.json declaring react-native)
    pkg = find_file(root, "package.json")
    if pkg is not None and '"react-native"' in read_text(pkg):
        found.append("rn")

    return found


def _find_xcodeproj(root: Path):
    """Find any *.xcodeproj / *.xcworkspace under root (bounded walk)."""
    seen = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith(".")]
        for name in dirnames + filenames:
            seen += 1
            if seen > 5000:
                return None
            if name.endswith((".xcodeproj", ".xcworkspace")):
                return Path(dirpath) / name
    return None


def run_scan(project: Path, platforms: list = None,
             target_sdk_min: int = 34) -> ScanResult:
    """Scan *project* and return an aggregated ScanResult."""
    project = project.resolve()
    result = ScanResult(project_path=str(project), rules_total=len(ALL_RULES))
    result.platforms_detected = platforms or detect_platforms(project)

    # Always run the cross-platform checks.
    scanners.general.scan(project, result)

    plats = set(result.platforms_detected)
    if plats & {"ios", "rn", "flutter"}:
        scanners.ios.scan(project, result)
    if plats & {"android", "rn", "flutter"}:
        scanners.android.scan(project, result,
                              target_sdk_min=target_sdk_min)
    if "flutter" in plats:
        scanners.flutter.scan(project, result)

    # Sort findings by severity weight then rule id for stable output.
    order = {"error": 0, "warn": 1, "info": 2}
    result.findings.sort(
        key=lambda f: (order.get(f.rule.severity, 3), f.rule.rule_id))
    return result
