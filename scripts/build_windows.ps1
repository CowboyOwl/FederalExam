$ErrorActionPreference = "Stop"

python -m pip install -r requirements-build.txt
python -m PyInstaller FederalExam.spec --noconfirm --clean

Write-Host "Build complete: dist\FederalExam\FederalExam.exe"
