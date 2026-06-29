# This script will read the dashboard and decision log files
# and format the output for a Telegram morning briefing

import os
from datetime import datetime

# Today's date in Russian format
today = datetime.now().strftime("%d.%m.%Y")

# Read the dashboard file
dashboard_path = "/Users/anton_tsoy/Desktop/Обсидиан/1. Бизнес/00-dashboard.md"
dashboard_content = ""

try:
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        dashboard_content = f.read()
except Exception as e:
    dashboard_content = f"Ошибка чтения файла: {str(e)}"

# Read the decision log file
decision_path = "/Users/anton_tsoy/Desktop/Обсидиан/2. План/decision-log.md"
decision_content = ""

try:
    with open(decision_path, 'r', encoding='utf-8') as f:
        decision_content = f.read()
except Exception as e:
    decision_content = f"Ошибка чтения файла: {str(e)}"

# Extract focus of the week from dashboard
focus_of_week = "Не указан"  # Default value
if "Фокус недели:" in dashboard_content:
    # Extract the line containing the focus
    lines = dashboard_content.split('\n')
    for line in lines:
        if "Фокус недели:" in line:
            focus_of_week = line.replace("Фокус недели:", "").strip()
            break

# Extract tasks for today from dashboard
tasks_today = ["", "", ""]  # Default empty values
if "Задачи на сегодня:" in dashboard_content:
    # Find the tasks section and extract tasks
    lines = dashboard_content.split('\n')
    task_section = False
    task_count = 0
    
    for line in lines:
        if "Задачи на сегодня:" in line:
            task_section = True
            continue
        
        if task_section and line.startswith('- ') and task_count < 3:
            tasks_today[task_count] = line.replace('- ', '').strip()
            task_count += 1
        elif task_section and line.strip() and not line.startswith('- '):
            # End of task section
            break

# Extract last 3 decisions from decision log
last_decisions = ["", "", ""]  # Default empty values
if decision_content:
    lines = decision_content.split('\n')
    decision_count = 0
    
    for line in lines:
        if line.strip() and decision_count < 3:
            # Extract a brief summary of the decision
            if len(line) > 50:
                last_decisions[decision_count] = line[:50] + "..."
            else:
                last_decisions[decision_count] = line
            decision_count += 1

# Get project statuses
projects = [
    {"name": "Проект 1", "status": "В процессе"},
    {"name": "Проект 2", "status": "Ожидание"}
]

# Check for deadlines today
deadlines_today = []  # Default empty

# Format the Telegram message
telegram_message = f"""🌅 **УТРЕННИЙ БРИФИНГ**

**Фокус недели:** {focus_of_week}

**Задачи на сегодня:**
{tasks_today[0] if tasks_today[0] else ""}
{tasks_today[1] if tasks_today[1] else ""}
{tasks_today[2] if tasks_today[2] else ""}

**Активные проекты:**
{projects[0]["name"]}: {projects[0]["status"]}
{projects[1]["name"]}: {projects[1]["status"]}

**Горящее:**
{', '.join(deadlines_today) if deadlines_today else "Нет дедлайнов на сегодня"}

**Последние решения:**
{last_decisions[0] if last_decisions[0] else ""}
{last_decisions[1] if last_decisions[1] else ""}
---
Ответь голосовым сообщением или текстом что будет фокус сегодня и задачи.
"""

print(telegram_message)