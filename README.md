# IndiaMART Lead Scraper & Manager

An advanced, anti-bot-protected, dual-mode lead management and scraping system for the IndiaMART Seller Lead Manager. It supports a **PyQt6 Desktop GUI Application** with an embedded Chromium engine, as well as a **Playwright CLI Scraper** optimized for headless server deployments.

---

## 🚀 Key Features

* **Dual Interface**:
  * **Desktop GUI App**: Built with `PyQt6` and `QtWebEngine` (Chromium). Allows you to monitor stats, interact with the browser directly, log in securely, and run scraping processes in a background thread.
  * **Headless CLI Version**: Built with `Playwright`. Ideal for cron jobs, terminal runs, or headless Linux servers.
* **🛡️ Built-in Anti-Bot & Account Safety Protection**:
  * **Human-like Interactions**: Uses coordinate-based mouse click emulation (`mousedown`, `mouseup`, `click` events) to pass anti-bot heuristics.
  * **Randomized Delays**: Automatically waits between **10 to 20 seconds** (configurable) between scraping leads.
  * **Dynamic Date Filtering**: Automates selecting "Custom Date" on the IndiaMART filter panel, reducing page requests by focusing only on unscraped target windows.
* **📊 Data Persistence & Auto-Exports**:
  * **SQLite Backend**: Saves lead data locally in `indiamart_leads.db` to prevent double-scraping.
  * **Spreadsheet Auto-Sync**: Automatically exports and keeps `indiamart_leads.xlsx` and `indiamart_leads.csv` updated in real-time.
* **🔑 Persistent Login**: Chromium profiles are saved locally, meaning you only need to sign in once.

---

## 📂 Project Structure

```
├── app/                  # Desktop GUI application source code (PyQt6)
│   ├── assets/           # App icons and media assets
│   ├── js_bridge.py      # JavaScript-to-Python WebEngine bridge with click/visibility utils
│   ├── main.py           # GUI application entry point
│   ├── main_window.py    # Main window UI and signal bindings
│   └── scrape_worker.py  # Background scraper thread logic
├── Linux/                # Optimized Linux environment resources (tested on Zorin OS)
│   ├── app/              # Linux app source mirror
│   ├── setup.sh          # Linux prerequisites and graphics library installer
│   ├── run.sh            # Linux launcher script
│   └── PKGBUILD          # Arch Linux / AUR package configuration
├── scraper.py            # Playwright CLI script (Windows / general)
├── config.py             # Centralized settings (selectors, delays, database paths)
├── db_manager.py         # SQLite database schema and query interface
├── build_windows.py      # PyInstaller script to compile the Windows .exe
└── requirements.txt      # Python dependencies
```

---

## 🛠️ Windows Installation & Usage

### Option A: Compiled Executable (GUI)
Simply run the pre-built application:
1. Navigate to `dist/IndiaMartScraper/`.
2. Run `IndiaMartScraper.exe`.

### Option B: Run from Source (Python)
1. **Clone & Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the Desktop GUI App**:
   ```bash
   python app/main.py
   ```
3. **Run the CLI Playwright Scraper**:
   ```bash
   # Install Playwright browsers first
   playwright install chromium
   
   # Launch scraping
   python scraper.py
   ```

---

## 🐧 Linux Installation & Usage (e.g., Zorin OS / Ubuntu)

An automated suite is available in the `Linux/` folder to configure native graphics libraries and virtual environments:

1. **Navigate to the Linux directory**:
   ```bash
   cd Linux
   ```
2. **Configure dependencies & permissions**:
   ```bash
   chmod +x setup.sh run.sh build_linux.sh build_appimage.sh build_deb.sh
   ./setup.sh
   ```
3. **Run the desktop app**:
   ```bash
   ./run.sh
   ```
4. **Compile & Package (AppImage or Debian package)**:
   * **To build a standalone `.AppImage`**:
     ```bash
     ./build_appimage.sh
     ```
     This generates `IndiaMartScraper-x86_64.AppImage` which runs directly.
   * **To build a `.deb` installer**:
     ```bash
     ./build_deb.sh
     ```
     This generates `indiamart-scraper_1.0.0_amd64.deb` for native system-wide installation.

> [!IMPORTANT]
> **Linux Power & Sleep Settings**: Linux desktops (like Zorin/Ubuntu GNOME) suspend GPU/UI rendering when the session locks. This freezes Chromium automation.
> * Set **Screen Blank** to **Never**.
> * Set **Automatic Suspend** to **Off**.
> * Set **Automatic Screen Lock** to **Off**.
> * To turn off the display safely, simply turn off your physical monitor's power button.

---

## ⚙️ Configuration & Customization

You can customize the scraping behavior directly in the [config.py](config.py) file:

| Setting | Default Value | Description |
| :--- | :--- | :--- |
| `MIN_DELAY` | `10` | Minimum anti-bot wait delay between lead interactions (seconds) |
| `MAX_DELAY` | `20` | Maximum anti-bot wait delay between lead interactions (seconds) |
| `DB_PATH` | `"indiamart_leads.db"` | SQLite database file location |
| `EXCEL_PATH` | `"indiamart_leads.xlsx"`| Auto-updated Excel spreadsheet path |
| `CSV_PATH` | `"indiamart_leads.csv"` | Auto-updated CSV path |

---

## 📝 Scraping Workflow

1. **Embedded login**: Log in to your seller panel in the embedded Chromium view.
2. **Navigate**: Go to the **Lead Manager** or **Messages** dashboard page.
3. **Scrape**: Click the **Start Scrape** button.
4. **Automation Flow**:
   * App opens the filters tab.
   * Checks if "Custom Date" filter is already active.
   * Inputs the target start and end dates in the calendar picker.
   * Clicks Apply, and scrolls the contact lists to parse detailed lead info from the modals.
