import sys
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

with open("datepicker_clean.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

day_cells = soup.select("[class*='rdrDay']")
print(f"Found {len(day_cells)} day cells.")
for idx, day in enumerate(day_cells[:8]):
    print(f"[{idx+1}] Class: {day.get('class')} | Text: '{day.get_text().strip()}'")
    print(f"    Outer HTML: {str(day).replace('\n', ' ')[:300]}")
