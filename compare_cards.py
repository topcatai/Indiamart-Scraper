import sys
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

with open("indiamarthtml2.txt", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

cards = soup.select("div[class*='lftcntctnew']")
print(f"Found {len(cards)} cards.")

for idx, card in enumerate(cards):
    print(f"\n--- Card {idx+1} (ID: {card.get('id')}) ---")
    print(f"  Parent Tag: {card.parent.name} | Parent Class: {card.parent.get('class')} | Parent Style: {card.parent.get('style')}")
    # Let's inspect all descendents of the card to see if any child has an active/selected class
    active_children = []
    for desc in card.descendants:
        if desc.name:
            classes = desc.get('class', [])
            if any('active' in c.lower() or 'select' in c.lower() for c in classes):
                active_children.append((desc.name, classes, desc.get_text().strip()[:50]))
    if active_children:
        print(f"  Active children: {active_children}")
    else:
        print("  No active/selected children found.")
