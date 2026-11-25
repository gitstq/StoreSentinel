"""Command-line interface for StoreSentinel."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .engine import run_scan
from .registry import ALL_RULES
from .reports import write_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="storesentinel",
        description=("Scan iOS / Android / Flutter / React Native projects "
                     "for common App Store & Google Play rejection risks. "
                     "Zero dependencies, CI-friendly."),
    )
    p.add_argument("project", nargs="?", default=".",
                   help="Path to the mobile project root (default: .)")
    p.add_argument("-f", "--format", choices=["text", "json", "sarif"],
                   default="text", help="Report format (default: text)")
    p.add_argument("-o", "--output", help="Write report to a file "
                                          "instead of stdout")
    p.add_argument("--target-sdk", type=int, default=34,
                   help="Minimum acceptable Android targetSdk (default: 34)")
    p.add_argument("--fail-on-error", action="store_true",
                   help="Exit with code 1 if any error-severity finding is "
                        "reported (CI gate mode)")
    p.add_argument("--list-rules", action="store_true",
                   help="List all built-in rules and exit")
    p.add_argument("--no-color", action="store_true",
                   help="Disable ANSI colors in text reports")
    p.add_argument("-V", "--version", action="version",
                   version=f"StoreSentinel {__version__}")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.list_rules:
        for r in ALL_RULES:
            print(f"{r.rule_id:<8} [{r.severity:<5}] [{r.platform:<7}] "
                  f"{r.title}")
        return 0

    root = Path(args.project)
    if not root.exists():
        print(f"error: project path not found: {root}", file=sys.stderr)
        return 2

    result = run_scan(root, target_sdk_min=args.target_sdk)
    write_report(result, args.format, args.output,
                 color=not args.no_color and args.format == "text")

    if args.fail_on_error and result.errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
