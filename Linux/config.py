# IndiaMART Scraper Configuration Settings

# --- Persistence & Output Paths ---
DB_PATH = "indiamart_leads.db"
EXCEL_PATH = "indiamart_leads.xlsx"
CSV_PATH = "indiamart_leads.csv"
CHROME_PROFILE_DIR = ".chrome_session"  # Persistent user session data

# --- Scraping Limits ---
# Set to None to run the full scraper without limit.
# Change to a number to stop early for testing.
RUN_LIMIT = None
DAILY_LIMIT = None
HEADLESS = False

# --- Anti-Bot / Delay settings (Seconds) ---
MIN_DELAY = 10
MAX_DELAY = 20
UI_PAUSE_MIN = 2.0  # Safe delay after clicks/navigation to let UI render
UI_PAUSE_MAX = 4.0


# --- Target Website ---
START_URL = "https://seller.indiamart.com/"

# --- CSS / XPath Selectors ---
# These selectors are designed to be generic. Since many modern websites use obfuscated or
# dynamic class names, we prioritize text-matching (Playwright locators) and generic patterns.

# 1. Left panel list selectors
# Scrollable container for the list of contact cards
LEFT_PANE_SCROLL_CONTAINER = "xpath=//div[contains(@class, 'ReactVirtualized__List') or contains(@class, 'list_split_view')]"
# Individual contact card elements inside the left panel list
LEFT_PANE_ITEMS = "xpath=//div[contains(@class, 'lftcntctnew')]"

# 2. Right pane / details panel selectors (in plain view)
# Contact Type banner (e.g. "Contact added through BuyLead consumed" or "Contact added through Enquiry received")
CONTACT_TYPE_BANNER = "xpath=//*[contains(text(), 'Contact added through')]"
# Requirement box (contains product name, specifications, and timestamp)
REQUIREMENT_BOX = "css=div.BuyLdC_brd"

# 3. View More button selector
# Button to open the full contact details modal
VIEW_MORE_BTN = "css=#viewDetails"

# 4. Details Modal popup selectors (when View More is clicked)
MODAL_CONTAINER = "css=aside.buyerNw, aside.nvd-media-aside"
# Modal Close Button
MODAL_CLOSE_BTN = "css=aside.buyerNw span.pof"

# Individual fields in the modal (fallback to text-based matching)
MODAL_NAME = "css=aside.buyerNw .newvdtl span[style*='font-weight: 700'], aside.buyerNw .newvdtl span[style*='font-weight: bold'], aside.buyerNw .newvdtl .nvd-avatar-rating-wrap + div > div > span"
MODAL_PHONE = "css=aside.buyerNw span.ml5"
MODAL_EMAIL = "css=aside.buyerNw span.ml5"
MODAL_ADDRESS = "css=aside.buyerNw div.nvd-contact-row-address span.nvd-contact-row-text, aside.buyerNw div.nvd-header-address-col span.ml5"
MODAL_WHATSAPP = "css=aside.buyerNw"
MODAL_GST = "css=aside.buyerNw"

# 5. Chat History Selectors
CHAT_MESSAGE_CONTAINER = "xpath=//div[contains(@class, 'infinite-scroll-component') or contains(@style, 'overflow-y')]"
CHAT_MESSAGE_ITEMS = "xpath=//div[contains(@class, 'left_side_msg') or contains(@class, 'right_side_msg') or contains(@class, 'contact-source-div') or contains(@class, 'contact_source_div')]"


# --- GUI Settings ---
GUI_WINDOW_TITLE = "IndiaMART Lead Scraper"
GUI_WINDOW_WIDTH = 1400
GUI_WINDOW_HEIGHT = 850
GUI_SESSION_DIR = ".gui_chrome_session"

# --- Support & Feedback (Codeberg Repo) ---
# Locked configuration: adjustments are based on user feedback.
CODEBERG_REPO_URL = "https://codeberg.org/YOUR_USERNAME/YOUR_REPO_NAME"
CODEBERG_ISSUES_URL = f"{CODEBERG_REPO_URL}/issues"




