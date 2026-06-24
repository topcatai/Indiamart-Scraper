import os
import sys
import shutil
import re
import datetime
from playwright.sync_api import sync_playwright

def run_test():
    print("=" * 60)
    print("   RUNNING AUTOMATED CUSTOM DATE FILTER TEST")
    print("=" * 60)

    # 1. Copy profile to avoid lock
    src_profile = ".gui_chrome_session"
    dst_profile = ".test_chrome_session"
    
    if os.path.exists(dst_profile):
        try:
            shutil.rmtree(dst_profile)
        except Exception as e:
            print(f"[-] Could not delete old test profile: {e}")
            
    print("[*] Copying Chrome profile for testing...")
    try:
        shutil.copytree(src_profile, dst_profile, ignore=shutil.ignore_patterns("SingletonLock", "Lock"))
    except Exception as e:
        print(f"[!] Warning copying profile (some files may be locked): {e}")

    with sync_playwright() as p:
        print("[*] Launching Chromium browser with test profile...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=dst_profile,
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
        
        # We navigate to the seller page. If logged in, it should load seller.indiamart.com/message
        # or we might need to go to messages/lead manager.
        print("[*] Navigating to IndiaMART Seller portal...")
        page.goto("https://seller.indiamart.com/")
        page.wait_for_timeout(2000)
        print("[*] Navigating directly to seller messages page...")
        page.goto("https://seller.indiamart.com/message")
        page.wait_for_timeout(5000)
        
        # Check if we need to wait for user to load Lead Manager
        if "login" in page.url or not page.locator("#filterCTA").first.is_visible():
            print("[!] Not on Lead Manager page. Please navigate there manually in the browser window.")
            print(f"    Current URL: {page.url}")
            input("Press [ENTER] in this terminal once you have loaded the Lead Manager page (with contacts list)...")
            
        print("[*] Lead Manager loaded. Starting automation test...")
        
        try:
            # Inject our central click utility
            js_utils = """
            window._utils = {
                getElement: function(sel) {
                    if (!sel) return null;
                    if (sel.startsWith('xpath=')) {
                        var path = sel.substring(6);
                        try {
                            var result = document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                            return result.singleNodeValue;
                        } catch(e) { return null; }
                    } else if (sel.startsWith('css=')) {
                        return document.querySelector(sel.substring(4));
                    } else {
                        return document.querySelector(sel);
                    }
                },
                click: function(el) {
                    if (!el) return;
                    var target = el;
                    try {
                        var rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            var x = rect.left + rect.width / 2;
                            var y = rect.top + rect.height / 2;
                            var hit = document.elementFromPoint(x, y);
                            if (hit && (el.contains(hit) || hit === el)) {
                                target = hit;
                            }
                        }
                    } catch(e) {}
                    
                    var events = ['mousedown', 'mouseup'];
                    for (var i = 0; i < events.length; i++) {
                        var ev = new MouseEvent(events[i], {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            buttons: 1
                        });
                        target.dispatchEvent(ev);
                    }
                    if (typeof target.click === 'function') {
                        target.click();
                    } else {
                        target.dispatchEvent(new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }));
                    }
                }
            };
            """
            page.evaluate(js_utils)
            print("[+] Injected _utils click helper.")
            
            # 1. Click filter icon
            print("[*] Clicking filter icon...")
            page.evaluate('window._utils.click(document.querySelector("#filterCTA"))')
            page.wait_for_timeout(1000)
            
            # 2. Click Filters tab
            print("[*] Clicking Filters tab...")
            page.evaluate('window._utils.click(document.querySelector("#filterPopup span[title=\'Filters\']"))')
            page.wait_for_timeout(1000)
            
            # 3. Click Date dropdown
            print("[*] Clicking Date dropdown...")
            # Let's find the Date dropdown via XPath or CSS
            date_dropdown_script = """
            (function() {
                var el = document.evaluate("//div[contains(., 'Date :')]//span[contains(@class, 'drpdwn')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (el) {
                    window._utils.click(el);
                    return true;
                }
                return false;
            })()
            """
            opened = page.evaluate(date_dropdown_script)
            print(f"[+] Date dropdown clicked, opened={opened}")
            page.wait_for_timeout(1000)
            
            # Dump info about all elements containing text "Custom Date"
            print("\n[*] Inspecting all elements containing text 'Custom Date':")
            inspect_script = """
            (function() {
                var elements = Array.from(document.querySelectorAll('*'));
                var results = [];
                for (var i = 0; i < elements.length; i++) {
                    var el = elements[i];
                    if (el.innerText && el.innerText.trim() === 'Custom Date') {
                        var rect = el.getBoundingClientRect();
                        results.push({
                            tagName: el.tagName.toLowerCase(),
                            className: el.className,
                            id: el.id,
                            width: rect.width,
                            height: rect.height,
                            visible: rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).display !== 'none',
                            isTrigger: el.classList.contains('innerdrpdwn') || 
                                       el.closest('.drpdwn') !== null || 
                                       el.closest('.text_fied_new') !== null || 
                                       el.closest('.text_fied_new_active') !== null
                        });
                    }
                }
                return results;
            })()
            """
            items = page.evaluate(inspect_script)
            for idx, item in enumerate(items):
                print(f"  [{idx+1}] <{item['tagName']}> id='{item['id']}' class='{item['className']}' | size={item['width']}x{item['height']} | visible={item['visible']} | isTrigger={item['isTrigger']}")
            
            # 4. Attempt to click Custom Date using our candidate selector
            print("\n[*] Running click_custom_script...")
            click_custom_script = """
            (function() {
                var elements = Array.from(document.querySelectorAll('span, div, li, a, p'));
                var candidates = [];
                for (var i = 0; i < elements.length; i++) {
                    var el = elements[i];
                    if (el.innerText.trim() === 'Custom Date') {
                        var isTrigger = el.classList.contains('innerdrpdwn') || 
                                        el.closest('.drpdwn') !== null || 
                                        el.closest('.text_fied_new') !== null || 
                                        el.closest('.text_fied_new_active') !== null;
                        if (!isTrigger) {
                            candidates.push(el);
                        }
                    }
                }
                console.log("Candidates found: " + candidates.length);
                if (candidates.length > 0) {
                    window._utils.click(candidates[0]);
                    return "Clicked candidate! Text: " + candidates[0].innerText + " Tag: " + candidates[0].tagName;
                }
                return "No candidates found!";
            })()
            """
            res = page.evaluate(click_custom_script)
            print(f"[+] Result of click_custom_script: {res}")
            page.wait_for_timeout(2000)
            
            # Let's check if customDatePicker is visible now
            datepicker_visible = page.locator("#customDatePicker").first.is_visible()
            print(f"[+] Is #customDatePicker visible? {datepicker_visible}")
            
            if not datepicker_visible:
                # If it's not visible, let's dump the DOM elements of the open dropdown so we can diagnose why candidates was 0
                print("\n[!] Diagnostic: Listing all elements inside #filterPopup when dropdown is open:")
                dump_dropdown_script = """
                (function() {
                    var results = [];
                    // Let's look for elements that might represent the dropdown list or options
                    var all = document.querySelectorAll('#filterPopup *');
                    for (var i = 0; i < all.length; i++) {
                        var el = all[i];
                        var style = window.getComputedStyle(el);
                        var rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0 && style.display !== 'none') {
                            if (el.innerText && ['Today', 'Yesterday', 'Custom Date', 'Select Date'].some(t => el.innerText.trim().includes(t))) {
                                results.push({
                                    tagName: el.tagName.toLowerCase(),
                                    className: el.className,
                                    text: el.innerText.trim().substring(0, 100),
                                    parentTag: el.parentElement.tagName.toLowerCase(),
                                    parentClass: el.parentElement.className
                                });
                            }
                        }
                    }
                    return results;
                })()
                """
                all_opts = page.evaluate(dump_dropdown_script)
                print(f"Found {len(all_opts)} elements matching dropdown options/texts:")
                for idx, opt in enumerate(all_opts):
                    print(f"  [{idx+1}] <{opt['tagName']}> class='{opt['className']}' | Text='{opt['text']}' | Sibling/Parent: <{opt['parentTag']}> class='{opt['parentClass']}'")
            
        except Exception as e:
            print(f"[!] Error during test automation: {e}")
            
        input("\nPress ENTER to close test browser...")
        context.close()

if __name__ == "__main__":
    run_test()
