#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display dialog "Python 3 est requis pour lancer FederalExam depuis le dossier source. Le navigateur va ouvrir la page de telechargement. Pour une utilisation sans Python, utilisez FederalExam.app." buttons {"OK"} default button "OK"' >/dev/null 2>&1 || true
  open "https://www.python.org/downloads/macos/"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Preparation de FederalExam..."
  python3 -m venv .venv
fi

source ".venv/bin/activate"

python - <<'PY'
import importlib.util
import subprocess
import sys

missing = [
    package
    for package in ("flask",)
    if importlib.util.find_spec(package) is None
]
if missing:
    print("Installation des dependances locales...")
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        "requirements.txt",
    ])
PY

echo "FederalExam demarre. Le navigateur va s'ouvrir automatiquement."
echo "Fermez cette fenetre pour arreter l'application."
python launcher.py
