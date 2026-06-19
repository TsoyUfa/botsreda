import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
from config import DB_PATH

# =======================
# ОБНОВЛЕНИЕ СУЩЕСТВУЮЩЕЙ БД
# =======================

async def update_existing_database():
    """Обновляет существующую базу данных до новой структуры."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()
        
        # Проверяем текущую структуру таблицы users
        await cursor.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"Текущие колонки users: {column_names}")
        
        # Добавляем недостающие колонки если их нет
        if 'last_activity' not in column_names:
            await cursor.execute("ALTER TABLE users ADD COLUMN last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✅ Добавлена колонка last_activity")
            
        if 'total_time_spent' not in column_names:
            await cursor.execute("ALTER TABLE users ADD COLUMN total_time_spent INTEGER DEFAULT 0")
            print("✅ Добавлена колонка total_time_spent")
            
        if 'total_sessions' not in column_names:
            await cursor.execute("ALTER TABLE users ADD COLUMN total_sessions INTEGER DEFAULT 0")
            print("✅ Добавлена колонка total_sessions")
            
        if 'last_name' not in column_names:
            await cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
            print("✅ Добавлена колонка last_name")
            
        if 'phone' not in column_names:
            await cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
            print("✅ Добавлена колонка phone")
            
        if 'email' not in column_names:
            await cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            print("✅ Добавлена колонка email")
            
        if 'agency' not in column_names:
            await cursor.execute("ALTER TABLE users ADD COLUMN agency TEXT")
            print("✅ Добавлена колонка agency")
            
        if 'experience_level' not in column_names:
            await cursor.execute("ALTER TABLE users ADD COLUMN experience_level TEXT DEFAULT 'beginner'")
            print("✅ Добавлена колонка experience_level")
            
        if 'is_active' not in column_names:
            await cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
            print("✅ Добавлена колонка is_active")
        
        # Переименовываем created_at в registration_date если нужно
        if 'created_at' in column_names and 'registration_date' not in column_names:
            await cursor.execute("ALTER TABLE users RENAME COLUMN created_at TO registration_date")
            print("✅ Переименована колонка created_at -> registration_date")
        
        # Удаляем колонку is_premium если она есть (больше не нужна)
        if 'is_premium' in column_names:
            # В SQLite нельзя удалить колонку, поэтому создаем новую таблицу
            await cursor.execute("""
                CREATE TABLE users_new (
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
                    total_time_spent INTEGER DEFAULT 0,
                    total_sessions INTEGER DEFAULT 0
                )
            """)
            
            # Копируем данные
            await cursor.execute("""
                INSERT INTO users_new (user_id, username, first_name, registration_date)
                SELECT user_id, username, first_name, created_at 
                FROM users
            """)
            
            # Удаляем старую таблицу и переименовываем новую
            await cursor.execute("DROP TABLE users")
            await cursor.execute("ALTER TABLE users_new RENAME TO users")
            print("✅ Таблица users перестроена без is_premium")
        
        await db.commit()
        print("✅ Структура таблицы users успешно обновлена!")
        
        # Теперь создаем индексы
        try:
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_activity ON users (last_activity)")
            print("✅ Создан индекс idx_users_activity")
        except Exception as e:
            print(f"⚠️ Индекс уже существует или ошибка: {e}")
        
        try:
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user_timestamp ON user_activity_log (user_id, timestamp)")
            print("✅ Создан индекс idx_activity_user_timestamp")
        except Exception as e:
            print(f"⚠️ Индекс уже существует или ошибка: {e}")
            
        try:
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_user_module ON user_progress (user_id, module_id)")
            print("✅ Создан индекс idx_progress_user_module")
        except Exception as e:
            print(f"⚠️ Индекс уже существует или ошибка: {e}")
            
        try:
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_quiz_user_module ON quiz_results (user_id, module_id)")
            print("✅ Создан индекс idx_quiz_user_module")
        except Exception as e:
            print(f"⚠️ Индекс уже существует или ошибка: {e}")
            
        try:
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON learning_sessions (user_id)")
            print("✅ Создан индекс idx_sessions_user")
        except Exception as e:
            print(f"⚠️ Индекс уже существует или ошибка: {e}")
            
        try:
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats (date)")
            print("✅ Создан индекс idx_daily_stats_date")
        except Exception as e:
            print(f"⚠️ Индекс уже существует или ошибка: {e}")
        
        await db.commit()
        print("✅ Все индексы созданы успешно!")

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
# ИНИЦИАЛИЗАЦИЯ
# =======================

async def init_analytics_db():
    """Инициализирует или обновляет базу данных с аналитикой."""
    await update_existing_database()
    print("✅ База данных аналитики успешно обновлена!")

# Тест при импорте
async def test_connection():
    try:
        await init_analytics_db()
        stats = await get_admin_dashboard()
        print("📊 Подключение к БД успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False