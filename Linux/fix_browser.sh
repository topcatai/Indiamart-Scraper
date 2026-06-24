#!/bin/bash
echo "=========================================================="
echo "    IndiaMART Scraper - Browser Fix Script"
echo "=========================================================="
echo ""

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHROME_SESSION="$SCRIPT_DIR/.chrome_session"
CURRENT_USER="$(whoami)"

echo "[1/6] Force-killing any running Chromium/Chrome/Python processes..."
sudo pkill -9 -f chromium 2>/dev/null
sudo pkill -9 -f chrome 2>/dev/null
sudo pkill -9 -f playwright 2>/dev/null
sudo pkill -9 -f "python3.*scraper" 2>/dev/null
sleep 2
echo "      Done."
echo ""

echo "[2/6] Deleting stale Chrome session directory..."
if [ -d "$CHROME_SESSION" ]; then
    rm -rf "$CHROME_SESSION"
    echo "      Removed: $CHROME_SESSION"
else
    echo "      Not found (OK): $CHROME_SESSION"
fi
echo ""

echo "[3/6] Cleaning Chromium temp/lock files from /tmp/..."
rm -rf /tmp/org.chromium.Chromium.* 2>/dev/null
rm -rf /tmp/.org.chromium.* 2>/dev/null
rm -rf /tmp/playwright* 2>/dev/null
rm -rf /tmp/.com.google.Chrome.* 2>/dev/null
echo "      Done."
echo ""

echo "[4/6] Cleaning root-owned temp files (requires sudo)..."
sudo rm -rf /tmp/org.chromium.Chromium.* 2>/dev/null
sudo rm -rf /tmp/.org.chromium.* 2>/dev/null
sudo rm -rf /tmp/playwright* 2>/dev/null
sudo rm -rf /tmp/.com.google.Chrome.* 2>/dev/null
echo "      Done."
echo ""

echo "[5/6] Fixing folder ownership (setting to $CURRENT_USER)..."
sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$SCRIPT_DIR"
echo "      Done: $SCRIPT_DIR"
echo ""

echo "[6/6] Fixing database file permissions..."
if [ -f "$SCRIPT_DIR/indiamart_leads.db" ]; then
    chmod 666 "$SCRIPT_DIR/indiamart_leads.db"
    echo "      Fixed: indiamart_leads.db"
fi
if [ -f "$SCRIPT_DIR/indiamart_leads.xlsx" ]; then
    chmod 666 "$SCRIPT_DIR/indiamart_leads.xlsx"
    echo "      Fixed: indiamart_leads.xlsx"
fi
if [ -f "$SCRIPT_DIR/indiamart_leads.csv" ]; then
    chmod 666 "$SCRIPT_DIR/indiamart_leads.csv"
    echo "      Fixed: indiamart_leads.csv"
fi
echo ""

echo "=========================================================="
echo "    All fixes applied!"
echo ""
echo "    NOW RUN (without sudo):"
echo "      ./run.sh"
echo ""
echo "    DO NOT use 'sudo ./run.sh'"
echo "=========================================================="
