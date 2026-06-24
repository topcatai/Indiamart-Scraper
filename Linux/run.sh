#!/bin/bash
# IndiaMART Scraper Linux Run Script

echo "=========================================================="
echo "          Starting IndiaMART Scraper..."
echo "=========================================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "[!] Error: Virtual environment (venv) not found."
    echo "    Please run the setup script first: ./setup.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Execute scraper script (GUI mode by default, CLI mode if --cli passed)
if [[ "$*" == *"--cli"* ]]; then
    echo "[*] Running in CLI mode..."
    # Filter out --cli argument and pass remaining to scraper.py
    args=()
    for arg in "$@"; do
        if [ "$arg" != "--cli" ]; then
            args+=("$arg")
        fi
    done
    python3 scraper.py "${args[@]}"
else
    echo "[*] Running in GUI Desktop App mode..."
    python3 -m app.main
fi

# Deactivate virtual environment when scraper exits
deactivate
