import os

# Telegram Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

# Database path (relative to the bot script)
DB_PATH = os.getenv("DB_PATH", "expert_city_bot.db")

# Payment configuration
# For YooKassa/Robokassa/Prodamus: paste the provider token from @BotFather
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "") 
# Price in rubles
PREMIUM_PRICE_RUB = 4990
# Price in Telegram Stars (if using Stars payment)
PREMIUM_PRICE_STARS = 250

# Course Modules list
MODULES = {
    1: {
        "title": "Блок 1. Роль Навигатора и Золотое Правило",
        "is_free": True,
        "quiz_threshold": 0.8  # 80% correct answers needed to pass
    },
    2: {
        "title": "Блок 2. JTBD-Диагностика и Боли Клиента",
        "is_free": False,
        "quiz_threshold": 0.8
    },
    3: {
        "title": "Блок 3. Финмоделирование и TCO за 5 лет",
        "is_free": False,
        "quiz_threshold": 0.8
    },
    4: {
        "title": "Блок 4. Анализ Застройщиков и shortlist",
        "is_free": False,
        "quiz_threshold": 0.8
    },
    5: {
        "title": "Блок 5. Регламент Показов и Презентация",
        "is_free": False,
        "quiz_threshold": 0.8
    },
    6: {
        "title": "Блок 6. Юридическая Безопасность и 214-ФЗ",
        "is_free": False,
        "quiz_threshold": 0.8
    },
    7: {
        "title": "Блок 7. ИИ-Ассистенты в Работе Агента",
        "is_free": False,
        "quiz_threshold": 0.8
    }
}
