#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install -r requirements-build.txt
python3 -m PyInstaller FederalExam-mac.spec --noconfirm --clean

echo "Build complete: dist/FederalExam.app"
