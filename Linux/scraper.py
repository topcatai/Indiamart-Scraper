#!/usr/bin/env python3
import os
import re
import random
import sys
import time
import datetime
import calendar
import argparse
from playwright.sync_api import sync_playwright
import db_manager
import config

# Global Windows console unicode encoding fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')

def parse_cli_args():
    """Parses command line arguments for start and end dates."""
    parser = argparse.ArgumentParser(description="IndiaMART Lead Manager Scraper")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD) for scraping", default=None)
    parser.add_argument("--end", help="End date (YYYY-MM-DD) for scraping", default=None)
    parser.add_argument("--reset", action="store_true", help="Reset Chrome profile cache")
    args, unknown = parser.parse_known_args()
    return args


def _navigate_calendar_to(page, target_year, target_month_idx):
    """Navigates the calendar select elements to target year and month if not already there."""
    year_select = page.locator("#customDatePicker .rdrYearPicker select").first
    month_select = page.locator("#customDatePicker .rdrMonthPicker select").first
    
    current_year = year_select.evaluate("el => el.value")
    current_month = month_select.evaluate("el => el.value")
    
    if current_year != str(target_year):
        print(f"[*] Selecting year {target_year} (current: {current_year})...")
        year_select.select_option(str(target_year), timeout=5000)
        page.wait_for_timeout(500)
        
    if current_month != str(target_month_idx):
        print(f"[*] Selecting month index {target_month_idx} (current: {current_month})...")
        month_select.select_option(str(target_month_idx), timeout=5000)
        page.wait_for_timeout(1000)

def _click_calendar_day(page, day_num):
    """Clicks the specified day number in the active month of the calendar."""
    day_str = str(day_num)
    day_locator = page.locator("#customDatePicker button.rdrDay:not(.rdrDayPassive):not(.rdrDayDisabled)").filter(
        has_text=re.compile(rf"^\s*{day_str}\s*$")
    ).first
    day_locator.click(timeout=5000)
    page.wait_for_timeout(1000)

def set_custom_date_filter(page, start_date, end_date):
    """
    Automates clicking the filter icon, selecting the 'Filters' tab, opening the
    Date dropdown, choosing 'Custom Date', and setting start and end dates in the
    single calendar widget.
    Falls back to a manual prompt if any automated step fails or times out.
    """
    print(f"\n[*] Applying date filter: {start_date} to {end_date}...")
    try:
        # Let any previous popup close transition settle first
        page.wait_for_timeout(600)

        # 1. Click filter icon if popup is not already visible
        filter_popup = page.locator("#filterPopup").first
        if not filter_popup.is_visible():
            print("[*] Clicking filter icon #filterCTA...")
            page.locator("#filterCTA").first.click(timeout=10000)
            page.wait_for_timeout(1000)
            
        # 2. Click "Filters" tab with verification and retry
        filters_tab_activated = False
        for attempt in range(3):
            filters_tab_activated = page.evaluate("""
            (function() {
                var tabs = document.querySelectorAll(".label-filter-tab");
                for (var i = 0; i < tabs.length; i++) {
                    var span = tabs[i].querySelector("span[title='Filters']");
                    if (span) {
                        return tabs[i].classList.contains('active');
                    }
                }
                return false;
            })()
            """)
            if filters_tab_activated:
                break
            print(f"[*] Attempt {attempt+1}: Filters tab not active. Clicking tab...")
            filters_tab = page.locator("#filterPopup span[title='Filters']").first
            filters_tab.click(timeout=5000)
            page.wait_for_timeout(800)
            
        if not filters_tab_activated:
            raise RuntimeError("Could not activate 'Filters' tab")
        
        # 3 & 4. Select "Custom Date" from Date dropdown
        date_already_custom = page.evaluate("""
        (function() {
            var labels = document.querySelectorAll("span.mf_lbl");
            for (var i = 0; i < labels.length; i++) {
                if (labels[i].innerText.includes("Date")) {
                    var parent = labels[i].parentElement;
                    if (parent) {
                        var activeDropdown = parent.querySelector("span.drpdwn.text_fied_new_active");
                        if (activeDropdown) {
                            var txt = activeDropdown.querySelector('.innerdrpdwn');
                            if (txt && txt.innerText.trim() === 'Custom Date') return true;
                        }
                    }
                }
            }
            return false;
        })()
        """)
        
        if not date_already_custom:
            date_dropdown = page.locator("xpath=//div[contains(., 'Date :') and (contains(@class, 'mb0') or contains(@class, 'brdr_btm'))]//span[contains(@class, 'drpdwn')]").first
            date_dropdown.click(timeout=5000)
            page.wait_for_timeout(1000)
            
            print("[*] Clicking 'Custom Date' option...")
            page.locator("#customdatelispan").click(timeout=5000)
            page.wait_for_timeout(1500)
        else:
            print("[*] Custom Date already selected, skipping dropdown selection.")
            page.wait_for_timeout(500)
        
        # 5. Click Start Date span target to ensure calendar popup is open
        start_target = page.locator("#custom_date_start").first
        start_target.click(timeout=5000)
        page.wait_for_selector("#customDatePicker", timeout=3000)
        page.wait_for_timeout(500)
        
        # 6. Navigate calendar to start year/month
        start_month_val = start_date.month - 1
        start_year_val = start_date.year
        print(f"[*] Navigating calendar to start: month={start_month_val}, year={start_year_val}")
        _navigate_calendar_to(page, start_year_val, start_month_val)
        
        # 7. Click start day
        print(f"[*] Clicking start day {start_date.day}...")
        _click_calendar_day(page, start_date.day)
        
        # 7.5 Click End Date target to switch focus to end date input
        print("[*] Clicking end date target (#custom_date_end)...")
        end_target = page.locator("#custom_date_end").first
        end_target.click(timeout=5000)
        page.wait_for_timeout(500)
        
        # 8. Navigate calendar to end year/month (only if month/year are different)
        end_month_val = end_date.month - 1
        end_year_val = end_date.year
        
        # We check if we need to navigate the calendar dropdowns for end date
        if start_month_val != end_month_val or start_year_val != end_year_val:
            print(f"[*] Navigating calendar to end: month={end_month_val}, year={end_year_val}")
            _navigate_calendar_to(page, end_year_val, end_month_val)
            
        # 9. Click end day
        print(f"[*] Clicking end day {end_date.day}...")
        _click_calendar_day(page, end_date.day)
        
        # 10. Click Apply button in the filter popup
        print("[*] Clicking Apply button...")
        apply_btn = page.locator("#filterPopup div.small_btn_filled_std", has_text="Apply").first
        apply_btn.click(timeout=5000)
        page.wait_for_timeout(3000)  # Wait for page reload to complete
        print("[+] Custom date filter applied successfully by Playwright.")
        return True
    except Exception as e:
        print(f"\n[!] Playwright date filter setting failed: {e}")
        print("!" * 80)
        print(" ACTION REQUIRED (MANUAL FALLBACK):")
        print(f" 1. Please click the Filter Icon, go to the 'Filters' tab.")
        print(f" 2. Set 'Custom Date' to: {start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}")
        print(" 3. Click the 'Apply' button in the filter popup.")
        print(" 4. Once the filter is applied and results are loaded, press ENTER in this terminal.")
        print("!" * 80 + "\n")
        input(f"Press [ENTER] when you have manually filtered for {start_date} to {end_date}...")
        return False
# --- Helper Classes & Functions ---

class ScrapeScheduler:
    """
    Manages scraping sleep intervals.
    """
    def _incremental_sleep(self, seconds):
        """Sleeps in smaller 10-second increments so Ctrl+C breaks immediately."""
        end_time = time.time() + seconds
        while time.time() < end_time:
            rem = end_time - time.time()
            sleep_chunk = min(rem, 10.0)
            if sleep_chunk > 0:
                time.sleep(sleep_chunk)


def parse_indiamart_date(date_str):
    """
    Parses IndiaMART date strings into DD-MM-YYYY format.
    Handles:
      - 'Yesterday' -> yesterday's date
      - 'HH:MM AM/PM' -> today's date
      - 'DD MMM' (e.g., '14 Jun') -> DD-MM-[Current/Previous Year]
      - "DD MMM'YY" (e.g., "03 Jun'25") -> DD-MM-20YY
      - Standard fallback
    """
    if not date_str:
        return ""
    
    cleaned = date_str.strip().replace('\xa0', ' ')
    
    # 1. Today's time (e.g., '12:13 PM', '09:45 AM')
    if re.search(r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b', cleaned) or (':' in cleaned and len(cleaned) <= 8):
        return datetime.date.today().strftime("%d-%m-%Y")
        
    # 2. Yesterday
    if cleaned.lower() == 'yesterday':
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        return yesterday.strftime("%d-%m-%Y")
        
    # 3. Handle '03 Jun'25' or '03 Jun\'25' or '03 Jun 25' or '03 Jun\' 25'
    match_with_year = re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s*\'?\s*(\d{2,4})', cleaned)
    if match_with_year:
        day_str, month_name, year_str = match_with_year.groups()
        day = int(day_str)
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        try:
            month = months.index(month_name.lower()[:3]) + 1
        except ValueError:
            return ""
        year = int(year_str)
        if year < 100:
            year += 2000
        return f"{day:02d}-{month:02d}-{year}"
        
    # 4. Handle '14 Jun' (no year)
    match_no_year = re.search(r'(\d{1,2})\s+([A-Za-z]{3})', cleaned)
    if match_no_year:
        day_str, month_name = match_no_year.groups()
        day = int(day_str)
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        try:
            month = months.index(month_name.lower()[:3]) + 1
        except ValueError:
            return ""
        
        today = datetime.date.today()
        year = today.year
        parsed_date = datetime.date(year, month, day)
        if parsed_date > today:
            year -= 1
        return f"{day:02d}-{month:02d}-{year}"
        
    return ""

class DelayPool:
    """Generates shuffled, non-repeating delay values within a specified range."""
    def __init__(self, min_val, max_val):
        self.min_val = min_val
        self.max_val = max_val
        self.pool = []

    def next_delay(self):
        if not self.pool:
            self.pool = list(range(self.min_val, self.max_val + 1))
            random.shuffle(self.pool)
            print(f"\n[*] Generated a new randomized delay pool of {len(self.pool)} unique integers ({self.min_val} to {self.max_val} seconds).")
        val = self.pool.pop()
        return val

def normalize_key(text):
    """Creates a clean, lowercase unique key from text for deduplication."""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    # Return first 128 chars to keep keys manageable
    return cleaned[:128]

def is_valid_contact_card(card):
    """
    Checks if a Playwright element is a valid, visible contact card based on visibility
    and logical dimensions (to avoid layout structural wrappers or icons).
    """
    try:
        if not card.is_visible():
            return False
            
        bbox = card.bounding_box()
        if not bbox:
            return False
            
        height = bbox['height']
        width = bbox['width']
        
        # A valid list card usually spans the left sidebar (approx. 150px - 600px)
        # and has a block height (approx. 50px - 220px) to show name, city, req, and date.
        if not (50 <= height <= 220):
            return False
        if not (150 <= width <= 600):
            return False
            
        # Get card inner text and ensure it's not a massive wrapper or empty
        card_text = card.inner_text().strip()
        if not card_text or len(card_text) > 1000:
            return False
            
        # Ensure it doesn't contain list-level header titles
        if "All Contacts" in card_text or "Reminders" in card_text:
            return False
            
        return True
    except Exception:
        return False

def extract_phone_numbers(text):
    """Scans text for phone numbers of various formats and returns them as a comma-separated string."""
    # Matches patterns like +91 99999 99999, 09999999999, 99999-99999, etc.
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}'
    matches = re.finditer(phone_pattern, text)
    numbers = []
    for match in matches:
        num = match.group().strip()
        # Clean non-digits (except optional leading +)
        cleaned_num = re.sub(r'[^\d+]', '', num)
        if len(cleaned_num) >= 10:
            numbers.append(cleaned_num)
    # Remove duplicates while preserving order
    unique_numbers = list(dict.fromkeys(numbers))
    return ", ".join(unique_numbers) if unique_numbers else None

def extract_emails(text):
    """Scans text for email addresses and returns them as a comma-separated string."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    matches = re.findall(email_pattern, text)
    unique_emails = list(dict.fromkeys([email.lower() for email in matches]))
    return ", ".join(unique_emails) if unique_emails else None

def extract_gst_number(text):
    """Scans text for a standard 15-digit Indian GST number."""
    # Format: 2 digits (state) + 5 chars (PAN) + 4 digits (PAN) + 1 char (PAN) + 1 digit (entity) + Z + 1 digit/char (checksum)
    gst_pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b'
    matches = re.findall(gst_pattern, text, re.IGNORECASE)
    if matches:
        return matches[0].upper()
    return None

def verify_card_match(card_name, card_text, modal_name, modal_text):
    """
    Robust verification checking if the details modal matches the clicked contact card.
    Supports matching either the Person's Name, the Company Name, or fallback sibling fields
    like address/location or product name to prevent virtualized DOM coordinate mis-clicks.
    """
    card_clean = re.sub(r'[^a-zA-Z0-9]', '', card_name).lower()
    modal_clean = re.sub(r'[^a-zA-Z0-9]', '', modal_name).lower()
    
    # 1. Direct Name/Prefix Match
    if card_clean[:4] == modal_clean[:4] and card_clean[:4] != "":
        return True
        
    # 2. Company Name Substring Match (for card names > 2 chars)
    if len(card_clean) > 2:
        modal_text_clean = re.sub(r'[^a-zA-Z0-9]', '', modal_text).lower()
        if card_clean[:6] in modal_text_clean:
            return True
            
    # 3. Sibling Line Checks (Location or Product Name matches)
    card_lines = [l.strip() for l in card_text.split('\n') if l.strip()]
    modal_text_lower = modal_text.lower()
    
    for line in card_lines[1:]:
        line_clean = line.lower().strip()
        if not line_clean:
            continue
        # Skip common interface keywords and timestamps
        if any(w in line_clean for w in ["am", "pm", "yesterday", "ago", "call attempted", "enquiry", "rate now"]):
            continue
        if len(line_clean) > 3 and line_clean in modal_text_lower:
            return True
            
    return False

def close_modal_if_open(page):
    """Attempts to close the details modal if it is currently visible on screen."""
    try:
        # Check if modal selector is visible
        modal = page.locator(config.MODAL_CONTAINER).first
        if modal.is_visible():
            print("[*] Modal detected. Attempting to close it...")
            close_btn = page.locator(config.MODAL_CLOSE_BTN).first
            if close_btn.is_visible():
                close_btn.click()
            else:
                # Fallback: Press Escape key to close the modal
                page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
    except Exception as e:
        # Fallback: Press Escape anyway to clear popup UI
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
        except:
            pass

def scroll_to_find_card(page, card_name, max_scrolls=6):
    """
    Scrolls the left pane scroll container up and down to find the card with card_name in the DOM.
    Checks if it is present in the DOM (locator.count() > 0) rather than just visible.
    """
    # Normalize whitespaces to prevent lookup failures from non-breaking spaces or double spacing
    search_name = " ".join(card_name.split())
    locator = page.locator(config.LEFT_PANE_ITEMS).filter(has_text=search_name).first
    
    # Check if already present in DOM
    try:
        if locator.count() > 0:
            return locator
    except:
        pass
        
    scroll_container = page.locator(config.LEFT_PANE_SCROLL_CONTAINER).first
    if not scroll_container.is_visible():
        return locator # Fallback
        
    # Scroll container to find it
    print(f"[*] Card '{card_name}' not visible in viewport. Scrolling container to locate it...")
    for direction in [1, -1]: # Try scrolling down, then up
        for _ in range(max_scrolls):
            try:
                # Scroll by 300px
                scroll_container.evaluate(f"el => el.scrollTop += {direction * 300}")
                page.wait_for_timeout(500) # Wait for rendering to execute
                if locator.count() > 0:
                    print(f"[+] Found card '{card_name}' in DOM after scrolling.")
                    return locator
            except Exception as e:
                break
    return locator

def scrape_conversation_history(page):
    """
    Extracts and formats all visible chat messages inside the conversation history panel.
    Scrolls up a few times to load older history if the scroll container is found.
    """
    print("[*] Extracting conversation history from chat panel...")
    chat_lines = []
    try:
        # 1. Attempt to scroll chat container to the top to load older messages
        try:
            chat_container = page.locator(config.CHAT_MESSAGE_CONTAINER).first
            if chat_container.is_visible():
                for _ in range(3):
                    chat_container.evaluate("el => el.scrollTop = 0")
                    page.wait_for_timeout(500)
        except Exception as scroll_err:
            # Silently pass if scrolling isn't supported or container not found
            pass
        
        # 2. Extract message items
        message_locs = page.locator(config.CHAT_MESSAGE_ITEMS).all()
        for loc in message_locs:
            try:
                if not loc.is_visible():
                    continue
                
                cls = loc.attribute("class") or ""
                raw_text = loc.inner_text().strip()
                if not raw_text:
                    continue
                
                # Attempt to extract and clean timestamp from message
                timestamp = loc.evaluate("""el => {
                    var tsLoc = el.querySelector(".time_stamp");
                    if (tsLoc) return tsLoc.innerText.trim();
                    
                    var sibling = el.nextElementSibling;
                    while (sibling) {
                        if (sibling.classList.contains("time_stamp") || sibling.querySelector(".time_stamp")) {
                            var innerTs = sibling.classList.contains("time_stamp") ? sibling : sibling.querySelector(".time_stamp");
                            return innerTs.innerText.trim();
                        }
                        sibling = sibling.nextElementSibling;
                    }
                    var parent = el.parentElement;
                    if (parent) {
                        var parentTs = parent.querySelector(".time_stamp");
                        if (parentTs) return parentTs.innerText.trim();
                    }
                    return "";
                }""")
                if timestamp and timestamp in raw_text:
                    raw_text = raw_text.replace(timestamp, "").strip()
                
                # Replace internal newlines with spaces for clean listing
                clean_text = re.sub(r'\n+', ' ', raw_text)
                clean_text = re.sub(r'\s+', ' ', clean_text)
                
                # Identify sender
                if "left_side_msg" in cls:
                    sender = "Buyer"
                elif "right_side_msg" in cls:
                    sender = "Seller"
                else:
                    sender = "System"
                
                ts_prefix = f"[{timestamp}] " if timestamp else ""
                chat_lines.append(f"{ts_prefix}{sender}: {clean_text}")
            except Exception as item_err:
                continue
    except Exception as e:
        print(f"[!] Warning: Could not scrape chat history: {e}")
        
    return "\n".join(chat_lines)

def scrape_right_pane(page, unique_key):
    """
    Scrapes contact details from the details panel, the opened modal, and chat history.
    Returns a dictionary of lead fields.
    """
    lead_data = {
        'unique_key': unique_key,
        'name': 'Unknown',
        'phone_number': '',
        'email_id': '',
        'gst': '',
        'address_location': '',
        'whatsapp_status': 'Unknown/No',
        'contact_type': 'Unknown',
        'requirement_details': '',
        'chat_history': '',
        'lead_date': ''
    }
    
    # 1. Extract Details from Main Right Pane
    print("[*] Extracting details from main right pane...")
    
    # Get Contact Type banner
    contact_type_banner = page.locator(config.CONTACT_TYPE_BANNER).first
    if contact_type_banner.is_visible():
        lead_data['contact_type'] = contact_type_banner.inner_text().strip()
    
    # Get Requirement details box
    requirement_box = page.locator(config.REQUIREMENT_BOX).first
    if requirement_box.is_visible():
        lead_data['requirement_details'] = requirement_box.inner_text().strip()
    else:
        req_card = page.locator("xpath=//div[contains(@class, 'card') and (contains(., 'Milling') or contains(., 'Machine') or contains(., 'CNC') or contains(., 'Fiber'))]").first
        if req_card.is_visible():
            lead_data['requirement_details'] = req_card.inner_text().strip()
    
    # 2. Ensure Modal is Open (Verification loop normally opens it)
    modal = page.locator(config.MODAL_CONTAINER).first
    if not modal.is_visible():
        # If for some reason it's not open, try to open it
        view_more_btn = page.locator(config.VIEW_MORE_BTN).first
        if not view_more_btn.is_visible():
            view_more_btn = page.locator("text=View More").first
        if view_more_btn.is_visible():
            view_more_btn.click()
            page.wait_for_selector(config.MODAL_CONTAINER, timeout=5000)
            page.wait_for_timeout(1000)
    
    # 3. Scrape Info from Detailed Modal
    if modal.is_visible():
        modal_text = modal.inner_text()
        
        # Extract Name
        modal_name = page.locator(config.MODAL_NAME).first
        if modal_name.is_visible():
            lead_data['name'] = modal_name.inner_text().strip()
        else:
            lines = [l.strip() for l in modal_text.split('\n') if l.strip()]
            if lines:
                lead_data['name'] = lines[0]
                
        # Extract Email
        email_link = modal.locator("a[href^='mailto:']").first
        if email_link.is_visible():
            lead_data['email_id'] = email_link.attribute("href").replace("mailto:", "").strip()
        else:
            lead_data['email_id'] = extract_emails(modal_text) or ""
    
        # Extract Phone
        phone_link = modal.locator("a[href^='tel:']").first
        if phone_link.is_visible():
            lead_data['phone_number'] = phone_link.attribute("href").replace("tel:", "").strip()
        else:
            lead_data['phone_number'] = extract_phone_numbers(modal_text) or ""
    
        # Extract Address
        address_lines = []
        lines = [line.strip() for line in modal_text.split('\n')]
        for idx, line in enumerate(lines):
            if line.upper() == "ADDRESS" and idx + 1 < len(lines):
                address_lines.append(lines[idx + 1])
                break
        if address_lines:
            lead_data['address_location'] = address_lines[0]
        else:
            address_loc = modal.locator(config.MODAL_ADDRESS).first
            if address_loc.is_visible():
                lead_data['address_location'] = address_loc.inner_text().replace("Address", "").replace("Location", "").strip()
    
        # Extract WhatsApp
        if "active on WhatsApp" in modal_text or "WhatsApp" in modal_text:
            whatsapp_el = modal.locator(config.MODAL_WHATSAPP).first
            if whatsapp_el.is_visible():
                lead_data['whatsapp_status'] = whatsapp_el.inner_text().strip()
            else:
                lead_data['whatsapp_status'] = "Active on WhatsApp" if "active on WhatsApp" in modal_text else "Yes"
        else:
            lead_data['whatsapp_status'] = "Not Active / Not Checked"
    
        # Extract GST
        gst_found = extract_gst_number(modal_text)
        lead_data['gst'] = gst_found if gst_found else "N/A"
    else:
        print("[!] Warning: Modal not visible during scraping. Scanning main view text fallback...")
        right_pane_text = page.locator("body").first.inner_text()
        lead_data['phone_number'] = extract_phone_numbers(right_pane_text) or ""
        lead_data['email_id'] = extract_emails(right_pane_text) or ""
        lead_data['gst'] = extract_gst_number(right_pane_text) or ""
    
    # 4. Scrape Chat History
    lead_data['chat_history'] = scrape_conversation_history(page)
    
    # Log details
    print(f"    - Name: {lead_data['name']}")
    print(f"    - Phone: {lead_data['phone_number']}")
    print(f"    - Email: {lead_data['email_id']}")
    print(f"    - GST: {lead_data['gst']}")
    print(f"    - Address: {lead_data['address_location']}")
    print(f"    - WhatsApp: {lead_data['whatsapp_status']}")
    print(f"    - Contact Type: {lead_data['contact_type']}")
    print(f"    - Chat History: {len(lead_data['chat_history'].splitlines())} messages scraped.")
    
    # 5. Close Modal
    close_modal_if_open(page)
    
    return lead_data

def _last_day_of_month(d):
    """Return the last day of the month for date d."""
    _, last_day = calendar.monthrange(d.year, d.month)
    return d.replace(day=last_day)

def _first_of_next_month(d):
    """Return the first day of the month after date d."""
    if d.month == 12:
        return d.replace(year=d.year + 1, month=1, day=1)
    return d.replace(month=d.month + 1, day=1)

# --- Main Running Function ---

def run_scraper():
    print("=" * 60)
    print("           INDIAMART INBOX SCRAPING UTILITY")
    print("=" * 60)
    
    # Initialize SQLite database
    db_manager.init_db()
    
    # Create scheduler instance
    scheduler = ScrapeScheduler()
    
    # Parse CLI Arguments
    args = parse_cli_args()
    cli_mode = False
    start_date = None
    end_date = None
    
    if args.start or args.end:
        cli_mode = True
        if args.start:
            try:
                start_date = datetime.datetime.strptime(args.start, "%Y-%m-%d").date()
            except ValueError:
                print(f"[!] Error: Invalid start date format: {args.start}. Use YYYY-MM-DD.")
                sys.exit(1)
        if args.end:
            try:
                end_date = datetime.datetime.strptime(args.end, "%Y-%m-%d").date()
            except ValueError:
                print(f"[!] Error: Invalid end date format: {args.end}. Use YYYY-MM-DD.")
                sys.exit(1)
                
        if start_date and not end_date:
            end_date = start_date + datetime.timedelta(days=6)
        elif end_date and not start_date:
            start_date = end_date - datetime.timedelta(days=6)
            
        print(f"[*] Command-line Mode: Scraping specific range {start_date} to {end_date} and will then exit.")
    
    # Handle reset flag
    if args.reset:
        import shutil
        if os.path.exists(config.CHROME_PROFILE_DIR):
            print(f"[*] Reset flag detected. Deleting Chrome profile directory: {config.CHROME_PROFILE_DIR}")
            try:
                shutil.rmtree(config.CHROME_PROFILE_DIR)
                print("[+] Chrome profile reset completed successfully.")
            except Exception as e:
                print(f"[!] Warning: Could not delete Chrome profile directory: {e}")

    # Track counts inside this active run window
    scraped_count = 0
    reached_run_limit = False
    reached_daily_limit = False
    
    # Auto-progression seed setup
    completed_periods = db_manager.get_completed_periods()
    if not cli_mode:
        max_lead_date = db_manager.get_max_lead_date()
        last_completed = db_manager.get_last_completed_period()
        initial_date_str = db_manager.get_initial_start_date()
        if max_lead_date:
            current_start = max_lead_date.replace(day=1)
            print(f"[*] Resuming scraping from month of last scraped lead: {current_start}")
        elif last_completed:
            last_date = datetime.datetime.strptime(last_completed, "%Y-%m-%d").date()
            current_start = _first_of_next_month(last_date)
        elif initial_date_str:
            current_start = datetime.datetime.strptime(initial_date_str, "%Y-%m-%d").date()
        else:
            # We don't have initial start date in db. We prompt in console.
            print("\n" + "="*60)
            print("FIRST-TIME SETUP: START DATE REQUIRED")
            print("Please provide the date of the first contact received in IndiaMART")
            print("(or the oldest contact in Lead Manager).")
            print("Reason: We start scraping from this date up to the current date,")
            print("which avoids checking empty periods before your account was active.")
            print("="*60 + "\n")
            while True:
                user_val = input("Enter start date (DD-MM-YYYY): ").strip()
                try:
                    parsed = datetime.datetime.strptime(user_val, "%d-%m-%Y").date()
                    if parsed > datetime.date.today():
                        print("[!] The date cannot be in the future. Please try again.")
                        continue
                    db_manager.set_initial_start_date(parsed.strftime("%Y-%m-%d"))
                    current_start = parsed
                    break
                except ValueError:
                    print("[!] Invalid date format. Please use DD-MM-YYYY format.")
            
    while True:
        
        # 2. Check if daily limit is reached for the day
        scraped_today = db_manager.get_scraped_today_count()
        limit_str = config.DAILY_LIMIT if config.DAILY_LIMIT is not None else "unlimited"
        print(f"[*] Daily limit check: {scraped_today} / {limit_str} leads scraped today.")
        if config.DAILY_LIMIT is not None and scraped_today >= config.DAILY_LIMIT:
            # We sleep until tomorrow morning (or Monday morning if tomorrow is Sunday)
            now = datetime.datetime.now()
            tomorrow = now.date() + datetime.timedelta(days=1)
            if tomorrow.weekday() == 6:
                tomorrow = tomorrow + datetime.timedelta(days=1)
            tomorrow_start = datetime.datetime.combine(tomorrow, datetime.time(8, 0, 0))
            sleep_seconds = (tomorrow_start - now).total_seconds()
            
            print(f"\n[!] Daily scraping limit of {config.DAILY_LIMIT} leads has already been reached for today.")
            print(f"[*] Sleeping until tomorrow morning ({tomorrow_start.strftime('%A, %I:%M %p')}) for {sleep_seconds/3600:.1f} hours...")
            scheduler._incremental_sleep(sleep_seconds)
            continue
            
        # Create the randomized delay generator
        delay_pool = DelayPool(config.MIN_DELAY, config.MAX_DELAY)
        
        # Initialize Playwright for this run window
        with sync_playwright() as p:
            print("[*] Launching Chromium browser with persistent profile...")
            os.makedirs(config.CHROME_PROFILE_DIR, exist_ok=True)
            
            # Clean up stale lock files left behind by previous crashed browser sessions.
            # Without this, Chromium refuses to start with "Failed to create a ProcessSingleton".
            for lock_file in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
                lock_path = os.path.join(config.CHROME_PROFILE_DIR, lock_file)
                try:
                    if os.path.exists(lock_path) or os.path.islink(lock_path):
                        os.remove(lock_path)
                        print(f"[*] Removed stale lock file: {lock_path}")
                except Exception as e:
                    print(f"[!] Warning: Could not remove {lock_path}: {e}")
            
            context = p.chromium.launch_persistent_context(
                user_data_dir=config.CHROME_PROFILE_DIR,
                headless=config.HEADLESS,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--excludeSwitches=enable-automation",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-gpu"
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
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
            """)
            
            # Go to starting URL
            print(f"[*] Navigating to {config.START_URL} (timeout 60s)...")
            try:
                page.goto(config.START_URL, timeout=60000)
            except Exception as goto_err:
                print(f"[!] Warning: Navigation to {config.START_URL} timed out or encountered an error: {goto_err}")
                print("[*] Attempting to proceed as the page might have loaded partially...")
            
            # Check if we are already logged in (skip prompt if container is visible within 5s)
            is_logged_in = False
            try:
                page.wait_for_selector(config.LEFT_PANE_SCROLL_CONTAINER, timeout=5000)
                is_logged_in = True
                print("[*] Detected active session and Lead Manager. Skipping manual login prompt...")
            except:
                pass
                
            if not is_logged_in:
                # Action required prompt to login
                print("\n" + "!" * 80)
                print(" ACTION REQUIRED:")
                print(" 1. Please LOG IN to your IndiaMART account in the browser window.")
                print(" 2. Navigate to your Lead Manager (All Contacts) screen.")
                print(" 3. Make sure the screen looks like the split pane (contacts on left, details on right).")
                print(" 4. ONCE YOU ARE READY, press ENTER in this terminal to start scraping.")
                print("!" * 80 + "\n")
                
                input("Press [ENTER] when you have logged in and loaded the Lead Manager...")
            
            print("[*] Beginning scraping loop...")
            
            # Start monthly scraping loop
            while True:
                # If we are in CLI mode and already scraped the specific period, exit this loop
                if cli_mode and start_date is None:
                    break
                
                # Determine current start/end dates
                if cli_mode:
                    current_start = start_date
                    current_end = end_date
                    # Clear start_date so we only run once
                    start_date = None
                    end_date = None
                else:
                    last_day = _last_day_of_month(current_start)
                    today = datetime.date.today()
                    
                    # If current start is in the future, we caught up
                    if current_start > today:
                        print(f"[*] Next period start {current_start} is in the future (today is {today}).")
                        break
                        
                    # Cap current_end to today since future calendar days are disabled
                    current_end = min(last_day, today)
                    
                    # Skip already completed periods (past months)
                    if current_start.strftime("%Y-%m-%d") in completed_periods:
                        print(f"[*] Period {current_start} to {current_end} is already completed. Skipping.")
                        current_start = _first_of_next_month(current_start)
                        continue
                
                print(f"\n" + "=" * 60)
                print(f" Scraping Period: {current_start} to {current_end}")
                print("=" * 60)
                
                # Apply date filter
                set_custom_date_filter(page, current_start, current_end)
                
                # Reset scroll container to top to start clean
                try:
                    scroll_container = page.locator(config.LEFT_PANE_SCROLL_CONTAINER).first
                    if scroll_container.is_visible():
                        scroll_container.evaluate("el => el.scrollTop = 0")
                except:
                    pass
                    
                page.wait_for_timeout(3000)
                
                # Reload scraped keys at the start of each period
                scraped_keys = db_manager.get_scraped_keys()
                
                # Reset scroll and scraping counters for the new period
                scraped_in_period = 0
                scroll_attempts = 0
                max_scroll_attempts = 5
                last_scroll_top = -2
                reached_end_of_list = False
                
                while True:
                        
                    # Locate all visible contact card elements in the left panel
                    cards = page.locator(config.LEFT_PANE_ITEMS).all()
                    
                    if not cards:
                        print("[!] No contact cards found. Trying to wait for page to render...")
                        page.wait_for_timeout(5000)
                        cards = page.locator(config.LEFT_PANE_ITEMS).all()
                        if not cards:
                            print("[*] Still no cards found for this period. It might be an empty period.")
                            reached_end_of_list = True
                            break
                    
                    unscraped_card_name = None
                    unscraped_card_text = None
                    unscraped_key = None
                    
                    # Inspect visible cards to find the first unscraped one
                    # Note: We do NOT use consecutive duplicate limit here, since we want to scroll to bottom.
                    # Duplicates are skipped by `insert_lead`'s secondary suffix check.
                    for card in cards:
                        try:
                            if not is_valid_contact_card(card):
                                continue
                                
                            card_text = card.inner_text().strip()
                            # Split lines to build unique key
                            lines = [line.strip() for line in card_text.split('\n') if line.strip()]
                            if not lines:
                                continue
                            
                            unique_key = normalize_key(" ".join(lines))
                            
                            if unique_key in scraped_keys:
                                continue
                            
                            # Extract date
                            date_text = card.evaluate("""el => {
                                var dateEl = el.querySelector('span.fs12.clr77:not(.wrd_elip)');
                                if (dateEl) return dateEl.innerText.trim();
                                var spans = el.querySelectorAll('span.clr77');
                                for (var i = 0; i < spans.length; i++) {
                                    var txt = spans[i].innerText.trim();
                                    if (txt && !spans[i].classList.contains('wrd_elip')) {
                                        return txt;
                                    }
                                }
                                return "";
                            }""")
                            
                            unscraped_card_name = " ".join(lines[0].split())
                            unscraped_card_text = card_text
                            unscraped_key = unique_key
                            unscraped_card_date_text = date_text
                            break
                        except Exception as e:
                            continue
                    
                    if unscraped_card_name:
                        # Reset scroll attempts since we found a card to scrape
                        scroll_attempts = 0
                        
                        try:
                            # Verification click-retry loop
                            retry_count = 0
                            max_clicks = 3
                            click_success = False
                            
                            while retry_count < max_clicks:
                                try:
                                    print(f"\n[*] Clicking next unscraped card '{unscraped_card_name}' (Attempt {retry_count + 1}/{max_clicks})...")
                                    
                                    # Locate card dynamically by text to prevent stale recycled references
                                    # Uses scroll_to_find_card helper to bring card back into DOM if virtualized out
                                    card_locator = scroll_to_find_card(page, unscraped_card_name)
                                    
                                    # Double-safe click strategy:
                                    try:
                                        name_el = card_locator.locator(f"text={unscraped_card_name}").first
                                        name_el.scroll_into_view_if_needed(timeout=3000)
                                        page.wait_for_timeout(1000)
                                        name_el.click(timeout=3000)
                                    except Exception as inner_click_err:
                                        card_locator.scroll_into_view_if_needed(timeout=3000)
                                        page.wait_for_timeout(1000)
                                        card_locator.click(position={'x': 20, 'y': 20}, timeout=3000)
                                    
                                    # Wait for UI to update right pane
                                    page.wait_for_timeout(random.uniform(config.UI_PAUSE_MIN, config.UI_PAUSE_MAX) * 1000)
                                    
                                    # Open the details modal using "View More" button click
                                    view_more_btn = page.locator(config.VIEW_MORE_BTN).first
                                    if not view_more_btn.is_visible():
                                        view_more_btn = page.locator("text=View More").first
                                        
                                    if view_more_btn.is_visible():
                                        view_more_btn.click()
                                        page.wait_for_selector(config.MODAL_CONTAINER, timeout=5000)
                                        page.wait_for_timeout(1000)
                                    else:
                                        print("[!] 'View More' button not visible. Cannot verify card match.")
                                    
                                    # Read details from modal for matching check
                                    modal_name = ""
                                    modal_text = ""
                                    modal = page.locator(config.MODAL_CONTAINER).first
                                    if modal.is_visible():
                                        modal_text = modal.inner_text().strip()
                                        modal_name_el = page.locator(config.MODAL_NAME).first
                                        if modal_name_el.is_visible():
                                            modal_name = modal_name_el.inner_text().strip()
                                        else:
                                            lines = [l.strip() for l in modal_text.split('\n') if l.strip()]
                                            modal_name = lines[0] if lines else ""
                                    
                                    is_match = verify_card_match(unscraped_card_name, unscraped_card_text, modal_name, modal_text)
                                        
                                    if not is_match:
                                        print(f"[!] Name mismatch detected! Card Name: '{unscraped_card_name}' vs. Modal Name: '{modal_name}'.")
                                        close_modal_if_open(page)
                                        retry_count += 1
                                        page.wait_for_timeout(2000)
                                        
                                        # Dynamic scroll nudge to redraw/realign virtual list
                                        try:
                                            scroll_container = page.locator(config.LEFT_PANE_SCROLL_CONTAINER).first
                                            if scroll_container.is_visible():
                                                scroll_container.evaluate("el => el.scrollTop += 5")
                                                page.wait_for_timeout(500)
                                                scroll_container.evaluate("el => el.scrollTop -= 5")
                                                page.wait_for_timeout(500)
                                        except:
                                            pass
                                        continue
                                    else:
                                        print(f"[+] Name matched: Card '{unscraped_card_name}' matches Modal '{modal_name}'.")
                                        click_success = True
                                        break
                                except Exception as click_err:
                                    print(f"[!] Error clicking/verifying card: {click_err}")
                                    close_modal_if_open(page)
                                    retry_count += 1
                                    page.wait_for_timeout(2000)
                            
                            if not click_success:
                                print(f"[!] Failed to click/verify contact card after {max_clicks} attempts. Skipping.")
                                scraped_keys.add(unscraped_key)
                                continue
                            
                            # Scrape details
                            lead_data = scrape_right_pane(page, unscraped_key)
                            
                            if lead_data:
                                lead_data['lead_date'] = parse_indiamart_date(unscraped_card_date_text)
                                # Insert to SQLite database
                                inserted = db_manager.insert_lead(lead_data)
                                if inserted:
                                    scraped_count += 1
                                    scraped_in_period += 1
                                    # Append/Export to spreadsheets
                                    db_manager.export_to_formats()
                                    print(f"[+] Successfully saved lead #{scraped_count} ({lead_data['name']}) to SQLite and exported sheets.")
                                else:
                                    print(f"[*] Lead '{lead_data['name']}' already existed in SQLite database (skipped save).")
                                
                                # Check if run limit has been reached
                                if config.RUN_LIMIT and scraped_count >= config.RUN_LIMIT:
                                    print(f"\n[*] Reached the run limit of {config.RUN_LIMIT} leads for this run.")
                                    reached_run_limit = True
                                    break
                                
                                # Check if daily limit is reached
                                scraped_today = db_manager.get_scraped_today_count()
                                if config.DAILY_LIMIT is not None and scraped_today >= config.DAILY_LIMIT:
                                    print(f"\n[!] Reached the daily limit of {config.DAILY_LIMIT} leads scraped today. Stopping to stay safe.")
                                    reached_daily_limit = True
                                    break
                        except Exception as e:
                            print(f"[!] Error processing contact card: {e}")
                            print("[*] Attempting to close modal and recover...")
                            close_modal_if_open(page)
                        
                        # Always add key to memory set to avoid retrying the same broken card in this session
                        scraped_keys.add(unscraped_key)
                        
                        # Always apply the non-repeating random anti-bot delay after any card click attempt (success or fail)
                        delay = delay_pool.next_delay()
                        print(f"[*] Anti-bot delay: sleeping for {delay} seconds...")
                        time.sleep(delay)
                    else:
                        # All currently visible cards have been scraped, we must scroll left panel down
                        print("[*] All visible contacts on screen are scraped. Scrolling down left pane...")
                        
                        scroll_result = -1
                        try:
                            # Resolve scroll container using Playwright's locator
                            scroll_container = page.locator(config.LEFT_PANE_SCROLL_CONTAINER).first
                            if scroll_container.is_visible():
                                scroll_result = scroll_container.evaluate("el => { el.scrollTop += 500; return el.scrollTop; }")
                                print(f"[*] Left list container scrolled via configuration selector. Position: {scroll_result}")
                        except Exception as scroll_err:
                            print(f"[*] Configuration scroll failed, attempting generic viewport search: {scroll_err}")
                        
                        if scroll_result == -1:
                            # Fallback: search for elements with scroll height greater than client height inside the DOM
                            try:
                                scroll_result = page.evaluate("""() => {
                                    const divs = document.querySelectorAll('div');
                                    for (const d of divs) {
                                        const style = window.getComputedStyle(d);
                                        if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && d.scrollHeight > d.clientHeight) {
                                            // Ensure it's on the left side of screen (Lead List pane)
                                            const rect = d.getBoundingClientRect();
                                            if (rect.left < window.innerWidth / 2) {
                                                d.scrollTop += 500;
                                                return d.scrollTop;
                                            }
                                        }
                                    }
                                    return -1;
                                }""")
                                print(f"[*] Left list container scrolled via generic fallback. Position: {scroll_result}")
                            except Exception as fallback_err:
                                print(f"[!] Generic scroll failed: {fallback_err}")
                                scroll_result = -1
                        
                        # If scroll result is -1 or did not change after multiple attempts, check if we've reached the end
                        if scroll_result == -1:
                            scroll_attempts += 1
                            print(f"[!] Warning: Could not locate or scroll container. Attempt {scroll_attempts}/{max_scroll_attempts}")
                            if scroll_attempts >= max_scroll_attempts:
                                print("[!] Max scroll attempts reached without success. Marking period completed.")
                                reached_end_of_list = True
                                break
                            page.wait_for_timeout(5000)  # Wait 5s before retrying
                        else:
                            # Check if the scroll position actually changed
                            if scroll_result == last_scroll_top:
                                scroll_attempts += 1
                                print(f"[*] Scroll position did not change ({scroll_result}). Already at the bottom or locked. Attempt {scroll_attempts}/{max_scroll_attempts}")
                                if scroll_attempts >= max_scroll_attempts:
                                    print("[*] Reached bottom of scroll container. Marking period completed.")
                                    reached_end_of_list = True
                                    break
                            else:
                                scroll_attempts = 0  # Reset on successful new scroll
                                last_scroll_top = scroll_result
                            
                            # Sleep a random delay (e.g. 5 to 8 seconds) to let lazy-loading execute naturally
                            scroll_sleep = random.uniform(5.0, 8.0)
                            print(f"[*] Scroll successful. Waiting {scroll_sleep:.1f}s for lazy loading...")
                            page.wait_for_timeout(scroll_sleep * 1000)
                
                # Check exit condition of inner loop
                if reached_run_limit or reached_daily_limit:
                    break
                    
                if reached_end_of_list:
                    start_str = current_start.strftime("%Y-%m-%d")
                    end_str = current_end.strftime("%Y-%m-%d")
                    
                    last_day_date = _last_day_of_month(current_start)
                    today_date = datetime.date.today()
                    
                    # We only mark the month completed if it is fully in the past.
                    if cli_mode or last_day_date < today_date:
                        db_manager.mark_period_completed(start_str, end_str)
                        if not cli_mode:
                            completed_periods.add(start_str)
                            current_start = _first_of_next_month(current_start)
                    else:
                        print(f"[*] Finished scraping current month up to today ({end_str}). Not marking completed since month is ongoing.")
                        if not cli_mode:
                            # Break the inner scraping loop so it closes playwright and sleeps/waits
                            break
                            
                    if cli_mode:
                        print(f"[+] CLI Mode: Finished scraping specified range {start_str} to {end_str}.")
                        break
            
            print("\n" + "=" * 60)
            print(" SCRAPING PROCESS WINDOW FINISHED")
            print(f" Total new leads scraped in this window: {scraped_count}")
            print(f" SQLite DB: {os.path.abspath(config.DB_PATH)}")
            print(f" Excel Sheet: {os.path.abspath(config.EXCEL_PATH)}")
            print(f" CSV Sheet: {os.path.abspath(config.CSV_PATH)}")
            print("=" * 60)
            
            context.close()
            
        # Exit if we reached a run-specific limit (e.g., test limits) or in CLI mode
        if reached_run_limit or cli_mode:
            break
            
        # If we caught up to the current/future period, sleep 1 hour before checking again
        if not cli_mode:
            today_date = datetime.date.today()
            if current_start > today_date or _last_day_of_month(current_start) >= today_date:
                print(f"\n[*] Caught up to the current date. Active period start is {current_start} (today is {today_date}).")
                print("[*] Sleeping for 1 hour before checking again...")
                scheduler._incremental_sleep(3600)

if __name__ == "__main__":
    try:
        run_scraper()
    except KeyboardInterrupt:
        print("\n[!] Scraping process paused/interrupted by user. Progress has been safely saved.")
        sys.exit(0)
