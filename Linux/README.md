# IndiaMART Desktop Scraper App - Linux (Zorin OS 18) Guide

This folder contains the files and automated helper scripts optimized for running the IndiaMART Desktop App on Linux, specifically tested on **Zorin OS 17/18** (which is built on Ubuntu/Debian).

---

## 1. Prerequisites

Before running the application, you must have Python 3, pip, and python3-venv installed on your Zorin OS system. Open a terminal in this folder and run:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

---

## 2. Quick Setup

We have provided a `setup.sh` script that automates the virtual environment creation and installs the graphical system library requirements for the embedded Chromium engine:

1. **Make the script executable:**
   ```bash
   chmod +x setup.sh
   ```
2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

### What this script does:
* Installs the system graphics libraries (like `libxcb`, `libxkbcommon`, `libegl`) required by Qt and Chromium WebEngine to run on Zorin OS.
* Creates a Python virtual environment (`venv`) to comply with PEP 668.
* Installs all Python dependencies (`PyQt6`, `PyQt6-WebEngine`, `pandas`, `openpyxl`).

---

## 3. How to Run the Application

Once setup is complete, you can launch the desktop application using the `run.sh` script:

1. **Make the script executable:**
   ```bash
   chmod +x run.sh
   ```
2. **Launch the application:**
   ```bash
   ./run.sh
   ```

### Scraping Walkthrough:
1. **Safety Dialog**: On the first launch, you must read and accept the Pre-Launch Safety Guidelines before the app opens.
2. **Embedded Login**: Log in manually to your IndiaMART account inside the embedded browser panel.
3. **Navigate**: Go to your **Lead Manager** dashboard inside the browser view (so the left contact list and right detail panel are loaded).
4. **Scrape**: Click **Start Scrape** on the left dashboard sidebar. The scraper thread runs in the background.
5. **Stats**: Monitor stats in real-time on the left sidebar.

### 🛡️ Built-in Safety & Compliance Rules
To safeguard your paid seller account from anti-bot detection systems:
* **Daylight Limit**: Scraping automatically randomizes and restricts itself to exactly **8 hours per day max**, running exclusively during daylight hours in your local region (calculated dynamically).
* **Speed Limits**: Random pauses of **15 to 30 seconds** are enforced between scraping actions to match human browsing speeds.
* **Risk Reduction**: Historical leads are scraped once and kept in the database. Subsequent runs will only scan the current ongoing month, minimizing requests and lowering operational risk.

---

## 4. Zorin OS Screen Lock & Sleep Optimizations

Since Zorin OS uses the GNOME desktop, it locks the screen and suspends the system after inactivity. 

**IMPORTANT: Do not lock the screen (`Super + L`) or let the PC go to sleep/hibernate while the scraper is actively running.**
* **Why?** Zorin OS suspends graphical UI rendering when the session is locked. Because the scraper drives the Chromium page inside the Qt window, suspending the graphics engine freezes the app's ability to click, scroll, or scrape.

### How to configure Zorin OS for uninterrupted scraping:
1. Open the **Settings** app in Zorin OS.
2. Select **Power** from the sidebar:
   * Set **Screen Blank** to **Never**.
   * Set **Automatic Suspend** to **Off**.
3. Select **Privacy -> Screen** (or Screen Lock):
   * Set **Automatic Screen Lock** to **Off**.
4. **Physical screen power:** Instead of locking the session, simply **turn off the physical monitor's power button**. The PC will stay fully awake and render the window in the background, allowing the script to scrape continuously and safely.

---

## 5. Output and Database Files

All files are created/updated locally in this `Linux` folder:
* **`indiamart_leads.db`**: SQLite database where all lead records are securely persisted.
* **`indiamart_leads.xlsx`** & **`indiamart_leads.csv`**: Exported spreadsheet sheets, automatically updated after every successful lead scrape.
* **`.gui_chrome_session/`**: Persistent Chromium folder storing your login state. You will not need to log in again on subsequent runs unless you manually delete this folder.

---

## 6. Feedback and Error Reporting
If you encounter any issues or errors while running the application, please report them to our Codeberg repository issue tracker by clicking the **🐞 Report an Error** button in the sidebar or visiting the issues page directly in your browser.
