#!/bin/bash
# Unified Linux Desktop Installer for IndiaMART Scraper
# Targets Debian, Arch, Fedora, and their forks.

# Exit immediately if a command exits with a non-zero status
set -e

INSTALL_DIR="$HOME/.local/share/indiamart-scraper"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "=========================================================="
echo "          IndiaMART Scraper Desktop Installer"
echo "=========================================================="
echo ""

# 1. Create installation directories
echo "[*] Creating local application directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# 2. Copy code files (excluding database/temporary files)
echo "[*] Copying application files..."
cp -rf config.py db_manager.py scraper.py requirements.txt app "$INSTALL_DIR/"

# 3. Create run.sh inside installation folder
cat << 'EOF' > "$INSTALL_DIR/run.sh"
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$DIR/venv/bin/activate"
python3 -m app.main "$@"
deactivate
EOF
chmod +x "$INSTALL_DIR/run.sh"

# 4. Setup virtual environment inside install directory
echo "[*] Setting up Python virtual environment..."
rm -rf "$INSTALL_DIR/venv"
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$INSTALL_DIR/requirements.txt"
deactivate

# 5. Create desktop entry launcher
echo "[*] Registering application launcher in desktop menu..."
cat <<EOF > "$DESKTOP_DIR/indiamart-scraper.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=IndiaMART Lead Scraper
Comment=Scrape and manage IndiaMART leads
Exec="$INSTALL_DIR/run.sh"
Icon=$INSTALL_DIR/app/styles.qss
Terminal=false
Categories=Office;Business;
StartupNotify=true
EOF

chmod +x "$DESKTOP_DIR/indiamart-scraper.desktop"

echo ""
echo "=========================================================="
echo "[+] Installation completed successfully!"
echo "    The 'IndiaMART Lead Scraper' icon is now available"
echo "    in your system's application menu."
echo "    You can launch it directly by clicking on the icon."
echo "=========================================================="
