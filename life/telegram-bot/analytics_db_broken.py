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
                started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed TIMESTAMP NULL,
                is_completed INTEGER DEFAULT 0,
                best_score REAL DEFAULT 0.0,
                attempts_count INTEGER DEFAULT 0,
                time_spent INTEGER DEFAULT 0,  -- в секундах
                last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE (user_id, module_id)
            )
        """)
        
        # Таблица логирования действий (ключевая для аналитики!)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT,  -- 'start_lesson', 'complete_quiz', 'view_audio', etc.
                module_id INTEGER NULL,
                session_id TEXT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,  -- JSON с дополнительными данными
                ip_address TEXT NULL,
                device_info TEXT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Таблица результатов тестов (детальная)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                module_id INTEGER,
                attempt_number INTEGER DEFAULT 1,
                score REAL DEFAULT 0.0,
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                time_spent INTEGER,  -- в секундах
                answers_data TEXT,  -- JSON с ответами
                ai_evaluation TEXT,  -- для текстовых ответов
                passed INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Таблица сессий обучения
        await db.execute("""
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id TEXT UNIQUE,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP NULL,
                duration INTEGER DEFAULT 0,  -- в секундах
                activities_count INTEGER DEFAULT 0,
                modules_accessed INTEGER DEFAULT 0,
                quizzes_completed INTEGER DEFAULT 0,
                device_type TEXT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Таблица статистики (агрегированные данные)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                total_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                total_sessions INTEGER DEFAULT 0,
                lessons_started INTEGER DEFAULT 0,
                lessons_completed INTEGER DEFAULT 0,
                quizzes_completed INTEGER DEFAULT 0,
                avg_session_duration REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем индексы для быстрого поиска
        await db.execute("CREATE INDEX IF NOT EXISTS idx_users_activity ON users (last_activity)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_activity_user_timestamp ON user_activity_log (user_id, timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_progress_user_module ON user_progress (user_id, module_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_quiz_user_module ON quiz_results (user_id, module_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON learning_sessions (user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats (date)")
        
        await db.commit()
        print("✅ База данных аналитики успешно инициализирована!")

# =======================
# ФУНКЦИИ ЛОГИРОВАНИЯ ДЕЙСТВИЙ
# =======================

async def log_user_action(user_id: int, action_type: str, details: Dict = None):
    """Логирует действие пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Обновляем время последней активности
        await db.execute("""
            UPDATE users 
            SET last_activity = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        """, (user_id,))
        
        # Логируем действие
        await db.execute("""
            INSERT INTO user_activity_log (user_id, action_type, details)
            VALUES (?, ?, ?)
        """, (user_id, action_type, json.dumps(details or {})))
        
        await db.commit()

async def log_lesson_start(user_id: int, module_id: int, session_id: str = None):
    """Логирует начало урока."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Создаем или обновляем запись прогресса
        await db.execute("""
            INSERT INTO user_progress (user_id, module_id, started)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, module_id) 
            DO UPDATE SET started = COALESCE(started, CURRENT_TIMESTAMP)
        """, (user_id, module_id))
        
        # Логируем действие
        await db.execute("""
            INSERT INTO user_activity_log (user_id, action_type, module_id, session_id, details)
            VALUES (?, 'start_lesson', ?, ?, ?)
        """, (user_id, module_id, session_id, json.dumps({'module_id': module_id})))
        
        await db.commit()

async def log_lesson_complete(user_id: int, module_id: int, score: float, time_spent: int = 0):
    """Логирует завершение урока."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Обновляем прогресс
        await db.execute("""
            UPDATE user_progress 
            SET is_completed = 1, 
                completed = CURRENT_TIMESTAMP,
                best_score = MAX(best_score, ?),
                attempts_count = attempts_count + 1,
                time_spent = time_spent + COALESCE(time_spent, 0),
                last_attempt = CURRENT_TIMESTAMP
            WHERE user_id = ? AND module_id = ?
        """, (score, user_id, module_id))
        
        # Логируем завершение
        await db.execute("""
            INSERT INTO user_activity_log (user_id, action_type, module_id, details)
            VALUES (?, 'complete_lesson', ?, ?)
        """, (user_id, module_id, json.dumps({
            'module_id': module_id,
            'score': score,
            'time_spent': time_spent
        })))
        
        await db.commit()

async def log_quiz_result(user_id: int, module_id: int, score: float, total_questions: int, 
                         correct_answers: int, time_spent: int = 0, attempt_number: int = 1):
    """Логирует результат теста."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Увеличиваем счетчик попыток
        await db.execute("""
            UPDATE user_progress 
            SET attempts_count = attempts_count + 1,
                best_score = MAX(best_score, ?),
                last_attempt = CURRENT_TIMESTAMP
            WHERE user_id = ? AND module_id = ?
        """, (score, user_id, module_id))
        
        # Сохраняем результат теста
        passed = 1 if score >= 0.8 else 0  # 80% - проходной балл
        await db.execute("""
            INSERT INTO quiz_results 
            (user_id, module_id, attempt_number, score, total_questions, correct_answers, time_spent, passed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, module_id, attempt_number, score, total_questions, correct_answers, time_spent, passed))
        
        # Логируем действие
        await db.execute("""
            INSERT INTO user_activity_log (user_id, action_type, module_id, details)
            VALUES (?, 'complete_quiz', ?, ?)
        """, (user_id, module_id, json.dumps({
            'module_id': module_id,
            'score': score,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'passed': passed
        })))
        
        await db.commit()

async def start_learning_session(user_id: int, session_id: str, device_type: str = None):
    """Начинает новую учебную сессию."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Логируем начало сессии
        await db.execute("""
            INSERT INTO learning_sessions (user_id, session_id, device_type)
            VALUES (?, ?, ?)
        """, (user_id, session_id, device_type))
        
        # Обновляем счетчик сессий пользователя
        await db.execute("""
            UPDATE users 
            SET total_sessions = total_sessions + 1
            WHERE user_id = ?
        """, (user_id,))
        
        await db.commit()

# =======================
# ФУНКЦИИ АНАЛИТИКИ И СТАТИСТИКИ
# =======================

async def get_user_analytics(user_id: int) -> Dict[str, Any]:
    """Получает полную аналитику по пользователю."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()
        
        # Базовая информация о пользователе
        await cursor.execute("""
            SELECT user_id, username, first_name, registration_date, last_activity, total_sessions
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        user_info = await cursor.fetchone()
        
        if not user_info:
            return None
            
        user_info = {
            'user_id': user_info[0],
            'username': user_info[1],
            'first_name': user_info[2],
            'registration_date': user_info[3],
            'last_activity': user_info[4],
            'total_sessions': user_info[5]
        }
        
        # Прогресс по модулям
        await cursor.execute("""
            SELECT module_id, started, completed, is_completed, best_score, attempts_count, time_spent
            FROM user_progress 
            WHERE user_id = ?
            ORDER BY module_id
        """, (user_id,))
        progress_rows = await cursor.fetchall()
        
        progress = []
        for row in progress_rows:
            progress.append({
                'module_id': row[0],
                'started': row[1],
                'completed': row[2],
                'is_completed': bool(row[3]),
                'best_score': row[4],
                'attempts_count': row[5],
                'time_spent': row[6]
            })
        
        # Статистика по тестам
        await cursor.execute("""
            SELECT COUNT(*) as total_attempts, 
                   AVG(score) as avg_score,
                   SUM(correct_answers) as correct_answers,
                   COUNT(DISTINCT module_id) as modules_tested
            FROM quiz_results 
            WHERE user_id = ?
        """, (user_id,))
        quiz_stats = await cursor.fetchone()
        
        quiz_stats = {
            'total_attempts': quiz_stats[0] or 0,
            'avg_score': round((quiz_stats[1] or 0) * 100, 1),
            'correct_answers': quiz_stats[2] or 0,
            'modules_tested': quiz_stats[3] or 0
        }
        
        # Активность за последние 7 дней
        await cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as actions
            FROM user_activity_log 
            WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (user_id,))
        weekly_activity = await cursor.fetchall()
        
        weekly_activity = [
            {'date': row[0], 'actions': row[1]} 
            for row in weekly_activity
        ]
        
        # Общее время в системе
        await cursor.execute("""
            SELECT SUM(time_spent) 
            FROM user_progress 
            WHERE user_id = ?
        """, (user_id,))
        total_time_result = await cursor.fetchone()
        total_learning_time = total_time_result[0] or 0
        
        return {
            'user_info': user_info,
            'progress': progress,
            'quiz_stats': quiz_stats,
            'weekly_activity': weekly_activity,
            'total_learning_time': total_learning_time
        }

async def get_admin_dashboard() -> Dict[str, Any]:
    """Получает статистику для админ-панели."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()
        
        # Общая статистика
        await cursor.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        await cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE last_activity >= datetime('now', '-7 days')
        """)
        active_users = (await cursor.fetchone())[0]
        
        await cursor.execute("""
            SELECT COUNT(*) FROM user_progress 
            WHERE is_completed = 1
        """)
        completed_lessons = (await cursor.fetchone())[0]
        
        await cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM user_progress 
            WHERE is_completed = 1
        """)
        certified_agents = (await cursor.fetchone())[0]
        
        await cursor.execute("""
            SELECT COUNT(*) FROM learning_sessions 
            WHERE DATE(start_time) = DATE('now')
        """)
        today_sessions = (await cursor.fetchone())[0]
        
        # Новые пользователи за 30 дней
        await cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE registration_date >= datetime('now', '-30 days')
        """)
        new_users_30d = (await cursor.fetchone())[0]
        
        # Популярные модули
        await cursor.execute("""
            SELECT module_id, COUNT(*) as views
            FROM user_activity_log 
            WHERE action_type = 'start_lesson'
            GROUP BY module_id
            ORDER BY views DESC
            LIMIT 7
        """)
        popular_modules = await cursor.fetchall()
        
        popular_modules = [
            {'module_id': row[0], 'views': row[1]} 
            for row in popular_modules
        ]
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'completed_lessons': completed_lessons,
            'certified_agents': certified_agents,
            'today_sessions': today_sessions,
            'new_users_30d': new_users_30d,
            'popular_modules': popular_modules
        }

# =======================
# ЭКСПОРТ ДАННЫХ
# =======================

async def export_user_data(format_type: str = 'json') -> str:
    """Экспортирует данные пользователей."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()
        
        # Получаем всех пользователей с их прогрессом
        await cursor.execute("""
            SELECT u.user_id, u.username, u.first_name, u.registration_date, u.last_activity,
                   up.module_id, up.is_completed, up.best_score, up.time_spent
            FROM users u
            LEFT JOIN user_progress up ON u.user_id = up.user_id
            ORDER BY u.last_activity DESC
        """)
        data = await cursor.fetchall()
        
        if format_type == 'json':
            # Группируем данные по пользователям
            users_data = {}
            for row in data:
                user_id = row[0]
                if user_id not in users_data:
                    users_data[user_id] = {
                        'user_id': user_id,
                        'username': row[1],
                        'first_name': row[2],
                        'registration_date': row[3],
                        'last_activity': row[4],
                        'progress': []
                    }
                
                if row[5]:  # Если есть данные по прогрессу
                    users_data[user_id]['progress'].append({
                        'module_id': row[5],
                        'is_completed': bool(row[6]),
                        'best_score': row[7],
                        'time_spent': row[8]
                    })
            
            return json.dumps(list(users_data.values()), indent=2, default=str)
        
        elif format_type == 'csv':
            # Формируем CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Заголовки
            writer.writerow([
                'User ID', 'Username', 'First Name', 'Registration Date', 'Last Activity',
                'Module ID', 'Completed', 'Best Score', 'Time Spent'
            ])
            
            # Данные
            for row in data:
                writer.writerow(row)
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")

# =======================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =======================

async def update_daily_stats():
    """Обновляет ежедневную статистику."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()
        
        today = datetime.now().date()
        
        # Считаем статистику за сегодня
        await cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM users WHERE last_activity >= datetime('now', '-1 day')) as active_users,
                (SELECT COUNT(*) FROM users WHERE DATE(registration_date) = ?) as new_users,
                (SELECT COUNT(*) FROM learning_sessions WHERE DATE(start_time) = ?) as total_sessions,
                (SELECT COUNT(*) FROM user_activity_log WHERE DATE(timestamp) = ? AND action_type = 'start_lesson') as lessons_started,
                (SELECT COUNT(*) FROM user_activity_log WHERE DATE(timestamp) = ? AND action_type = 'complete_lesson') as lessons_completed,
                (SELECT COUNT(*) FROM user_activity_log WHERE DATE(timestamp) = ? AND action_type = 'complete_quiz') as quizzes_completed,
                (SELECT AVG(duration) FROM learning_sessions WHERE DATE(start_time) = ? AND duration > 0) as avg_session_duration
        """, (today, today, today, today, today, today))
        
        stats = await cursor.fetchone()
        
        # Вставляем или обновляем запись
        await cursor.execute("""
            INSERT OR REPLACE INTO daily_stats 
            (date, total_users, active_users, new_users, total_sessions, 
             lessons_started, lessons_completed, quizzes_completed, avg_session_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (today, *stats))
        
        await db.commit()

# Инициализация при импорте
async def ensure_analytics_db():
    """Убеждается, что база данных аналитики создана."""
    try:
        await init_analytics_db()
    except Exception as e:
        print(f"Ошибка при инициализации БД аналитики: {e}")