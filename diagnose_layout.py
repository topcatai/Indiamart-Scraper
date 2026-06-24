import os
from playwright.sync_api import sync_playwright
import config

def run_diagnose():
    print("=" * 60)
    print("         INDIAMART LAYOUT DIAGNOSTIC UTILITY")
    print("=" * 60)
    
    output_lines = []
    def log(msg):
        print(msg)
        output_lines.append(msg)

    with sync_playwright() as p:
        log("[*] Launching Chromium browser with persistent profile...")
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
        
        log(f"[*] Navigating to {config.START_URL}...")
        page.goto(config.START_URL)
        
        print("\n" + "!" * 80)
        print(" ACTION REQUIRED:")
        print(" 1. Please LOG IN to your IndiaMART account in the browser window.")
        print(" 2. Navigate to your Lead Manager (All Contacts) screen.")
        print(" 3. Make sure the contact cards (Yogesh Barde, etc.) are visible on the left.")
        print(" 4. Press ENTER in this terminal to start layout diagnosis.")
        print("!" * 80 + "\n")
        
        input("Press [ENTER] when you have loaded the Lead Manager...")
        
        log("\n[*] Running diagnostic scan on DOM...")
        
        # 1. Search for key terms on the page to identify card elements
        target_names = ["Yogesh Barde", "Borde Sumedha", "Ema Enterprises", "Yogesh Barde is active on WhatsApp", "View More", "Contact added through"]
        
        log("\n--- Part 1: Finding Element Structures for Targets ---")
        for name in target_names:
            log(f"\n[*] Scanning for text matches of: '{name}'")
            # Search for elements containing the text
            locators = page.locator(f"text={name}").all()
            if not locators:
                # Try case insensitive search or xpath contains
                locators = page.locator(f"xpath=//*[contains(text(), '{name}')]").all()
                
            log(f"    Found {len(locators)} element(s)")
            
            for idx, loc in enumerate(locators):
                try:
                    # Get details
                    tag_name = loc.evaluate("el => el.tagName")
                    class_list = loc.evaluate("el => el.className")
                    outer_html = loc.evaluate("el => el.outerHTML")
                    bbox = loc.bounding_box()
                    visible = loc.is_visible()
                    
                    log(f"    [{idx + 1}] Tag: <{tag_name.lower()}> | Visible: {visible}")
                    log(f"        Classes: {class_list}")
                    if bbox:
                        log(f"        Bounding Box: x={bbox['x']:.1f}, y={bbox['y']:.1f}, width={bbox['width']:.1f}, height={bbox['height']:.1f}")
                    else:
                        log(f"        Bounding Box: None")
                    
                    # Print parent element details
                    parent_details = loc.evaluate("""el => {
                        let p = el.parentElement;
                        if (!p) return "None";
                        return p.tagName.toLowerCase() + " (class='" + p.className + "')";
                    }""")
                    log(f"        Parent: {parent_details}")
                    
                    # Print higher ancestor hierarchy
                    ancestor_hierarchy = loc.evaluate("""el => {
                        let path = [];
                        let curr = el.parentElement;
                        for (let i = 0; i < 4 && curr; i++) {
                            path.push(curr.tagName.toLowerCase() + (curr.className ? "." + curr.className.split(' ').join('.') : ""));
                            curr = curr.parentElement;
                        }
                        return path.join(" -> ");
                    }""")
                    log(f"        Ancestors: {ancestor_hierarchy}")
                    log(f"        Snippet: {outer_html[:150].strip()}...")
                except Exception as e:
                    log(f"        Error analyzing match: {e}")
        
        # 2. Diagnose Scroll Container
        log("\n--- Part 2: Analyzing Scrollable Elements ---")
        try:
            scrollable_divs = page.evaluate("""() => {
                const results = [];
                const divs = document.querySelectorAll('div');
                let count = 0;
                for (const d of divs) {
                    const style = window.getComputedStyle(d);
                    const isScrollable = (style.overflowY === 'auto' || style.overflowY === 'scroll') && d.scrollHeight > d.clientHeight;
                    if (isScrollable) {
                        const rect = d.getBoundingClientRect();
                        results.push({
                            id: count++,
                            classes: d.className,
                            tagName: d.tagName.toLowerCase(),
                            scrollHeight: d.scrollHeight,
                            clientHeight: d.clientHeight,
                            rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                        });
                    }
                }
                return results;
            }""")
            log(f"Found {len(scrollable_divs)} scrollable div elements:")
            for s in scrollable_divs:
                log(f"    ID {s['id']}: <{s['tagName']}> class='{s['classes']}'")
                log(f"       Dimensions: scrollHeight={s['scrollHeight']}, clientHeight={s['clientHeight']}")
                log(f"       Rect: x={s['rect']['x']:.1f}, y={s['rect']['y']:.1f}, width={s['rect']['width']:.1f}, height={s['rect']['height']:.1f}")
        except Exception as e:
            log(f"Error checking scrollable elements: {e}")
            
        # Write report to file
        report_path = "layout_diagnosis.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
            
        log(f"\n[*] Diagnostic report saved successfully to: {os.path.abspath(report_path)}")
        context.close()

if __name__ == "__main__":
    run_diagnose()
