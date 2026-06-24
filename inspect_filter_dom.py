import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

with open("indiamarthtml2.txt", "r", encoding="utf-8") as f:
    content = f.read()

matches = [m.start() for m in re.finditer('FILTER_OPEN_CTA', content)]
print(f"Matches count: {len(matches)}")
for idx, pos in enumerate(matches):
    start = max(0, pos - 150)
    end = min(len(content), pos + 150)
    print(f"\nMatch {idx+1} (offset {pos}):")
    print(content[start:end].replace('\n', ' '))
