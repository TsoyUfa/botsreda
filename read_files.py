#!/usr/bin/env python3
import os

# Read the dashboard file
dashboard_path = "/Users/anton_tsoy/Desktop/Обсидиан/1. Бизнес/00-dashboard.md"
if os.path.exists(dashboard_path):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        dashboard_content = f.read()
    print("=== DASHBOARD CONTENT ===")
    print(dashboard_content)
else:
    print("Dashboard file not found")

# Read the decision log file
decision_path = "/Users/anton_tsoy/Desktop/Обсидиан/2. План/decision-log.md"
if os.path.exists(decision_path):
    with open(decision_path, 'r', encoding='utf-8') as f:
        decision_content = f.read()
    print("\n=== DECISION LOG CONTENT ===")
    print(decision_content)
else:
    print("Decision log file not found")

# List files in clients directory
clients_dir = "/Users/anton_tsoy/Desktop/Обсидиан/2. План/02_clients/"
if os.path.exists(clients_dir):
    print(f"\n=== FILES IN {clients_dir} ===")
    for file in os.listdir(clients_dir):
        if os.path.isfile(os.path.join(clients_dir, file)):
            print(f"- {file}")
else:
    print("Clients directory not found")