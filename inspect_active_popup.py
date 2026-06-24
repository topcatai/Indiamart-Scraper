import os
import sys
from playwright.sync_api import sync_playwright
import config

def inspect_active_popup():
    print("=" * 60)
    print("         INDIAMART FILTER POPUP INSPECTOR")
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
        print(" 3. Once you see the contact lists and the filter icon on screen, press ENTER in this terminal.")
        print("!" * 80 + "\n")
        
        input("Press [ENTER] when you have loaded the Lead Manager in the browser...")
        
        print("\n[*] Clicking filter icon '#filterCTA'...")
        try:
            filter_icon = page.locator("#filterCTA").first
            filter_icon.click(timeout=5000)
            print("[+] Filter icon clicked.")
        except Exception as e:
            print(f"[!] Error clicking filter icon: {e}")
            print("[*] Fallback: trying to find filter icon by class or svg...")
            try:
                page.locator(".filtericon").first.click(timeout=5000)
                print("[+] Filter icon clicked via class fallback.")
            except Exception as e2:
                print(f"[!] Fallback failed: {e2}")
                input("Please click the filter icon manually in the browser, then press ENTER here...")
        
        page.wait_for_timeout(1000)
        
        print("[*] Switching to 'Filters' tab...")
        try:
            filters_tab = page.locator("span[title='Filters']").first
            filters_tab.click(timeout=5000)
            print("[+] Clicked 'Filters' tab.")
        except Exception as e:
            print(f"[!] Error clicking 'Filters' tab: {e}")
            input("Please click the 'Filters' tab manually, then press ENTER here...")
            
        page.wait_for_timeout(2000)
        
        # Now dump the popup HTML
        popup = page.locator("#filterPopup").first
        if popup.count() > 0:
            outer_html = popup.evaluate("el => el.outerHTML")
            with open("active_filter_popup.html", "w", encoding="utf-8") as f:
                f.write(outer_html)
            print(f"[+] Rendered filter popup HTML saved to: {os.path.abspath('active_filter_popup.html')}")
            
            # Print analysis of date dropdown and inputs
            print("\n[*] Analyzing DOM elements inside popup...")
            elements = popup.evaluate("""el => {
                const results = [];
                // Find all dropdowns/selects/inputs/spans/buttons
                const items = el.querySelectorAll('input, select, button, div.dropdown, div.select, span, div');
                for (const item of items) {
                    const text = item.innerText ? item.innerText.trim() : '';
                    const classList = item.className;
                    const id = item.id;
                    const placeholder = item.getAttribute('placeholder') || '';
                    const type = item.getAttribute('type') || '';
                    
                    // Only return significant elements to reduce output size
                    if (id || classList.includes('btn') || item.tagName.toLowerCase() === 'select' || item.tagName.toLowerCase() === 'input' || text.includes('Date') || text.includes('Apply')) {
                        results.push({
                            tagName: item.tagName.toLowerCase(),
                            id: id,
                            className: classList,
                            type: type,
                            placeholder: placeholder,
                            text: text.substring(0, 50).replace(/\\n/g, ' ')
                        });
                    }
                }
                return results;
            }""")
            
            for idx, item in enumerate(elements[:40]):
                print(f"    [{idx+1}] <{item['tagName']}> id='{item['id']}' | class='{item['className']}' | type='{item['type']}' | placeholder='{item['placeholder']}' | text='{item['text']}'")
        else:
            print("[-] Could not find #filterPopup in the DOM!")
            
        context.close()

if __name__ == "__main__":
    inspect_active_popup()
