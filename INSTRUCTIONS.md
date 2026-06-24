# IndiaMART Lead Scraper - Operating Instructions

This manual explains how to run, compile, and operate both the **Windows** and **Linux** versions of the IndiaMART Lead Scraper (GUI and CLI).

---

## 💻 Windows Build & Operations

### 1. Running the Pre-built GUI Application
We have pre-compiled the GUI application into a standalone folder using PyInstaller:
1. Navigate to: `dist/IndiaMartScraper/`
2. Launch: **`IndiaMartScraper.exe`**

### 2. Operating the GUI Scraper
1. **First Launch (Safety Dialog)**: Read and accept the Pre-Launch Safety Guidelines.
2. **Embedded Login**: The browser panel on the right will display the IndiaMART Seller page. Log in using your mobile number/password.
3. **Navigate to Lead Manager**:
   * Click **Lead Manager** or **Messages** in the sidebar.
   * Make sure the left panel (leads list) and right panel (lead details) are fully loaded.
4. **Trigger Scraping**:
   * Click the **Start Scrape** button on the left panel of the desktop application.
   * The scraper will open the filters menu, select "Custom Date", set the date window (starting from your last scraped lead or a custom date), apply the filter, and begin parsing contacts.
5. **Monitoring & Exports**:
   * Watch progress and log console updates in real-time.
   * Data is automatically saved to the SQLite database (`indiamart_leads.db`) and exported to `indiamart_leads.xlsx` and `indiamart_leads.csv` in the app directory.

### 3. Rebuilding the Windows Binary
If you modify the source code and want to compile a new `.exe`:
```bash
pip install -r requirements.txt
python build_windows.py
```
The new build will be generated in `dist/IndiaMartScraper/`.

---

## 🐧 Linux Build & Operations (Zorin OS / Ubuntu / Debian)

Because PyInstaller cannot cross-compile across different operating systems, the Linux binary must be built on your Linux machine.

### 1. Setting up & Running from Source
1. Open a terminal in the `Linux/` folder.
2. Make scripts executable and run the setup script (which installs required system graphics libraries for Chromium, creates a virtual environment, and installs dependencies):
   ```bash
   chmod +x setup.sh run.sh
   ./setup.sh
   ```
3. Run the GUI application:
   ```bash
   ./run.sh
   ```

### 2. Compiling the Linux Binary & building a Debian Package (.deb)
To package the app as a native `.deb` installer on Linux:
1. Make the build scripts executable:
   ```bash
   chmod +x build_linux.sh build_deb.sh
   ```
2. Run the Debian packager:
   ```bash
   ./build_deb.sh
   ```
This will compile the application via PyInstaller and pack it into a Debian installer: `Linux/indiamart-scraper_1.0.0_amd64.deb`.
3. To install it system-wide:
   ```bash
   sudo dpkg -i indiamart-scraper_1.0.0_amd64.deb
   ```

---

## 🖥️ Command Line (CLI) headless operation

If you want to run the scraper in headless mode (no GUI window) or on a remote Linux server:

### Windows CLI:
```bash
pip install playwright pandas openpyxl
playwright install chromium
python scraper.py
```

### Linux CLI:
```bash
cd Linux
python3 -m venv venv
source venv/bin/activate
pip install playwright pandas openpyxl
playwright install chromium
python scraper.py
```

---

## 🛡️ Critical Performance & Anti-Bot Tips

* **Screen Lock (Linux)**: Do **not** lock the screen (`Super + L`) or let the PC suspend/sleep while scraping. Locking the screen freezes Chromium graphics rendering, which halts Playwright/QtWebEngine interactions. Disable automatic screen lock and screen blanks in your system power settings, and turn off your physical monitor button instead.
* **Scraping Delays**: The scraper utilizes a safety sleep delay of **10 to 20 seconds** between lead scrapes. Do not attempt to reduce this further, as IndiaMART's server-side rate limits can flag rapid sequential clicks.
