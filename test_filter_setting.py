import os
import re
import sys
from playwright.sync_api import sync_playwright
import datetime
import config

def test_filter():
    print("=" * 60)
    print("      INDIAMART CUSTOM DATE FILTER TESTER")
    print("=" * 60)
    
    # Test dates: July 13, 2020 to July 19, 2020
    start_date = datetime.date(2020, 7, 13)
    end_date = datetime.date(2020, 7, 19)
    
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
        
        try:
            # 1. Click filter icon if popup is not already visible
            filter_popup = page.locator("#filterPopup").first
            if not filter_popup.is_visible():
                print("[*] Clicking filter icon #filterCTA...")
                page.locator("#filterCTA").first.click(timeout=10000)
                page.wait_for_timeout(1000)
                
            # 2. Click "Filters" tab
            filters_tab = page.locator("#filterPopup span[title='Filters']").first
            filters_tab.click(timeout=5000)
            page.wait_for_timeout(1000)
            
            # 3. Click Date dropdown
            date_dropdown = page.locator("xpath=//div[contains(., 'Date :') and (contains(@class, 'mb0') or contains(@class, 'brdr_btm'))]//span[contains(@class, 'drpdwn')]").first
            date_dropdown.click(timeout=5000)
            page.wait_for_timeout(1000)
            
            # 4. Click 'Custom Date' option
            custom_date_option = page.locator("text=Custom Date").first
            custom_date_option.click(timeout=5000)
            page.wait_for_timeout(1500)
            
            # 5. Click Start Date span target to activate start datepicker
            start_target = page.locator("#custom_date_start").first
            start_target.click(timeout=5000)
            page.wait_for_timeout(1000)
            
            # 6. Select start year and month
            start_month_val = str(start_date.month - 1)
            start_year_val = str(start_date.year)
            
            print(f"[*] Selecting start year {start_year_val} and month index {start_month_val}...")
            page.locator("#customDatePicker .rdrYearPicker select").first.select_option(start_year_val)
            page.wait_for_timeout(500)
            page.locator("#customDatePicker .rdrMonthPicker select").first.select_option(start_month_val)
            page.wait_for_timeout(1000)
            
            # 7. Click start day button (excluding passive days)
            start_day_str = str(start_date.day)
            print(f"[*] Clicking start day {start_day_str}...")
            start_day_locator = page.locator("#customDatePicker button.rdrDay:not(.rdrDayPassive)").filter(
                has_text=re.compile(rf"^\s*{start_day_str}\s*$")
            ).first
            start_day_locator.click(timeout=5000)
            page.wait_for_timeout(1000)
            
            # 8. Click End Date span target to ensure it is active
            end_target = page.locator("#custom_date_end").first
            end_target.click(timeout=5000)
            page.wait_for_timeout(1000)
            
            # 9. Select end year and month
            end_month_val = str(end_date.month - 1)
            end_year_val = str(end_date.year)
            
            print(f"[*] Selecting end year {end_year_val} and month index {end_month_val}...")
            page.locator("#customDatePicker .rdrYearPicker select").first.select_option(end_year_val)
            page.wait_for_timeout(500)
            page.locator("#customDatePicker .rdrMonthPicker select").first.select_option(end_month_val)
            page.wait_for_timeout(1000)
            
            # 10. Click end day button (excluding passive days)
            end_day_str = str(end_date.day)
            print(f"[*] Clicking end day {end_day_str}...")
            end_day_locator = page.locator("#customDatePicker button.rdrDay:not(.rdrDayPassive)").filter(
                has_text=re.compile(rf"^\s*{end_day_str}\s*$")
            ).first
            end_day_locator.click(timeout=5000)
            page.wait_for_timeout(1000)
            
            # 11. Click Apply button in the filter popup
            print("[*] Clicking Apply button...")
            apply_btn = page.locator("#filterPopup div.small_btn_filled_std", has_text="Apply").first
            apply_btn.click(timeout=5000)
            page.wait_for_timeout(2000)
            print("[+] Custom date filter applied successfully!")
            
        except Exception as e:
            print(f"[!] Error: {e}")
            import traceback
            traceback.print_exc()
            
        input("Press ENTER to close browser...")
        context.close()

if __name__ == "__main__":
    test_filter()
