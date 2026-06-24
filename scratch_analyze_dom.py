import sys, re
sys.stdout.reconfigure(errors='replace')

with open('dist/IndiaMartScraper/datepicker_error.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the Date section and print a large chunk
idx = content.find('Date :')
if idx >= 0:
    start = max(0, idx - 100)
    end = min(len(content), idx + 1500)
    print("=== Date section from error dump ===")
    print(content[start:end])
else:
    print("Date : not found in error dump")

# Find the Custom Date occurrence
print("\n\n=== Custom Date context ===")
for m in re.finditer('Custom Date', content):
    start = max(0, m.start() - 200)
    end = min(len(content), m.end() + 200)
    print(f"pos {m.start()}:")
    print(content[start:end])
