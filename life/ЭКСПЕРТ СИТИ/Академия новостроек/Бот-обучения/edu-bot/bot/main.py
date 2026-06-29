"""Entry point: initialise bot, create DB tables, start polling."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BT_KEY
from bot.db import init_db
from bot.handlers import start as start_handler
from bot.handlers import student as student_handler
from bot.handlers import admin as admin_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("academy-bot")


async def main():
    if not BT_KEY:
        logger.error("BOT_TOKEN is empty! Check .env file.")
        sys.exit(1)

    # Create data dir if missing
    import os
    os.makedirs("data", exist_ok=True)

    bot = Bot(
        token=BT_KEY,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register routers (order matters: start first)
    dp.include_router(start_handler.router)
    dp.include_router(admin_handler.router)
    dp.include_router(student_handler.router)

    # Init database
    await init_db()
    logger.info("Database initialised.")

    # Set bot commands
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск / главное меню"),
    ])

    logger.info("Bot starting polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
