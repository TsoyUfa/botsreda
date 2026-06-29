import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bot.db")

def init_db():
    """Инициализация базы данных и создание таблиц, если они не существуют."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица пользователей (агентов)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            is_subscribed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица скачиваний лид-магнитов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            keyword TEXT,
            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # Таблица результатов тестов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            user_id INTEGER PRIMARY KEY,
            score INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # Таблица очереди автодогрева (drip-кампании)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drip_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message_type TEXT,
            send_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # Таблица B2C лидов из калькулятора
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            goal TEXT,
            dp TEXT,
            comfort_payment TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def add_user(user_id: int, username: str, full_name: str):
    """Добавление нового пользователя или обновление существующего."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, username, full_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name
    """, (user_id, username, full_name))
    conn.commit()
    conn.close()

def update_subscription(user_id: int, is_subscribed: bool):
    """Обновление статуса подписки на Telegram-канал."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET is_subscribed = ? WHERE user_id = ?
    """, (1 if is_subscribed else 0, user_id))
    conn.commit()
    conn.close()

def add_download(user_id: int, keyword: str):
    """Логирование скачивания лид-магнита."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO downloads (user_id, keyword)
        VALUES (?, ?)
    """, (user_id, keyword.upper()))
    conn.commit()
    conn.close()

def save_quiz_result(user_id: int, score: int):
    """Сохранение результатов тестирования."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quiz_results (user_id, score, completed_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            score = excluded.score,
            completed_at = CURRENT_TIMESTAMP
    """, (user_id, score))
    conn.commit()
    conn.close()

def schedule_drip(user_id: int, message_type: str, send_at: datetime):
    """Планирование отправки автодогрева в drip-очередь."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Проверим, нет ли уже запланированного догрева этого типа для пользователя
    cursor.execute("""
        SELECT id FROM drip_schedule 
        WHERE user_id = ? AND message_type = ? AND status = 'pending'
    """, (user_id, message_type))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute("""
            INSERT INTO drip_schedule (user_id, message_type, send_at)
            VALUES (?, ?, ?)
        """, (user_id, message_type, send_at.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    conn.close()

def get_pending_drips():
    """Получение всех запланированных к отправке сообщений, время которых пришло."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        SELECT id, user_id, message_type FROM drip_schedule
        WHERE status = 'pending' AND send_at <= ?
    """, (now_str,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_drip_status(drip_id: int, status: str):
    """Обновление статуса drip-сообщения (sent, failed, cancelled)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE drip_schedule SET status = ? WHERE id = ?
    """, (status, drip_id))
    conn.commit()
    conn.close()

def cancel_pending_drips(user_id: int, message_type: str):
    """Отмена запланированных drip-сообщений определенного типа для пользователя."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE drip_schedule SET status = 'cancelled'
        WHERE user_id = ? AND message_type = ? AND status = 'pending'
    """, (user_id, message_type))
    conn.commit()
    conn.close()

def get_all_users_for_broadcast(segment: str = "all"):
    """Получение списка ID пользователей для рассылки."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if segment == "all":
        cursor.execute("SELECT user_id FROM users")
    elif segment == "quiz_completed":
        cursor.execute("SELECT user_id FROM quiz_results")
    elif segment == "quiz_pending":
        cursor.execute("SELECT user_id FROM users WHERE user_id NOT IN (SELECT user_id FROM quiz_results)")
    else:
        cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_leads_csv_data():
    """Сбор подробных данных об агентах для CSV выгрузки."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Собираем данные: ID, юзернейм, имя, подписка на канал, балл за тест, дата регистрации
    cursor.execute("""
        SELECT u.user_id, u.username, u.full_name, u.is_subscribed, qr.score, u.created_at
        FROM users u
        LEFT JOIN quiz_results qr ON u.user_id = qr.user_id
        ORDER BY u.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_stats():
    """Сбор статистики по использованию бота."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Всего пользователей
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Прошли тест
    cursor.execute("SELECT COUNT(*), AVG(score) FROM quiz_results")
    quiz_row = cursor.fetchone()
    total_quizzes = quiz_row[0]
    avg_score = round(quiz_row[1], 2) if quiz_row[1] is not None else 0.0
    
    # Скачивания по кодовым словам
    cursor.execute("SELECT keyword, COUNT(*) FROM downloads GROUP BY keyword ORDER BY COUNT(*) DESC")
    downloads_by_keyword = cursor.fetchall()
    
    conn.close()
    
    return {
        "total_users": total_users,
        "total_quizzes": total_quizzes,
        "avg_score": avg_score,
        "downloads_by_keyword": downloads_by_keyword
    }

def add_lead(user_id: int, username: str, full_name: str, goal: str, dp: str, comfort_payment: str, phone: str):
    """Сохранение B2C лида из калькулятора."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leads (user_id, username, full_name, goal, dp, comfort_payment, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, full_name, goal, dp, comfort_payment, phone))
    conn.commit()
    conn.close()

def get_b2c_leads_csv_data():
    """Сбор подробных данных о B2C лидах для CSV выгрузки."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, username, full_name, goal, dp, comfort_payment, phone, created_at
        FROM leads
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows
