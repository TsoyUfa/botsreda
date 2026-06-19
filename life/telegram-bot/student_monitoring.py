import aiosqlite
import json
from datetime import datetime
from typing import List, Dict, Any
from config import DB_PATH
from aiogram import F, types

# =======================
# ЛОГИРОВАНИЕ ОТВЕТОВ СТУДЕНТОВ
# =======================

async def init_student_responses_db():
    """Инициализация базы данных для хранения ответов студентов."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS student_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                module_id INTEGER,
                question_type TEXT,
                question TEXT,
                answer TEXT,
                is_correct BOOLEAN,
                score REAL,
                ai_feedback TEXT,
                voice_file_id TEXT,
                voice_duration INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Индекс для быстрого поиска
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_responses_user 
            ON student_responses(user_id, created_at)
        """)
        
        await db.commit()

async def log_text_response(
    user_id: int, 
    module_id: int, 
    question: str, 
    answer: str, 
    is_correct: bool = None,
    score: float = None,
    ai_feedback: str = None
):
    """Логирование текстового ответа студента."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO student_responses 
            (user_id, module_id, question_type, question, answer, is_correct, score, ai_feedback)
            VALUES (?, ?, 'free_text', ?, ?, ?, ?, ?)
        """, (user_id, module_id, question, answer, is_correct, score, ai_feedback))
        await db.commit()

async def log_choice_response(
    user_id: int, 
    module_id: int, 
    question: str, 
    answer: str, 
    is_correct: bool
):
    """Логирование ответа с выбором варианта."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO student_responses 
            (user_id, module_id, question_type, question, answer, is_correct)
            VALUES (?, ?, 'choice', ?, ?, ?)
        """, (user_id, module_id, question, answer, is_correct))
        await db.commit()

async def log_voice_response(
    user_id: int,
    module_id: int,
    question: str,
    voice_file_id: str,
    voice_duration: int,
    transcript: str = None
):
    """Логирование голосового ответа студента."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO student_responses 
            (user_id, module_id, question_type, question, answer, voice_file_id, voice_duration)
            VALUES (?, ?, 'voice', ?, ?, ?, ?, ?)
        """, (user_id, module_id, question, transcript or "", voice_file_id, voice_duration))
        await db.commit()

async def get_student_responses(user_id: int, limit: int = 50) -> List[Dict]:
    """Получить все ответы студента."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT * FROM student_responses 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        
        columns = [desc[0] for desc in cursor.description]
        rows = await cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]

async def get_recent_voice_messages(limit: int = 10) -> List[Dict]:
    """Получить последние голосовые сообщения."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT sr.*, u.first_name, u.username 
            FROM student_responses sr
            JOIN users u ON sr.user_id = u.user_id
            WHERE sr.question_type = 'voice'
            ORDER BY sr.created_at DESC 
            LIMIT ?
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        rows = await cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]

async def get_student_responses_export(user_id: int) -> str:
    """Получить все данные студента для экспорта в JSON."""
    responses = await get_student_responses(user_id, limit=1000)
    
    # Сгруппируем по модулям
    by_module = {}
    for response in responses:
        module_id = response['module_id']
        if module_id not in by_module:
            by_module[module_id] = []
        by_module[module_id].append(response)
    
    export_data = {
        'user_id': user_id,
        'export_date': datetime.now().isoformat(),
        'total_responses': len(responses),
        'responses_by_module': by_module,
        'voice_messages': [r for r in responses if r['question_type'] == 'voice'],
        'text_responses': [r for r in responses if r['question_type'] in ['free_text', 'choice']]
    }
    
    return json.dumps(export_data, ensure_ascii=False, indent=2)

# =======================
# ОБРАБОТЧИКИ ГОЛОСОВЫХ СООБЩЕНИЙ
# =======================

def register_voice_handlers(dp, bot):
    """Регистрация обработчиков голосовых сообщений."""
    
    @dp.message(F.voice)
    async def handle_voice_message(message: types.Message):
        """Обработка голосового сообщения."""
        user_id = message.from_user.id
        voice = message.voice
        
        # Скачиваем голосовое сообщение для обработки
        file_info = await bot.get_file(voice.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        
        # Здесь можно добавить распознавание речи
        # Пока просто логируем
        await log_voice_response(
            user_id=user_id,
            module_id=0,  # Голосовое сообщение не в рамках теста
            question="Голосовое сообщение",
            voice_file_id=voice.file_id,
            voice_duration=voice.duration,
            transcript=None  # Здесь будет распознанный текст
        )
        
        # Отправляем подтверждение
        await message.answer("🎙️ Ваше голосовое сообщение получено и сохранено!")

# =======================
# ИНИЦИАЛИЗАЦИЯ
# =======================

async def init_student_monitoring():
    """Инициализация системы мониторинга студентов."""
    await init_student_responses_db()
    print("✅ Система мониторинга ответов студентов инициализирована")
    print("🎙️ Теперь логируются:")
    print("  • Текстовые ответы на тесты")
    print("  • Ответы с выбором варианта")
    print("  • Голосовые сообщения")
    print("  • ИИ-оценка текстовых ответов")