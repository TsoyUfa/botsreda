"""Конфигурация бота: загрузка .env и настройки."""
import os
from dotenv import load_dotenv

load_dotenv()

# Основные настройки
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
DB_PATH = os.environ.get("DB_PATH", "bot_obucheniya.db")

# API ключи
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PAYMENT_PROVIDER_TOKEN = os.environ.get("PAYMENT_PROVIDER_TOKEN", "")

# TWA (Telegram Web App) URL
TWA_URL = os.environ.get("TWA_URL", "")

# Чат куратора для проверки домашних заданий
CURATOR_CHAT_ID = int(os.environ.get("CURATOR_CHAT_ID", ADMIN_IDS[0] if ADMIN_IDS else 0))

# Настройки бота
PREMIUM_PRICE_RUB = 4990  # Стоимость премиум-доступа

# Модули обучения "Среда обучения 2.0"
MODULES = {
    1: {
        "title": "Блок 1: Перезагрузка и Точка А",
        "free": True,
        "description": "Слом иллюзий, оцифровка Точки А и роль Навигатора"
    },
    2: {
        "title": "Блок 2: Золотое правило и JTBD", 
        "free": True,
        "description": "Золотое правило подбора и JTBD-диагностика"
    },
    3: {
        "title": "Блок 3: Продукт и Аудит ЖК",
        "free": True,
        "description": "Технический и коммерческий аудит новостроек"
    },
    4: {
        "title": "Блок 4: Финансовый инжиниринг",
        "free": True,
        "description": "Продукты-драйверы и сценарные расчеты"
    },
    5: {
        "title": "Блок 5: Стандарт сделки и Регламенты",
        "free": True,
        "description": "18 шагов безопасной сделки и фиксация уникальности"
    },
    6: {
        "title": "Блок 6: Трафик и Возражения",
        "free": True,
        "description": "Каналы привлечения клиентов и алгоритм ЛПСД"
    }
}

# Новостройки для бронирования
BUILDINGS = {
    "Гранат": {
        "name": "ЖК Гранат",
        "price_from": "8.5 млн ₽",
        "location": "САО, м. Петровско-Разумовская",
        "description": "Комфорт-класс с развитой инфраструктурой"
    },
    "Изумруд": {
        "name": "ЖК Изумруд",
        "price_from": "6.2 млн ₽", 
        "location": "ЦАО, м. Проспект Вернадского",
        "description": "Бизнес-класс в престижном районе"
    },
    "Сапфир": {
        "name": "ЖК Сапфир",
        "price_from": "9.1 млн ₽",
        "location": "ЮЗАО, м. Юго-Западная", 
        "description": "Элит-класс с панорамными видами"
    }
}

# Проверка конфигурации
def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

def is_configured() -> bool:
    """Проверка, настроен ли бот"""
    if not BOT_TOKEN:
        return False
    if not ADMIN_IDS:
        return False
    return True