import os
import sys
from playwright.sync_api import sync_playwright
import config

def run_diagnose_chat():
    print("=" * 60)
    print("         INDIAMART CHAT MESSAGE DIAGNOSTIC UTILITY")
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
        
        # Inject script to bypass navigator.webdriver detection
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        print(f"[*] Navigating to {config.START_URL}...")
        page.goto(config.START_URL)
        
        print("\n" + "!" * 80)
        print(" ACTION REQUIRED:")
        print(" 1. Please LOG IN to your IndiaMART account in the browser window.")
        print(" 2. Navigate to your Message Centre.")
        # Ask to click on a contact that has multiple messages and timestamps visible on screen
        print(" 3. Click on a contact that has active chat history (e.g. Satish with outgoing calls and messages).")
        print(" 4. Make sure the message history is visible in the center/right pane.")
        print(" 5. Press ENTER in this terminal to start scanning the chat elements.")
        print("!" * 80 + "\n")
        
        input("Press [ENTER] when you have loaded a contact with chat history...")
        
        print("\n[*] Scanning DOM for chat elements...")
        
        # Let's search for typical text content in chat history
        search_terms = [
            "Call attempted",
            "enquiring",
            "This buyer has viewed your catalog",
            "Anusha",
            "2025",  # typical year in timestamp
            "PM",    # typical time format
            "AM"
        ]
        
        for term in search_terms:
            print(f"\n[*] Scanning for text match: '{term}'")
            locators = page.locator(f"xpath=//*[contains(text(), '{term}')]").all()
            print(f"    Found {len(locators)} element(s)")
            
            # Print the structure of the first 3 matches
            for idx, loc in enumerate(locators[:3]):
                try:
                    tag_name = loc.evaluate("el => el.tagName")
                    class_list = loc.evaluate("el => el.className")
                    outer_html = loc.evaluate("el => el.outerHTML")
                    visible = loc.is_visible()
                    
                    print(f"    [{idx + 1}] Tag: <{tag_name.lower()}> | Visible: {visible} | Class: '{class_list}'")
                    # Trace ancestors to find the message bubble wrapper
                    ancestors = loc.evaluate("""el => {
                        let path = [];
                        let curr = el.parentElement;
                        for (let i = 0; i < 5 && curr; i++) {
                            path.push(curr.tagName.toLowerCase() + (curr.className ? "." + curr.className.split(' ').join('.') : ""));
                            curr = curr.parentElement;
                        }
                        return path.join(" -> ");
                    }""")
                    print(f"        Ancestors: {ancestors}")
                    print(f"        HTML Snippet: {outer_html[:200].strip()}...")
                except Exception as e:
                    print(f"        Error analyzing: {e}")
                    
        # Let's also search for elements containing specific classes commonly used for chat message logs
        # like "message", "chat", "conversation", "bubble", "msg", "received", "sent"
        print("\n[*] Analyzing general container structures in the center pane...")
        try:
            # Look for divs in the right half of the screen
            containers = page.evaluate("""() => {
                const results = [];
                const divs = document.querySelectorAll('div');
                for (const d of divs) {
                    const rect = d.getBoundingClientRect();
                    // Message container should be in the center/right area, visible, and have a class
                    if (rect.left > window.innerWidth / 3 && rect.width > 200 && rect.height > 20 && d.className) {
                        const classLower = d.className.toLowerCase();
                        if (classLower.includes('msg') || classLower.includes('message') || classLower.includes('chat') || classLower.includes('bubble') || classLower.includes('conv') || classLower.includes('rcv') || classLower.includes('snt')) {
                            results.push({
                                tagName: d.tagName.toLowerCase(),
                                className: d.className,
                                text: d.innerText.substring(0, 100).replace(/\\n/g, ' ')
                            });
                        }
                    }
                }
                // Return unique entries by class name
                const unique = [];
                const seen = new Set();
                for (const item of results) {
                    if (!seen.has(item.className)) {
                        seen.add(item.className);
                        unique.push(item);
                    }
                }
                return unique.slice(0, 15);
            }""")
            print(f"Found {len(containers)} unique potential message container classes:")
            for c in containers:
                print(f"    - <{c['tagName']}> class='{c['className']}' | Snippet: {c['text'][:80]}...")
        except Exception as e:
            print(f"Error scanning containers: {e}")

        context.close()

if __name__ == "__main__":
    run_diagnose_chat()
