"""Тестовый скрипт для проверки логики бота Тони Павлович."""
import asyncio
import sys
import os

# Добавим текущую папку в пути поиска
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import db
import config
from bot import detect_timezone_by_city, parse_message_intent

async def run_tests():
    print("🚀 НАЧАЛО ТЕСТИРОВАНИЯ ЛОГИКИ БОТА...")
    
    # Инициализируем БД
    await db.init_db()
    
    # 1. Тест определения таймзоны
    print("\n--- ТЕСТ 1: Определение таймзоны по городу ---")
    cities = ["Москва", "Уфа", "Новосибирск", "Владивосток"]
    for city in cities:
        tz = await detect_timezone_by_city(city)
        print(f"Город: {city} -> Таймзона: {tz}")
        
    # 2. Регистрация тестового пользователя
    print("\n--- ТЕСТ 2: Регистрация тестового пользователя ---")
    test_user_id = 99999111
    await db.add_user(
        user_id=test_user_id,
        username="test_realtor",
        full_name="Иван Тестовый-Риелтор",
        timezone="Asia/Yekaterinburg",
        role="user"
    )
    user = await db.get_user(test_user_id)
    print(f"Пользователь зарегистрирован: {user}")
    
    # 3. Тест ИИ-парсинга намерений
    print("\n--- ТЕСТ 3: ИИ-разбор сообщений (CRM и Заметки) ---")
    test_phrases = [
        "У меня новый клиент Рустем, телефон +79876543210, хочет купить 3-комнатную квартиру в ЖК Символ",
        "Надо позвонить Рустему завтра в 14:30 и предложить ЖК Новатор",
        "выполнен созвон с Рустемом",
        "покажи мои активные дела и клиентов",
        "Интересная идея: делать подборки ЖК с расчетом ежемесячного платежа для Reels."
    ]
    
    for phrase in test_phrases:
        print(f"\nВходной текст: \"{phrase}\"")
        parsed = await parse_message_intent(phrase, test_user_id, "Иван")
        print(f"Результат разбора: {parsed}")
        
        # Эмуляция логики бота
        intent = parsed.get("intent")
        if intent == "crm_add_client":
            c_id = await db.add_crm_client(
                test_user_id, 
                parsed.get("client_name"), 
                parsed.get("phone"), 
                'in_work', 
                parsed.get("details")
            )
            print(f"   [БД] Клиент успешно добавлен с ID {c_id}")
        elif intent == "crm_add_task":
            client = await db.find_crm_client_by_name(test_user_id, parsed.get("client_name"))
            c_id = client["client_id"] if client else None
            t_id = await db.add_crm_task(
                test_user_id,
                c_id,
                parsed.get("task_text"),
                parsed.get("due_date")
            )
            print(f"   [БД] Задача добавлена с ID {t_id} (Привязка к клиенту ID: {c_id})")
        elif intent == "show_crm":
            clients = await db.get_crm_clients(test_user_id)
            tasks = await db.get_pending_tasks(test_user_id)
            print(f"   [БД] Клиентов в базе: {len(clients)}, Задач в базе: {len(tasks)}")
        elif intent == "complete_task":
            tasks = await db.get_pending_tasks(test_user_id)
            if tasks:
                await db.complete_task(tasks[0]["task_id"])
                print(f"   [БД] Задача ID {tasks[0]['task_id']} отмечена выполненной")
        elif intent == "save_note":
            await db.add_user_note(test_user_id, parsed.get("note_text") or phrase)
            print(f"   [БД] Заметка сохранена в базу знаний")

    # 4. Проверка записей в БД
    print("\n--- ТЕСТ 4: Проверка результирующих записей в БД ---")
    clients = await db.get_crm_clients(test_user_id)
    tasks = await db.get_pending_tasks(test_user_id)
    notes = await db.get_user_notes(test_user_id)
    
    print(f"Итого клиентов в CRM: {clients}")
    print(f"Итого задач в CRM: {tasks}")
    print(f"Итого сохраненных мыслей/заметок: {notes}")
    
    print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")

if __name__ == "__main__":
    # Запускаем асинхронный тест
    asyncio.run(run_tests())
