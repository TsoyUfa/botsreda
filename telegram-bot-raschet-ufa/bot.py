import os
import logging
import sqlite3
import csv
import re
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "8895453398:AAF-pi4CGYgPCfnjo61dTiTeezlSqWjeBJs")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5690724590"))
DB_PATH = os.getenv("DB_PATH", "leads.db")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Инициализация БД
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Таблица пользователей (для рассылки)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Таблица квалифицированных лидов
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

# Состояния формы FSM
class LeadForm(StatesGroup):
    waiting_for_goal = State()
    waiting_for_dp = State()
    waiting_for_payment = State()
    waiting_for_contact = State()

# Состояния админки
class AdminForm(StatesGroup):
    waiting_for_broadcast = State()

router = Router()

# Клавиатуры под мобильный
def get_goal_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Своё первое жильё"), KeyboardButton(text="🔑 Переезд из аренды")],
            [KeyboardButton(text="👨‍👩‍👧‍👦 Расширение для детей"), KeyboardButton(text="💼 Сохранить деньги от инфляции")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_dp_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Нет первоначального взноса (0 ₽)")],
            [KeyboardButton(text="🔹 До 1.5 млн ₽"), KeyboardButton(text="🔸 1.5 – 3 млн ₽")],
            [KeyboardButton(text="🔥 Более 3 млн ₽")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_payment_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔹 До 35 000 ₽ / мес"), KeyboardButton(text="🔸 35 000 – 50 000 ₽ / мес")],
            [KeyboardButton(text="🔥 50 000 – 70 000 ₽ / мес"), KeyboardButton(text="🚀 Свыше 70 000 ₽ / мес")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить контакт и получить расчет", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# --- АДМИН-КОМАНДЫ ---

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    admin_menu = (
        "⚙️ <b>Панель администратора @Raschetufa_bot</b>\n\n"
        "Доступные команды:\n"
        "📊 /leads — выгрузить список всех лидов в CSV\n"
        "📢 /broadcast — сделать рассылку по пользователям бота\n\n"
        "Все новые лиды будут автоматически дублироваться сюда в чат."
    )
    await message.answer(admin_menu, parse_mode="HTML")

@router.message(Command("leads"))
async def cmd_leads(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, username, full_name, goal, dp, comfort_payment, phone, created_at FROM leads ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        await message.answer("В базе данных пока нет лидов.")
        return
        
    csv_file_path = "leads_export.csv"
    with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "User ID", "Telegram Username", "Имя контакта", "Задача (JTBD)", "Накопления (ПВ)", "Комфортный платеж", "Телефон", "Дата создания"])
        writer.writerows(rows)
        
    document = FSInputFile(csv_file_path)
    await bot.send_document(chat_id=ADMIN_ID, document=document, caption="📊 Список B2C-лидов (сводная таблица)")
    os.remove(csv_file_path)

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("✍️ <b>Введите текст для рассылки.</b>\n\n"
                         "Вы можете отформатировать его, добавить ссылку или прикрепить изображение.", parse_mode="HTML")
    await state.set_state(AdminForm.waiting_for_broadcast)

@router.message(AdminForm.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    
    # Сбор всех уникальных пользователей, кто запускал бота
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await message.answer("Нет пользователей для рассылки.")
        return
        
    sent_count = 0
    fail_count = 0
    
    status_msg = await message.answer(f"⏳ Запускаю рассылку для {len(users)} пользователей...")
    
    for (user_id,) in users:
        # Не отправляем самому себе
        if user_id == ADMIN_ID:
            continue
        try:
            # Копируем сообщение полностью (сохраняется текст, фото, кнопки)
            await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            sent_count += 1
            await asyncio.sleep(0.05)  # Защита от лимитов Telegram (anti-flood)
        except Exception as e:
            fail_count += 1
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            
    await status_msg.edit_text(
        f"📢 <b>Рассылка завершена!</b>\n\n"
        f"✅ Доставлено сообщений: <b>{sent_count}</b>\n"
        f"❌ Пользователи заблокировали бота: <b>{fail_count}</b>",
        parse_mode="HTML"
    )

# --- ПОЛЬЗОВАТЕЛЬСКАЯ ВОРОНКА ---

# Обработчик старта
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    # Сохранение пользователя в общую базу
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, username, full_name)
        VALUES (?, ?, ?)
    """, (
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    ))
    conn.commit()
    conn.close()
    
    welcome_text = (
        "Привет! Я цифровой ассистент Антона Цоя.\n\n"
        "Антон сейчас проводит встречи на стройплощадках Уфы, "
        "поэтому я помогаю ему собрать первичные данные, чтобы он подготовил "
        "для вас точные финансовые расчеты вручную.\n\n"
        "Какую главную задачу вы сейчас решаете?"
    )
    await message.answer(welcome_text, reply_markup=get_goal_keyboard())
    await state.set_state(LeadForm.waiting_for_goal)

# Обработчик выбора задачи
@router.message(LeadForm.waiting_for_goal)
async def process_goal(message: Message, state: FSMContext):
    await state.update_data(goal=message.text)
    await message.answer(
        "Какая сумма накоплений (резерв под первый взнос) у вас реально есть на руках?",
        reply_markup=get_dp_keyboard()
    )
    await state.set_state(LeadForm.waiting_for_dp)

# Обработчик выбора взноса
@router.message(LeadForm.waiting_for_dp)
async def process_dp(message: Message, state: FSMContext):
    await state.update_data(dp=message.text)
    await message.answer(
        "Какой ежемесячный платёж будет комфортен и не задушит семейный бюджет?",
        reply_markup=get_payment_keyboard()
    )
    await state.set_state(LeadForm.waiting_for_payment)

# Обработчик выбора платежа и вывод вердикта
@router.message(LeadForm.waiting_for_payment)
async def process_payment(message: Message, state: FSMContext):
    data = await state.update_data(comfort_payment=message.text)
    
    # Проверка выбора "без ПВ"
    has_no_dp = "Нет первоначального взноса" in data['dp']
    
    if has_no_dp:
        verdict = (
            "📉 <b>Финансовый вердикт:</b>\n\n"
            "При отсутствии первого взноса стандартные ипотечные программы банков со ставкой 21% не сработают.\n\n"
            "Однако в Уфе сейчас есть застройщики, которые предлагают рассрочки без ПВ или субсидированные программы с отложенным взносом.\n\n"
            "Я уже передал ваши данные Антону. Он вручную выберет подходящие лоты с нулевым взносом.\n\n"
            "Нажмите кнопку ниже, чтобы отправить ваш контакт, и Антон пришлет вам расчеты в WhatsApp или Telegram."
        )
    else:
        verdict = (
            "📊 <b>Финансовый вердикт:</b>\n\n"
            "При вашем взносе и комфортном платеже ипотека по рыночной ставке 21% сейчас финансово невыгодна (переплата составит более 250% за срок кредита).\n\n"
            "Но под ваши параметры отлично подходят 2 схемы: <b>Траншевая ипотека</b> (платёж 150 ₽/мес до сдачи) и <b>Семейная</b> (через созаёмщика под 6%).\n\n"
            "Антон вручную подберёт 3 конкретных лота в Уфе под ваш коридор, рассчитает платежи по этим схемам и напишет вам лично.\n\n"
            "Нажмите кнопку ниже, чтобы отправить контакт для связи."
        )
        
    await message.answer(verdict, parse_mode="HTML", reply_markup=get_contact_keyboard())
    await state.set_state(LeadForm.waiting_for_contact)

# Обработчик отправки контакта
@router.message(LeadForm.waiting_for_contact, F.contact)
async def process_contact(message: Message, state: FSMContext, bot: Bot):
    contact = message.contact
    phone = contact.phone_number
    data = await state.get_data()
    
    # Сохранение лида в SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leads (user_id, username, full_name, goal, dp, comfort_payment, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        message.from_user.id,
        message.from_user.username,
        f"{contact.first_name} {contact.last_name or ''}".strip(),
        data['goal'],
        data['dp'],
        data['comfort_payment'],
        phone
    ))
    conn.commit()
    conn.close()
    
    # Генерация карточки лида для Антона (в HTML-формате для защиты от спецсимволов)
    lead_info = (
        "🔥 <b>Новый лид с расчёта уфа бот!</b>\n\n"
        f"👤 <b>Имя:</b> {contact.first_name} {contact.last_name or ''}\n"
        f"📱 <b>Телефон:</b> <code>{phone}</code>\n"
        f"✈️ <b>Telegram:</b> @{message.from_user.username or 'нет юзернейма'}\n\n"
        f"🎯 <b>Задача:</b> {data['goal']}\n"
        f"💰 <b>Накопления (ПВ):</b> {data['dp']}\n"
        f"💳 <b>Комфортный платеж:</b> {data['comfort_payment']}"
    )
    
    # Отправка уведомления админу (Антону)
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=lead_info, parse_mode="HTML")
        logger.info(f"Notification sent to admin {ADMIN_ID}")
    except Exception as e:
        logger.error(f"Failed to send notification to admin: {e}")
        
    await message.answer(
        "Спасибо! Ваши данные отправлены Антону.\n\n"
        "Он подготовит сравнительный расчет по 3 схемам и свяжется с вами в ближайшее время.\n\n"
        "💬 Кстати, вы можете писать любые вопросы прямо в этот чат — они автоматически приходят Антону, и он ответит вам здесь же.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()

# --- ВСТРОЕННЫЙ ЧАТ ПОДДЕРЖКИ (FEEDBACK) ---

@router.message(F.text)
async def handle_user_message(message: Message, state: FSMContext, bot: Bot):
    # Пропускаем, если пользователь находится в процессе опроса FSM
    current_state = await state.get_state()
    if current_state is not None:
        return

    # Логика обработки ответов Администратора (Антона)
    if message.from_user.id == ADMIN_ID:
        if message.reply_to_message:
            reply_text = message.reply_to_message.text or message.reply_to_message.caption
            if reply_text:
                # Извлекаем ID пользователя с помощью регулярного выражения
                match = re.search(r"ID пользователя:\s*(\d+)", reply_text)
                if match:
                    user_id = int(match.group(1))
                    try:
                        # Отправляем сообщение пользователя обратно клиенту от лица бота
                        await bot.send_message(chat_id=user_id, text=message.text)
                        await message.reply(f"✅ Сообщение отправлено пользователю (ID: {user_id})")
                    except Exception as e:
                        await message.reply(f"❌ Ошибка отправки: {e}")
                    return
        return

    # Логика пересылки сообщений клиентов Антону в личку
    forward_text = (
        f"✉️ <b>Новое сообщение от пользователя в боте</b>\n\n"
        f"👤 <b>Имя:</b> {message.from_user.full_name}\n"
        f"✈️ <b>Юзернейм:</b> @{message.from_user.username or 'нет'}\n"
        f"🆔 <b>ID пользователя:</b> <code>{message.from_user.id}</code>\n\n"
        f"💬 <b>Текст сообщения:</b>\n<i>{message.text}</i>\n\n"
        f"👉 <i>Чтобы ответить пользователю, сделайте <b>Reply (Ответить)</b> на это сообщение.</i>"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=forward_text, parse_mode="HTML")
        await message.answer("Ваше сообщение отправлено Антону. Он ответит вам прямо в этом чате в ближайшее время.")
    except Exception as e:
        logger.error(f"Failed to forward message to admin: {e}")

async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    logger.info("Bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
