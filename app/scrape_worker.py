import re
import random
import datetime
import calendar
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
import db_manager
import config

# --- Copy helper functions from scraper.py to avoid Playwright dependency on import ---

def normalize_key(text):
    """Creates a clean, lowercase unique key from text for deduplication."""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    return cleaned[:128]

def extract_phone_numbers(text):
    """Scans text for phone numbers of various formats and returns them as a comma-separated string."""
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}'
    matches = re.finditer(phone_pattern, text)
    numbers = []
    for match in matches:
        num = match.group().strip()
        cleaned_num = re.sub(r'[^\d+]', '', num)
        if len(cleaned_num) >= 10:
            numbers.append(cleaned_num)
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
    gst_pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b'
    matches = re.findall(gst_pattern, text, re.IGNORECASE)
    if matches:
        return matches[0].upper()
    return None

def verify_card_match(card_name, card_text, modal_name, modal_text):
    """Robust verification checking if the details modal matches the clicked contact card."""
    card_clean = re.sub(r'[^a-zA-Z0-9]', '', card_name).lower()
    modal_clean = re.sub(r'[^a-zA-Z0-9]', '', modal_name).lower()
    
    if card_clean[:4] == modal_clean[:4] and card_clean[:4] != "":
        return True
        
    if len(card_clean) > 2:
        modal_text_clean = re.sub(r'[^a-zA-Z0-9]', '', modal_text).lower()
        if card_clean[:6] in modal_text_clean:
            return True
            
    card_lines = [l.strip() for l in card_text.split('\n') if l.strip()]
    modal_text_lower = modal_text.lower()
    
    for line in card_lines[1:]:
        line_clean = line.lower().strip()
        if not line_clean:
            continue
        if any(w in line_clean for w in ["am", "pm", "yesterday", "ago", "call attempted", "enquiry", "rate now"]):
            continue
        if len(line_clean) > 3 and line_clean in modal_text_lower:
            return True
            
    return False

def _last_day_of_month(d):
    """Return the last day of the month for date d."""
    _, last_day = calendar.monthrange(d.year, d.month)
    return d.replace(day=last_day)

def _first_of_next_month(d):
    """Return the first day of the month after date d."""
    if d.month == 12:
        return d.replace(year=d.year + 1, month=1, day=1)
    return d.replace(month=d.month + 1, day=1)


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
        return self.pool.pop()


# --- JS Bridge Helpers within worker thread ---

def _navigate_calendar_to(js_bridge, target_year, target_month_idx):
    year_sel = "#customDatePicker .rdrYearPicker select"
    month_sel = "#customDatePicker .rdrMonthPicker select"
    
    current_year = js_bridge.get_value(year_sel)
    current_month = js_bridge.get_value(month_sel)
    
    if current_year is None or current_month is None:
        raise RuntimeError("Custom date picker selects not found in DOM.")
    
    if current_year != str(target_year):
        if not js_bridge.select_option(year_sel, str(target_year)):
            raise RuntimeError(f"Could not select year: {target_year}")
        QThread.msleep(500)
        
    if current_month != str(target_month_idx):
        if not js_bridge.select_option(month_sel, str(target_month_idx)):
            raise RuntimeError(f"Could not select month index: {target_month_idx}")
        QThread.msleep(1000)

def _click_calendar_day(js_bridge, day_num):
    script = f"""
    (function() {{
        var buttons = _utils.getElements("#customDatePicker button.rdrDay:not(.rdrDayPassive):not(.rdrDayDisabled)");
        var target = "{day_num}".trim();
        for (var i = 0; i < buttons.length; i++) {{
            var btn = buttons[i];
            var numSpan = btn.querySelector('.rdrDayNumber span');
            var text = numSpan ? numSpan.innerText.trim() : btn.innerText.trim();
            if (text === target) {{
                _utils.click(btn);
                return true;
            }}
        }}
        return false;
    }})()
    """
    res = js_bridge.execute_js(script)
    QThread.msleep(1000)
    return bool(res)

def set_custom_date_filter(js_bridge, start_date, end_date, worker=None):
    if worker:
        worker.status_message.emit(f"Applying date filter: {start_date} to {end_date}...")
    
    try:
        # Let any previous popup close transition settle first
        QThread.msleep(600)

        # 1. Click filter icon if popup not visible
        if not js_bridge.is_visible("#filterPopup"):
            if not js_bridge.click("#filterCTA"):
                raise RuntimeError("Could not click filter button (#filterCTA)")
            QThread.msleep(1000)
            if not js_bridge.wait_for_selector("#filterPopup", timeout_ms=3000):
                raise RuntimeError("Filter popup did not become visible after clicking #filterCTA")
            
        # 2. Click Filters tab with verification and retry
        filters_tab_activated = False
        for attempt in range(3):
            # Check if Filters tab is active
            filters_tab_activated = js_bridge.execute_js("""
            (function() {
                var tabs = document.querySelectorAll(".label-filter-tab");
                for (var i = 0; i < tabs.length; i++) {
                    var span = tabs[i].querySelector("span[title='Filters']");
                    if (span) {
                        if (tabs[i].classList.contains('active')) {
                            return true;
                        }
                        // Not active, try clicking both the tab container and the span
                        _utils.click(tabs[i]);
                        _utils.click(span);
                        return false;
                    }
                }
                return false;
            })()
            """)
            if filters_tab_activated:
                break
            QThread.msleep(800)
            
        if not filters_tab_activated:
            raise RuntimeError("Could not activate 'Filters' tab")
        
        # 3 & 4. Select "Custom Date" from Date dropdown
        # Check if "Custom Date" is already the active selection
        date_already_custom = js_bridge.execute_js("""
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
            # Need to open dropdown and select Custom Date
            # First click the Date dropdown trigger to open the options list
            if not js_bridge.click("xpath=//div[contains(., 'Date :')]//span[contains(@class, 'drpdwn')]"):
                raise RuntimeError("Could not click Date dropdown")
            QThread.msleep(800)
            
            # Click #customdatelispan (only exists while dropdown is open)
            if not js_bridge.click("#customdatelispan"):
                # Fallback: try clicking by text within the open dropdown
                fallback_script = """
                (function() {
                    var spans = document.querySelectorAll('.dropdown_list span.spncls');
                    for (var i = 0; i < spans.length; i++) {
                        if (spans[i].innerText.trim() === 'Custom Date') {
                            _utils.click(spans[i]);
                            return true;
                        }
                    }
                    return false;
                })()
                """
                if not js_bridge.execute_js(fallback_script):
                    raise RuntimeError("Could not click 'Custom Date' option")
            QThread.msleep(1500)
        else:
            if worker:
                worker.log("[*] Custom Date already selected, skipping dropdown selection.")
            QThread.msleep(500)
        
        # 5. Click Start Date target
        if not js_bridge.click("#custom_date_start"):
            raise RuntimeError("Could not click start date target (#custom_date_start)")
        if not js_bridge.wait_for_selector("#customDatePicker", timeout_ms=3000):
            raise RuntimeError("Calendar popup (#customDatePicker) did not become visible.")
        QThread.msleep(500)
        
        # 6. Navigate start year/month
        start_month_val = start_date.month - 1
        start_year_val = start_date.year
        _navigate_calendar_to(js_bridge, start_year_val, start_month_val)
        
        # 7. Click start day
        if not _click_calendar_day(js_bridge, start_date.day):
            raise RuntimeError(f"Could not click start day: {start_date.day}")
        
        # 7.5 Click End Date target to switch focus to end date input
        if not js_bridge.click("#custom_date_end"):
            raise RuntimeError("Could not click end date target (#custom_date_end)")
        QThread.msleep(500)
        
        # 8. Navigate end year/month (if different)
        end_month_val = end_date.month - 1
        end_year_val = end_date.year
        if start_month_val != end_month_val or start_year_val != end_year_val:
            _navigate_calendar_to(js_bridge, end_year_val, end_month_val)
            
        # 9. Click end day
        if not _click_calendar_day(js_bridge, end_date.day):
            raise RuntimeError(f"Could not click end day: {end_date.day}")
        
        # 10. Click Apply
        click_apply_script = """
        (function() {
            var buttons = _utils.getElements("#filterPopup div.small_btn_filled_std");
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].innerText.trim() === 'Apply') {
                    _utils.click(buttons[i]);
                    return true;
                }
            }
            return false;
        })()
        """
        if not js_bridge.execute_js(click_apply_script):
            raise RuntimeError("Could not click Apply button")
        QThread.msleep(3000)
        return True
    except Exception as e:
        if worker:
            worker.log(f"Error setting custom date filter: {e}")
            # Diagnostics: dump calendar DOM to datepicker_error.html
            try:
                picker_html = js_bridge.execute_js("document.getElementById('customDatePicker') ? document.getElementById('customDatePicker').outerHTML : (document.getElementById('filterPopup') ? document.getElementById('filterPopup').outerHTML : document.body.innerHTML)")
                with open("datepicker_error.html", "w", encoding="utf-8") as f:
                    f.write(picker_html or "")
                worker.log("[Diagnostic] Dumped calendar DOM to datepicker_error.html")
            except Exception as dump_err:
                worker.log(f"[Diagnostic] Failed to dump calendar: {dump_err}")
                
            worker.status_message.emit("Automated date filter failed. Prompting user...")
            start_str = start_date.strftime("%d %b %Y")
            end_str = end_date.strftime("%d %b %Y")
            # Emit signal. Since main window will connect using BlockingQueuedConnection,
            # this will block the worker thread until the user dismisses the dialog.
            worker.manual_filter_needed.emit(start_str, end_str)
            return True
        return False

def scroll_to_find_card(js_bridge, card_name, max_scrolls=6):
    sel = card_name.replace('"', '\\"')
    find_script = f"""
    (function() {{
        var cards = _utils.getElements("{config.LEFT_PANE_ITEMS}");
        var search = "{sel}".replace(/\\s+/g, ' ').trim();
        for (var i = 0; i < cards.length; i++) {{
            var text = cards[i].innerText.replace(/\\s+/g, ' ').trim();
            if (text.includes(search)) {{
                cards[i].scrollIntoView({{block: 'center'}});
                return true;
            }}
        }}
        return false;
    }})()
    """
    if js_bridge.execute_js(find_script):
        return True
        
    scroll_container = config.LEFT_PANE_SCROLL_CONTAINER
    for direction in [1, -1]:
        for _ in range(max_scrolls):
            scroll_script = f"""
            (function() {{
                var container = _utils.getElement("{scroll_container}");
                if (container) {{
                    container.scrollTop += {direction * 300};
                    return container.scrollTop;
                }}
                return -1;
            }})()
            """
            js_bridge.execute_js(scroll_script)
            QThread.msleep(500)
            if js_bridge.execute_js(find_script):
                return True
    return False

def close_modal_if_open(js_bridge):
    if js_bridge.is_visible(config.MODAL_CONTAINER):
        if js_bridge.is_visible(config.MODAL_CLOSE_BTN):
            js_bridge.click(config.MODAL_CLOSE_BTN)
        else:
            escape_script = """
            var e = new KeyboardEvent('keydown', { bubbles: true, cancelable: true, key: 'Escape', keyCode: 27 });
            document.dispatchEvent(e);
            """
            js_bridge.execute_js(escape_script)
        QThread.msleep(1000)

def scrape_conversation_history(js_bridge):
    scroll_chat_script = f"""
    (function() {{
        var chat = _utils.getElement("{config.CHAT_MESSAGE_CONTAINER}");
        if (chat) {{
            chat.scrollTop = 0;
            return true;
        }}
        return false;
    }})()
    """
    js_bridge.execute_js(scroll_chat_script)
    QThread.msleep(500)
    
    scrape_messages_script = f"""
    (function() {{
        var messages = _utils.getElements("{config.CHAT_MESSAGE_ITEMS}");
        var chatLines = [];
        for (var i = 0; i < messages.length; i++) {{
            var loc = messages[i];
            if (loc.offsetWidth === 0) continue;
            var cls = loc.className || "";
            var rawText = loc.innerText.trim();
            if (!rawText) continue;
            
            var timestamp = "";
            var tsLoc = loc.querySelector(".time_stamp");
            if (tsLoc) {{
                timestamp = tsLoc.innerText.trim();
            }} else {{
                var sibling = loc.nextElementSibling;
                while (sibling) {{
                    if (sibling.classList.contains("time_stamp") || sibling.querySelector(".time_stamp")) {{
                        var innerTs = sibling.classList.contains("time_stamp") ? sibling : sibling.querySelector(".time_stamp");
                        timestamp = innerTs.innerText.trim();
                        break;
                    }}
                    sibling = sibling.nextElementSibling;
                }}
                if (!timestamp) {{
                    var parent = loc.parentElement;
                    if (parent) {{
                        var parentTs = parent.querySelector(".time_stamp");
                        if (parentTs) {{
                            timestamp = parentTs.innerText.trim();
                        }}
                    }}
                }}
            }}
            if (timestamp && rawText.includes(timestamp)) {{
                rawText = rawText.replace(timestamp, "").trim();
            }}
            
            var cleanText = rawText.replace(/\\n+/g, " ").replace(/\\s+/g, " ").trim();
            var sender = "System";
            if (cls.includes("left_side_msg")) {{
                sender = "Buyer";
            }} else if (cls.includes("right_side_msg")) {{
                sender = "Seller";
            }}
            
            var tsPrefix = timestamp ? "[" + timestamp + "] " : "";
            chatLines.push(tsPrefix + sender + ": " + cleanText);
        }}
        return chatLines.join("\\n");
    }})()
    """
    return js_bridge.execute_js(scrape_messages_script) or ""

def scrape_right_pane(js_bridge, unique_key):
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
    
    lead_data['contact_type'] = js_bridge.get_text(config.CONTACT_TYPE_BANNER) or "Unknown"
    
    req_box_text = js_bridge.get_text(config.REQUIREMENT_BOX)
    if not req_box_text:
        fallback_xpath = "xpath=//div[contains(@class, 'card') and (contains(., 'Milling') or contains(., 'Machine') or contains(., 'CNC') or contains(., 'Fiber'))]"
        req_box_text = js_bridge.get_text(fallback_xpath)
    lead_data['requirement_details'] = req_box_text or ""
    
    if not js_bridge.is_visible(config.MODAL_CONTAINER):
        if js_bridge.is_visible(config.VIEW_MORE_BTN):
            js_bridge.click(config.VIEW_MORE_BTN)
        else:
            js_bridge.click("xpath=//*[text()='View More']")
        js_bridge.wait_for_selector(config.MODAL_CONTAINER, 5000)
        QThread.msleep(1000)
        
    if js_bridge.is_visible(config.MODAL_CONTAINER):
        modal_text = js_bridge.get_text(config.MODAL_CONTAINER) or ""
        
        modal_name = js_bridge.get_text(config.MODAL_NAME)
        if modal_name:
            lead_data['name'] = modal_name.strip()
        else:
            lines = [l.strip() for l in modal_text.split('\n') if l.strip()]
            lead_data['name'] = lines[0] if lines else "Unknown"
            
        email_script = f"""
        (function() {{
            var modal = _utils.getElement("{config.MODAL_CONTAINER}");
            if (!modal) return null;
            var link = modal.querySelector("a[href^='mailto:']");
            return link ? link.getAttribute("href").replace("mailto:", "").trim() : null;
        }})()
        """
        email_val = js_bridge.execute_js(email_script)
        if email_val:
            lead_data['email_id'] = email_val
        else:
            lead_data['email_id'] = extract_emails(modal_text) or ""
            
        phone_script = f"""
        (function() {{
            var modal = _utils.getElement("{config.MODAL_CONTAINER}");
            if (!modal) return null;
            var link = modal.querySelector("a[href^='tel:']");
            return link ? link.getAttribute("href").replace("tel:", "").trim() : null;
        }})()
        """
        phone_val = js_bridge.execute_js(phone_script)
        if phone_val:
            lead_data['phone_number'] = phone_val
        else:
            lead_data['phone_number'] = extract_phone_numbers(modal_text) or ""
            
        address_lines = []
        lines = [line.strip() for line in modal_text.split('\n')]
        for idx, line in enumerate(lines):
            if line.upper() == "ADDRESS" and idx + 1 < len(lines):
                address_lines.append(lines[idx + 1])
                break
        if address_lines:
            lead_data['address_location'] = address_lines[0]
        else:
            lead_data['address_location'] = (js_bridge.get_text(config.MODAL_ADDRESS) or "").replace("Address", "").replace("Location", "").strip()
            
        if "active on WhatsApp" in modal_text or "WhatsApp" in modal_text:
            whatsapp_text = js_bridge.get_text(config.MODAL_WHATSAPP) or ""
            if whatsapp_text:
                lead_data['whatsapp_status'] = whatsapp_text.strip()
            else:
                lead_data['whatsapp_status'] = "Active on WhatsApp" if "active on WhatsApp" in modal_text else "Yes"
        else:
            lead_data['whatsapp_status'] = "Not Active / Not Checked"
            
        gst_found = extract_gst_number(modal_text)
        lead_data['gst'] = gst_found if gst_found else "N/A"
    else:
        body_text = js_bridge.get_text("body") or ""
        lead_data['phone_number'] = extract_phone_numbers(body_text) or ""
        lead_data['email_id'] = extract_emails(body_text) or ""
        lead_data['gst'] = extract_gst_number(body_text) or ""
        
    lead_data['chat_history'] = scrape_conversation_history(js_bridge)
    close_modal_if_open(js_bridge)
    
    return lead_data


# --- Background Thread Class ---

class ScrapeWorker(QThread):
    lead_scraped = pyqtSignal(dict)
    status_message = pyqtSignal(str)
    all_contacts_found = pyqtSignal(int)
    finished = pyqtSignal()
    manual_filter_needed = pyqtSignal(str, str)
    log_message = pyqtSignal(str)

    def __init__(self, js_bridge):
        super().__init__()
        self.js_bridge = js_bridge
        self.mutex = QMutex()
        self.pause_cond = QWaitCondition()
        self.is_paused = False
        self.is_running = True
        self.retry_mode = False
        self.start_date_override = None


    def pause(self):
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()
        self.status_message.emit("Scraping paused by user.")

    def resume(self):
        self.mutex.lock()
        self.is_paused = False
        self.pause_cond.wakeAll()
        self.mutex.unlock()
        self.status_message.emit("Resuming scraping process...")

    def stop(self):
        self.mutex.lock()
        self.is_running = False
        self.is_paused = False
        self.pause_cond.wakeAll()
        self.mutex.unlock()
        self.status_message.emit("Scraping stopped.")

    def check_pause(self):
        self.mutex.lock()
        while self.is_paused and self.is_running:
            self.pause_cond.wait(self.mutex)
        self.mutex.unlock()


    def log(self, message):
        print(f"[Worker] {message}")
        self.log_message.emit(str(message))

    def read_all_contacts_count(self):
        script = """
        (function() {
            var el = document.querySelector('.allCntText');
            if (el) {
                var txt = el.innerText;
                var match = txt.match(/\\d+[,.\\d]*/);
                if (match) {
                    return parseInt(match[0].replace(/[,.]/g, ''), 10);
                }
            }
            return null;
        })()
        """
        val = self.js_bridge.execute_js(script)
        try:
            return int(val) if val is not None else None
        except:
            return None

    def run(self):
        self.is_running = True
        self.is_paused = False
        
        self.status_message.emit("Initializing database tables...")
        db_manager.init_db()
        
        if self.retry_mode:
            self.run_retry_loop()
        else:
            self.run_monthly_loop()
            
        self.finished.emit()

    def run_monthly_loop(self):
        self.status_message.emit("Loading completed periods...")
        completed_periods = db_manager.get_completed_periods()
        
        if hasattr(self, 'start_date_override') and self.start_date_override:
            current_start = self.start_date_override
            self.log(f"Custom scraping start date: {current_start}")
        else:
            max_lead_date = db_manager.get_max_lead_date()
            initial_date_str = db_manager.get_initial_start_date()
            last_completed = db_manager.get_last_completed_period()
            if max_lead_date:
                current_start = max_lead_date.replace(day=1)
                self.log(f"Resuming scraping from month of last scraped lead: {current_start}")
            elif last_completed:
                last_date = datetime.datetime.strptime(last_completed, "%Y-%m-%d").date()
                current_start = _first_of_next_month(last_date)
            elif initial_date_str:
                current_start = datetime.datetime.strptime(initial_date_str, "%Y-%m-%d").date()
            else:
                current_start = datetime.date.today()
            
        scraped_count = 0
        delay_pool = DelayPool(config.MIN_DELAY, config.MAX_DELAY)
        
        # Scan total contact count on start
        self.status_message.emit("Scanning total contact count from page...")
        all_contacts = self.read_all_contacts_count()
        if all_contacts:
            self.all_contacts_found.emit(all_contacts)
            
        while self.is_running:
            self.check_pause()
            if not self.is_running:
                break
                
            today = datetime.date.today()
            if current_start > today:
                self.status_message.emit("Scraper caught up to the current calendar date.")
                break
                
            last_day = _last_day_of_month(current_start)
            current_end = min(last_day, today)
            
            start_str = current_start.strftime("%Y-%m-%d")
            if start_str in completed_periods:
                current_start = _first_of_next_month(current_start)
                continue
                
            # Filter date range
            success = set_custom_date_filter(self.js_bridge, current_start, current_end, self)
            if not success:
                self.status_message.emit("Date filter failed. Retrying in 5 seconds...")
                QThread.msleep(5000)
                continue
                
            # Scroll to top of list container
            scroll_top_script = f"""
            (function() {{
                var container = _utils.getElement("{config.LEFT_PANE_SCROLL_CONTAINER}");
                if (container) container.scrollTop = 0;
            }})()
            """
            self.js_bridge.execute_js(scroll_top_script)
            QThread.msleep(3000)
            
            scraped_keys = db_manager.get_scraped_keys()
            scroll_attempts = 0
            max_scroll_attempts = 5
            last_scroll_top = -2
            reached_end_of_list = False
            
            while self.is_running:
                self.check_pause()
                if not self.is_running:
                    break
                    
                # Read all visible contact card texts
                get_cards_script = f"""
                (function() {{
                    var cards = _utils.getElements("xpath=//div[contains(@class, 'lftcntctnew')]");
                    var results = [];
                    for (var i = 0; i < cards.length; i++) {{
                        var h = cards[i].offsetHeight;
                        var w = cards[i].offsetWidth;
                        if (h >= 50 && h <= 220 && w >= 150 && w <= 600) {{
                            var txt = cards[i].innerText.trim();
                            if (txt && !txt.includes("All Contacts") && !txt.includes("Reminders") && txt.length < 1000) {{
                                var dateText = "";
                                var dateEl = cards[i].querySelector('span.fs12.clr77:not(.wrd_elip)');
                                if (dateEl) {{
                                    dateText = dateEl.innerText.trim();
                                }} else {{
                                    var spans = cards[i].querySelectorAll('span.clr77');
                                    for (var j = 0; j < spans.length; j++) {{
                                        var t = spans[j].innerText.trim();
                                        if (t && !spans[j].classList.contains('wrd_elip')) {{
                                            dateText = t;
                                            break;
                                        }}
                                    }}
                                }}
                                results.push({{
                                    text: txt,
                                    index: i,
                                    date_text: dateText
                                }});
                            }}
                        }}
                    }}
                    return results;
                }})()
                """
                cards_data = self.js_bridge.execute_js(get_cards_script)
                if not cards_data:
                    self.status_message.emit("Waiting for contact cards to load...")
                    QThread.msleep(5000)
                    cards_data = self.js_bridge.execute_js(get_cards_script)
                    if not cards_data:
                        reached_end_of_list = True
                        break
                        
                unscraped_card = None
                for cdata in cards_data:
                    card_text = cdata['text']
                    card_date_text = cdata.get('date_text', '')
                    lines = [line.strip() for line in card_text.split('\n') if line.strip()]
                    if not lines:
                        continue
                    ukey = normalize_key(" ".join(lines))
                    if ukey not in scraped_keys:
                        unscraped_card = {
                            'name': " ".join(lines[0].split()),
                            'text': card_text,
                            'key': ukey,
                            'date_text': card_date_text
                        }
                        break
                        
                if unscraped_card:
                    scroll_attempts = 0
                    card_name = unscraped_card['name']
                    card_key = unscraped_card['key']
                    
                    self.status_message.emit(f"Scraping lead: {card_name}...")
                    
                    # Try click/verify
                    click_success = False
                    for attempt in range(3):
                        self.check_pause()
                        if not self.is_running:
                            break
                            
                        # Scroll to find card
                        found = scroll_to_find_card(self.js_bridge, card_name)
                        if not found:
                            QThread.msleep(1000)
                            continue
                            
                        # Click card
                        click_script = f"""
                        (function() {{
                            var cards = _utils.getElements("{config.LEFT_PANE_ITEMS}");
                            var search = "{card_name.replace('"', '\\"')}".replace(/\\s+/g, ' ').trim();
                            for (var i = 0; i < cards.length; i++) {{
                                var txt = cards[i].innerText.replace(/\\s+/g, ' ').trim();
                                if (txt.includes(search)) {{
                                    var inner = Array.from(cards[i].querySelectorAll('span, div, p, a')).find(el => el.innerText.trim() === search);
                                    if (inner) {{
                                        inner.click();
                                    }} else {{
                                        cards[i].click();
                                    }}
                                    return true;
                                }}
                            }}
                            return false;
                        }})()
                        """
                        self.js_bridge.execute_js(click_script)
                        QThread.msleep(int(random.uniform(config.UI_PAUSE_MIN, config.UI_PAUSE_MAX) * 1000))
                        
                        # Open details modal
                        if not self.js_bridge.is_visible(config.MODAL_CONTAINER):
                            if self.js_bridge.is_visible(config.VIEW_MORE_BTN):
                                self.js_bridge.click(config.VIEW_MORE_BTN)
                            else:
                                self.js_bridge.click("xpath=//*[text()='View More']")
                            self.js_bridge.wait_for_selector(config.MODAL_CONTAINER, 5000)
                            QThread.msleep(1000)
                            
                        # Validate match
                        modal_name = ""
                        modal_text = ""
                        if self.js_bridge.is_visible(config.MODAL_CONTAINER):
                            modal_text = self.js_bridge.get_text(config.MODAL_CONTAINER) or ""
                            modal_name = self.js_bridge.get_text(config.MODAL_NAME) or ""
                            if not modal_name:
                                lines = [l.strip() for l in modal_text.split('\n') if l.strip()]
                                modal_name = lines[0] if lines else ""
                                
                        if verify_card_match(card_name, unscraped_card['text'], modal_name, modal_text):
                            click_success = True
                            break
                        else:
                            self.log(f"Mismatch: card '{card_name}' vs modal '{modal_name}'")
                            close_modal_if_open(self.js_bridge)
                            QThread.msleep(2000)
                            # Nudge list
                            nudge_script = f"""
                            (function() {{
                                var container = _utils.getElement("{config.LEFT_PANE_SCROLL_CONTAINER}");
                                if (container) {{
                                    container.scrollTop += 5;
                                    setTimeout(function() {{ container.scrollTop -= 5; }}, 500);
                                }}
                            }})()
                            """
                            self.js_bridge.execute_js(nudge_script)
                            QThread.msleep(1000)
                            
                    if not click_success:
                        self.log(f"Verification failed for card '{card_name}'. Saving to failed contacts...")
                        db_manager.insert_failed_contact(
                            card_key, card_name, unscraped_card['text'],
                            "Verification name mismatch or click failed",
                            start_str, current_end.strftime("%Y-%m-%d")
                        )
                        scraped_keys.add(card_key)
                        continue
                        
                    # Scrape details
                    try:
                        lead_data = scrape_right_pane(self.js_bridge, card_key)
                        lead_data['lead_date'] = parse_indiamart_date(unscraped_card.get('date_text', ''))
                        inserted = db_manager.insert_lead(lead_data)
                        if inserted:
                            scraped_count += 1
                            db_manager.export_to_formats()
                            self.lead_scraped.emit(lead_data)
                            self.status_message.emit(f"Successfully scraped lead #{scraped_count}: {lead_data['name']}")
                            db_manager.remove_failed_contact(card_key)
                        else:
                            self.status_message.emit(f"Skipped duplicate lead: {lead_data['name']}")
                    except Exception as scrape_err:
                        self.log(f"Error scraping details: {scrape_err}")
                        db_manager.insert_failed_contact(
                            card_key, card_name, unscraped_card['text'],
                            f"Scrape details error: {scrape_err}",
                            start_str, current_end.strftime("%Y-%m-%d")
                        )
                    finally:
                        close_modal_if_open(self.js_bridge)
                        
                    scraped_keys.add(card_key)
                    
                    # Anti-bot delay
                    delay = delay_pool.next_delay()
                    self.status_message.emit(f"Anti-bot delay: sleeping {delay}s...")
                    for d in range(delay):
                        self.check_pause()
                        if not self.is_running:
                            break
                        QThread.msleep(1000)
                else:
                    # Scroll down list
                    self.status_message.emit("Scanning scroll bottom... Scrolling down list panel.")
                    scroll_result = -1
                    scroll_container = config.LEFT_PANE_SCROLL_CONTAINER
                    scroll_script = f"""
                    (function() {{
                        var container = _utils.getElement("{scroll_container}");
                        if (container) {{
                            container.scrollTop += 500;
                            return container.scrollTop;
                        }}
                        return -1;
                    }})()
                    """
                    scroll_val = self.js_bridge.execute_js(scroll_script)
                    if scroll_val is not None:
                        scroll_result = int(scroll_val)
                        
                    if scroll_result == -1:
                        fallback_scroll = """
                        (function() {
                            var divs = document.querySelectorAll('div');
                            for (var i = 0; i < divs.length; i++) {
                                var d = divs[i];
                                var style = window.getComputedStyle(d);
                                if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && d.scrollHeight > d.clientHeight) {
                                    var rect = d.getBoundingClientRect();
                                    if (rect.left < window.innerWidth / 2) {
                                        d.scrollTop += 500;
                                        return d.scrollTop;
                                    }
                                }
                            }
                            return -1;
                        })()
                        """
                        res_val = self.js_bridge.execute_js(fallback_scroll)
                        if res_val is not None:
                            scroll_result = int(res_val)
                            
                    if scroll_result == -1:
                        scroll_attempts += 1
                        if scroll_attempts >= max_scroll_attempts:
                            reached_end_of_list = True
                            break
                        QThread.msleep(5000)
                    else:
                        if scroll_result == last_scroll_top:
                            scroll_attempts += 1
                            if scroll_attempts >= max_scroll_attempts:
                                reached_end_of_list = True
                                break
                        else:
                            scroll_attempts = 0
                            last_scroll_top = scroll_result
                            
                        scroll_sleep = random.uniform(5.0, 8.0)
                        QThread.msleep(int(scroll_sleep * 1000))
                        
            if reached_end_of_list:
                if current_end < today:
                    db_manager.mark_period_completed(start_str, current_end.strftime("%Y-%m-%d"))
                    completed_periods.add(start_str)
                    current_start = _first_of_next_month(current_start)
                else:
                    self.status_message.emit("Scraper caught up to the current ongoing month.")
                    break

    def run_retry_loop(self):
        self.status_message.emit("Fetching failed contacts from database...")
        failed_contacts = db_manager.get_failed_contacts()
        
        if not failed_contacts:
            self.status_message.emit("No failed contacts to retry.")
            return
            
        self.status_message.emit(f"Found {len(failed_contacts)} failed contacts to retry.")
        delay_pool = DelayPool(config.MIN_DELAY, config.MAX_DELAY)
        
        current_filter_start = None
        current_filter_end = None
        
        for failed in failed_contacts:
            self.check_pause()
            if not self.is_running:
                break
                
            card_key = failed['unique_key']
            card_name = failed['card_name']
            card_text = failed['card_text']
            p_start = failed['period_start']
            p_end = failed['period_end']
            
            self.status_message.emit(f"Retrying lead: {card_name}...")
            
            # Check/apply date filter
            if p_start != current_filter_start or p_end != current_filter_end:
                self.status_message.emit(f"Applying date filter for retry period: {p_start} to {p_end}...")
                s_date = datetime.datetime.strptime(p_start, "%Y-%m-%d").date()
                e_date = datetime.datetime.strptime(p_end, "%Y-%m-%d").date()
                
                success = set_custom_date_filter(self.js_bridge, s_date, e_date, self)
                if not success:
                    self.log(f"Failed to apply date filter for retry. Skipping {card_name}.")
                    continue
                current_filter_start = p_start
                current_filter_end = p_end
                QThread.msleep(3000)
                
            # Scroll to find card
            found = scroll_to_find_card(self.js_bridge, card_name)
            if not found:
                self.log(f"Card '{card_name}' could not be located in retry window.")
                continue
                
            # Click card
            self.check_pause()
            click_script = f"""
            (function() {{
                var cards = _utils.getElements("{config.LEFT_PANE_ITEMS}");
                var search = "{card_name.replace('"', '\\"')}".replace(/\\s+/g, ' ').trim();
                for (var i = 0; i < cards.length; i++) {{
                    var txt = cards[i].innerText.replace(/\\s+/g, ' ').trim();
                    if (txt.includes(search)) {{
                        var inner = Array.from(cards[i].querySelectorAll('span, div, p, a')).find(el => el.innerText.trim() === search);
                        if (inner) {{
                            inner.click();
                        }} else {{
                            cards[i].click();
                        }}
                        return true;
                    }}
                }}
                return false;
            }})()
            """
            self.js_bridge.execute_js(click_script)
            QThread.msleep(int(random.uniform(config.UI_PAUSE_MIN, config.UI_PAUSE_MAX) * 1000))
            
            # Open details modal
            if not self.js_bridge.is_visible(config.MODAL_CONTAINER):
                if self.js_bridge.is_visible(config.VIEW_MORE_BTN):
                    self.js_bridge.click(config.VIEW_MORE_BTN)
                else:
                    self.js_bridge.click("xpath=//*[text()='View More']")
                self.js_bridge.wait_for_selector(config.MODAL_CONTAINER, 5000)
                QThread.msleep(1000)
                
            # Validate match
            modal_name = ""
            modal_text = ""
            if self.js_bridge.is_visible(config.MODAL_CONTAINER):
                modal_text = self.js_bridge.get_text(config.MODAL_CONTAINER) or ""
                modal_name = self.js_bridge.get_text(config.MODAL_NAME) or ""
                if not modal_name:
                    lines = [l.strip() for l in modal_text.split('\n') if l.strip()]
                    modal_name = lines[0] if lines else ""
                    
            click_success = verify_card_match(card_name, card_text, modal_name, modal_text)
            
            if click_success:
                # Query card date text from the active card
                get_card_date_script = f"""
                (function() {{
                    var cards = _utils.getElements("xpath=//div[contains(@class, 'lftcntctnew')]");
                    var search = "{card_name.replace('"', '\\"')}".replace(/\\s+/g, ' ').trim();
                    for (var i = 0; i < cards.length; i++) {{
                        var txt = cards[i].innerText.replace(/\\s+/g, ' ').trim();
                        if (txt.includes(search)) {{
                            var dateEl = cards[i].querySelector('span.fs12.clr77:not(.wrd_elip)');
                            if (dateEl) return dateEl.innerText.trim();
                            var spans = cards[i].querySelectorAll('span.clr77');
                            for (var j = 0; j < spans.length; j++) {{
                                var t = spans[j].innerText.trim();
                                if (t && !spans[j].classList.contains('wrd_elip')) {{
                                    return t;
                                }}
                            }}
                        }}
                    }}
                    return "";
                }})()
                """
                retry_date_text = self.js_bridge.execute_js(get_card_date_script) or ""
                try:
                    lead_data = scrape_right_pane(self.js_bridge, card_key)
                    lead_data['lead_date'] = parse_indiamart_date(retry_date_text)
                    inserted = db_manager.insert_lead(lead_data)
                    if inserted:
                        db_manager.export_to_formats()
                        self.lead_scraped.emit(lead_data)
                        self.status_message.emit(f"Successfully scraped retry lead: {lead_data['name']}")
                    else:
                        self.status_message.emit(f"Lead '{lead_data['name']}' already saved.")
                    db_manager.remove_failed_contact(card_key)
                except Exception as scrape_err:
                    self.log(f"Error scraping details on retry: {scrape_err}")
                finally:
                    close_modal_if_open(self.js_bridge)
            else:
                self.log(f"Retry verification failed for: {card_name}")
                close_modal_if_open(self.js_bridge)
                
            # Random delay
            delay = delay_pool.next_delay()
            self.status_message.emit(f"Anti-bot delay: sleeping {delay}s...")
            for d in range(delay):
                self.check_pause()
                if not self.is_running:
                    break
                QThread.msleep(1000)
                
        self.status_message.emit("Retry failed contacts complete.")
