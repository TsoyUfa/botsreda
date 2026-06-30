import os
import re
import sqlite3
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Load env variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/anton_tsoy/Desktop/Обсидиан")
DB_PATH = os.path.join(os.path.dirname(__file__), "bot_history.db")

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Warning: GEMINI_API_KEY is not set.")

# Init SQLite DB for tracking queries
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            username TEXT,
            query TEXT,
            source_file TEXT,
            reply TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def log_query(user_id, username, query, source_file, reply):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO query_logs (user_id, username, query, source_file, reply) VALUES (?, ?, ?, ?, ?)",
            (str(user_id), username or "unknown", query, source_file or "None", reply)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging query: {e}")

# Index relevant files from Obsidian vault
def get_kb_files():
    kb = {}
    
    # We want to scan the '6. обучения агентов' folder and 'Методичка 2.0.md' specifically
    paths_to_scan = [
        os.path.join(VAULT_PATH, "6. обучения агентов"),
        os.path.join(VAULT_PATH, "Методичка 2.0.md")
    ]
    
    for path in paths_to_scan:
        if not os.path.exists(path):
            continue
            
        if os.path.isfile(path) and path.endswith(".md"):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    kb[os.path.basename(path)] = f.read()
            except Exception as e:
                print(f"Error reading {path}: {e}")
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".md") and "archive" not in root.lower():
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                kb[file] = f.read()
                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")
    return kb

def find_relevant_context(query, kb):
    """Find the note that matches the query best using word overlap scoring."""
    tokens = re.findall(r'\w+', query.lower())
    # Exclude very short query words
    tokens = [t for t in tokens if len(t) > 2]
    
    if not tokens:
        return "", None, 0
        
    best_file = None
    best_score = 0
    best_content = ""
    
    for file, content in kb.items():
        score = 0
        content_lower = content.lower()
        
        # Simple word density score
        for token in tokens:
            # Add score for each occurrence
            score += content_lower.count(token)
            
        # Give extra weight if keyword appears in the filename/title
        file_title = os.path.splitext(file)[0].lower()
        for token in tokens:
            if token in file_title:
                score += 15
                
        if score > best_score:
            best_score = score
            best_file = file
            best_content = content
            
    return best_content, best_file, best_score

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 Приветствую! Я — ИИ-Ассистент команды брокеров Антона Цоя.\n\n"
        "Я знаю регламенты, чек-листы первого касания, схемы траншевых и субсидированных ипотек, "
        "а также методические материалы из базы знаний.\n\n"
        "Задай мне любой вопрос (например: *«Как отрабатывать возражение по высоким ставкам?»* или "
        "*«В чем суть траншевой ипотеки?»*), и я отвечу тебе строго по регламентам Антона."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def get_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to check what agents are asking."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username, query, timestamp FROM query_logs ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            await update.message.reply_text("История запросов пока пуста.")
            return
            
        history_text = "📊 *Последние 10 запросов от команды:*\n\n"
        for user, query, ts in rows:
            history_text += f"🕒 {ts[:16]} | @{user}: {query[:60]}...\n"
            
        await update.message.reply_text(history_text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Ошибка получения истории: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    user = update.message.from_user
    
    # Notify user that bot is typing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # 1. Read Knowledge Base from Obsidian
    kb = get_kb_files()
    if not kb:
        await update.message.reply_text("Ошибка: База знаний пуста или папка с обучениями не найдена.")
        return
        
    # 2. Find context
    context_text, source_file, score = find_relevant_context(user_query, kb)
    
    # 3. Generate answer via Gemini
    if not api_key:
        reply = "[Имитация бота]: API Ключ не задан. Запрос принят."
        await update.message.reply_text(reply)
        return
        
    # Tone of Voice instructions
    system_instruction = (
        "Ты — ИИ-Ассистент брокеров команды Антона Цоя. Твоя задача — отвечать на вопросы агентов "
        "строго на основе предоставленных материалов из базы знаний Антона. Если в предоставленном контексте "
        "нет ответа на этот вопрос, скажи вежливо, что этой информации нет в текущих регламентах компании.\n\n"
        "Стиль ответов — Tone of Voice Антона Цоя:\n"
        "- Прямо, по делу, без лишней воды и длинных вступлений.\n"
        "- Я объясняю, а не продаю: пиши фактами, приводи конкретные схемы и цифры.\n"
        "- Общайся на равных, с достоинством, как партнер с партнером (win-win), без лести.\n"
        "- Если приводишь расчеты — пиши их четко и понятно."
    )
    
    prompt = f"""
Контекст из базы знаний Антона Цоя (Источник: {source_file or 'Не найден'}):
\"\"\"
{context_text[:12000] if context_text else 'Релевантные регламенты не найдены.'}
\"\"\"

Вопрос агента: "{user_query}"

Дай краткий и точный ответ по делу, опираясь на контекст и следуя Tone of Voice.
"""
    
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        reply = response.text.strip()
        
        # Append source tag to reply
        if source_file:
            reply += f"\n\n📖 _Источник: {os.path.splitext(source_file)[0]}_"
        else:
            reply += "\n\n⚠️ _В регламентах компании точного ответа не найдено._"
            
        await update.message.reply_text(reply, parse_mode="Markdown")
        
        # Log to DB
        log_query(user.id, user.username, user_query, source_file, reply)
        
    except Exception as e:
        error_reply = f"Извини, произошла техническая ошибка при обработке запроса: {str(e)}"
        await update.message.reply_text(error_reply)
        log_query(user.id, user.username, user_query, source_file, error_reply)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "your_telegram_bot_token_here":
        print("Error: TELEGRAM_BOT_TOKEN is not configured in .env file.")
        print("Бот не запущен. Пожалуйста, укажите токен в .env.")
        return
        
    init_db()
    print("=== Запуск Telegram-бота ===")
    print(f"База данных логов: {DB_PATH}")
    
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", get_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()
