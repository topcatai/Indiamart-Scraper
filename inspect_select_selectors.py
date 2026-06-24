import sys
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

with open("datepicker_body.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

datepicker = soup.find(id="customDatePicker")
if not datepicker:
    print("[-] #customDatePicker not found in DOM dump!")
    sys.exit(1)

# Find all select elements inside datepicker
selects = datepicker.find_all("select")
print(f"Found {len(selects)} select elements:")
for idx, s in enumerate(selects):
    # Print select tag and its options
    parent_classes = s.parent.get('class') if s.parent else []
    print(f"  [{idx+1}] <select> Class: {s.get('class')} | Sibling/Parent Class: {parent_classes}")
    options = [o.get_text().strip() for o in s.find_all("option")]
    print(f"      Options (first 5): {options[:5]}")
    print(f"      Options (last 5): {options[-5:]}")
    # Print outer HTML of select
    print(f"      Outer HTML: {str(s)[:250]}...")

# Find day buttons/grid inside datepicker
# Usually, day picker cells have classes like .rdrDay, .rdrDayNumber, or just buttons
print("\n--- Day Cells/Buttons ---")
day_buttons = datepicker.find_all(class_=lambda c: c and any('day' in c.lower() for c in c))
print(f"Found {len(day_buttons)} day elements.")
for idx, day in enumerate(day_buttons[:15]):
    print(f"  [{idx+1}] Tag: <{day.name}> | Class: {day.get('class')} | Text: '{day.get_text().strip()}'")
    # outer HTML
    print(f"      Outer HTML: {str(day)[:180].replace('\n', ' ')}")
    
# Let's write the clean pretty HTML of customDatePicker to a file
with open("datepicker_clean.html", "w", encoding="utf-8") as out:
    out.write(datepicker.prettify())
print("\nSaved datepicker_clean.html for inspection.")
