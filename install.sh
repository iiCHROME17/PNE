#!/usr/bin/env bash
# Install PNE dependencies (Linux/macOS)
set -e

echo "Installing Python dependencies..."
pip3 install -r "$(dirname "$0")/requirements.txt"
echo "Done."
