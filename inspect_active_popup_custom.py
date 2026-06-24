import os
import sys
from playwright.sync_api import sync_playwright
import config

def inspect_custom_date():
    print("=" * 60)
    print("      INDIAMART CUSTOM DATE FIELD INSPECTOR")
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
            # Let's target the Date dropdown (the one next to 'Date :')
            # The dropdown has class 'drpdwn' and is in the 'Date' container
            # Sibling to the 'Date :' text label
            date_dropdown = page.locator("xpath=//div[contains(., 'Date :') and contains(@class, 'mb0') or contains(@class, 'brdr_btm')]//span[contains(@class, 'drpdwn')]").first
            date_dropdown.click(timeout=5000)
            print("[+] Date dropdown clicked.")
        except Exception as e:
            print(f"[!] Direct date dropdown click failed: {e}")
            try:
                # Try simple click on "Select Date"
                page.locator("text=Select Date").first.click(timeout=5000)
                print("[+] Clicked via 'Select Date' text.")
            except Exception as e2:
                print(f"[!] Click 'Select Date' failed: {e2}")
                input("Please click the Date dropdown manually, then press ENTER...")
                
        page.wait_for_timeout(1000)
        
        print("[*] Selecting 'Custom Date' option...")
        try:
            # Let's locate the 'Custom Date' option in the list
            custom_date_opt = page.locator("text=Custom Date").first
            custom_date_opt.click(timeout=5000)
            print("[+] 'Custom Date' option clicked.")
        except Exception as e:
            print(f"[!] Selecting 'Custom Date' failed: {e}")
            input("Please click 'Custom Date' option manually in the browser, then press ENTER...")
            
        page.wait_for_timeout(2000)
        
        # Now let's dump the updated filter popup HTML
        popup = page.locator("#filterPopup").first
        if popup.count() > 0:
            outer_html = popup.evaluate("el => el.outerHTML")
            with open("active_filter_popup_custom.html", "w", encoding="utf-8") as f:
                f.write(outer_html)
            print(f"[+] Custom Date filter popup HTML saved to: {os.path.abspath('active_filter_popup_custom.html')}")
            
            # Print analysis of new input fields
            print("\n[*] Analyzing newly appeared input fields inside the popup:")
            elements = popup.evaluate("""el => {
                const results = [];
                const inputs = el.querySelectorAll('input');
                for (const input of inputs) {
                    const style = window.getComputedStyle(input);
                    const rect = input.getBoundingClientRect();
                    results.push({
                        tagName: 'input',
                        id: input.id,
                        className: input.className,
                        type: input.getAttribute('type') || '',
                        placeholder: input.getAttribute('placeholder') || '',
                        value: input.value,
                        visible: rect.width > 0 && rect.height > 0 && style.display !== 'none'
                    });
                }
                return results;
            }""")
            
            for idx, item in enumerate(elements):
                print(f"    [{idx+1}] <input> id='{item['id']}' | class='{item['className']}' | type='{item['type']}' | placeholder='{item['placeholder']}' | value='{item['value']}' | visible={item['visible']}")
                
            # Let's print parent container info for inputs
            print("\n[*] Parent structures containing input fields:")
            parent_details = popup.evaluate("""el => {
                const results = [];
                const inputs = el.querySelectorAll('input');
                for (const input of inputs) {
                    let parent = input.parentElement;
                    results.push({
                        inputClass: input.className,
                        parentTag: parent.tagName.toLowerCase(),
                        parentClass: parent.className,
                        parentHTML: parent.outerHTML.substring(0, 200).replace(/\\n/g, ' ')
                    });
                }
                return results;
            }""")
            for idx, item in enumerate(parent_details):
                print(f"    [{idx+1}] InputClass: '{item['inputClass']}' | Parent: <{item['parentTag']}> class='{item['parentClass']}' | Snippet: {item['parentHTML']}")
        else:
            print("[-] Could not find #filterPopup in DOM.")
            
        context.close()

if __name__ == "__main__":
    inspect_custom_date()
