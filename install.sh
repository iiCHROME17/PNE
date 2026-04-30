#!/usr/bin/env bash
# Install PNE dependencies (Linux/macOS)
set -e

echo "Installing Python dependencies..."
pip3 install -r "$(dirname "$0")/requirements.txt"

echo ""
echo "Checking Ollama..."
if ! command -v ollama &>/dev/null; then
    echo "WARNING: Ollama not found in PATH."
    echo "Download and install it from https://ollama.com before running the server."
else
    echo "Ollama found. Pulling model qwen2.5:3b..."
    ollama pull qwen2.5:3b
fi

echo ""
echo "Done."
