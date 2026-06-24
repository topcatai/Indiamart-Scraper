#!/usr/bin/env python3
import os
from playwright.sync_api import sync_playwright
import config

def run_diagnose():
    with sync_playwright() as p:
        os.makedirs(config.CHROME_PROFILE_DIR, exist_ok=True)
        context = p.chromium.launch_persistent_context(
            user_data_dir=config.CHROME_PROFILE_DIR,
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            no_viewport=True
        )
        
        page = context.pages[0]
        
        # Inject script to bypass navigator.webdriver detection
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page.goto(config.START_URL)
        print("[*] Waiting 5 seconds for page load...")
        page.wait_for_timeout(5000)
        
        print("\n--- 1. REQUIREMENT CARD ANCESTORS ---")
        # Find elements containing "Requirement Type"
        el = page.locator("text=Requirement Type").first
        if not el.is_visible():
            el = page.locator("text=Probable Requirement").first
            
        if el.is_visible():
            print("[+] Element containing Requirement Type is visible.")
            # Print outer HTML of the element and its ancestors up to 5 levels
            outer = el.evaluate("el => el.outerHTML")
            print(f"Snippet: {outer[:150]}...")
            
            ancestors = el.evaluate("""el => {
                let p = el;
                let path = [];
                for (let i = 0; i < 7 && p; i++) {
                    path.push(p.tagName.toLowerCase() + (p.className ? "." + p.className.split(' ').join('.') : ""));
                    p = p.parentElement;
                }
                return path.join(" -> ");
            }""")
            print("Ancestors path:", ancestors)
        else:
            print("[-] Element containing Requirement Type is NOT visible.")
            
        print("\n--- 2. CONTACT TYPE BANNER ---")
        # Find elements containing "Contact added through"
        banner = page.locator("text=Contact added through").first
        if not banner.is_visible():
            banner = page.locator("text=BuyLead consumed").first
            
        if banner.is_visible():
            print("[+] Banner containing Contact Type is visible.")
            outer = banner.evaluate("el => el.outerHTML")
            print(f"Snippet: {outer[:150]}...")
            
            ancestors = banner.evaluate("""el => {
                let p = el;
                let path = [];
                for (let i = 0; i < 5 && p; i++) {
                    path.push(p.tagName.toLowerCase() + (p.className ? "." + p.className.split(' ').join('.') : ""));
                    p = p.parentElement;
                }
                return path.join(" -> ");
            }""")
            print("Ancestors path:", ancestors)
        else:
            print("[-] Banner containing Contact Type is NOT visible.")
            
        context.close()

if __name__ == "__main__":
    run_diagnose()
