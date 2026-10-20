@echo off
setlocal

cd /d "%~dp0..\src"

if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)

call ".venv\Scripts\activate.bat"

python -m pip install --upgrade pip
pip install -r ..\requirements-build.txt
python -c "import os; [os.makedirs(d, exist_ok=True) for d in ('logs', 'media', 'static')]"

pyinstaller --clean --noconfirm bulk_emailer.spec

echo Build complete: %~dp0..\src\dist\bulk_emailer.exe

endlocal
