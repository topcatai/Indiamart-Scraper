import sys
import re
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

with open("datepicker_body.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# Find divs/spans that have classes or IDs related to datepicker/calendar
print("=== Scanning for datepicker/calendar tags ===")
datepicker_divs = soup.find_all(lambda tag: tag.name == 'div' and (
    (tag.get('id') and 'calendar' in tag.get('id').lower()) or
    (tag.get('class') and any('calendar' in c.lower() or 'datepicker' in c.lower() for c in tag.get('class')))
))

for idx, div in enumerate(datepicker_divs):
    print(f"[{idx+1}] Div Tag: <{div.name}> | ID: '{div.get('id')}' | Class: {div.get('class')}")
    # Print first 500 characters of its content
    print(f"  Snippet: {str(div)[:500].replace('\n', ' ')}")

# If no container was found directly, search for any element containing the text 'July' or '2020' or days numbers
print("\n=== Searching for month/year labels or calendars by content ===")
july_els = soup.find_all(text=re.compile(r'July|2020|2025|2026', re.IGNORECASE))
print(f"Found {len(july_els)} text matches.")
for idx, text_el in enumerate(july_els[:10]):
    parent = text_el.parent
    print(f"  [{idx+1}] Text: '{text_el.strip()}' | Parent Tag: <{parent.name}> | Class: {parent.get('class')} | ID: '{parent.get('id')}'")
    # Print parent's parent to see nesting
    if parent.parent:
        print(f"    Parent's Parent: <{parent.parent.name}> | Class: {parent.parent.get('class')}")

# Let's write the entire calendar DOM to a text file for deep inspection
# We can search for the calendar overlay by looking for absolute positioning on body's direct children
print("\n=== Body's Direct Children that might be the overlay ===")
for idx, child in enumerate(soup.body.find_all(recursive=False)):
    classes = child.get('class', [])
    style = child.get('style', '')
    text = child.get_text().strip()[:100].replace('\n', ' ')
    print(f"  [{idx+1}] <{child.name}> | Class: {classes} | Style: '{style}' | Text snippet: '{text}'")
    if 'calendar' in str(child).lower() or 'datepicker' in str(child).lower() or 'date-picker' in str(child).lower():
        print("    [!] This child contains calendar keywords!")
        # Let's save this specific overlay subtree to a file
        with open(f"calendar_overlay_{idx+1}.html", "w", encoding="utf-8") as out:
            out.write(child.prettify())
        print(f"    [+] Saved calendar_overlay_{idx+1}.html")
