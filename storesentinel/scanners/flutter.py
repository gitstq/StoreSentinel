"""Flutter scanner: pubspec.yaml release-readiness checks.

A minimal regex-based parser is used on purpose: StoreSentinel is a
zero-dependency tool and only needs a handful of top-level keys.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..fsutil import find_file, read_text
from ..models import Finding, Rule, ScanResult, SEVERITY_ERROR, SEVERITY_WARN

RULE_FLT_VERSION = Rule(
    "FLT001", SEVERITY_ERROR,
    "pubspec.yaml has no version",
    "Flutter release builds require a top-level `version:` in pubspec.yaml "
    "(used for versionName/versionCode generation on Android and "
    "CFBundleShortVersionString on iOS).",
    "Add a line like:  version: 1.0.0+1",
    "flutter",
)

RULE_FLT_DESC = Rule(
    "FLT002", SEVERITY_WARN,
    "pubspec.yaml has no description",
    "A missing or empty `description:` weakens package identity and blocks "
    "clean publishing workflows.",
    "Add a short one-line description to pubspec.yaml.",
    "flutter",
)


def scan(root: Path, result: ScanResult) -> None:
    """Run all Flutter rules against the project rooted at *root*."""
    pubspec = find_file(root, "pubspec.yaml")
    if pubspec is None:
        return
    text = read_text(pubspec)
    if not text:
        return
    rel = str(pubspec.relative_to(root))

    version = re.search(r"^version:\s*(\S+)", text, re.MULTILINE)
    if not version:
        result.findings.append(Finding(
            RULE_FLT_VERSION, "pubspec.yaml: no top-level `version:` entry",
            rel))

    desc = re.search(r"^description:\s*(.*)$", text, re.MULTILINE)
    if not desc or not desc.group(1).strip():
        result.findings.append(Finding(
            RULE_FLT_DESC, "pubspec.yaml: description missing or empty",
            rel))
