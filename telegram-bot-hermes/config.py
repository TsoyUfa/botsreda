"""Конфигурация бота Hermes: загрузка переменных окружения."""
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Telegram
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]

# Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# GitHub
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "TsoyUfa")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "obsidian-vault")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
OBSIDIAN_INBOX_DIR = os.environ.get("OBSIDIAN_INBOX_DIR", "Inbox").strip("/")

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором бота"""
    return user_id in ADMIN_IDS

def validate_config() -> tuple[bool, str]:
    """Проверка наличия всех критических настроек"""
    if not BOT_TOKEN:
        return False, "BOT_TOKEN отсутствует в настройках"
    if not ADMIN_IDS:
        return False, "ADMIN_IDS отсутствует в настройках (укажите ваш Telegram User ID)"
    if not GITHUB_TOKEN:
        return False, "GITHUB_TOKEN отсутствует в настройках"
    if not GITHUB_OWNER or not GITHUB_REPO:
        return False, "Параметры репозитория GITHUB_OWNER или GITHUB_REPO не настроены"
    return True, "OK"
