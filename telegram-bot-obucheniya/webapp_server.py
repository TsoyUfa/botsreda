"""Flask API-сервер для Telegram Web App «Среда обучения 2.0»."""
import os
import re
import asyncio
import logging
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Добавляем путь к текущей директории в sys.path для корректных импортов
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
import db
import lessons

# Инициализация логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("webapp_server")

load_dotenv()

app = Flask(__name__)

# Хелпер для запуска асинхронных корутин из синхронного Flask
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# CORS-заголовки для поддержки Netlify / GitHub Pages
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/health', methods=['GET', 'POST'])
def health_check():
    """Проверка работоспособности"""
    return jsonify({"status": "ok", "message": "Sreda 2.0 API server is running"})

@app.route('/api/user/data', methods=['POST'])
def get_user_data():
    """Получение или создание профиля пользователя"""
    data = request.json or {}
    user_id = data.get("user_id")
    username = data.get("username", "")
    first_name = data.get("first_name", "Студент")
    
    if not user_id:
        return jsonify({"success": False, "error": "user_id is required"}), 400
        
    # Ищем пользователя, если его нет — создаем
    user = run_async(db.get_user(user_id))
    if not user:
        run_async(db.create_user(user_id, username, full_name=first_name))
        user = run_async(db.get_user(user_id))
        
    # Рассчитываем детальный прогресс для TWA
    progress = {}
    current_block = user["current_block"]
    current_lesson = user["current_lesson"]
    status = user["status"]
    
    for block_id in range(1, 7):
        total = 2  # В каждом блоке Среды 2.0 ровно 2 урока
        completed_lessons = []
        
        if block_id < current_block or status == "completed":
            completed_lessons = [f"{block_id}.1", f"{block_id}.2"]
        elif block_id == current_block:
            if status == "awaiting_review":
                completed_lessons = [f"{block_id}.1", f"{block_id}.2"]
            elif current_lesson == f"{block_id}.2":
                completed_lessons = [f"{block_id}.1"]
                
        progress[str(block_id)] = {
            "lessons_completed": len(completed_lessons),
            "total_lessons": total,
            "completed_lessons": completed_lessons,
            "study_time": len(completed_lessons) * 15
        }
        
    # Добавляем общий статус курса в прогресс
    progress["status"] = status
    progress["current_block"] = current_block
    progress["current_lesson"] = current_lesson
    
    return jsonify({
        "success": True,
        "user_info": {
            "id": user["user_id"],
            "full_name": user["full_name"],
            "username": user["username"],
            "status": status,
            "current_block": current_block,
            "current_lesson": current_lesson
        },
        "progress": progress
    })

@app.route('/api/modules/list', methods=['POST'])
def list_modules():
    """Получение списка блоков обучения"""
    modules = []
    for block_id, block in config.MODULES.items():
        modules.append({
            "id": block_id,
            "title": block["title"],
            "description": block["description"],
            "estimated_time": "45 мин"
        })
    return jsonify({"success": True, "modules": modules})

@app.route('/api/modules/lessons', methods=['POST'])
def list_lessons():
    """Получение уроков конкретного модуля"""
    data = request.json or {}
    module_id = int(data.get("module_id", 1))
    
    block = lessons.BLOCKS.get(module_id)
    if not block:
        return jsonify({"success": False, "error": f"Block {module_id} not found"}), 404
        
    lessons_list = []
    for lesson_idx, lesson in block["lessons"].items():
        has_video = "video_url" in lesson or "https://youtu" in lesson.get("content", "")
        has_files = "pdf" in lesson.get("content", "").lower() or "excel" in lesson.get("content", "").lower()
        lessons_list.append({
            "id": f"{module_id}.{lesson_idx}",
            "title": lesson["title"],
            "duration": "20 мин",
            "has_video": has_video,
            "has_files": has_files
        })
    return jsonify({"success": True, "lessons": lessons_list})

@app.route('/api/lessons/content', methods=['POST'])
def get_lesson_content():
    """Получение контента урока с ИИ-рендерингом и ДЗ"""
    data = request.json or {}
    lesson_id = data.get("lesson_id", "1.1")
    
    try:
        block_id, lesson_idx = map(int, lesson_id.split('.'))
    except ValueError:
        return jsonify({"success": False, "error": "Invalid lesson_id format"}), 400
        
    block = lessons.BLOCKS.get(block_id)
    if not block:
        return jsonify({"success": False, "error": f"Block {block_id} not found"}), 404
        
    lesson = block["lessons"].get(lesson_idx)
    if not lesson:
        return jsonify({"success": False, "error": f"Lesson {lesson_idx} not found in Block {block_id}"}), 404
        
    # Преобразуем Markdown в HTML для отображения на фронтенде
    html_content = lessons.markdown_to_html(lesson["content"])
    
    # Парсим видео-ссылки (YouTube)
    video_url = ""
    urls = re.findall(r'(https?://[^\s<>"]+|www\.[^\s<>"]+)', lesson["content"])
    for u in urls:
        if any(p in u for p in ["youtube.com", "youtu.be", "kinescope.io", "vk.com"]):
            video_url = u
            break
            
    # Добавляем ссылки на файлы из контента
    files = []
    if "docs.google.com/document" in lesson["content"]:
        files.append({
            "name": "Методическое руководство.pdf",
            "type": "pdf",
            "url": "https://docs.google.com/document/d/e/2PACX-1vT30mP2xXpW4K12J43uL7293/pub"
        })
    if "docs.google.com/spreadsheets" in lesson["content"]:
        files.append({
            "name": "Шаблон финансового расчета.xlsx",
            "type": "xls",
            "url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT30mP2xXpW4K12J43uL7293/pub"
        })
        
    # Извлекаем домашнее задание, если оно есть
    assignment = None
    if "homework" in lesson:
        assignment = {
            "id": f"hw_{block_id}",
            "description": lesson["homework"]["content"],
            "type": lesson["homework"].get("type", "text")
        }
        
    return jsonify({
        "success": True,
        "lesson": {
            "id": lesson_id,
            "title": lesson["title"],
            "duration": "20 мин",
            "video_url": video_url,
            "text_content": html_content,
            "files": files,
            "assignment": assignment
        }
    })

async def async_submit_homework(user_id, block_number, text_content):
    """Асинхронная логика сохранения ДЗ и отправки куратору"""
    # 1. Сохраняем домашку в БД
    hw_id = await db.create_homework(user_id, block_number, "text", text_content)
    # 2. Обновляем статус студента в БД
    await db.update_user_status(user_id, "awaiting_review")
    # 3. Достаем данные студента
    user = await db.get_user(user_id)
    
    # 4. Отправляем куратору инлайн-карту для проверки
    bot = Bot(token=config.BOT_TOKEN)
    curator_builder = InlineKeyboardBuilder()
    curator_builder.button(text="✅ Одобрить", callback_data=f"approve_hw_{hw_id}")
    curator_builder.button(text="❌ Отклонить", callback_data=f"reject_hw_{hw_id}")
    curator_builder.adjust(2)
    
    caption_text = (
        f"🔔 <b>Новое ДЗ по Блоку {block_number} (сдано через TWA)!</b>\n\n"
        f"👤 <b>Студент:</b> {user['full_name']} (@{user['username'] or 'нет'})\n"
        f"📝 <b>Формат:</b> Текстовый ответ\n\n"
        f"<b>Ответ:</b>\n{text_content}"
    )
    
    # Защита от слишком длинного текста в Telegram
    if len(caption_text) > 4000:
        caption_text = caption_text[:3900] + "...\n[Текст обрезан]"
        
    await bot.send_message(
        chat_id=config.CURATOR_CHAT_ID,
        text=caption_text,
        reply_markup=curator_builder.as_markup(),
        parse_mode="HTML"
    )
    
    # Закрываем сессию aiogram бота
    session = await bot.get_session()
    if session:
        await session.close()
        
    return hw_id

@app.route('/api/assignments/submit', methods=['POST'])
def submit_assignment():
    """Сдача текстового домашнего задания из Web App"""
    data = request.json or {}
    user_id = data.get("user_id")
    block_number = int(data.get("block_number", 1))
    text_content = data.get("text_content", "").strip()
    
    if not user_id or not text_content:
        return jsonify({"success": False, "error": "user_id and text_content are required"}), 400
        
    try:
        run_async(async_submit_homework(user_id, block_number, text_content))
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error submitting assignment: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/user/stats', methods=['POST'])
def user_stats():
    """Получение статистики обучения для профиля"""
    data = request.json or {}
    user_id = int(data.get("user_id", 0))
    
    user = run_async(db.get_user(user_id))
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
        
    current_block = user["current_block"]
    status = user["status"]
    
    # Считаем пройденные модули и уроки
    modules_completed = current_block - 1
    if status == "completed":
        modules_completed = 6
        
    lessons_completed = modules_completed * 2
    if status == "awaiting_review":
        lessons_completed += 2
    elif current_block <= 6 and user["current_lesson"] == f"{current_block}.2":
        lessons_completed += 1
        
    study_hours = round((lessons_completed * 20) / 60, 1)
    assignments_completed = modules_completed
    
    stats = {
        "modules_completed": modules_completed,
        "lessons_completed": lessons_completed,
        "study_hours": study_hours,
        "assignments_completed": assignments_completed
    }
    
    # Достижения ученика
    achievements = [
        {"name": "Быстрый старт", "icon": "🚀", "unlocked": current_block > 1 or status == "completed"},
        {"name": "Финансовый гуру", "icon": "📊", "unlocked": current_block > 4 or status == "completed"},
        {"name": "Агент-Навигатор", "icon": "🏆", "unlocked": status == "completed"}
    ]
    
    return jsonify({
        "success": True,
        "stats": stats,
        "achievements": achievements
    })

if __name__ == '__main__':
    # Автоматическая инициализация БД перед стартом API
    run_async(db.init_db())
    
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Sreda 2.0 TWA API Server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
