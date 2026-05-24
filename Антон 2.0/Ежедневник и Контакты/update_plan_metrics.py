#!/usr/bin/env python3
"""
Автоматический подсчёт метрик для плана на ноябрь 2025
Скрипт читает файл плана и считает выполненные задачи, прогресс по целям
"""

import re
from datetime import datetime
from pathlib import Path

# Путь к файлу плана
PLAN_FILE = Path(__file__).parent / "План на ноябрь 2025.md"

def count_completed_tasks(content):
    """Подсчитать количество выполненных задач (отмеченных [x] или [X])"""
    completed = len(re.findall(r'- \[x\]', content, re.IGNORECASE))
    total = len(re.findall(r'- \[ \]', content)) + completed
    return completed, total

def count_workouts(content):
    """Подсчитать количество выполненных тренировок"""
    # Ищем таблицу тренировок
    workout_section = re.search(
        r'### Тренировки.*?\n\n(.*?)\n\n',
        content,
        re.DOTALL
    )
    if workout_section:
        workouts = re.findall(r'\| .* \| .* \| .* \| \[x\]', workout_section.group(1), re.IGNORECASE)
        return len(workouts)
    return 0

def count_posts(content):
    """Подсчитать количество постов в соцсетях"""
    posts_section = re.search(
        r'### Посты в соцсетях.*?\n\n(.*?)\n\n',
        content,
        re.DOTALL
    )
    if posts_section:
        posts = re.findall(r'\| \d+ \|.*?\| \[x\]', posts_section.group(1), re.IGNORECASE)
        return len(posts)
    return 0

def calculate_progress(current, target):
    """Рассчитать процент прогресса"""
    if target == 0:
        return 0
    return min(round((current / target) * 100), 100)

def get_status_emoji(progress):
    """Получить эмодзи статуса на основе прогресса"""
    if progress < 50:
        return "🔴"
    elif progress < 80:
        return "🟡"
    else:
        return "🟢"

def update_kr_progress(content):
    """Обновить прогресс Key Results в файле"""
    # Подсчитываем метрики
    completed_tasks, total_tasks = count_completed_tasks(content)
    workouts = count_workouts(content)
    posts = count_posts(content)
    
    # Рассчитываем прогресс
    tasks_progress = calculate_progress(completed_tasks, total_tasks)
    workouts_progress = calculate_progress(workouts, 10)
    posts_progress = calculate_progress(posts, 12)
    
    print("=" * 60)
    print("📊 ОТЧЁТ ПО МЕТРИКАМ НОЯБРЯ 2025")
    print("=" * 60)
    print(f"\n✅ Выполнено задач: {completed_tasks}/{total_tasks} ({tasks_progress}%)")
    print(f"🏋️  Тренировок: {workouts}/10 ({workouts_progress}%)")
    print(f"📱 Постов: {posts}/12 ({posts_progress}%)")
    
    # Общий прогресс (среднее из доступных метрик)
    available_metrics = [tasks_progress, workouts_progress, posts_progress]
    overall_progress = sum(available_metrics) // len(available_metrics)
    
    print(f"\n🎯 Общий прогресс: {overall_progress}%")
    print(f"📊 Статус: {get_status_emoji(overall_progress)}")
    
    print("\n" + "=" * 60)
    print("💡 Рекомендации:")
    print("=" * 60)
    
    if workouts_progress < 50:
        print("⚠️  Мало тренировок! Запланируй как минимум 3 на этой неделе")
    if posts_progress < 50:
        print("⚠️  Мало постов! Создай контент-план на неделю")
    if tasks_progress < 70:
        print("⚠️  Много незавершённых задач! Пересмотри приоритеты")
    
    if overall_progress >= 80:
        print("🎉 Отличная работа! Продолжай в том же духе!")
    
    print("\n" + "=" * 60)
    
    return {
        'tasks_completed': completed_tasks,
        'tasks_total': total_tasks,
        'tasks_progress': tasks_progress,
        'workouts': workouts,
        'workouts_progress': workouts_progress,
        'posts': posts,
        'posts_progress': posts_progress,
        'overall_progress': overall_progress
    }

def generate_weekly_report(week_number):
    """Генерировать отчёт за неделю"""
    print(f"\n📅 ОТЧЁТ ЗА НЕДЕЛЮ {week_number}")
    print("=" * 60)
    print("Для генерации детального отчёта за неделю,")
    print("заполните раздел 'Итоги недели' в файле плана")
    print("=" * 60)

def main():
    """Основная функция"""
    print("\n🤖 Запуск автоматического подсчёта метрик...")
    print(f"📁 Файл: {PLAN_FILE}")
    
    if not PLAN_FILE.exists():
        print(f"❌ Ошибка: Файл не найден: {PLAN_FILE}")
        return
    
    # Читаем содержимое файла
    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Обновляем метрики
    metrics = update_kr_progress(content)
    
    # Определяем текущую неделю ноября
    today = datetime.now()
    week_of_november = (today.day - 6) // 7 + 1
    
    if 1 <= week_of_november <= 4:
        generate_weekly_report(week_of_november)
    
    print(f"\n✅ Анализ завершён: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("\n💡 Совет: Запускай этот скрипт каждое воскресенье перед еженедельным ревью!\n")

if __name__ == "__main__":
    main()

