@echo off
title PNE Server

:: Start Ollama if not already running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if errorlevel 1 (
    echo [PNE] Starting Ollama...
    start "Ollama" ollama serve
    timeout /t 4 /nobreak >nul
) else (
    echo [PNE] Ollama already running.
)

:: Ensure model is available
echo [PNE] Checking model qwen2.5:3b...
ollama pull qwen2.5:3b

:: Start uvicorn from Models directory
cd /d "D:\Programming\PNE (Github)\cs3ip\Models"
echo [PNE] Starting API server on port 8000...
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
