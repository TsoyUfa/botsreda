import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
from config import DB_PATH

# =======================
# УЛУЧШЕННАЯ БАЗА ДАННЫХ С АНАЛИТИКОЙ
# =======================

async def init_analytics_db():
    """Инициализирует расширенную базу данных с аналитикой."""
    async with aiosqlite.connect(DB_PATH) as db:
        
        # Основная таблица пользователей (расширенная)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                email TEXT,
                agency TEXT,
                experience_level TEXT DEFAULT 'beginner',
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                total_time_spent INTEGER DEFAULT 0,  -- в минутах
                total_sessions INTEGER DEFAULT 0
            )
        """)
        
        # Таблица прогресса (улучшенная)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                module_id INTEGER,
                lesson_started_at TIMESTAMP,
                lesson_completed_at TIMESTAMP,
                time_spent INTEGER DEFAULT 0,  # в секундах
                completion_percentage REAL DEFAULT 0.0,
                quiz_attempts INTEGER DEFAULT 0,
                best_score REAL DEFAULT 0.0,
                is_completed INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица логирования действий (ключевая для аналитики!)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT,  # 'start_lesson', 'complete_lesson', 'start_quiz', 'audio_listen', 'menu_click'
                action_details TEXT,  # JSON с деталями
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица результатов тестов (детальная)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                module_id INTEGER,
                question_id INTEGER,
                question_type TEXT,  # 'choice', 'free_text'
                user_answer TEXT,
                correct_answer TEXT,
                is_correct INTEGER,
                score REAL,
                time_spent INTEGER,  # в секундах
                attempt_number INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ai_evaluation TEXT,  # для текстовых ответов
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица сессий обучения
        await db.execute("""
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_end TIMESTAMP,
                duration INTEGER DEFAULT 0,  # в секундах
                modules_viewed INTEGER DEFAULT 0,
                lessons_completed INTEGER DEFAULT 0,
                quizzes_taken INTEGER DEFAULT 0,
                device_type TEXT DEFAULT 'telegram',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица статистики (агрегированные данные)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                total_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                new_registrations INTEGER DEFAULT 0,
                lessons_completed INTEGER DEFAULT 0,
                quizzes_passed INTEGER DEFAULT 0,
                avg_session_duration INTEGER DEFAULT 0,
                most_popular_module INTEGER
            )
        """)
        
        await db.commit()

# =======================
# ФУНКЦИИ ЛОГИРОВАНИЯ ДЕЙСТВИЙ
# =======================

async def log_user_action(user_id: int, action_type: str, details: Dict[str, Any] = None, session_id: str = None):
    """Логирует любое действие пользователя в системе."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_activity_log (user_id, action_type, action_details, session_id)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            action_type,
            json.dumps(details) if details else None,
            session_id
        ))
        
        # Обновляем время последней активности
        await db.execute("""
            UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?
        """, (user_id,))
        
        await db.commit()

async def log_lesson_start(user_id: int, module_id: int, session_id: str = None):
    """Логирует начало урока."""
    details = {
        'module_id': module_id,
        'module_title': get_module_title(module_id)
    }
    
    # Создаем или обновляем запись прогресса
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO user_progress 
            (user_id, module_id, lesson_started_at, completion_percentage)
            VALUES (?, ?, CURRENT_TIMESTAMP, 0.0)
        """, (user_id, module_id))
        await db.commit()
    
    await log_user_action(user_id, 'start_lesson', details, session_id)

async def log_lesson_complete(user_id: int, module_id: int, time_spent: int, session_id: str = None):
    """Логирует завершение урока."""
    details = {
        'module_id': module_id,
        'module_title': get_module_title(module_id),
        'time_spent': time_spent
    }
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE user_progress 
            SET lesson_completed_at = CURRENT_TIMESTAMP, time_spent = ?, completion_percentage = 100.0
            WHERE user_id = ? AND module_id = ?
        """, (time_spent, user_id, module_id))
        await db.commit()
    
    await log_user_action(user_id, 'complete_lesson', details, session_id)

async def log_quiz_attempt(user_id: int, module_id: int, question_data: Dict, result: Dict, session_id: str = None):
    """Логирует попытку ответа на вопрос теста."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO quiz_results 
            (user_id, module_id, question_id, question_type, user_answer, correct_answer, 
             is_correct, score, time_spent, attempt_number, ai_evaluation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            module_id,
            question_data.get('question_id'),
            question_data.get('type'),
            result.get('user_answer'),
            question_data.get('correct_answer'),
            result.get('is_correct', False),
            result.get('score', 0.0),
            result.get('time_spent', 0),
            result.get('attempt_number', 1),
            result.get('ai_evaluation')
        ))
        
        # Увеличиваем счетчик попыток
        await db.execute("""
            UPDATE user_progress SET quiz_attempts = quiz_attempts + 1 
            WHERE user_id = ? AND module_id = ?
        """, (user_id, module_id))
        
        await db.commit()
    
    details = {
        'module_id': module_id,
        'question_id': question_data.get('question_id'),
        'is_correct': result.get('is_correct', False),
        'score': result.get('score', 0.0)
    }
    
    await log_user_action(user_id, 'quiz_attempt', details, session_id)

async def start_learning_session(user_id: int, device_type: str = 'telegram'):
    """Начинает новую сессию обучения."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO learning_sessions (user_id, session_start, device_type)
            VALUES (CURRENT_TIMESTAMP, ?, ?)
        """, (user_id, device_type))
        
        session_id = f"session_{cursor.lastrowid}_{user_id}"
        
        # Логируем начало сессии
        await log_user_action(user_id, 'session_start', {'device_type': device_type}, session_id)
        
        await db.commit()
        return session_id

async def end_learning_session(session_id: str, user_id: int, duration: int = None):
    """Завершает сессию обучения."""
    async with aiosqlite.connect(DB_PATH) as db:
        if duration:
            await db.execute("""
                UPDATE learning_sessions 
                SET session_end = CURRENT_TIMESTAMP, duration = ?
                WHERE session_id = ? AND user_id = ?
            """, (duration, session_id, user_id))
        else:
            await db.execute("""
                UPDATE learning_sessions 
                SET session_end = CURRENT_TIMESTAMP
                WHERE session_id = ? AND user_id = ?
            """, (session_id, user_id))
        
        await db.commit()

# =======================
# ФУНКЦИИ АНАЛИТИКИ И СТАТИСТИКИ
# =======================

async def get_user_analytics(user_id: int) -> Dict[str, Any]:
    """Получает полную аналитику по пользователю."""
    async with aiosqlite.connect(DB_PATH) as db:
        
        # Базовая информация о пользователе
        user = await db.execute("""
            SELECT * FROM users WHERE user_id = ?
        """, (user_id,))
        user_data = await user.fetchone()
        
        if not user_data:
            return {}
        
        # Прогресс по модулям
        progress = await db.execute("""
            SELECT module_id, lesson_started_at, lesson_completed_at, time_spent, 
                   completion_percentage, quiz_attempts, best_score, is_completed
            FROM user_progress WHERE user_id = ?
        """, (user_id,))
        progress_data = await progress.fetchall()
        
        # Статистика по тестам
        quiz_stats = await db.execute("""
            SELECT COUNT(*) as total_attempts, 
                   AVG(score) as avg_score, 
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers,
                   COUNT(DISTINCT module_id) as modules_tested
            FROM quiz_results WHERE user_id = ?
        """, (user_id,))
        quiz_data = await quiz_stats.fetchone()
        
        # Активность за последние 7 дней
        week_activity = await db.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as actions
            FROM user_activity_log 
            WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (user_id,))
        week_data = await week_activity.fetchall()
        
        # Общее время в системе
        total_time = await db.execute("""
            SELECT SUM(duration) as total_time
            FROM learning_sessions 
            WHERE user_id = ? AND duration IS NOT NULL
        """, (user_id,))
        time_data = await total_time.fetchone()
        
        return {
            'user_info': {
                'user_id': user_data[0],
                'username': user_data[1],
                'first_name': user_data[2],
                'registration_date': user_data[6],
                'last_activity': user_data[7],
                'total_sessions': user_data[10]
            },
            'progress': [
                {
                    'module_id': row[0],
                    'started': row[1],
                    'completed': row[2],
                    'time_spent': row[3],
                    'completion': row[4],
                    'quiz_attempts': row[5],
                    'best_score': row[6],
                    'is_completed': row[7]
                } for row in progress_data
            ],
            'quiz_stats': {
                'total_attempts': quiz_data[0] or 0,
                'avg_score': round(quiz_data[1] or 0, 2),
                'correct_answers': quiz_data[2] or 0,
                'modules_tested': quiz_data[3] or 0
            },
            'weekly_activity': [
                {'date': row[0], 'actions': row[1]} for row in week_data
            ],
            'total_learning_time': time_data[0] or 0
        }

async def get_admin_dashboard() -> Dict[str, Any]:
    """Получает данные для админ-панели."""
    async with aiosqlite.connect(DB_PATH) as db:
        
        # Общая статистика
        total_users = await db.execute("SELECT COUNT(*) FROM users")
        active_users = await db.execute("""
            SELECT COUNT(*) FROM users 
            WHERE last_activity >= datetime('now', '-7 days')
        """)
        new_users = await db.execute("""
            SELECT COUNT(*) FROM users 
            WHERE registration_date >= datetime('now', '-30 days')
        """)
        
        # Статистика по обучению
        completed_lessons = await db.execute("""
            SELECT COUNT(*) FROM user_progress WHERE is_completed = 1
        """)
        passed_quizzes = await db.execute("""
            SELECT COUNT(DISTINCT user_id) FROM user_progress 
            WHERE is_completed = 1 AND best_score >= 0.8
        """)
        
        # Популярные модули
        popular_modules = await db.execute("""
            SELECT module_id, COUNT(*) as views
            FROM user_activity_log 
            WHERE action_type = 'start_lesson'
            GROUP BY module_id
            ORDER BY views DESC
            LIMIT 5
        """)
        
        # Активные сессии сегодня
        today_sessions = await db.execute("""
            SELECT COUNT(*) FROM learning_sessions 
            WHERE DATE(session_start) = DATE('now')
        """)
        
        return {
            'total_users': (await total_users.fetchone())[0],
            'active_users': (await active_users.fetchone())[0],
            'new_users_30d': (await new_users.fetchone())[0],
            'completed_lessons': (await completed_lessons.fetchone())[0],
            'certified_agents': (await passed_quizzes.fetchone())[0],
            'today_sessions': (await today_sessions.fetchone())[0],
            'popular_modules': [
                {'module_id': row[0], 'views': row[1]} for row in await popular_modules.fetchall()
            ]
        }

# =======================
# ЭКСПОРТ ДАННЫХ
# =======================

async def export_user_data(user_id: int) -> str:
    """Экспортирует все данные пользователя в JSON."""
    analytics = await get_user_analytics(user_id)
    return json.dumps(analytics, indent=2, ensure_ascii=False, default=str)

async def export_daily_report(date: str = None) -> str:
    """Экспортирует ежедневный отчет."""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    async with aiosqlite.connect(DB_PATH) as db:
        report = await db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM users WHERE DATE(registration_date) = ?) as new_users,
                (SELECT COUNT(*) FROM user_activity_log WHERE DATE(timestamp) = ?) as total_actions,
                (SELECT COUNT(*) FROM user_progress WHERE DATE(lesson_completed_at) = ?) as completed_lessons,
                (SELECT AVG(score) FROM quiz_results WHERE DATE(timestamp) = ?) as avg_quiz_score
        """, (date, date, date, date))
        
        data = await report.fetchone()
        
        return {
            'date': date,
            'new_users': data[0] or 0,
            'total_actions': data[1] or 0,
            'completed_lessons': data[2] or 0,
            'avg_quiz_score': round(data[3] or 0, 2)
        }

# Вспомогательные функции
def get_module_title(module_id: int) -> str:
    """Возвращает название модуля по ID."""
    titles = {
        1: "Блок 1. Роль Навигатора и Золотое Правило",
        2: "Блок 2. JTBD-Диагностика и Боли Клиента",
        3: "Блок 3. Финмоделирование и TCO за 5 лет",
        4: "Блок 4. Анализ застройщиков",
        5: "Блок 5. Стандарты показов",
        6: "Блок 6. Скрипты продаж",
        7: "Блок 7. Юридическая безопасность"
    }
    return titles.get(module_id, f"Блок {module_id}")