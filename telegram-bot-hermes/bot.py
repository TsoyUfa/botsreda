"""
Основной скрипт Telegram-бота Hermes.
Принимает текст и голосовые сообщения, расшифровывает голос через Gemini API
и сохраняет в виде markdown-файлов в репозитории GitHub.
"""
import logging
import asyncio
from datetime import datetime
import base64
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ContentType
from aiogram.filters import CommandStart, Command

import config
import calendar_service
import google.generativeai as genai

# Инициализация логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("HermesBot")

# Проверка конфигурации
is_ok, err_msg = config.validate_config()
if not is_ok:
    logger.error(f"Ошибка конфигурации: {err_msg}")
    raise ValueError(err_msg)

# Инициализация Gemini
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
    logger.info("Gemini API успешно инициализирован.")
else:
    logger.warning("GEMINI_API_KEY не задан. Голосовые сообщения не смогут быть расшифрованы.")

# Инициализация Bot и Dispatcher
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Фильтр для проверки администратора
def admin_only(message: Message) -> bool:
    is_adm = config.is_admin(message.from_user.id)
    if not is_adm:
        logger.warning(f"Попытка доступа от неавторизованного пользователя: {message.from_user.id} (@{message.from_user.username})")
    return is_adm

async def transcribe_audio(audio_bytes: bytes) -> str:
    """Расшифровка аудиофайла через Gemini API 1.5 Flash."""
    if not config.GEMINI_API_KEY:
        raise ValueError("Gemini API ключ не настроен.")
    
    loop = asyncio.get_running_loop()
    
    def _call_gemini():
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "Ты — ассистент по транскрибации. Переведи эту аудиозапись (голосовое сообщение) в текст. "
            "Запиши только расшифрованный русский текст, исправь явные грамматические ошибки, но сохрани исходный смысл. "
            "Не добавляй от себя никаких комментариев, вводных слов или метаданных. Только расшифровка."
        )
        response = model.generate_content([
            {
                "mime_type": "audio/ogg",
                "data": audio_bytes
            },
            prompt
        ])
        return response.text.strip()

    return await loop.run_in_executor(None, _call_gemini)

async def upload_to_github(file_path: str, content: str, commit_message: str) -> bool:
    """Загрузка файла в репозиторий GitHub через REST API."""
    url = f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"token {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Кодируем контент в base64
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": commit_message,
        "content": content_b64,
        "branch": config.GITHUB_BRANCH
    }
    
    async with aiohttp.ClientSession() as session:
        # Проверяем, существует ли файл, чтобы получить его SHA (если нужно обновить, хотя мы пишем новые файлы)
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                payload["sha"] = data["sha"]
                logger.info(f"Файл {file_path} уже существует, будет обновлен (sha: {data['sha']})")
        
        # Делаем коммит/запись
        async with session.put(url, headers=headers, json=payload) as resp:
            if resp.status in [200, 201]:
                logger.info(f"Файл {file_path} успешно записан в GitHub.")
                return True
            else:
                err_body = await resp.text()
                logger.error(f"Ошибка записи в GitHub API (Код: {resp.status}): {err_body}")
                return False

async def append_to_archive(text: str, source_type: str) -> bool:
    """Добавление записи в единый файл-архив на GitHub в хронологическом порядке."""
    if not config.TELEGRAM_LOG_FILE:
        return False
        
    url = f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/contents/{config.TELEGRAM_LOG_FILE}"
    headers = {
        "Authorization": f"token {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    # Форматируем новый блок для записи
    new_entry = (
        f"\n## [{date_str} {time_str}] Тип: {source_type}\n"
        f"{text.strip()}\n"
        f"\n---\n"
    )
    
    async with aiohttp.ClientSession() as session:
        sha = None
        current_content = ""
        
        # 1. Получаем текущее содержимое файла архива
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                sha = data["sha"]
                current_content = base64.b64decode(data["content"]).decode("utf-8")
                logger.info(f"Файл архива {config.TELEGRAM_LOG_FILE} найден, дополняем (sha: {sha})")
            elif resp.status == 404:
                # Если файла нет, инициализируем его
                current_content = (
                    "# Архив голосовых и текстовых заметок Telegram\n\n"
                    "Все сообщения, отправленные через бота, сохраняются здесь хронологически.\n\n"
                )
                logger.info(f"Файл архива {config.TELEGRAM_LOG_FILE} не найден, создаем новый.")
            else:
                logger.error(f"Ошибка получения архива с GitHub (Код: {resp.status})")
                return False
                
        # 2. Объединяем старое содержимое с новой записью
        updated_content = current_content + new_entry
        content_b64 = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"Append new telegram note to archive: {date_str} {time_str}",
            "content": content_b64,
            "branch": config.GITHUB_BRANCH
        }
        if sha:
            payload["sha"] = sha
            
        # 3. Обновляем файл на GitHub
        async with session.put(url, headers=headers, json=payload) as resp:
            if resp.status in [200, 201]:
                logger.info(f"Архив {config.TELEGRAM_LOG_FILE} успешно обновлен.")
                return True
            else:
                err_body = await resp.text()
                logger.error(f"Ошибка записи архива в GitHub API (Код: {resp.status}): {err_body}")
                return False

def generate_markdown_content(text: str, source_type: str) -> str:
    """Форматирование заметки в формате Markdown с Frontmatter метаданными."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    return f"""---
date: {date_str}
time: {time_str}
tags:
  - inbox
  - telegram
type: {source_type}
---

{text}
"""

@dp.message(CommandStart(), admin_only)
async def cmd_start(message: Message):
    """Приветственное сообщение."""
    await message.reply(
        "👋 Привет, Антон! Я бот **Hermes**.\n\n"
        "Отправь мне текстовое или голосовое сообщение, и я автоматически сохраню его "
        f"в папку `{config.OBSIDIAN_INBOX_DIR}` твоего Obsidian репозитория на GitHub.\n\n"
        "Готов к работе!"
    )

@dp.message(F.text, admin_only)
async def handle_text_message(message: Message):
    """Обработка текстовых сообщений."""
    status_msg = await message.reply("⚡ Сохраняю текстовую заметку...")
    
    now = datetime.now()
    filename = f"tg-{now.strftime('%Y%m%d-%H%M%S')}.md"
    file_path = f"{config.OBSIDIAN_INBOX_DIR}/{filename}"
    
    md_content = generate_markdown_content(message.text, "text")
    commit_msg = f"Add telegram text note: {filename}"
    
    success = await upload_to_github(file_path, md_content, commit_msg)
    
    if success:
        # Дополнительно записываем в архив
        archive_success = await append_to_archive(message.text, "text")
        archive_info = "\n📦 Добавлено в архив." if archive_success else "\n⚠️ Ошибка записи в архив."
        
        # Google Calendar Integration
        calendar_info = ""
        try:
            cal_result = await calendar_service.process_and_add_to_calendar(message.text)
            if cal_result:
                time_info = cal_result['start']
                if cal_result.get('all_day'):
                    time_info = f"{time_info.split('T')[0]} (весь день)"
                else:
                    time_info = datetime.fromisoformat(cal_result['start']).strftime('%d.%m.%Y в %H:%M')
                calendar_info = f"\n📅 Добавлено в Google Календарь:\n**{cal_result['title']}** ({time_info})"
        except Exception as cal_err:
            logger.error(f"Ошибка при обработке календаря: {cal_err}")
            
        await status_msg.edit_text(
            f"✅ Заметка успешно сохранена на GitHub!\n"
            f"📄 Файл: `{file_path}`"
            f"{archive_info}"
            f"{calendar_info}",
            parse_mode="Markdown"
        )
    else:
        await status_msg.edit_text("❌ Не удалось отправить заметку на GitHub. Проверьте логи сервера.")

@dp.message(F.voice, admin_only)
async def handle_voice_message(message: Message):
    """Обработка голосовых сообщений."""
    status_msg = await message.reply("🎙️ Загружаю голосовое сообщение...")
    
    try:
        # Скачиваем голосовой файл
        voice_file = await bot.get_file(message.voice.file_id)
        
        # Скачиваем файл в память
        audio_buffer = bytearray()
        async with aiohttp.ClientSession() as session:
            file_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{voice_file.file_path}"
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    audio_buffer = await resp.read()
                else:
                    raise Exception(f"Ошибка загрузки файла Telegram API: {resp.status}")
        
        await status_msg.edit_text("🤖 Расшифровываю голос через Gemini...")
        
        # Транскрибируем
        text = await transcribe_audio(bytes(audio_buffer))
        
        if not text:
            await status_msg.edit_text("⚠️ Не удалось распознать текст в голосовом сообщении.")
            return
            
        await status_msg.edit_text(f"✍️ Расшифрованный текст:\n\n*\"{text}\"*\n\n⚡ Сохраняю в GitHub...")
        
        # Формируем и отправляем на GitHub
        now = datetime.now()
        filename = f"tg-{now.strftime('%Y%m%d-%H%M%S')}.md"
        file_path = f"{config.OBSIDIAN_INBOX_DIR}/{filename}"
        
        md_content = generate_markdown_content(text, "voice")
        commit_msg = f"Add telegram voice note: {filename}"
        
        success = await upload_to_github(file_path, md_content, commit_msg)
        
        if success:
            # Дополнительно записываем в архив
            archive_success = await append_to_archive(text, "voice")
            archive_info = "\n📦 Добавлено в общий архив." if archive_success else "\n⚠️ Ошибка записи в архив."
            
            # Google Calendar Integration
            calendar_info = ""
            try:
                cal_result = await calendar_service.process_and_add_to_calendar(text)
                if cal_result:
                    time_info = cal_result['start']
                    if cal_result.get('all_day'):
                        time_info = f"{time_info.split('T')[0]} (весь день)"
                    else:
                        time_info = datetime.fromisoformat(cal_result['start']).strftime('%d.%m.%Y в %H:%M')
                    calendar_info = f"\n📅 Добавлено в Google Календарь:\n**{cal_result['title']}** ({time_info})"
            except Exception as cal_err:
                logger.error(f"Ошибка при обработке календаря: {cal_err}")
                
            await status_msg.edit_text(
                f"✅ Голосовая заметка сохранена!\n\n"
                f"📝 **Текст:**\n{text}\n\n"
                f"📄 **Файл:** `{file_path}`{archive_info}{calendar_info}",
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text("❌ Голос расшифрован, но не удалось записать в GitHub.")
            
    except Exception as e:
        logger.exception("Ошибка при обработке голосового сообщения")
        await status_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")

async def main():
    logger.info("Запуск бота Hermes...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
