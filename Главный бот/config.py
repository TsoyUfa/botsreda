import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8895453398:AAF-pi4CGYgPCfnjo61dTiTeezlSqWjeBJs")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5690724590"))

# Telegram канал для проверки подписки
CHANNEL_ID = os.getenv("CHANNEL_ID", "@anton_tsoy_sreda")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/anton_tsoy_sreda")

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "bot.db")
LEAD_MAGNETS_DIR = os.path.join(DATA_DIR, "lead_magnets")

# Словарь соответствия кодовых слов и файлов
# Ключ: кодовое слово (в верхнем регистре)
# Значение: словарь с названием лид-магнита и именем файла для отправки
LEAD_MAGNETS = {
    "РЫНОК": {
        "title": "Чек-лист: 5 навыков системного брокера в 2026 году",
        "file_name": "1_checklist_skills.md",
        "source_name": "1. Чек-лист - 5 навыков системного брокера в 2026 году.md"
    },
    "LTV": {
        "title": "Руководство: Как рассчитать LTV клиента",
        "file_name": "2_guide_ltv.md",
        "source_name": "2. Руководство - Как рассчитать LTV клиента.md"
    },
    "ЭТАПЫ": {
        "title": "Скрипт: Что отвечать на просьбу скинуть планировки",
        "file_name": "3_script_layouts.md",
        "source_name": "3. Скрипт - Что отвечать на просьбу скинуть планировки.md"
    },
    "ПРАВИЛА": {
        "title": "Гайд: Регламент первой встречи и перевод на аудит",
        "file_name": "4_guide_first_meeting.md",
        "source_name": "4. Гайд - Регламент первой встречи и перевод на аудит.md"
    },
    "РАСЧЕТ": {
        "title": "Методичка: 4 инструмента продаж без господдержки",
        "file_name": "5_manual_no_subsidies.md",
        "source_name": "5. Методичка - 4 инструмента продаж без господдержки.md"
    },
    "ПУШКА": {
        "title": "Шаблон: Презентация financial расчета клиенту",
        "file_name": "6_template_calc_presentation.md",
        "source_name": "6. Шаблон - Презентация financial расчета клиенту.md"
    },
    "ЭКСПЕРТ": {
        "title": "Чек-лист: Маркеры слабой позиции брокера",
        "file_name": "7_checklist_weak_position.md",
        "source_name": "7. Чек-лист - Маркеры слабой позиции брокера.md"
    },
    "КОНТАКТ": {
        "title": "Главная методичка: От заявки до встречи",
        "file_name": "8_main_manual_touch_to_meeting.md",
        "source_name": "8. Главная методичка - От заявки до встречи.md"
    },
    "КЛИЕНТ": {
        "title": "Методичка: Как выбрать новостройку без переплат",
        "file_name": "client_manual.md",
        "source_name": "Методичка_для_клиента.md"
    },
    "INZINER": {
        "title": "Практикум: Способы покупки",
        "file_name": "inziner.pdf",
        "source_name": "Практикум — Способы покупки.pdf"
    }
}

