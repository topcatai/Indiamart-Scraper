#!/bin/bash
# IndiaMART Scraper Linux (Zorin OS / Ubuntu) Setup Script

# Exit immediately if a command exits with a non-zero status
set -e

echo "=========================================================="
echo "          IndiaMART Scraper Linux Setup Script"
echo "=========================================================="
echo ""

# Step 1: Check Python installation
echo "[*] Checking Python3 installation..."
if ! command -v python3 &> /dev/null; then
    echo "[!] Error: python3 is not installed."
    echo "    Please run: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    exit 1
fi
echo "[+] Python3 is installed."

# Step 2: Install system libraries for Qt and QWebEngine (requires sudo)
echo "[*] Installing system dependencies for PyQt6/QtWebEngine (requires sudo)..."
sudo apt update

# Core graphical dependencies
sudo apt install -y libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-shm0 libxcb-sync1 libxcb-xfixes0 \
    libxcb-xinerama0 libxcb-xinput0 libegl1 libnss3 libnspr4 libdbus-1-3 \
    libfontconfig1 libxrandr2

# Try modern libgl1 first, fallback to older libgl1-mesa-glx
echo "[*] Installing OpenGL runtime dependency..."
sudo apt install -y libgl1 || sudo apt install -y libgl1-mesa-glx || echo "[!] Warning: OpenGL libs could not be installed."

# Try modern libasound2t64 first (Ubuntu 24.04+ / Zorin 18+), fallback to libasound2
echo "[*] Installing ALSA audio runtime dependency..."
sudo apt install -y libasound2t64 || sudo apt install -y libasound2 || echo "[!] Warning: Audio libs could not be installed."

# Step 3: Create Python Virtual Environment
echo "[*] Creating virtual environment (venv)..."
rm -rf venv
python3 -m venv venv
echo "[+] Virtual environment created successfully."

# Step 4: Install dependencies
echo "[*] Activating virtual environment and installing python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "[+] Python dependencies installed."

echo ""
echo "=========================================================="
echo "[+] Setup completed successfully!"
echo "    To run the app, execute: ./run.sh"
echo "=========================================================="
