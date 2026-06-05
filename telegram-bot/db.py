import sqlite3
import aiosqlite
from config import DB_PATH

async def init_db():
    """Initializes the database tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Table of users and their profile / premium state
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_premium INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table of unlocked modules per user
        # User 1 always has Module 1 unlocked (it is free)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id INTEGER,
                module_id INTEGER,
                is_unlocked INTEGER DEFAULT 0,
                is_completed INTEGER DEFAULT 0,
                score REAL,
                PRIMARY KEY (user_id, module_id)
            )
        """)
        
        # Payment logs
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                currency TEXT,
                payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def create_user(user_id: int, username: str, first_name: str):
    """Creates a new user if they don't exist and unlocks Block 1."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        # Unlock Block 1 (which is free)
        await db.execute(
            "INSERT OR IGNORE INTO user_progress (user_id, module_id, is_unlocked) VALUES (?, 1, 1)",
            (user_id,)
        )
        await db.commit()

async def get_user(user_id: int):
    """Retrieves user info."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def is_premium(user_id: int) -> bool:
    """Checks if the user has premium access unlocked."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_premium FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else False

async def unlock_premium(user_id: int):
    """Grants premium access and unlocks Blocks 2-7."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Mark premium in users table
        await db.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
        # Unlock Blocks 2-7
        for module_id in range(2, 8):
            await db.execute(
                "INSERT OR REPLACE INTO user_progress (user_id, module_id, is_unlocked) VALUES (?, ?, 1)",
                (user_id, module_id)
            )
        await db.commit()

async def get_user_progress(user_id: int):
    """Gets all blocks progress for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT module_id, is_unlocked, is_completed, score FROM user_progress WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()

async def is_module_unlocked(user_id: int, module_id: int) -> bool:
    """Checks if a specific block is unlocked."""
    # Premium users have blocks 2-7 unlocked
    premium = await is_premium(user_id)
    if premium or module_id == 1:
        return True
        
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT is_unlocked FROM user_progress WHERE user_id = ? AND module_id = ?",
            (user_id, module_id)
        ) as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else False

async def save_quiz_result(user_id: int, module_id: int, score: float, is_completed: bool):
    """Saves the score and completion status of a quiz."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_progress (user_id, module_id, is_unlocked, is_completed, score) VALUES (?, ?, 1, ?, ?)",
            (user_id, module_id, int(is_completed), score)
        )
        
        # If successfully completed, unlock the next block (only if it is free or user has premium)
        if is_completed:
            next_module = module_id + 1
            if next_module <= 7:
                has_premium = await is_premium(user_id)
                # Next module is unlocked only if it's free OR user is premium
                should_unlock = (next_module == 1 or has_premium)
                if should_unlock:
                    await db.execute(
                        "INSERT OR IGNORE INTO user_progress (user_id, module_id, is_unlocked) VALUES (?, ?, 1)",
                        (user_id, next_module)
                    )
        await db.commit()

async def log_payment(user_id: int, amount: float, currency: str, payload: str):
    """Logs the payment details."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payments (user_id, amount, currency, payload) VALUES (?, ?, ?, ?)",
            (user_id, amount, currency, payload)
        )
        await db.commit()
