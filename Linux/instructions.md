# IndiaMART Scraper - Quick Setup & Run Instructions

This guide provides a quick summary of how to set up, run, and optimize the IndiaMART Desktop App on Linux (Zorin OS 18).

---

## 1. Automated Scripts Provided

We have created two automated bash scripts inside the `Linux` folder:
* **`setup.sh`**: Installs graphical system dependencies, creates a Python virtual environment (`venv`), and installs PyQt6/WebEngine dependencies.
* **`run.sh`**: Activates the virtual environment, launches the desktop app dashboard, and deactivates the virtual environment when finished.

---

## 2. Quick Setup & Run Steps

Open a terminal in the `Linux` folder and execute the following commands:

```bash
# Step 1: Install Python3 virtual environment package (if not installed)
sudo apt update && sudo apt install -y python3-venv python3-pip

# Step 2: Make the automated scripts executable
chmod +x setup.sh run.sh

# Step 3: Run the setup script to install all dependencies
./setup.sh

# Step 4: Start the desktop application
./run.sh
```

---

## 3. App Controls & Anti-Bot Safety Limits
To safeguard your paid seller account:
* **Pre-Launch Safety Dialog**: Shown on the first run. Check the box and accept to proceed.
* **8-Hour Daily Limit**: Scraping automatically restricts itself to **8 hours max per day**, running only during daylight hours in your local region (calculated dynamically).
* **15-30s Delay**: Safe randomized delays are enforced between lead clicks to mimic human speeds.
* **Incremental Mode**: Historical leads are cached once. Subsequent runs scan only the current ongoing month to minimize risk.

---

## 4. Zorin OS System Optimizations (Screen Lock & Sleep)

Because the scraper operates inside the GUI window, Zorin OS must continue to draw the graphical interface. **If Zorin OS locks or suspends, the scraper will freeze.**

### Required Changes in Zorin Settings:
1. Open **Settings** -> **Power**:
   * Set **Screen Blank** to **Never**.
   * Set **Automatic Suspend** to **Off**.
2. Open **Settings** -> **Privacy** -> **Screen Lock** (or Screen):
   * Set **Automatic Screen Lock** to **Off**.
3. **Turn off the screen safely:** Do not lock the session (`Super + L`) or let the machine sleep. Instead, simply **turn off the physical power button on your monitor**. The computer will stay awake, rendering the browser page in the background, allowing the script to scrape continuously.

---

## 5. Output and Data Files
* **`indiamart_leads.db`**: SQLite Database.
* **`indiamart_leads.xlsx`** & **`indiamart_leads.csv`**: Spreadsheet files, updated after every successful lead.
* **`.gui_chrome_session/`**: Persistent Chromium browser profile (keeps you logged in).
