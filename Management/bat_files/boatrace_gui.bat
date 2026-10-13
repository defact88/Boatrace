@echo off

if not "%~1"=="minimized" (
    start /min cmd /c "%~f0" minimized %*
    exit /b
)

python "C:\boatrace\UI\boatrace_gui.py"

if %errorlevel% neq 0 (
    @echo on
    pause
)