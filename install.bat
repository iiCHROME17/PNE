@echo off
REM Install PNE dependencies (Windows)
echo Installing Python dependencies...
pip install -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo.
    echo pip failed. Trying pip3...
    pip3 install -r "%~dp0requirements.txt"
)
echo Done.
pause
