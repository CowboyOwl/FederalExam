#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install -r requirements-build.txt
python3 -m PyInstaller FederalExam-mac.spec --noconfirm --clean

if command -v codesign >/dev/null 2>&1; then
  codesign --force --deep --sign - dist/FederalExam.app || true
fi

echo "Build complete: dist/FederalExam.app"
