#!/bin/bash
# Debian Package Builder for IndiaMART Scraper
# Run this on a Debian-based Linux system (Debian, Ubuntu, Mint, Zorin OS, etc.)

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo "          Debian Package Builder (.deb)"
echo "=========================================================="
echo ""

# Check for dpkg-deb command
if ! command -v dpkg-deb &> /dev/null; then
    echo "[!] Error: dpkg-deb command not found."
    echo "    This packager script must be run on a Debian/Ubuntu-based system."
    exit 1
fi

# 1. Build PyInstaller binary if it doesn't exist
echo "[*] Ensuring PyInstaller binary is compiled..."
if [ ! -f "../dist/IndiaMartScraper/IndiaMartScraper" ]; then
    echo "    Binary not found. Compiling via build_linux.sh..."
    if [ -f "../build_linux.sh" ]; then
        chmod +x ../build_linux.sh
        ../build_linux.sh
    else
        echo "[!] Error: build_linux.sh not found in parent directory."
        exit 1
    fi
else
    echo "    [+] Found existing PyInstaller binary."
fi

# 2. Setup build folder
BUILD_DIR="deb_build_temp"
echo "[*] Setting up temporary build directory: $BUILD_DIR..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/indiamart-scraper"
mkdir -p "$BUILD_DIR/usr/share/applications"

# 3. Copy debian packaging files
echo "[*] Copying package configuration files..."
cp -rf debian-pkg/DEBIAN/* "$BUILD_DIR/DEBIAN/"
cp -rf debian-pkg/usr/* "$BUILD_DIR/usr/"

# 4. Copy the compiled application binary and directory structure
echo "[*] Copying PyInstaller compilation output to /opt..."
cp -rf ../dist/IndiaMartScraper/* "$BUILD_DIR/opt/indiamart-scraper/"

# 5. Fix permissions (crucial for debian packaging)
echo "[*] Setting permissions on packaging files..."
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/postrm"
find "$BUILD_DIR" -type d -exec chmod 755 {} \;
find "$BUILD_DIR" -type f -exec chmod 644 {} \;
chmod 755 "$BUILD_DIR/opt/indiamart-scraper/IndiaMartScraper"
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# 6. Build the package
PACKAGE_NAME="indiamart-scraper_1.0.0_amd64.deb"
echo "[*] Generating package: $PACKAGE_NAME..."
dpkg-deb --build "$BUILD_DIR" "$PACKAGE_NAME"

# 7. Cleanup
rm -rf "$BUILD_DIR"

echo ""
echo "=========================================================="
echo "[+] Debian package built successfully!"
echo "    File: Linux/$PACKAGE_NAME"
echo "    Install via: sudo dpkg -i $PACKAGE_NAME"
echo "=========================================================="
