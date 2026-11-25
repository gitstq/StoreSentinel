#!/usr/bin/env bash
# One-click packaging: tests -> zipapp -> wheel -> SHA256 checksums.
# Usage: ./build.sh [--skip-tests]
set -euo pipefail
cd "$(dirname "$0")"

VERSION=$(python3 -c "import storesentinel;print(storesentinel.__version__)")
DIST=dist
NAME="storesentinel-${VERSION}"

if [ "${1:-}" != "--skip-tests" ]; then
  echo "[1/4] Running tests..."
  python3 -m unittest discover -s tests -q
else
  echo "[1/4] Skipping tests."
fi

echo "[2/4] Building zipapp..."
mkdir -p "$DIST"
rm -f "$DIST/${NAME}.pyz"
# Stage the package one level down so `storesentinel` stays importable
# inside the archive while __main__.py sits at the archive root.
STAGING=$(mktemp -d)
mkdir -p "$STAGING/storesentinel"
cp -r storesentinel/. "$STAGING/storesentinel/"
printf 'from storesentinel.cli import main\nimport sys\nsys.exit(main())\n' \
  > "$STAGING/__main__.py"
python3 -m zipapp "$STAGING" \
  -p "/usr/bin/env python3" \
  -o "$DIST/${NAME}.pyz" \
  -c
rm -rf "$STAGING"

echo "[3/4] Building wheel..."
python3 -m pip wheel . --no-deps -w "$DIST" -q 2>/dev/null \
  || echo "(pip wheel unavailable; zipapp still produced)"

echo "[4/4] Generating checksums..."
cd "$DIST"
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum ./* > SHA256SUMS.txt
else
  shasum -a 256 ./* > SHA256SUMS.txt
fi
echo "Done. Artifacts in $DIST/:"
ls -la
