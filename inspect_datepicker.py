import os
import sys
from playwright.sync_api import sync_playwright
import config

def inspect_datepicker():
    print("=" * 60)
    print("      INDIAMART DATEPICKER OVERLAY INSPECTOR")
    print("=" * 60)
    
    with sync_playwright() as p:
        print("[*] Launching Chromium browser with persistent profile...")
        os.makedirs(config.CHROME_PROFILE_DIR, exist_ok=True)
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=config.CHROME_PROFILE_DIR,
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--excludeSwitches=enable-automation"
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="Asia/Kolkata",
            no_viewport=True,
            slow_mo=100
        )
        
        page = context.pages[0]
        page.goto(config.START_URL)
        
        print("\n" + "!" * 80)
        print(" ACTION REQUIRED:")
        print(" 1. Ensure you are logged into your IndiaMART account.")
        print(" 2. Load the Lead Manager (All Contacts) screen.")
        print(" 3. Once you see the contact lists, press ENTER in this terminal.")
        print("!" * 80 + "\n")
        
        input("Press [ENTER] when you have loaded the Lead Manager...")
        
        print("\n[*] Opening filter popup...")
        try:
            page.locator("#filterCTA").first.click(timeout=5000)
            page.wait_for_timeout(1000)
            
            page.locator("#filterPopup span[title='Filters']").first.click(timeout=5000)
            page.wait_for_timeout(1000)
            print("[+] Filters tab opened.")
        except Exception as e:
            print(f"[!] Error opening filters: {e}")
            input("Please open Filters tab manually, then press ENTER...")
            
        print("[*] Clicking Date dropdown...")
        try:
            page.locator("xpath=//div[contains(., 'Date :') and (contains(@class, 'mb0') or contains(@class, 'brdr_btm'))]//span[contains(@class, 'drpdwn')]").first.click(timeout=5000)
            page.wait_for_timeout(1000)
            print("[+] Date dropdown clicked.")
        except Exception as e:
            print(f"[!] Click date dropdown failed: {e}")
            input("Please click Date dropdown manually, then press ENTER...")
            
        print("[*] Selecting 'Custom Date' option...")
        try:
            page.locator("text=Custom Date").first.click(timeout=5000)
            page.wait_for_timeout(2000)
            print("[+] 'Custom Date' selected.")
        except Exception as e:
            print(f"[!] Custom Date select failed: {e}")
            input("Please select 'Custom Date' manually, then press ENTER...")
            
        print("[*] Clicking '#custom_date_start' to trigger datepicker calendar...")
        try:
            page.locator("#custom_date_start").click(timeout=5000)
            print("[+] '#custom_date_start' clicked.")
        except Exception as e:
            print(f"[!] Clicking '#custom_date_start' failed: {e}")
            input("Please click the Start Date field manually in the browser, then press ENTER...")
            
        page.wait_for_timeout(2000)
        
        # Dump the entire page body HTML
        body_html = page.locator("body").evaluate("el => el.innerHTML")
        with open("datepicker_body.html", "w", encoding="utf-8") as f:
            f.write(body_html)
        print(f"[+] Full body HTML (with active datepicker) saved to: {os.path.abspath('datepicker_body.html')}")
        
        # Check if there are any datepicker elements in the body
        # Let's search for typical calendar classes (e.g. react-calendar, DayPicker, calendar, Mui, flatpickr, datepicker)
        import re
        calendar_keywords = ['calendar', 'datepicker', 'daypicker', 'month', 'year', 'date-picker', 'flatpickr', 'MuiPickers']
        print("\n[*] Checking for calendar-related keywords in the DOM:")
        for kw in calendar_keywords:
            matches = len(re.findall(kw, body_html, re.IGNORECASE))
            print(f"  Keyword '{kw}': {matches} occurrence(s)")
            
        context.close()

if __name__ == "__main__":
    inspect_datepicker()
