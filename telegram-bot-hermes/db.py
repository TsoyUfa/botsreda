"""Модуль работы с базой данных SQLite через aiosqlite для бота Тони Павлович."""
import os
import aiosqlite
from datetime import datetime
import logging

logger = logging.getLogger("HermesBot.db")

DB_FILE = "/Users/anton_tsoy/Desktop/Обсидиан/anton_pavlovich.db"

async def init_db():
    """Инициализация таблиц базы данных."""
    async with aiosqlite.connect(DB_FILE) as db:
        # 1. Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                timezone TEXT DEFAULT 'Asia/Yekaterinburg',
                role TEXT DEFAULT 'user', -- 'user' или 'admin'
                status TEXT DEFAULT 'active', -- 'active' или 'blocked'
                last_morning_brief TEXT, -- YYYY-MM-DD
                last_evening_prompt TEXT, -- YYYY-MM-DD
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Таблица планирования и рефлексии (вместо старой daily_records)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT, -- YYYY-MM-DD
                morning_plan TEXT,
                evening_reflection TEXT,
                insights TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, date)
            )
        """)

        # 3. Таблица клиентов CRM
        await db.execute("""
            CREATE TABLE IF NOT EXISTS crm_clients (
                client_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                client_name TEXT NOT NULL,
                phone TEXT,
                status TEXT DEFAULT 'in_work', -- 'in_work', 'deal', 'archive'
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        # 4. Таблица задач CRM и напоминаний
        await db.execute("""
            CREATE TABLE IF NOT EXISTS crm_tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                client_id INTEGER,
                task_text TEXT NOT NULL,
                due_date TEXT, -- YYYY-MM-DD HH:MM
                is_completed INTEGER DEFAULT 0, -- 0 или 1
                reminded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (client_id) REFERENCES crm_clients (client_id)
            )
        """)

        # 5. Таблица заметок пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_notes (
                note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                note_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        await db.commit()
        logger.info(f"База данных успешно инициализирована: {DB_FILE}")

# ==========================================
# ПОЛЬЗОВАТЕЛИ
# ==========================================

async def add_user(user_id: int, username: str, full_name: str, timezone: str = 'Asia/Yekaterinburg', role: str = 'user'):
    """Добавление или обновление пользователя."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name, timezone, role)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                timezone = excluded.timezone,
                role = excluded.role
        """, (user_id, username, full_name, timezone, role))
        await db.commit()

async def get_user(user_id: int):
    """Получение пользователя по Telegram ID."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id, username, full_name, timezone, role, status FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "username": row[1],
                    "full_name": row[2],
                    "timezone": row[3],
                    "role": row[4],
                    "status": row[5]
                }
            return None

async def get_all_users():
    """Получение списка всех пользователей."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id, username, full_name, timezone, role, status FROM users") as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "user_id": r[0],
                    "username": r[1],
                    "full_name": r[2],
                    "timezone": r[3],
                    "role": r[4],
                    "status": r[5]
                }
                for r in rows
            ]

# ==========================================
# ПЛАНИРОВАНИЕ И РЕФЛЕКСИЯ
# ==========================================

async def save_morning_plan(user_id: int, date_str: str, plan_text: str):
    """Сохранение или обновление утреннего плана."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT INTO daily_logs (user_id, date, morning_plan)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET morning_plan = excluded.morning_plan
        """, (user_id, date_str, plan_text))
        await db.commit()

async def save_evening_reflection(user_id: int, date_str: str, reflection_text: str, insights: str = None):
    """Сохранение или обновление вечерней рефлексии."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT INTO daily_logs (user_id, date, evening_reflection, insights)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET 
                evening_reflection = excluded.evening_reflection,
                insights = COALESCE(excluded.insights, daily_logs.insights)
        """, (user_id, date_str, reflection_text, insights))
        await db.commit()

async def get_daily_log(user_id: int, date_str: str):
    """Получение записи лога за конкретную дату."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT morning_plan, evening_reflection, insights 
            FROM daily_logs 
            WHERE user_id = ? AND date = ?
        """, (user_id, date_str)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "morning_plan": row[0] or "",
                    "evening_reflection": row[1] or "",
                    "insights": row[2] or ""
                }
            return None

async def get_recent_logs(user_id: int, limit: int = 7):
    """Получение последних N логов пользователя для сводок."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT date, morning_plan, evening_reflection, insights 
            FROM daily_logs 
            WHERE user_id = ? AND (morning_plan IS NOT NULL OR evening_reflection IS NOT NULL)
            ORDER BY date DESC 
            LIMIT ?
        """, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "date": r[0],
                    "morning_plan": r[1] or "",
                    "evening_reflection": r[2] or "",
                    "insights": r[3] or ""
                }
                for r in rows
            ]

# ==========================================
# CRM КЛИЕНТЫ
# ==========================================

async def add_crm_client(user_id: int, client_name: str, phone: str = None, status: str = 'in_work', details: str = None):
    """Добавление нового клиента."""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            INSERT INTO crm_clients (user_id, client_name, phone, status, details)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, client_name, phone, status, details))
        client_id = cursor.lastrowid
        await db.commit()
        return client_id

async def get_crm_clients(user_id: int):
    """Получение списка всех клиентов пользователя."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT client_id, client_name, phone, status, details 
            FROM crm_clients 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "client_id": r[0],
                    "client_name": r[1],
                    "phone": r[2] or "",
                    "status": r[3],
                    "details": r[4] or ""
                }
                for r in rows
            ]

async def update_crm_client(client_id: int, status: str = None, details: str = None):
    """Обновление статуса и деталей клиента."""
    async with aiosqlite.connect(DB_FILE) as db:
        if status and details:
            await db.execute("UPDATE crm_clients SET status = ?, details = ? WHERE client_id = ?", (status, details, client_id))
        elif status:
            await db.execute("UPDATE crm_clients SET status = ? WHERE client_id = ?", (status, client_id))
        elif details:
            await db.execute("UPDATE crm_clients SET details = ? WHERE client_id = ?", (details, client_id))
        await db.commit()

async def find_crm_client_by_name(user_id: int, name: str):
    """Поиск клиента по имени (нечувствительный к регистру поиск подстроки)."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT client_id, client_name 
            FROM crm_clients 
            WHERE user_id = ? AND client_name LIKE ?
            LIMIT 1
        """, (user_id, f"%{name}%")) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"client_id": row[0], "client_name": row[1]}
            return None

# ==========================================
# CRM ЗАДАЧИ
# ==========================================

async def add_crm_task(user_id: int, client_id: int, task_text: str, due_date: str = None):
    """Добавление новой задачи."""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("""
            INSERT INTO crm_tasks (user_id, client_id, task_text, due_date)
            VALUES (?, ?, ?, ?)
        """, (user_id, client_id, task_text, due_date))
        task_id = cursor.lastrowid
        await db.commit()
        return task_id

async def get_pending_tasks(user_id: int):
    """Получение невыполненных задач пользователя."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT t.task_id, t.task_text, t.due_date, c.client_name, c.client_id
            FROM crm_tasks t
            LEFT JOIN crm_clients c ON t.client_id = c.client_id
            WHERE t.user_id = ? AND t.is_completed = 0
            ORDER BY t.due_date ASC, t.created_at DESC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "task_id": r[0],
                    "task_text": r[1],
                    "due_date": r[2] or "",
                    "client_name": r[3] or "Без клиента",
                    "client_id": r[4]
                }
                for r in rows
            ]

async def complete_task(task_id: int):
    """Отметка задачи как выполненной."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE crm_tasks SET is_completed = 1 WHERE task_id = ?", (task_id,))
        await db.commit()

async def get_all_pending_tasks_for_reminders():
    """Получение всех невыполненных задач с датой напоминания для фонового планировщика."""
    async with aiosqlite.connect(DB_FILE) as db:
        # Выбираем задачи, где срок не пуст, задача не выполнена и еще не было напоминания (reminded_at IS NULL)
        async with db.execute("""
            SELECT t.task_id, t.user_id, t.task_text, t.due_date, c.client_name, u.timezone
            FROM crm_tasks t
            LEFT JOIN crm_clients c ON t.client_id = c.client_id
            LEFT JOIN users u ON t.user_id = u.user_id
            WHERE t.is_completed = 0 AND t.due_date IS NOT NULL AND t.due_date != '' AND t.reminded_at IS NULL
        """) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "task_id": r[0],
                    "user_id": r[1],
                    "task_text": r[2],
                    "due_date": r[3],
                    "client_name": r[4] or "Без клиента",
                    "timezone": r[5] or "Asia/Yekaterinburg"
                }
                for r in rows
            ]

async def mark_task_reminded(task_id: int):
    """Фиксация времени отправки напоминания по задаче."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE crm_tasks SET reminded_at = CURRENT_TIMESTAMP WHERE task_id = ?", (task_id,))
        await db.commit()

async def mark_morning_brief_sent(user_id: int, date_str: str):
    """Отметка об отправке утреннего брифинга."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE users SET last_morning_brief = ? WHERE user_id = ?", (date_str, user_id))
        await db.commit()

async def mark_evening_prompt_sent(user_id: int, date_str: str):
    """Отметка об отправке вечернего запроса рефлексии."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE users SET last_evening_prompt = ? WHERE user_id = ?", (date_str, user_id))
        await db.commit()

async def add_user_note(user_id: int, note_text: str):
    """Сохранение заметки пользователя в БД."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT INTO user_notes (user_id, note_text)
            VALUES (?, ?)
        """, (user_id, note_text))
        await db.commit()

async def get_user_notes(user_id: int, limit: int = 10):
    """Получение последних N заметок пользователя."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT note_id, note_text, created_at
            FROM user_notes
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "note_id": r[0],
                    "note_text": r[1],
                    "created_at": r[2]
                }
                for r in rows
            ]


