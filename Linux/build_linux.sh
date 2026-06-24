#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "[*] Checking for PyInstaller..."
if ! command -v pyinstaller &> /dev/null; then
    echo "[!] Error: pyinstaller command not found."
    echo "    Please install it locally or compile in an offline environment with PyInstaller present."
    exit 1
fi
echo "[+] PyInstaller found."


# Run PyInstaller
# On Linux, path separator for add-data is colon ':'
echo "[*] Packaging application with PyInstaller..."
pyinstaller --noconfirm --onedir --windowed \
    --name=IndiaMartScraper \
    --add-data="app/styles.qss:app" \
    --add-data="app/assets/icon.png:app/assets" \
    --clean \
    app/main.py

echo "=============================================="
echo "[+] Linux build completed successfully!"
echo "Output directory: dist/IndiaMartScraper/"
echo "=============================================="
