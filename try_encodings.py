import os
from datetime import datetime

# Today's date
today = datetime.now().strftime("%d.%m.%Y")

# Try to read the dashboard file with different encodings
dashboard_path = "/Users/anton_tsoy/Desktop/Обсидиан/1. Бизнес/00-dashboard.md"
dashboard_content = ""

encodings = ['utf-8', 'cp1251', 'iso-8859-5', 'koi8-r']

for encoding in encodings:
    try:
        with open(dashboard_path, 'r', encoding=encoding) as f:
            dashboard_content = f.read()
        print(f"Successfully read dashboard file with {encoding} encoding")
        break
    except Exception as e:
        print(f"Failed to read with {encoding}: {str(e)}")

# Try to read the decision log file with different encodings
decision_path = "/Users/anton_tsoy/Desktop/Обсидиан/2. План/decision-log.md"
decision_content = ""

for encoding in encodings:
    try:
        with open(decision_path, 'r', encoding=encoding) as f:
            decision_content = f.read()
        print(f"Successfully read decision log file with {encoding} encoding")
        break
    except Exception as e:
        print(f"Failed to read with {encoding}: {str(e)}")

# Print the content
print("\n=== DASHBOARD CONTENT ===")
print(dashboard_content)

print("\n=== DECISION LOG CONTENT ===")
print(decision_content)