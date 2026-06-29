#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_data.py — Парсит ключевые файлы Obsidian vault и генерирует dashboard/data.json
Запускается автоматически как часть publish_to_github.sh
"""

import json
import re
import os
from datetime import datetime, date

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Пути к ключевым файлам
FILES = {
    "strategy_focus":    "1. Бизнес/01_strategy/90-day-focus.md",
    "target_500k":       "1. Бизнес/01_strategy/target-500k.md",
    "business_dashboard":"1. Бизнес/00-dashboard.md",
    "operations_tasks":  "1. Бизнес/09_operations/tasks.md",
    "role":              "3. Мой клон/role.md",
    "decision_filters":  "1. Бизнес/01_strategy/decision-filters.md",
}

def read_file(rel_path):
    full_path = os.path.join(VAULT_ROOT, rel_path)
    if not os.path.exists(full_path):
        return ""
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()

def parse_checkboxes(text):
    """Парсит [ ] и [x] чекбоксы из markdown."""
    tasks = []
    for line in text.split("\n"):
        m = re.match(r'\s*[-*]\s+\[([ xXvV])\]\s+(.+)', line)
        if m:
            done = m.group(1).strip().lower() in ['x', 'v']
            title = m.group(2).strip()
            # Убираем Obsidian-ссылки типа [[file|text]] → text
            title = re.sub(r'\[\[.*?\|(.+?)\]\]', r'\1', title)
            title = re.sub(r'\[\[(.+?)\]\]', r'\1', title)
            # Убираем markdown жирный/курсив
            title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)
            title = re.sub(r'\*(.+?)\*', r'\1', title)
            title = title.strip()
            tasks.append({"title": title, "done": done})
    return tasks

def parse_section(text, heading):
    """Извлекает содержимое секции по заголовку (## Heading)."""
    pattern = rf'##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)'
    m = re.search(pattern, text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""

def parse_current_phase(text):
    """Определяет текущую фазу в 90-day-focus.md."""
    phases = re.findall(r'##\s+(Фаза\s+\d+\..*?)(?=\n)', text)
    # Ищем фазу с незакрытыми задачами
    phase_blocks = re.split(r'(?=##\s+Фаза)', text)
    for block in phase_blocks:
        if '- [ ]' in block:
            heading_m = re.match(r'##\s+(Фаза\s+\d+[.\s].*?)(?=\n)', block)
            if heading_m:
                return heading_m.group(1).strip()
    return phases[0] if phases else "Фаза 1"

def parse_projects_from_dashboard(text):
    """Парсит активные проекты из бизнес-дашборда."""
    projects = []
    # Ищем блоки типа "**Название:**"
    blocks = re.findall(r'\*\*(.+?)\*\*[:\s]*\n(.*?)(?=\n\*\*|\Z)', text, re.DOTALL)
    seen = set()
    for name, content in blocks:
        name = name.strip().rstrip(':').strip()
        if name in seen or len(name) > 60:
            continue
        # Игнорируем технические поля
        skip_words = ['минимальный', 'флагманский', 'главный', 'текущий', 'приоритет', 'целевая', 'фокус', 'что']
        if any(w in name.lower() for w in skip_words):
            continue
        tasks = parse_checkboxes(content)
        if tasks or len(name) < 50:
            seen.add(name)
            projects.append({
                "name": name,
                "tasks": tasks[:6],  # Не более 6 задач на проект
            })
    return projects[:5]

def parse_not_doing(text):
    """Парсит блок 'Что НЕ делаем сейчас'."""
    section = parse_section(text, "Что НЕ делаем сейчас")
    items = []
    for line in section.split("\n"):
        m = re.match(r'\s*[-*]\s+(.+)', line)
        if m:
            item = re.sub(r'\*\*(.+?)\*\*', r'\1', m.group(1).strip())
            items.append(item)
    return items

def parse_financial_goal(text):
    """Парсит финансовую цель из файла target-500k.md."""
    amount = 500000
    currency = "₽"
    date_target = "Август 2026"
    # Ищем конкретный сценарий
    scenarios = []
    blocks = re.split(r'\n##\s+', text)
    for block in blocks:
        total_m = re.search(r'Итого\s*=\s*([\d\s]+)\s*₽', block)
        if total_m:
            val = int(re.sub(r'\s', '', total_m.group(1)))
            name_m = re.match(r'(.+?)\n', block)
            scenarios.append({
                "name": name_m.group(1).strip() if name_m else "Сценарий",
                "total": val
            })
    return {
        "amount": amount,
        "currency": currency,
        "date": date_target,
        "scenarios": scenarios
    }

def parse_strategic_focus(text):
    """Парсит стратегический фокус из role.md."""
    section = parse_section(text, "🎯 Главный фокус и бизнес-цели")
    if not section:
        section = parse_section(text, "Главный фокус и бизнес-цели")
    lines = [l.strip() for l in section.split('\n') if l.strip() and not l.startswith('#')]
    return ' '.join(lines[:3]) if lines else ""

def parse_priorities_from_dashboard(text):
    """Парсит приоритетные офферы."""
    section = parse_section(text, "Приоритетные офферы")
    items = []
    for line in section.split('\n'):
        m = re.match(r'\s*\d+\.\s+(.+)', line)
        if m:
            item = re.sub(r'\*\*(.+?)\*\*', r'\1', m.group(1).strip())
            item = re.sub(r'\[Фокус.*?\]', '', item).strip()
            item = re.sub(r'\s+', ' ', item)
            items.append(item)
    return items

def parse_focus_7days(text):
    """Парсит блок 'Фокус на ближайшие 7 дней'."""
    section = parse_section(text, "Фокус на ближайшие 7 дней")
    result = []
    current_project = None
    for line in section.split('\n'):
        # Заголовок проекта
        h = re.match(r'\*\*(.+?)\*\*', line)
        if h:
            current_project = h.group(1).strip().rstrip(':').strip()
        # Задача
        t = re.match(r'\s*[-*]\s+\[([ xXvV])\]\s+(.+)', line)
        if t and current_project:
            done = t.group(1).strip().lower() in ['x', 'v']
            title = re.sub(r'\[\[.*?\|(.+?)\]\]', r'\1', t.group(2))
            title = re.sub(r'\[\[(.+?)\]\]', r'\1', title)
            title = re.sub(r'\*.*?\*', '', title).strip()
            title = re.sub(r'\s+', ' ', title).strip()
            result.append({
                "project": current_project,
                "title": title,
                "done": done
            })
    return result

def determine_week_number():
    """Возвращает номер текущей недели года."""
    return date.today().isocalendar()[1]

def build_output(strategy_text, target_text, dashboard_text, tasks_text, role_text):
    current_phase = parse_current_phase(strategy_text)
    phase_section_match = re.search(
        rf'(##\s+{re.escape(current_phase)}.*?)(?=\n##\s+Фаза|\n##\s+Главный|\Z)',
        strategy_text, re.DOTALL
    )
    phase_tasks = []
    if phase_section_match:
        phase_tasks = parse_checkboxes(phase_section_match.group(1))

    focus_7days = parse_focus_7days(dashboard_text)
    not_doing = parse_not_doing(dashboard_text)
    priorities = parse_priorities_from_dashboard(dashboard_text)
    financial = parse_financial_goal(target_text)
    strategic_focus = parse_strategic_focus(role_text)

    # Главный KPI из файла стратегии
    kpi_m = re.search(r'##\s+Главный KPI\s*\n(.+)', strategy_text)
    main_kpi = kpi_m.group(1).strip() if kpi_m else "Количество разговоров с платящими ЛПРами"

    # Операционные задачи (24-hour priority)
    ops_section = parse_section(tasks_text, "1\\) Решение на сегодня")
    if not ops_section:
        ops_section = parse_section(tasks_text, "Шаг 2. Распределение по блокам действий")
    ops_tasks = parse_checkboxes(ops_section)

    return {
        "generated_at": datetime.now().isoformat(),
        "week_number": determine_week_number(),
        "year": date.today().year,

        "strategic": {
            "focus": strategic_focus,
            "current_phase": current_phase,
            "main_kpi": main_kpi,
            "phase_tasks": phase_tasks,
        },

        "financial": financial,

        "week_goals": focus_7days,

        "priorities": priorities[:4],

        "ops_tasks_today": ops_tasks[:5],

        "not_doing": not_doing,
    }

def main():
    print("📊 Генерация данных дашборда из Obsidian vault...")
    data = {}
    for key, path in FILES.items():
        data[key] = read_file(path)
        status = "✅" if data[key] else "⚠️  (не найден)"
        print(f"  {status} {path}")

    output = build_output(
        strategy_text=data["strategy_focus"],
        target_text=data["target_500k"],
        dashboard_text=data["business_dashboard"],
        tasks_text=data["operations_tasks"],
        role_text=data["role"],
    )

    output_path = os.path.join(VAULT_ROOT, "dashboard", "data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Данные записаны: dashboard/data.json")
    print(f"   Текущая фаза: {output['strategic']['current_phase']}")
    print(f"   Целей на неделю: {len(output['week_goals'])}")
    print(f"   Операционных задач: {len(output['ops_tasks_today'])}")

if __name__ == "__main__":
    main()
