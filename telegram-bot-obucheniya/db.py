"""Работа с базой данных (aiosqlite)."""
import asyncio
import aiosqlite
from datetime import datetime
import json
from typing import List, Dict, Any, Optional, Tuple
from config import DB_PATH, MODULES

async def init_db():
    """Инициализация базы данных - создание таблиц"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                full_name TEXT,
                phone TEXT,
                is_premium BOOLEAN DEFAULT 0,
                invite_code TEXT,
                current_block INTEGER DEFAULT 1,
                current_lesson TEXT DEFAULT '1.1',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Миграция: Проверим наличие колонок, если таблица была создана ранее
        async with db.execute("PRAGMA table_info(users)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
        
        if "full_name" not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
        if "current_block" not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN current_block INTEGER DEFAULT 1")
        if "current_lesson" not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN current_lesson TEXT DEFAULT '1.1'")
        if "status" not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")

        # Таблица прогресса пользователей (оставляем для обратной совместимости)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                module_id INTEGER,
                lesson_id INTEGER,
                is_unlocked BOOLEAN DEFAULT 0,
                is_completed BOOLEAN DEFAULT 0,
                score REAL DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Таблица результатов тестов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                module_id INTEGER,
                test_id INTEGER,
                score REAL,
                is_passed BOOLEAN,
                answers TEXT,
                taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Таблица домашних заданий
        await db.execute("""
            CREATE TABLE IF NOT EXISTS homeworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                block_number INTEGER,
                file_type TEXT, -- 'voice' или 'text'
                file_id TEXT, -- Telegram File ID для голосовых сообщений, либо сам текст ДЗ
                status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
                curator_comment TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        # Таблица бронирований
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                building_code TEXT,
                apartment_info TEXT,
                customer_name TEXT,
                customer_phone TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Таблица платежей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                currency TEXT DEFAULT 'RUB',
                payment_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Таблица инвайт-кодов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS invite_codes (
                code TEXT PRIMARY KEY,
                created_by INTEGER,
                max_uses INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица рассылок
        await db.execute("""
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                message_type TEXT DEFAULT 'text',
                target_users TEXT, -- JSON массив user_ids
                sent_by INTEGER,
                sent_at TIMESTAMP,
                status TEXT DEFAULT 'draft'
            )
        """)
        
        # Таблица уникальных лотов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                developer_name TEXT,
                rooms TEXT,
                area REAL,
                base_price REAL,
                layout_image_url TEXT,
                is_unique BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица вариаций финансовых программ для лотов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lot_variations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER,
                program_name TEXT,
                subsidized_rate REAL,
                markup_percent REAL,
                monthly_payment REAL,
                calculation_details_json TEXT,
                FOREIGN KEY (lot_id) REFERENCES lots (id)
            )
        """)
        
        # Таблица мероприятий
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                event_type TEXT, -- 'online' или 'offline'
                event_date TIMESTAMP,
                location TEXT,
                max_seats INTEGER DEFAULT 0,
                registered_count INTEGER DEFAULT 0
            )
        """)
        
        # Таблица регистраций на мероприятия
        await db.execute("""
            CREATE TABLE IF NOT EXISTS event_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                user_id INTEGER,
                status TEXT DEFAULT 'registered', -- 'registered', 'attended', 'cancelled'
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Таблица логов чатов с ИИ
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_message TEXT,
                bot_response TEXT,
                retrieved_chunks TEXT,
                tokens_used REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        await db.commit()


# Функции для работы с пользователями
async def create_user(user_id: int, username: str, full_name: str = "", phone: str = "", invite_code: str = ""):
    """Создание нового пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO users 
               (user_id, username, full_name, phone, invite_code, current_block, current_lesson, status) 
               VALUES (?, ?, ?, ?, ?, 1, '1.1', 'active')""",
            (user_id, username, full_name, phone, invite_code)
        )
        await db.commit()

async def get_user(user_id: int) -> Optional[Dict]:
    """Получение информации о пользователе с явным перечислением полей"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT user_id, username, full_name, phone, is_premium, invite_code, 
                      current_block, current_lesson, status, created_at 
               FROM users WHERE user_id = ?""", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "username": row[1],
                    "full_name": row[2] or "",
                    "first_name": (row[2] or "").split(" ")[0] if row[2] else "", # Для обратной совместимости
                    "phone": row[3] or "",
                    "is_premium": bool(row[4]),
                    "invite_code": row[5] or "",
                    "current_block": row[6],
                    "current_lesson": row[7],
                    "status": row[8],
                    "created_at": row[9]
                }
            return None

async def update_user_phone(user_id: int, phone: str):
    """Обновление телефона пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET phone = ? WHERE user_id = ?",
            (phone, user_id)
        )
        await db.commit()

async def update_user_name(user_id: int, full_name: str):
    """Обновление ФИО пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET full_name = ? WHERE user_id = ?",
            (full_name, user_id)
        )
        await db.commit()

async def update_user_status(user_id: int, status: str):
    """Обновление статуса обучения пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET status = ? WHERE user_id = ?",
            (status, user_id)
        )
        await db.commit()

async def update_user_lesson(user_id: int, current_lesson: str):
    """Обновление текущего активного урока"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET current_lesson = ? WHERE user_id = ?",
            (current_lesson, user_id)
        )
        await db.commit()

async def update_user_block(user_id: int, current_block: int):
    """Обновление текущего блока обучения"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET current_block = ? WHERE user_id = ?",
            (current_block, user_id)
        )
        await db.commit()

async def update_user_premium(user_id: int, is_premium: bool):
    """Обновление премиум-статуса пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_premium = ? WHERE user_id = ?",
            (int(is_premium), user_id)
        )
        await db.commit()

async def is_premium(user_id: int) -> bool:
    """Проверка премиум-статуса пользователя"""
    user = await get_user(user_id)
    return user and user["is_premium"]

# Функции для работы с домашними заданиями
async def create_homework(user_id: int, block_number: int, file_type: str, file_id: str) -> int:
    """Создание нового домашнего задания и возврат его ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """INSERT INTO homeworks (user_id, block_number, file_type, file_id, status)
               VALUES (?, ?, ?, ?, 'pending')""",
            (user_id, block_number, file_type, file_id)
        ) as cursor:
            hw_id = cursor.lastrowid
            await db.commit()
            return hw_id

async def get_homework(hw_id: int) -> Optional[Dict]:
    """Получение информации по ДЗ"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT h.id, h.user_id, h.block_number, h.file_type, h.file_id, 
                      h.status, h.curator_comment, h.submitted_at, h.reviewed_at,
                      u.full_name, u.username
               FROM homeworks h
               JOIN users u ON h.user_id = u.user_id
               WHERE h.id = ?""", (hw_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "user_id": row[1],
                    "block_number": row[2],
                    "file_type": row[3],
                    "file_id": row[4],
                    "status": row[5],
                    "curator_comment": row[6],
                    "submitted_at": row[7],
                    "reviewed_at": row[8],
                    "full_name": row[9],
                    "username": row[10]
                }
            return None

async def approve_homework(hw_id: int):
    """Одобрение домашнего задания куратором"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE homeworks 
               SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP 
               WHERE id = ?""", (hw_id,)
        )
        await db.commit()

async def reject_homework(hw_id: int, comment: str):
    """Отклонение домашнего задания куратором с комментарием"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE homeworks 
               SET status = 'rejected', curator_comment = ?, reviewed_at = CURRENT_TIMESTAMP 
               WHERE id = ?""", (comment, hw_id)
        )
        await db.commit()

# Функции для работы с прогрессом
async def get_user_progress(user_id: int) -> List[Tuple]:
    """Получение прогресса пользователя по всем модулям"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT module_id, is_unlocked, is_completed, score, completed_at
               FROM user_progress 
               WHERE user_id = ? ORDER BY module_id""",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()

async def unlock_module(user_id: int, module_id: int):
    """Разблокировка модуля для пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO user_progress 
               (user_id, module_id, is_unlocked) 
               VALUES (?, ?, 1)""",
            (user_id, module_id)
        )
        await db.commit()

async def complete_module(user_id: int, module_id: int, score: float = 1.0):
    """Завершение модуля пользователем"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE user_progress 
               SET is_completed = 1, score = ?, completed_at = CURRENT_TIMESTAMP
               WHERE user_id = ? AND module_id = ?""",
            (score, user_id, module_id)
        )
        await db.commit()

# Функции для работы с тестами
async def save_test_result(user_id: int, module_id: int, test_id: int, score: float, is_passed: bool, answers: str = "{}"):
    """Сохранение результата теста"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO test_results 
               (user_id, module_id, test_id, score, is_passed, answers) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, module_id, test_id, score, int(is_passed), answers)
        )
        await db.commit()

# Функции для бронирований
async def create_booking(user_id: int, building_code: str, apartment_info: str, customer_name: str, customer_phone: str):
    """Создание нового бронирования"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO bookings 
               (user_id, building_code, apartment_info, customer_name, customer_phone) 
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, building_code, apartment_info, customer_name, customer_phone)
        )
        await db.commit()

async def get_user_bookings(user_id: int) -> List[Tuple]:
    """Получение бронирований пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT b.*, u.first_name 
               FROM bookings b
               LEFT JOIN users u ON b.user_id = u.user_id
               WHERE b.user_id = ? 
               ORDER BY b.created_at DESC""",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()

# Административные функции
async def get_all_users() -> List[Tuple]:
    """Получение всех пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT user_id, username, first_name, is_premium, created_at 
               FROM users 
               ORDER BY created_at DESC"""
        ) as cursor:
            return await cursor.fetchall()

async def count_users() -> int:
    """Подсчет общего количества пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]

async def count_premium_users() -> int:
    """Подсчет премиум-пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1") as cursor:
            row = await cursor.fetchone()
            return row[0]

async def get_progress_overview() -> List[Tuple]:
    """Общая статистика по прохождению модулей"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT module_id, 
                      COUNT(CASE WHEN is_completed = 1 THEN 1 END) as completions,
                      AVG(score) as avg_score
               FROM user_progress 
               GROUP BY module_id"""
        ) as cursor:
            return await cursor.fetchall()

async def get_recent_bookings() -> List[Tuple]:
    """Получение недавних бронирований для администрации"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT b.*, u.first_name 
               FROM bookings b
               LEFT JOIN users u ON b.user_id = u.user_id
               ORDER BY b.created_at DESC 
               LIMIT 50"""
        ) as cursor:
            return await cursor.fetchall()

# --- Новые функции прототипа «Среда Обучения 2.0» ---

async def create_lot(title: str, developer_name: str, rooms: str, area: float, base_price: float, layout_image_url: str = "", is_unique: bool = False) -> int:
    """Создание лота и возврат его ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """INSERT INTO lots (title, developer_name, rooms, area, base_price, layout_image_url, is_unique)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, developer_name, rooms, area, base_price, layout_image_url, int(is_unique))
        ) as cursor:
            lot_id = cursor.lastrowid
            await db.commit()
            return lot_id

async def create_lot_variation(lot_id: int, program_name: str, subsidized_rate: float, markup_percent: float, monthly_payment: float, calculation_details_json: str) -> int:
    """Создание финансовой вариации для лота"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """INSERT INTO lot_variations (lot_id, program_name, subsidized_rate, markup_percent, monthly_payment, calculation_details_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (lot_id, program_name, subsidized_rate, markup_percent, monthly_payment, calculation_details_json)
        ) as cursor:
            var_id = cursor.lastrowid
            await db.commit()
            return var_id

async def get_all_lots() -> List[Dict]:
    """Получение всех лотов с их вариациями"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM lots ORDER BY is_unique DESC, created_at DESC") as cursor:
            rows = await cursor.fetchall()
            lots = []
            for row in rows:
                lot = dict(row)
                # Получаем вариации для этого лота
                async with db.execute("SELECT * FROM lot_variations WHERE lot_id = ?", (lot["id"],)) as v_cursor:
                    v_rows = await v_cursor.fetchall()
                    lot["variations"] = [dict(v) for v in v_rows]
                lots.append(lot)
            return lots

async def create_event(title: str, description: str, event_type: str, event_date: str, location: str, max_seats: int = 0) -> int:
    """Создание мероприятия"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """INSERT INTO events (title, description, event_type, event_date, location, max_seats, registered_count)
               VALUES (?, ?, ?, ?, ?, ?, 0)""",
            (title, description, event_type, event_date, location, max_seats)
        ) as cursor:
            event_id = cursor.lastrowid
            await db.commit()
            return event_id

async def get_all_events() -> List[Dict]:
    """Получение всех мероприятий"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM events ORDER BY event_date ASC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def register_for_event(event_id: int, user_id: int) -> bool:
    """Регистрация пользователя на мероприятие"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, зарегистрирован ли уже
        async with db.execute(
            "SELECT id FROM event_registrations WHERE event_id = ? AND user_id = ?",
            (event_id, user_id)
        ) as cursor:
            if await cursor.fetchone():
                return False  # Уже зарегистрирован
        
        # Проверяем места
        async with db.execute(
            "SELECT max_seats, registered_count FROM events WHERE id = ?",
            (event_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                max_seats, registered_count = row
                if max_seats > 0 and registered_count >= max_seats:
                    return False  # Нет мест
            
        # Регистрируем
        await db.execute(
            "INSERT INTO event_registrations (event_id, user_id, status) VALUES (?, ?, 'registered')",
            (event_id, user_id)
        )
        # Увеличиваем счетчик
        await db.execute(
            "UPDATE events SET registered_count = registered_count + 1 WHERE id = ?",
            (event_id,)
        )
        await db.commit()
        return True

async def get_user_event_registrations(user_id: int) -> List[Dict]:
    """Получение регистраций пользователя на мероприятия"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT e.*, er.status as reg_status, er.registered_at
               FROM event_registrations er
               JOIN events e ON er.event_id = e.id
               WHERE er.user_id = ?
               ORDER BY e.event_date ASC""",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def log_ai_chat(user_id: int, user_message: str, bot_response: str, retrieved_chunks: str, tokens_used: float = 0):
    """Логирование общения с ИИ"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO ai_chat_logs (user_id, user_message, bot_response, retrieved_chunks, tokens_used)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, user_message, bot_response, retrieved_chunks, tokens_used)
        )
        await db.commit()