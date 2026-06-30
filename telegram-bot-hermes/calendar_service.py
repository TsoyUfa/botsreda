import logging
import json
import asyncio
from datetime import datetime
import aiohttp
import google.generativeai as genai
import config

logger = logging.getLogger("HermesBot.Calendar")

async def parse_event_with_gemini(text: str) -> dict:
    """
    Анализирует текст с помощью Gemini и извлекает параметры события календаря.
    Возвращает словарь с параметрами события или None, если событие не найдено.
    """
    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY не настроен, парсинг календаря пропущен.")
        return {"is_event": False}

    now = datetime.now()
    current_time_iso = now.isoformat()
    # Получаем день недели на русском
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    day_of_week = days[now.weekday()]

    prompt = f"""
Ты — умный помощник для планирования. Проанализируй следующий текст и определи, содержит ли он задачу, встречу, созвон или любое другое событие, которое нужно внести в Google Календарь.

Исходный текст: "{text}"

Информация для привязки относительного времени:
- Текущая дата и время: {current_time_iso}
- Текущий день недели: {day_of_week}

Правила разбора:
1. Если это просто общая заметка, мысль, факт, кусок кода или не содержит указания на задачу/встречу, верни JSON: {{"is_event": false}}
2. Если это задача или встреча (например: "встреча завтра в 15:00", "созвон в пятницу", "напомни сделать отчет к среде", "купить молоко сегодня в 18"):
   - Вычисли абсолютные дату и время начала и окончания события в формате ISO-8601 (без указания таймзоны, просто локальное время: YYYY-MM-DDTHH:MM:SS).
   - Если указана дата, но нет времени, установи 'all_day' в true, а время начала на 00:00:00.
   - Если указано только время начала, по умолчанию сделай длительность 1 час.
   - Верни JSON с полями:
     - "is_event": true
     - "title": Краткое название события на русском (например, "Встреча с инвестором", "Купить молоко")
     - "start": "YYYY-MM-DDTHH:MM:SS" (время начала)
     - "end": "YYYY-MM-DDTHH:MM:SS" (время окончания)
     - "all_day": true/false
     - "description": Полное описание (или исходный текст)

Верни ТОЛЬКО валидный JSON без разметки markdown (без ```json ... ```), без лишнего текста, комментариев или пробелов.
"""

    try:
        loop = asyncio.get_running_loop()
        def _call_gemini():
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
            
        response_text = await loop.run_in_executor(None, _call_gemini)
        
        # Очистим от разметки markdown, если она есть
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                response_text = "\n".join(lines[1:-1]).strip()
                
        data = json.loads(response_text)
        return data
    except Exception as e:
        logger.error(f"Ошибка парсинга события через Gemini: {e}")
        return {"is_event": False}

async def add_to_google_calendar(event_data: dict) -> dict:
    """
    Отправляет параметры события на Google Apps Script Web App.
    Возвращает ответ от вебхука в виде словаря.
    """
    url = config.GOOGLE_CALENDAR_WEBHOOK_URL
    if not url:
        logger.warning("GOOGLE_CALENDAR_WEBHOOK_URL не настроен.")
        return {"status": "error", "message": "Webhook URL not configured"}
        
    payload = {
        "title": event_data.get("title"),
        "start": event_data.get("start"),
        "end": event_data.get("end"),
        "all_day": event_data.get("all_day", False),
        "description": event_data.get("description", "")
      }
      
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=15) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"Событие успешно добавлено в Google Календарь: {result}")
                    return result
                else:
                    err_text = await resp.text()
                    logger.error(f"Ошибка при вызове Apps Script (Код {resp.status}): {err_text}")
                    return {"status": "error", "message": f"Server returned code {resp.status}"}
    except Exception as e:
        logger.error(f"Не удалось подключиться к Google Apps Script Web App: {e}")
        return {"status": "error", "message": str(e)}

async def process_and_add_to_calendar(text: str) -> dict:
    """
    Полный цикл: парсинг текста через Gemini -> добавление в Google Календарь при обнаружении события.
    Возвращает результат добавления или None, если событие не обнаружено/произошла ошибка.
    """
    if not config.GOOGLE_CALENDAR_WEBHOOK_URL:
        return None
        
    parsed = await parse_event_with_gemini(text)
    if parsed.get("is_event"):
        logger.info(f"Обнаружено событие в тексте: {parsed['title']} на {parsed['start']}")
        result = await add_to_google_calendar(parsed)
        if result.get("status") == "success":
            return {
                "title": parsed["title"],
                "start": parsed["start"],
                "end": parsed["end"],
                "all_day": parsed["all_day"],
                "calendar_name": result.get("calendar_name", "Дефолтный")
            }
    return None
