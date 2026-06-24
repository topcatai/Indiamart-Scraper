import sys
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

with open("indiamarthtml2.txt", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

popup = soup.select_one("#filterPopup")
if not popup:
    print("[-] #filterPopup not found in indiamarthtml2.txt!")
    sys.exit(1)

print("[+] #filterPopup found!")
with open("filter_popup_structure.html", "w", encoding="utf-8") as out:
    out.write(popup.prettify())
print("Saved filter_popup_structure.html")

# Let's search for "Date" section and input elements
print("\n--- Analysing Inputs and Dropdowns inside #filterPopup ---")
# Find all select dropdowns, inputs, textareas
inputs = popup.find_all(['select', 'input', 'button', 'span', 'div'])
print(f"Total element count in popup: {len(popup.find_all())}")

# Search specifically for text matches related to "Date"
date_elements = []
for el in popup.find_all(True):
    text = el.get_text().strip()
    if "Date" in text or "Start Date" in text or "End Date" in text:
        date_elements.append(el)

print(f"Found {len(date_elements)} elements matching 'Date'")
# Print elements that look like sections
for idx, el in enumerate(date_elements[:15]):
    # Let's print tag name and first line of text
    text_clean = el.get_text().strip().replace('\n', ' ')[:120]
    print(f"  [{idx+1}] Tag: <{el.name}> | Class: {el.get('class')} | Style: {el.get('style')} | Text: '{text_clean}'")
