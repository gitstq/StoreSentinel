"""Shared filesystem helpers for scanners."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, Optional

SKIP_DIRS = {
    ".git", ".gradle", ".idea", ".svn", "build", "Build", "DerivedData",
    "Pods", "node_modules", "vendor", "__pycache__", ".dart_tool",
    ".flutter-plugins", "dist", "out", ".venv", "venv", "Carthage",
}

# Upper bound to keep scanning fast on huge trees.
MAX_FILES = 20000


def iter_files(root: Path, suffixes: Optional[set] = None,
               names: Optional[set] = None) -> Iterator[Path]:
    """Yield files under *root* whose suffix/name matches, skipping junk dirs."""
    seen = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and not d.startswith(".")]
        for fn in filenames:
            seen += 1
            if seen > MAX_FILES:
                return
            p = Path(dirpath) / fn
            if names is not None and fn in names:
                yield p
            elif suffixes is not None and p.suffix in suffixes:
                yield p


def find_file(root: Path, filename: str, skip_dirs: Optional[set] = None
              ) -> Optional[Path]:
    """Return the first file named *filename* under root, or None.

    Prefers shallow matches: results are sorted by path depth.
    """
    skip = (skip_dirs or SKIP_DIRS)
    candidates: list = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip
                       and not d.startswith(".")]
        if filename in filenames:
            candidates.append(Path(dirpath) / filename)
    candidates.sort(key=lambda p: len(p.parts))
    return candidates[0] if candidates else None


def read_text(path: Path, limit: int = 2_000_000) -> str:
    """Best-effort text read (errors ignored) with a size cap."""
    try:
        if path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
