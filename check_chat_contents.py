import sys
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

def check_chat(filename):
    print(f"\n=== Chat message logs in {filename} ===")
    with open(filename, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    # Message items matching config.CHAT_MESSAGE_ITEMS
    messages = soup.select("div[class*='left_side_msg'], div[class*='right_side_msg']")
    print(f"Total message items: {len(messages)}")
    for idx, msg in enumerate(messages[:5]):
        print(f"  [{idx+1}] Text: {msg.get_text().strip().replace('\n', ' ')}")

check_chat("indiamarthtml.txt")
check_chat("indiamarthtml2.txt")
