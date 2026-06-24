#!/bin/bash
# Zorin / Ubuntu AppImage Packager for IndiaMART Scraper
# Run this inside the Linux/ directory.

set -e

# 1. Check if venv exists
if [ ! -d "venv" ]; then
    echo "[!] Error: Virtual environment (venv) not found."
    echo "    Please run the setup script first: ./setup.sh"
    exit 1
fi

# 2. Activate virtual environment and ensure pyinstaller is installed
echo "[*] Activating virtual environment..."
source venv/bin/activate

echo "[*] Ensuring PyInstaller is installed in venv..."
pip install --upgrade pip
pip install pyinstaller

# 3. Compile the standalone binary via build_linux.sh
echo "[*] Compiling application using PyInstaller..."
chmod +x build_linux.sh
./build_linux.sh

# 4. Setup temporary AppDir structure
APPDIR="IndiaMartScraper.AppDir"
echo "[*] Setting up AppDir directory: $APPDIR..."
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy compiled files
cp -rf dist/IndiaMartScraper/* "$APPDIR/usr/bin/"
cp -f app/assets/icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/indiamart-scraper.png"
cp -f app/assets/icon.png "$APPDIR/indiamart-scraper.png"

# Create Desktop entry
cat << 'EOF' > "$APPDIR/indiamart-scraper.desktop"
[Desktop Entry]
Name=IndiaMART Lead Scraper
Exec=IndiaMartScraper
Icon=indiamart-scraper
Type=Application
Categories=Network;Utility;
Terminal=false
Comment=Advanced anti-bot lead scraper and manager
EOF

# Create AppRun script
cat << 'EOF' > "$APPDIR/AppRun"
#!/bin/sh
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/IndiaMartScraper" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# 5. Download appimagetool if not present
if [ ! -f "appimagetool" ]; then
    echo "[*] Downloading appimagetool..."
    wget -q https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-x86_64.AppImage -O appimagetool
    chmod +x appimagetool
fi

# 6. Generate the AppImage
echo "[*] Packaging into AppImage..."
export ARCH=x86_64
./appimagetool "$APPDIR" "IndiaMartScraper-x86_64.AppImage"

# Clean up
rm -rf "$APPDIR"

echo ""
echo "=========================================================="
echo "[+] AppImage built successfully!"
echo "    File: Linux/IndiaMartScraper-x86_64.AppImage"
echo "    Run it using: ./IndiaMartScraper-x86_64.AppImage"
echo "=========================================================="
