@echo off
REM Install PNE dependencies (Windows)

echo Installing Python dependencies...
pip install -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo.
    echo pip failed. Trying pip3...
    pip3 install -r "%~dp0requirements.txt"
    if %errorlevel% neq 0 (
        echo ERROR: Could not install Python dependencies. Is Python installed?
        pause
        exit /b 1
    )
)

echo.
echo Checking Ollama...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Ollama not found in PATH.
    echo Download and install it from https://ollama.com before running the server.
) else (
    echo Ollama found. Pulling model qwen2.5:3b...
    ollama pull qwen2.5:3b
)

echo.
echo Done.
pause
