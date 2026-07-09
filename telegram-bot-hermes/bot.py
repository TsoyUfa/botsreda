"""
Основной скрипт Telegram-бота Hermes (Тони Павлович).
Принимает текст и голосовые сообщения, расшифровывает голос через Gemini API,
содержит многопользовательский трекер целей/рефлексии, ИИ-CRM Джарвис для риелторов,
и интеграцию с Obsidian/GitHub для Антона Цоя.
"""
import logging
import asyncio
from datetime import datetime
import base64
import aiohttp
import os
import subprocess
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ContentType
from aiogram.filters import CommandStart, Command
from aiogram.client.session.aiohttp import AiohttpSession

import config
import calendar_service
import google.generativeai as genai
import db

# Состояния пользователей
user_states = {}

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
proxy_url = os.getenv("PROXY_URL")
if proxy_url:
    bot = Bot(token=config.BOT_TOKEN, session=AiohttpSession(proxy=proxy_url))
    logger.info(f"Запуск бота Hermes с прокси: {proxy_url}")
else:
    bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Фильтр для проверки администратора
def admin_only(message: Message) -> bool:
    return config.is_admin(message.from_user.id)

# ==========================================
# УТИЛИТЫ И ИНТЕГРАЦИЯ GITHUB
# ==========================================

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
    
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": commit_message,
        "content": content_b64,
        "branch": config.GITHUB_BRANCH
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                payload["sha"] = data["sha"]
                logger.info(f"Файл {file_path} уже существует, будет обновлен (sha: {data['sha']})")
        
        async with session.put(url, headers=headers, json=payload) as resp:
            if resp.status in [200, 201]:
                logger.info(f"Файл {file_path} успешно записан в GitHub.")
                return True
            else:
                err_body = await resp.text()
                logger.error(f"Ошибка записи в GitHub API (Код: {resp.status}): {err_body}")
                return False

async def append_to_archive(text: str, source_type: str) -> bool:
    """Добавление записи в единый файл-архив на GitHub (только для админа)."""
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
    
    new_entry = (
        f"\n## [{date_str} {time_str}] Тип: {source_type}\n"
        f"{text.strip()}\n"
        f"\n---\n"
    )
    
    async with aiohttp.ClientSession() as session:
        sha = None
        current_content = ""
        
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                sha = data["sha"]
                current_content = base64.b64decode(data["content"]).decode("utf-8")
            elif resp.status == 404:
                current_content = (
                    "# Архив голосовых и текстовых заметок Telegram\n\n"
                    "Все сообщения, отправленные через бота, сохраняются здесь хронологически.\n\n"
                )
            else:
                logger.error(f"Ошибка получения архива с GitHub (Код: {resp.status})")
                return False
                
        updated_content = current_content + new_entry
        content_b64 = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"Append new telegram note to archive: {date_str} {time_str}",
            "content": content_b64,
            "branch": config.GITHUB_BRANCH
        }
        if sha:
            payload["sha"] = sha
            
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

# ==========================================
# ИНСТРУМЕНТЫ И ЛОГИКА АНТОНА ПАВЛОВИЧА (ИИ-АГЕНТ)
# ==========================================

def run_local_command(cmd: str) -> str:
    """Выполнить bash-команду на компьютере Mac в папке Obsidian vault."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
            cwd=config.OBSIDIAN_VAULT_PATH,
            timeout=30
        )
        output = ""
        if result.stdout:
            output += f"--- OUT ---\n{result.stdout}\n"
        if result.stderr:
            output += f"--- ERR ---\n{result.stderr}\n"
        if not output:
            output = "Команда выполнена без вывода."
        return output
    except subprocess.TimeoutExpired:
        return "Ошибка: Превышено время ожидания (30 секунд)."
    except Exception as e:
        return f"Ошибка при выполнении команды: {str(e)}"

def read_local_file(filepath: str) -> str:
    """Прочитать содержимое файла на компьютере."""
    full_path = filepath if os.path.isabs(filepath) else os.path.join(config.OBSIDIAN_VAULT_PATH, filepath)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Ошибка чтения файла: {str(e)}"

def write_local_file(filepath: str, content: str) -> str:
    """Записать или перезаписать файл на компьютере."""
    full_path = filepath if os.path.isabs(filepath) else os.path.join(config.OBSIDIAN_VAULT_PATH, filepath)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Успешно записано в {filepath}"
    except Exception as e:
        return f"Ошибка записи файла: {str(e)}"

def list_local_dir(dirpath: str = ".") -> str:
    """Показать список файлов и папок в директории."""
    full_path = dirpath if os.path.isabs(dirpath) else os.path.join(config.OBSIDIAN_VAULT_PATH, dirpath)
    try:
        items = os.listdir(full_path)
        result = []
        for item in items:
            item_path = os.path.join(full_path, item)
            is_dir = os.path.isdir(item_path)
            prefix = "[DIR] " if is_dir else "[FILE]"
            result.append(f"{prefix} {item}")
        return "\n".join(result) if result else "Папка пуста."
    except Exception as e:
        return f"Ошибка списка папки: {str(e)}"

async def run_anton_pavlovich_agent(prompt: str, is_admin_user: bool = False) -> str:
    """Запуск ИИ-агентского интерфейса Тони Павлович. Админам доступны bash-инструменты."""
    if not config.GEMINI_API_KEY:
        return "Ошибка: Ключ Gemini API не настроен."
        
    loop = asyncio.get_running_loop()
    
    def _call_agent():
        tools = [run_local_command, read_local_file, write_local_file, list_local_dir] if is_admin_user else None
        
        system_instruction = (
            "Ты — Антон Павлович, умный, рассудительный и преданный личный ассистент риелтора. "
            "Твоя задача — отвечать на вопросы, помогать структурировать информацию и давать мудрые советы. "
            "Общайся вежливо, по-деловому (в стиле Антона Павловича Чехова — интеллигентно, уважительно, с легкой иронией и лаконично), "
            "отвечай на русском языке."
        )
        if is_admin_user:
            system_instruction += (
                " У тебя есть доступ к компьютеру Mac Антона Цоя через локальные инструменты (выполнение bash-команд, чтение/запись файлов). "
                "Выполняй системные задачи бережно и аккуратно."
            )
            
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=tools,
            system_instruction=system_instruction
        )
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(prompt)
        return response.text
        
    try:
        return await loop.run_in_executor(None, _call_agent)
    except Exception as e:
        logger.exception("Ошибка в работе агента Антона Павловича")
        return f"Произошла ошибка в работе агента: {str(e)}"

# ==========================================
# ИИ-РАЗБОР И CRM
# ==========================================

async def detect_timezone_by_city(city: str) -> str:
    """Определение часового пояса IANA по названию города через Gemini."""
    if not config.GEMINI_API_KEY:
        return "Asia/Yekaterinburg"
        
    prompt = f"""
Определи часовой пояс в формате IANA (например, "Europe/Moscow", "Asia/Yekaterinburg", "Asia/Novosibirsk", "Asia/Krasnoyarsk", "Asia/Vladivostok") для следующего города:
"{city}"

Ответь ТОЛЬКО названием часового пояса, без markdown-разметки, без пробелов, без комментариев и знаков препинания. Например: "Europe/Moscow".
Если город неизвестен или находится за пределами РФ, верни наиболее подходящий часовой пояс РФ или "Asia/Yekaterinburg" по умолчанию.
"""
    try:
        loop = asyncio.get_running_loop()
        def _call_gemini():
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip().replace('"', '').replace("'", "")
            
        res = await loop.run_in_executor(None, _call_gemini)
        return res
    except Exception as e:
        logger.error(f"Ошибка определения таймзоны для {city}: {e}")
        return "Asia/Yekaterinburg"

async def parse_message_intent(text: str, user_id: int, user_name: str) -> dict:
    """Анализирует сообщение через Gemini API и возвращает структурированный JSON намерений."""
    if not config.GEMINI_API_KEY:
        return {"intent": "save_note", "note_text": text}
        
    now = datetime.now()
    user_data = await db.get_user(user_id)
    timezone_str = user_data["timezone"] if user_data else "Asia/Yekaterinburg"
    try:
        user_tz = ZoneInfo(timezone_str)
        user_time = datetime.now(user_tz)
    except Exception:
        user_time = now
        
    current_time_str = user_time.strftime("%Y-%m-%d %H:%M:%S")
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    day_of_week = days[user_time.weekday()]
    
    prompt = f"""
Ты — умный ИИ-ассистент риелтора по имени Тони Павлович. Твоя задача — проанализировать текст сообщения пользователя ({user_name}) и определить его намерение.

Текущая дата и время пользователя: {current_time_str} ({day_of_week})

Возможные намерения:
1. "crm_add_client": Добавить нового клиента или обновить информацию о существующем.
   Примеры: "Новый покупатель Марат, ищет квартиру в ЖК Гранд Авеню", "Клиентка Ирина 89173332211, хочет продать вторичку".
2. "crm_add_task": Добавить задачу по клиенту с датой/временем напоминания.
   Примеры: "Надо перезвонить Марату завтра в 14:00", "Встреча с Ириной в пятницу в 12:00 на объекте", "В среду в 10 утра отправить презентацию Марату".
   Критически важно: вычисли абсолютную дату и время напоминания (due_date) в формате YYYY-MM-DD HH:MM. Относительные даты ("завтра", "в среду", "в пятницу") вычисляй на основе даты {current_time_str.split()[0]}.
3. "show_crm": Запрос списка клиентов или задач.
   Примеры: "покажи мои задачи", "кто у меня в клиентах", "какие планы", "список дел".
4. "complete_task": Риелтор сообщает о завершении дела.
   Примеры: "задача по Марату выполнена", "позвонил Ирине", "сделал задачу".
5. "save_note": Обычная мысль, черновик, конспект выступления, инсайт. Не содержит параметров сделок или конкретных задач с напоминанием.
   Примеры: "Идея для reels про ипотечные ставки", "Инсайт: клиенты боятся роста первоначального взноса".

Проанализируй текст:
"{text}"

Верни ответ в формате JSON со следующими полями (если поле применить нельзя, верни null):
{{
  "intent": "crm_add_client" | "crm_add_task" | "show_crm" | "complete_task" | "save_note",
  "client_name": "Имя клиента (например, Ирина, Марат)",
  "phone": "номер телефона (если есть)",
  "details": "суть запроса клиента, бюджет, ЖК, пожелания",
  "task_text": "краткое описание того, что нужно сделать",
  "due_date": "YYYY-MM-DD HH:MM (абсолютная дата и время напоминания)",
  "note_text": "текст заметки (для save_note)"
}}

Верни ТОЛЬКО валидный JSON без разметки markdown (без ```json ... ```), без лишнего текста или комментариев.
"""
    try:
        loop = asyncio.get_running_loop()
        def _call_gemini():
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
            
        response_text = await loop.run_in_executor(None, _call_gemini)
        
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                response_text = "\n".join(lines[1:-1]).strip()
                
        import json
        data = json.loads(response_text)
        return data
    except Exception as e:
        logger.error(f"Ошибка разбора намерения в Gemini: {e}")
        return {"intent": "save_note", "note_text": text}

async def generate_monthly_reflection_report(user_id: int) -> str:
    """Генерирует ИИ-отчет по итогам рефлексии пользователя за последние 30 дней."""
    logs = await db.get_recent_logs(user_id, 30)
    if not logs:
        return "За последние 30 дней не найдено записей планирования и рефлексии. Начните вести ежедневный учет, чтобы я мог составить отчет."
        
    user_data = await db.get_user(user_id)
    name = user_data["full_name"] if user_data else "Коллега"
    
    analysis_text = ""
    for log in logs:
        analysis_text += f"Дата: {log['date']}\n"
        if log['morning_plan']:
            analysis_text += f"Утренний план:\n{log['morning_plan']}\n"
        if log['evening_reflection']:
            analysis_text += f"Вечерний итог:\n{log['evening_reflection']}\n"
        analysis_text += "-----------\n"
        
    prompt = f"""
Ты — Антон Павлович, умный, рассудительный и преданный ИИ-коуч риелторов. Твоя задача — проанализировать ежедневные отчеты планирования и рефлексии риелтора ({name}) за последний месяц и составить глубокий, аналитический и мотивирующий отчет.

Данные рефлексии риелтора за месяц:
{analysis_text}

Составь отчет по следующему плану (используй стиль Чехова — интеллигентно, уважительно, с легкой иронией и лаконично):
1. **Общий фокус месяца:** Какие цели преобладали, куда уходили основные усилия.
2. **Анализ продуктивности:** Что получалось выполнять стабильно, а какие задачи систематически откладывались или проваливались.
3. **Ключевые инсайты:** Самые ценные выводы и решения, к которым пришел риелтор.
4. **Персональные рекомендации:** 3-5 конкретных, практических шагов по улучшению результатов на следующий месяц.

Ответь в красивой markdown-разметке на русском языке.
"""
    try:
        loop = asyncio.get_running_loop()
        def _call_gemini():
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
            
        return await loop.run_in_executor(None, _call_gemini)
    except Exception as e:
        logger.error(f"Ошибка генерации отчета рефлексии: {e}")
        return f"Произошла ошибка при анализе отчета: {str(e)}"

# ==========================================
# РЕФЛЕКСИЯ И БРИФИНГИ
# ==========================================

async def save_reflection(user_id: int, text: str) -> bool:
    """Сохранение рефлексии в БД, локальный файл Obsidian и в архив (только для админа)."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    # 1. Сохраняем в SQLite БД
    await db.save_evening_reflection(user_id, date_str, text)
    
    if not config.is_admin(user_id):
        return True
        
    log = await db.get_daily_log(user_id, date_str)
    morning_plan = log["morning_plan"] if log else ""
    morning_plan_section = f"\n### Запланировано утром:\n{morning_plan}\n" if morning_plan else ""
    
    reflection_content = f"""---
type: reflection
date: {date_str}
time: {time_str}
tags:
  - reflection
  - daily-log
---

# Рефлексия дня ({date_str})
{morning_plan_section}
### Итоги вечера:
{text.strip()}
"""
    
    filename = f"Reflection-{date_str}.md"
    local_path = os.path.join(config.OBSIDIAN_VAULT_PATH, "Inbox", filename)
    
    try:
        # Пишем локально
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(reflection_content)
            
        logger.info(f"Рефлексия сохранена локально: {local_path}")
        
        # Отправляем на GitHub
        github_path = f"{config.OBSIDIAN_INBOX_DIR}/{filename}"
        await upload_to_github(github_path, reflection_content, f"Add reflection for {date_str}")
        
        # И дописываем в общий архив
        await append_to_archive(f"**РЕФЛЕКСИЯ ДНЯ:**\n{text}", "reflection")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения рефлексии: {e}")
        return False

async def send_morning_briefing_to_user(user_id: int, date_str: str):
    """Сборка и отправка утреннего брифинга конкретному пользователю."""
    logger.info(f"Генерация утреннего брифинга для {user_id}...")
    
    if config.is_admin(user_id):
        dashboard_path = os.path.join(config.OBSIDIAN_VAULT_PATH, "1. Бизнес/00-dashboard.md")
        
        focus_of_week = "Не указан"
        tasks_today = []
        
        if os.path.exists(dashboard_path):
            try:
                with open(dashboard_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for line in content.split('\n'):
                    if "Фокус недели:" in line:
                        focus_of_week = line.replace("Фокус недели:", "").strip()
                        break
                        
                lines = content.split('\n')
                task_section = False
                for line in lines:
                    if "Задачи на сегодня:" in line:
                        task_section = True
                        continue
                    if task_section and line.startswith('- '):
                        tasks_today.append(line.replace('- ', '').strip())
                        if len(tasks_today) >= 5:
                            break
                    elif task_section and line.strip() and not line.startswith('- ') and not line.startswith('#'):
                        task_section = False
            except Exception as e:
                logger.error(f"Ошибка парсинга дашборда: {e}")
                
        tasks_str = "\n".join([f"• {t}" for t in tasks_today]) if tasks_today else "Нет задач на сегодня"
        recent_logs = await db.get_recent_logs(user_id, 7)
        recent_plans_str = ""
        if recent_logs:
            recent_plans_str = "\n".join([f"📅 {log['date']}:\n{log['morning_plan'].strip()}" for log in recent_logs if log['morning_plan']])
        else:
            recent_plans_str = "Нет предыдущих планов в базе данных."
            
        message = (
            f"🌅 **УТРЕННИЙ БРИФИНГ — {date_str}**\n\n"
            f"🎯 **Фокус недели:**\n{focus_of_week}\n\n"
            f"📋 **План на сегодня:**\n{tasks_str}\n\n"
            f"📚 **Цели за последние 7 дней:**\n{recent_plans_str}\n\n"
            f"--- \n"
            f"Антон Павлович готов к работе. Напишите или наговорите ваши корректировки к плану на сегодня."
        )
        plan_to_save = f"Фокус недели: {focus_of_week}\nЗадачи:\n{tasks_str}"
        await db.save_morning_plan(user_id, date_str, plan_to_save)
        await bot.send_message(user_id, message, parse_mode="Markdown")
    else:
        pending_tasks = await db.get_pending_tasks(user_id)
        tasks_str = ""
        if pending_tasks:
            tasks_str = "\n".join([f"• {t['task_text']} (клиент: {t['client_name']})" for t in pending_tasks[:5]])
        else:
            tasks_str = "Нет запланированных задач в CRM."
            
        recent_logs = await db.get_recent_logs(user_id, 3)
        recent_plans_str = ""
        if recent_logs:
            recent_plans_str = "\n".join([f"📅 {log['date']}:\n{log['morning_plan'].strip()}" for log in recent_logs if log['morning_plan']])
        else:
            recent_plans_str = "Вы еще не планировали цели в боте."
            
        message = (
            f"🌅 **ДОБРОЕ УТРО, КОЛЛЕГА! — {date_str}**\n\n"
            f"📋 **Задачи из вашей CRM:**\n{tasks_str}\n\n"
            f"🎯 **Ваши предыдущие цели:**\n{recent_plans_str}\n\n"
            f"--- \n"
            f"Напишите или наговорите ваш **фокус и цели на сегодня**. Я бережно запишу их."
        )
        user_states[user_id] = "awaiting_morning_plan"
        await bot.send_message(user_id, message, parse_mode="Markdown")

async def send_evening_prompt_to_user(user_id: int, date_str: str):
    """Сборка и отправка вечернего опроса рефлексии."""
    logger.info(f"Отправка вечернего запроса для {user_id}...")
    log = await db.get_daily_log(user_id, date_str)
    plan_info = ""
    if log and log["morning_plan"]:
        plan_info = f"📝 **Что планировалось на сегодня:**\n{log['morning_plan']}\n\n"
        
    message = (
        f"🌆 **ИТОГИ ДНЯ — {date_str}**\n\n"
        f"Как прошли ваши дела сегодня?\n\n"
        f"{plan_info}"
        f"✅ **Что из запланированного удалось выполнить?**\n"
        f"❌ **Что не выполнили и почему?**\n"
        f"💡 **Какие инсайты или решения появились?**\n\n"
        f"🎤 *Наговорите голосовым или напишите ответ.*"
    )
    user_states[user_id] = "awaiting_reflection"
    await bot.send_message(user_id, message, parse_mode="Markdown")

# ==========================================
# ПЛАНИРОВЩИК (КРОН)
# ==========================================

async def scheduler_loop():
    """Фоновый цикл проверки времени по часовым поясам пользователей."""
    logger.info("Запуск фонового планировщика...")
    while True:
        try:
            users = await db.get_all_users()
            for user in users:
                user_id = user["user_id"]
                if user["status"] != "active":
                    continue
                
                timezone_str = user["timezone"] or "Asia/Yekaterinburg"
                try:
                    user_tz = ZoneInfo(timezone_str)
                    user_local_time = datetime.now(user_tz)
                except Exception as tz_err:
                    logger.error(f"Таймзона {timezone_str} у пользователя {user_id} не найдена: {tz_err}")
                    user_tz = ZoneInfo("Asia/Yekaterinburg")
                    user_local_time = datetime.now(user_tz)
                
                today_str = user_local_time.strftime("%Y-%m-%d")
                
                # Утренний брифинг в 8:30
                if user_local_time.hour == 8 and user_local_time.minute == 30:
                    if user["last_morning_brief"] != today_str:
                        await send_morning_briefing_to_user(user_id, today_str)
                        await db.mark_morning_brief_sent(user_id, today_str)
                
                # Вечерний опрос в 20:00
                if user_local_time.hour == 20 and user_local_time.minute == 0:
                    if user["last_evening_prompt"] != today_str:
                        await send_evening_prompt_to_user(user_id, today_str)
                        await db.mark_evening_prompt_sent(user_id, today_str)
            
            # Проверка CRM напоминаний
            pending_tasks = await db.get_all_pending_tasks_for_reminders()
            for task in pending_tasks:
                timezone_str = task["timezone"] or "Asia/Yekaterinburg"
                try:
                    user_tz = ZoneInfo(timezone_str)
                    user_local_time = datetime.now(user_tz)
                except Exception:
                    user_tz = ZoneInfo("Asia/Yekaterinburg")
                    user_local_time = datetime.now(user_tz)
                
                try:
                    task_due_time = datetime.strptime(task["due_date"], "%Y-%m-%d %H:%M")
                    task_due_time = task_due_time.replace(tzinfo=user_tz)
                    
                    if user_local_time >= task_due_time:
                        msg = (
                            f"🔔 **НАПОМИНАНИЕ ПО ЗАДАЧЕ**\n\n"
                            f"👥 **Клиент:** {task['client_name']}\n"
                            f"📝 **Что сделать:** {task['task_text']}\n"
                            f"📅 **Срок:** {task['due_date']}\n\n"
                            f"Для отметки выполнения напишите: `выполнил задачу по {task['client_name']}`"
                        )
                        await bot.send_message(task["user_id"], msg, parse_mode="Markdown")
                        await db.mark_task_reminded(task["task_id"])
                except Exception as task_err:
                    logger.error(f"Ошибка напоминания по задаче {task['task_id']}: {task_err}")
                    
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Ошибка в цикле планировщика: {e}")
            await asyncio.sleep(10)

# ==========================================
# ОБРАБОТЧИКИ СООБЩЕНИЙ И КОМАНД
# ==========================================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Старт бота и запуск регистрации, если пользователя нет в базе."""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if user:
        role_str = "администратор" if user["role"] == "admin" else "риелтор"
        await message.reply(
            f"👋 С возвращением, *{user['full_name']}*!\n\n"
            f"Рад приветствовать вас снова в качестве {role_str} системы.\n"
            f"Тони Павлович готов к работе. Напишите вашу мысль или задачу по клиенту.",
            parse_mode="Markdown"
        )
    else:
        user_states[user_id] = {"state": "register_name"}
        await message.reply(
            "👋 Здравствуйте! Я — **Тони Павлович**, ваш личный ИИ-ассистент риелтора и CRM-помощник.\n\n"
            "Похоже, вы здесь впервые. Пожалуйста, напишите ваше **ФИО** для начала регистрации.",
            parse_mode="Markdown"
        )

@dp.message(Command("test_briefing"))
async def cmd_test_briefing(message: Message):
    """Принудительный запуск утреннего брифинга."""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await message.reply("Вы еще не зарегистрированы.")
        return
    await message.reply("🔄 Запуск утреннего брифинга...")
    now = datetime.now(ZoneInfo(user["timezone"]))
    await send_morning_briefing_to_user(user_id, now.strftime("%Y-%m-%d"))

@dp.message(Command("test_reflection"))
async def cmd_test_reflection(message: Message):
    """Принудительный запуск вечернего запроса."""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await message.reply("Вы еще не зарегистрированы.")
        return
    await message.reply("🔄 Запуск вечернего опроса рефлексии...")
    now = datetime.now(ZoneInfo(user["timezone"]))
    await send_evening_prompt_to_user(user_id, now.strftime("%Y-%m-%d"))

@dp.message(Command("report"))
async def cmd_report(message: Message):
    """Запрос ИИ-отчета рефлексии за 30 дней."""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await message.reply("Вы еще не зарегистрированы.")
        return
    status_msg = await message.reply("🧠 Тони Павлович собирает данные и анализирует вашу рефлексию за последний месяц...")
    report = await generate_monthly_reflection_report(user_id)
    await status_msg.edit_text(report, parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Рассылка сообщения всем ученикам (только админ)."""
    user_id = message.from_user.id
    if not config.is_admin(user_id):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
        
    text = message.text[11:].strip()
    if not text:
        await message.reply("Использование: `/broadcast [текст сообщения]`")
        return
        
    users = await db.get_all_users()
    sent_count = 0
    for u in users:
        try:
            await bot.send_message(u["user_id"], f"📢 **ОБЪЯВЛЕНИЕ ОТ РУКОВОДИТЕЛЯ:**\n\n{text}", parse_mode="Markdown")
            sent_count += 1
        except Exception as e:
            logger.error(f"Не удалось отправить рассылку для {u['user_id']}: {e}")
            
    await message.reply(f"✅ Рассылка успешно отправлена {sent_count} пользователям.")

# ==========================================
# ОБРАБОТКА ОБЫЧНЫХ СООБЩЕНИЙ
# ==========================================

async def process_text_message(message: Message, text: str):
    """Обработка входящего текста (как набранного, так и распознанного из голоса)."""
    user_id = message.from_user.id
    state = user_states.get(user_id)
    
    # 1. Проверяем регистрацию
    user = await db.get_user(user_id)
    if not user:
        if isinstance(state, dict) and state.get("state") == "register_name":
            name = text.strip()
            user_states[user_id] = {"state": "register_city", "name": name}
            await message.reply(
                f"Приятно познакомиться, *{name}*!\n\n"
                f"🏙️ Теперь напишите ваш **город**. Это необходимо для корректной работы расписания.",
                parse_mode="Markdown"
            )
            return
        elif isinstance(state, dict) and state.get("state") == "register_city":
            city = text.strip()
            name = state["name"]
            
            timezone = await detect_timezone_by_city(city)
            role = "admin" if config.is_admin(user_id) else "user"
            
            await db.add_user(user_id, message.from_user.username or "", name, timezone, role)
            user_states[user_id] = None
            
            await message.reply(
                f"🎉 **Регистрация успешно завершена!**\n\n"
                f"👤 **Имя:** {name}\n"
                f"🏙️ **Город:** {city}\n"
                f"⏰ **Часовой пояс:** `{timezone}`\n\n"
                f"Каждое утро в **8:30** я буду присылать вам цели, а вечером в **20:00** — итоги дня.\n"
                f"Для добавления задачи в CRM просто напишите мне (например: *'встреча с Мариной в среду в 15:00'*).",
                parse_mode="Markdown"
            )
            return
        else:
            user_states[user_id] = {"state": "register_name"}
            await message.reply(
                "👋 Пожалуйста, напишите ваше **ФИО** для регистрации в системе.",
                parse_mode="Markdown"
            )
            return
            
    # 2. Проверяем состояние планирования (утро)
    if state == "awaiting_morning_plan":
        user_states[user_id] = None
        timezone_str = user["timezone"] or "Asia/Yekaterinburg"
        today_str = datetime.now(ZoneInfo(timezone_str)).strftime("%Y-%m-%d")
        
        await db.save_morning_plan(user_id, today_str, text)
        await message.reply("🎯 Отлично, ваши цели на сегодня зафиксированы! Хорошего рабочего дня! 🚀")
        return

    # 3. Проверяем состояние рефлексии (вечер)
    if state == "awaiting_reflection":
        user_states[user_id] = None
        status_msg = await message.reply("📝 Сохраняю рефлексию...")
        success = await save_reflection(user_id, text)
        if success:
            await status_msg.edit_text("✅ Ваша рефлексия успешно сохранена! Спокойной ночи! 🌙")
        else:
            await status_msg.edit_text("⚠️ Возникла заминка при записи рефлексии (но данные сохранены в локальную базу данных).")
        return

    # 4. Проверяем команду ИИ-Агента Антона Павловича
    text_lower = text.lower()
    is_agent_cmd = False
    prompt = text
    
    if text_lower.startswith("антон павлович") or text_lower.startswith("тони павлович"):
        # Отрезаем имя агента
        prompt = text[14:].strip().strip(",")
        is_agent_cmd = True
    elif text_lower.startswith("/agent"):
        prompt = text[7:].strip()
        is_agent_cmd = True
        
    if is_agent_cmd:
        if not prompt:
            await message.reply("Слушаю вас. Какое поручение вы хотите дать?")
            return
            
        status_msg = await message.reply("🧠 Тони Павлович принял задачу и приступает к выполнению...")
        is_admin_user = config.is_admin(user_id)
        agent_result = await run_anton_pavlovich_agent(prompt, is_admin_user)
        await status_msg.edit_text(f"🤖 **Результат работы Тони Павловича:**\n\n{agent_result}")
        return

    # 5. Обычное поведение: ИИ-разбор CRM и Заметок
    parsed = await parse_message_intent(text, user_id, user["full_name"])
    intent = parsed.get("intent", "save_note")
    
    if intent == "crm_add_client":
        client_name = parsed.get("client_name")
        phone = parsed.get("phone")
        details = parsed.get("details")
        
        if not client_name:
            await message.reply("⚠️ Не удалось извлечь имя клиента. Напишите, пожалуйста, точнее: *Добавить клиента [Имя]*")
            return
            
        await db.add_crm_client(user_id, client_name, phone, 'in_work', details)
        reply = (
            f"👤 **НОВЫЙ КЛИЕНТ ДОБАВЛЕН В CRM**\n\n"
            f"👤 **Имя:** {client_name}\n"
            f"📞 **Телефон:** {phone or 'Не указан'}\n"
            f"📋 **Детали:** {details or 'Не указаны'}\n"
        )
        await message.reply(reply, parse_mode="Markdown")
        
    elif intent == "crm_add_task":
        client_name = parsed.get("client_name")
        task_text = parsed.get("task_text")
        due_date = parsed.get("due_date")
        
        if not task_text or not due_date:
            await message.reply("⚠️ Не удалось разобрать задачу или время напоминания. Пожалуйста, укажите дату и время (например: *завтра в 12:00*).")
            return
            
        client_id = None
        if client_name:
            client = await db.find_crm_client_by_name(user_id, client_name)
            if client:
                client_id = client["client_id"]
                client_name = client["client_name"]
            else:
                client_id = await db.add_crm_client(user_id, client_name)
                
        await db.add_crm_task(user_id, client_id, task_text, due_date)
        
        reply = (
            f"📅 **ЗАДАЧА CRM СОЗДАНА**\n\n"
            f"👥 **Клиент:** {client_name or 'Без клиента'}\n"
            f"📝 **Что сделать:** {task_text}\n"
            f"⏰ **Срок:** {due_date}\n\n"
            f"Я напомню вовремя! 🚀"
        )
        await message.reply(reply, parse_mode="Markdown")
        
    elif intent == "show_crm":
        clients = await db.get_crm_clients(user_id)
        tasks = await db.get_pending_tasks(user_id)
        
        clients_str = "\n".join([f"• {c['client_name']} ({c['phone'] or 'нет тел.'})" for c in clients[:10]]) if clients else "Нет клиентов."
        tasks_str = "\n".join([f"• {t['due_date']}: {t['task_text']} (клиент: {t['client_name']})" for t in tasks[:10]]) if tasks else "Нет активных задач."
        
        reply = (
            f"📊 **ВАША CRM-ПАНЕЛЬ**\n\n"
            f"👥 **Клиенты:**\n{clients_str}\n\n"
            f"📋 **Предстоящие задачи:**\n{tasks_str}"
        )
        await message.reply(reply, parse_mode="Markdown")
        
    elif intent == "complete_task":
        client_name = parsed.get("client_name")
        tasks = await db.get_pending_tasks(user_id)
        
        target_task = None
        if client_name and tasks:
            for t in tasks:
                if client_name.lower() in t["client_name"].lower():
                    target_task = t
                    break
        elif tasks:
            target_task = tasks[0]
            
        if target_task:
            await db.complete_task(target_task["task_id"])
            await message.reply(f"✅ Задача *'{target_task['task_text']}'* по клиенту *{target_task['client_name']}* успешно выполнена!")
        else:
            await message.reply("⚠️ Не найдено активных задач для отметки выполнения.")
            
    else:  # intent == "save_note"
        note_text = parsed.get("note_text") or text
        
        if config.is_admin(user_id):
            status_msg = await message.reply("⚡ Сохраняю заметку в Obsidian...")
            now = datetime.now()
            filename = f"tg-{now.strftime('%Y%m%d-%H%M%S')}.md"
            file_path = f"{config.OBSIDIAN_INBOX_DIR}/{filename}"
            md_content = generate_markdown_content(note_text, "text")
            commit_msg = f"Add telegram text note: {filename}"
            
            success = await upload_to_github(file_path, md_content, commit_msg)
            
            if success:
                await append_to_archive(note_text, "text")
                calendar_info = ""
                try:
                    cal_result = await calendar_service.process_and_add_to_calendar(note_text)
                    if cal_result:
                        time_info = cal_result['start']
                        if cal_result.get('all_day'):
                            time_info = f"{time_info.split('T')[0]} (весь день)"
                        else:
                            time_info = datetime.fromisoformat(cal_result['start']).strftime('%d.%m.%Y в %H:%M')
                        calendar_info = f"\n📅 Добавлено в Google Календарь:\n**{cal_result['title']}** ({time_info})"
                except Exception as cal_err:
                    logger.error(f"Ошибка календаря: {cal_err}")
                    
                await status_msg.edit_text(
                    f"✅ Заметка успешно сохранена на GitHub!\n"
                    f"📄 Файл: `{file_path}`"
                    f"{calendar_info}",
                    parse_mode="Markdown"
                )
            else:
                await status_msg.edit_text("❌ Не удалось отправить заметку на GitHub. Записано локально в БД.")
                await db.add_user_note(user_id, note_text)
        else:
            await db.add_user_note(user_id, note_text)
            await message.reply("📝 Мысль успешно сохранена в ваш архив Тони Павловича!")

@dp.message(F.text)
async def handle_text_message(message: Message):
    """Основной обработчик текста."""
    await process_text_message(message, message.text)

@dp.message(F.voice)
async def handle_voice_message(message: Message):
    """Основной обработчик голосовых сообщений (расшифровка + выполнение)."""
    status_msg = await message.reply("🎙️ Загружаю голосовое сообщение...")
    
    try:
        voice_file = await bot.get_file(message.voice.file_id)
        
        audio_buffer = bytearray()
        async with aiohttp.ClientSession() as session:
            file_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{voice_file.file_path}"
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    audio_buffer = await resp.read()
                else:
                    raise Exception(f"Ошибка загрузки голосового файла: {resp.status}")
        
        await status_msg.edit_text("🤖 Расшифровываю голос через Gemini...")
        text = await transcribe_audio(bytes(audio_buffer))
        
        if not text:
            await status_msg.edit_text("⚠️ Не удалось распознать текст в голосовом сообщении.")
            return
            
        await status_msg.delete()
        
        # Отправляем сообщение о распознанном тексте
        await message.reply(f"✍️ **Распознанный текст:**\n_\"{text}\"_", parse_mode="Markdown")
        
        # Запускаем обработку текста
        await process_text_message(message, text)
            
    except Exception as e:
        logger.exception("Ошибка при обработке голосового сообщения")
        await status_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")

async def main():
    logger.info("Запуск бота Тони Павлович...")
    await db.init_db()
    asyncio.create_task(scheduler_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
