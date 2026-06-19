#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функциональности Telegram-бота
без реального подключения к Telegram API
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
import db
import lessons

async def test_database():
    """Тестирование базы данных"""
    print("🗂️ Тестирование базы данных...")
    try:
        await db.init_db()
        print("✅ База данных успешно инициализирована")
        
        # Тест создания пользователя
        test_user_id = 12345
        await db.create_user(test_user_id, "testuser", "Тестовый Пользователь")
        print("✅ Тестовый пользователь создан")
        
        # Тест проверки премиум-доступа
        is_premium = await db.is_premium(test_user_id)
        print(f"🔒 Премиум-доступ пользователя: {is_premium}")
        
        # Тест сохранения результата теста
        await db.save_quiz_result(test_user_id, 1, 0.85, True)
        print("✅ Результат теста сохранен")
        
        # Тест получения прогресса
        progress = await db.get_user_progress(test_user_id)
        print(f"📊 Прогресс пользователя: {progress}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при работе с базой данных: {e}")
        return False

def test_config():
    """Тестирование конфигурации"""
    print("⚙️ Тестирование конфигурации...")
    try:
        print(f"🔑 Токен бота: {'✅ Установлен' if config.BOT_TOKEN != 'YOUR_TELEGRAM_BOT_TOKEN' else '❌ Не установлен'}")
        print(f"💳 Токен платежей: {'✅ Установлен' if config.PAYMENT_PROVIDER_TOKEN else '❌ Не установлен'}")
        print(f"🤖 Gemini API: {'✅ Установлен' if config.GEMINI_API_KEY else '❌ Не установлен'}")
        print(f"💰 Цена Premium: {config.PREMIUM_PRICE_RUB} ₽")
        print(f"📚 Количество модулей: {len(config.MODULES)}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке конфигурации: {e}")
        return False

def test_lessons():
    """Тестирование уроков"""
    print("📖 Тестирование уроков...")
    try:
        for module_id, lesson_data in lessons.LESSONS.items():
            print(f"📚 Модуль {module_id}: {lesson_data['title']}")
            if 'quiz' in lesson_data:
                print(f"  📝 Вопросов в тесте: {len(lesson_data['quiz'])}")
                for i, question in enumerate(lesson_data['quiz']):
                    print(f"    {i+1}. {question['type']}: {question['question'][:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке уроков: {e}")
        return False

async def main():
    """Основная тестовая функция"""
    print("🚀 Начало тестирования Telegram-бота Эксперт Сити")
    print("=" * 50)
    
    # Тест конфигурации
    config_ok = test_config()
    
    # Тест уроков
    lessons_ok = test_lessons()
    
    # Тест базы данных
    db_ok = await test_database()
    
    print("=" * 50)
    print("📊 Результаты тестирования:")
    print(f"⚙️ Конфигурация: {'✅ OK' if config_ok else '❌ FAIL'}")
    print(f"📖 Уроки: {'✅ OK' if lessons_ok else '❌ FAIL'}")
    print(f"🗂️ База данных: {'✅ OK' if db_ok else '❌ FAIL'}")
    
    if config_ok and lessons_ok and db_ok:
        print("🎉 Все тесты пройдены! Бот готов к запуску с правильными токенами.")
        print("\n📝 Что нужно для запуска:")
        print("1. Установить реальный BOT_TOKEN в .env файл")
        print("2. При необходимости установить PAYMENT_PROVIDER_TOKEN и GEMINI_API_KEY")
        print("3. Запустить: python3 bot.py")
    else:
        print("❌ Некоторые тесты не пройдены. Проверьте ошибки выше.")
    
    return config_ok and lessons_ok and db_ok

if __name__ == "__main__":
    asyncio.run(main())