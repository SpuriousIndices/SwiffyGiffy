@echo off
setlocal
echo ============================================================
echo   Building SwiffyGiffy Standalone Executable (.exe)
echo ============================================================

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    py -3 -m venv .venv
)

echo Installing / verifying dependencies...
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

echo Running PyInstaller build...
.\.venv\Scripts\python.exe build_exe.py

echo.
echo Build finished! Check the dist\SwiffyGiffy.exe file.
pause

