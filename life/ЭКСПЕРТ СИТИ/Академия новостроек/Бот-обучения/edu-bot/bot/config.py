"""Config loader: reads .env and exposes settings."""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram bot API key
BT_KEY = os.environ.get("BOT_TOKEN", "")

# Admin Telegram IDs (comma-separated in .env)
_raw = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = []
for _x in _raw.split(","):
    _x = _x.strip()
    if _x.isdigit():
        ADMIN_IDS.append(int(_x))

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///data/academy.db")
