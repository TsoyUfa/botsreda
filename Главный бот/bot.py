import os
import re
import csv
import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, 
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from aiogram.client.session.aiohttp import AiohttpSession

import db
import config
from questions import QUIZ_QUESTIONS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Состояния FSM
class QuizState(StatesGroup):
    answering = State()

class SupportState(StatesGroup):
    chatting = State()

class AdminState(StatesGroup):
    waiting_for_broadcast = State()

class LeadForm(StatesGroup):
    waiting_for_goal = State()
    waiting_for_dp = State()
    waiting_for_payment = State()
    waiting_for_contact = State()

router = Router()

# Вспомогательные функции
def map_param_to_keyword(param: str) -> str:
    """Маппинг реферального параметра или кодового слова в стандартное кодовое слово."""
    param = param.strip().upper()
    # Обработка reels_X
    match = re.match(r"REELS_(\d+)", param)
    if match:
        num = int(match.group(1))
        mapping = {
            1: "РЫНОК", 2: "LTV", 3: "ЭТАПЫ", 4: "ПРАВИЛА",
            5: "РАСЧЕТ", 6: "ПУШКА", 7: "ЭКСПЕРТ", 8: "КОНТАКТ"
        }
        return mapping.get(num, None)
    
    # Обработка reels_слово
    if param.startswith("REELS_"):
        word = param[6:]
        if word in config.LEAD_MAGNETS:
            return word
            
    # Прямое совпадение
    if param in config.LEAD_MAGNETS:
        return param
        
    return None

async def check_user_subscription(bot: Bot, user_id: int) -> bool:
    """Проверка подписки пользователя на Telegram-канал."""
    if user_id == config.ADMIN_ID:
        return True
    try:
        chat_member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        is_sub = chat_member.status in ["creator", "administrator", "member"]
        db.update_subscription(user_id, is_sub)
        return is_sub
    except Exception as e:
        logger.error(f"Ошибка проверки подписки для {user_id}: {e}")
        # В случае ошибки API (например, если бот не админ в канале) возвращаем False
        return False

def get_main_keyboard():
    """Клавиатура главного меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧮 Рассчитать ипотеку/рассрочку")],
            [KeyboardButton(text="📄 Получить методичку клиента")]
        ],
        resize_keyboard=True,
        persistent=True
    )

def get_cancel_keyboard():
    """Клавиатура отмены."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

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

async def deliver_lead_magnet(bot: Bot, user_id: int, keyword: str):
    """Выдача лид-магнита в чат (с автоопределением PDF версии)."""
    magnet = config.LEAD_MAGNETS[keyword]
    
    # Путь к PDF версии
    pdf_file_name = magnet["file_name"].replace(".md", ".pdf")
    pdf_source_name = magnet["source_name"].replace(".md", ".pdf")
    pdf_file_path = os.path.join(config.LEAD_MAGNETS_DIR, pdf_file_name)
    
    # Путь к MD версии
    md_file_path = os.path.join(config.LEAD_MAGNETS_DIR, magnet["file_name"])
    
    # Проверяем, какой файл использовать (приоритет у PDF)
    if os.path.exists(pdf_file_path):
        file_path = pdf_file_path
        send_name = pdf_source_name
    elif os.path.exists(md_file_path):
        file_path = md_file_path
        send_name = magnet["source_name"]
    else:
        # Если ни один не найден
        await bot.send_message(
            chat_id=user_id,
            text=f"⚠️ Извините, файл **{magnet['title']}** временно недоступен. Антон уже уведомлен."
        )
        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text=f"🚨 Отсутствует файл лид-магнита в папке (ни .pdf, ни .md): `{md_file_path}`"
        )
        return
        
    try:
        # Отправляем документ
        document = FSInputFile(file_path, filename=send_name)
        await bot.send_document(
            chat_id=user_id,
            document=document,
            caption=f"🔥 Держи полезный материал:\n«<b>{magnet['title']}</b>»\n\nСкачивай и внедряй в практику!",
            parse_mode="HTML"
        )
        
        # Запись в БД
        db.add_download(user_id, keyword)
        
        # Планирование автодогрева через 24 часа
        # Сначала отменяем любые прошлые запланированные приглашения к тесту
        db.cancel_pending_drips(user_id, "quiz_invite")
        
        # Назначаем новое время отправки (24 часа)
        send_time = datetime.now() + timedelta(hours=24)
        db.schedule_drip(user_id, "quiz_invite", send_time)
        
    except Exception as e:
        logger.error(f"Ошибка при доставке файла {keyword} для {user_id}: {e}")
        await bot.send_message(
            chat_id=user_id,
            text="❌ Произошла техническая ошибка при отправке файла. Попробуйте еще раз позже."
        )

# --- ПОЛЬЗОВАТЕЛЬСКИЕ ОБРАБОТЧИКИ ---

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name
    
    # Добавление пользователя в БД
    db.add_user(user_id, username, full_name)
    
    # Проверка аргументов старта
    args = message.text.split()
    if len(args) > 1:
        keyword = map_param_to_keyword(args[1])
        if keyword:
            is_sub = await check_user_subscription(bot, user_id)
            if is_sub:
                await deliver_lead_magnet(bot, user_id, keyword)
            else:
                # Требуем подписку
                magnet = config.LEAD_MAGNETS[keyword]
                sub_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔗 Подписаться на канал", url=config.CHANNEL_LINK)],
                    [InlineKeyboardButton(text="✅ Проверить подписку", callback_data=f"check_sub:{keyword}")]
                ])
                await message.answer(
                    f"Привет! Рад видеть коллегу. 🤝\n\n"
                    f"Вы пришли за полезным материалом: «<b>{magnet['title']}</b>».\n\n"
                    f"Для того чтобы забрать файл, подпишитесь на мой Telegram-канал. Там я еженедельно выкладываю разборы реальных звонков агентов и делюсь фишками продаж:\n\n"
                    f"👉 <a href='{config.CHANNEL_LINK}'>Telegram-канал Антона Цоя</a>\n\n"
                    f"Подписались? Нажмите кнопку ниже для получения:",
                    parse_mode="HTML",
                    reply_markup=sub_kb
                )
            return

    # Стандартный вход без параметров
    welcome_text = (
        "Салют! Я — цифровой помощник Антона Цоя 🤖\n\n"
        "Здесь мы разбираемся в ипотечных платежах и учимся выгодно покупать квартиры в новостройках. "
        "Антон собирает сложные финансовые модели для клиентов, обучает рынок системным продажам и показывает реальную математику сделок.\n\n"
        "Что вы можете сделать здесь ⤵️"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@router.callback_query(F.data.startswith("check_sub:"))
async def cb_check_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    keyword = callback.data.split(":")[1]
    
    is_sub = await check_user_subscription(bot, user_id)
    if is_sub:
        await callback.message.delete()
        await deliver_lead_magnet(bot, user_id, keyword)
        await callback.answer("Подписка подтверждена!", show_alert=False)
    else:
        await callback.answer("❌ Вы еще не подписались на канал! Подпишитесь и попробуйте снова.", show_alert=True)

# Главное меню: Материалы
@router.message(F.text == "📚 Получить материалы")
async def show_materials(message: Message):
    text = (
        "💡 <b>Доступные материалы для скачивания:</b>\n\n"
        "Отправьте в чат соответствующее <b>кодовое слово</b>:\n\n"
        "🔑 <b>РЫНОК</b> — Чек-лист '5 навыков брокера в 2026 году'\n"
        "🔑 <b>LTV</b> — Руководство 'Как рассчитать LTV клиента'\n"
        "🔑 <b>ЭТАПЫ</b> — Скрипт 'Что отвечать на просьбу о планировках'\n"
        "🔑 <b>ПРАВИЛА</b> — Гайд 'Регламент первой встречи'\n"
        "🔑 <b>РАСЧЕТ</b> — Методичка '4 инструмента без господдержки'\n"
        "🔑 <b>ПУШКА</b> — Шаблон 'Презентация financial расчета'\n"
        "🔑 <b>ЭКСПЕРТ</b> — Чек-лист 'Маркеры слабой позиции брокера'\n"
        "🔑 <b>КОНТАКТ</b> — Главная методичка 'От заявки до встречи'\n\n"
        "<i>Просто напишите слово (например, <b>РЫНОК</b>) сообщением в этот чат!</i>"
    )
    await message.answer(text, parse_mode="HTML")

# Главное меню: Задать вопрос
@router.message(F.text == "💬 Задать вопрос Антону")
async def start_support(message: Message, state: FSMContext):
    await state.set_state(SupportState.chatting)
    await message.answer(
        "✍️ <b>Режим связи с Антоном Цоем</b>\n\n"
        "Напишите свой вопрос или отправьте аудиозапись вашего разговора с клиентом на разбор.\n"
        "Я мгновенно перешлю это Антону. Как только он ответит, сообщение придет прямо в этот чат!",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(F.text == "❌ Отмена", SupportState.chatting)
async def cancel_support(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Возвращаемся в главное меню.", reply_markup=get_main_keyboard())

# --- B2C КАЛЬКУЛЯТОР ИПОТЕКИ/РАССРОЧКИ (FSM) ---

@router.message(F.text == "🧮 Рассчитать ипотеку/рассрочку")
async def start_calculator(message: Message, state: FSMContext):
    await state.clear()
    welcome_calc = (
        "Привет! Я цифровой ассистент Антона Цоя.\n\n"
        "Антон сейчас проводит встречи на стройплощадках Уфы, "
        "поэтому я помогаю ему собрать первичные данные, чтобы он подготовил "
        "для вас точные финансовые расчеты вручную.\n\n"
        "Какую главную задачу вы сейчас решаете?"
    )
    await message.answer(welcome_calc, reply_markup=get_goal_keyboard())
    await state.set_state(LeadForm.waiting_for_goal)

@router.message(LeadForm.waiting_for_goal)
async def process_calc_goal(message: Message, state: FSMContext):
    await state.update_data(goal=message.text)
    await message.answer(
        "Какая сумма накоплений (резерв под первый взнос) у вас реально есть на руках?",
        reply_markup=get_dp_keyboard()
    )
    await state.set_state(LeadForm.waiting_for_dp)

@router.message(LeadForm.waiting_for_dp)
async def process_calc_dp(message: Message, state: FSMContext):
    await state.update_data(dp=message.text)
    await message.answer(
        "Какой ежемесячный платёж будет комфортен и не задушит семейный бюджет?",
        reply_markup=get_payment_keyboard()
    )
    await state.set_state(LeadForm.waiting_for_payment)

@router.message(LeadForm.waiting_for_payment)
async def process_calc_payment(message: Message, state: FSMContext):
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

@router.message(LeadForm.waiting_for_contact, F.contact | F.text)
async def process_calc_contact(message: Message, state: FSMContext, bot: Bot):
    if message.contact:
        phone = message.contact.phone_number
        contact_name = f"{message.contact.first_name} {message.contact.last_name or ''}".strip()
    else:
        phone = message.text
        if not re.match(r"^\+?[0-9\s\-()]{7,20}$", phone):
            await message.answer("⚠️ Пожалуйста, отправьте корректный номер телефона кнопкой ниже или введите его вручную в формате +79991234567:")
            return
        contact_name = message.from_user.full_name
        
    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    # Сохраняем лид в БД
    db.add_lead(user_id, username, contact_name, data['goal'], data['dp'], data['comfort_payment'], phone)
    
    # Формируем карточку лида для Антона
    lead_info = (
        "🔥 <b>Новый лид с расчёта уфа бот!</b>\n\n"
        f"👤 <b>Имя:</b> {contact_name}\n"
        f"📱 <b>Телефон:</b> <code>{phone}</code>\n"
        f"✈️ <b>Telegram:</b> @{username or 'нет юзернейма'}\n\n"
        f"🎯 <b>Задача:</b> {data['goal']}\n"
        f"💰 <b>Накопления (ПВ):</b> {data['dp']}\n"
        f"💳 <b>Комфортный платеж:</b> {data['comfort_payment']}"
    )
    
    try:
        await bot.send_message(chat_id=config.ADMIN_ID, text=lead_info, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")
        
    await message.answer(
        "Спасибо! Ваши данные отправлены Антону.\n\n"
        "Он подготовит сравнительный расчет по 3 схемам и свяжется с вами в ближайшее время.\n\n"
        "💬 Кстати, вы можете писать любые вопросы прямо в этот чат — они автоматически приходят Антону, и он ответит вам здесь же.",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

# --- РАЗВЕТВЛЕНИЕ ВЫДАЧИ МЕТОДИЧЕК (B2B/B2C) ---

@router.message(F.text == "📄 Получить методичку клиента")
async def show_client_manual_branch(message: Message, state: FSMContext):
    await state.clear()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я агент по недвижимости", callback_data="client_role:agent")],
        [InlineKeyboardButton(text="Я покупаю квартиру себе", callback_data="client_role:self")]
    ])
    
    await message.answer(
        "Для кого вы хотите получить методичку?",
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("client_role:"))
async def process_client_role(callback: CallbackQuery, state: FSMContext, bot: Bot):
    role = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    await callback.message.delete()
    
    if role == "agent":
        # Логика выдачи методички для агентов (B2B, требует подписки)
        keyword = "КОНТАКТ"
        is_sub = await check_user_subscription(bot, user_id)
        if is_sub:
            await deliver_lead_magnet(bot, user_id, keyword)
        else:
            magnet = config.LEAD_MAGNETS[keyword]
            sub_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Подписаться на канал", url=config.CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ Проверить подписку", callback_data=f"check_sub:{keyword}")]
            ])
            await callback.message.answer(
                f"Привет! Рад видеть коллегу. 🤝\n\n"
                f"Вы пришли за полезным материалом: «<b>{magnet['title']}</b>».\n\n"
                f"Для того чтобы забрать файл, подпишитесь на мой Telegram-канал. Там я еженедельно выкладываю разборы реальных звонков агентов и делюсь фишками продаж:\n\n"
                f"👉 <a href='{config.CHANNEL_LINK}'>Telegram-канал Антона Цоя</a>\n\n"
                f"Подписались? Нажмите кнопку ниже для получения:",
                parse_mode="HTML",
                reply_markup=sub_kb
            )
    else:
        # Логика выдачи методички для покупателей (B2C, прямая выдача)
        await deliver_lead_magnet(bot, user_id, "КЛИЕНТ")
        
    await callback.answer()

# --- ЛОГИКА ЭКСПРЕСС-ТЕСТИРОВАНИЯ (10 вопросов) ---

async def send_quiz_question(message: Message, state: FSMContext, question_index: int):
    """Отправка вопроса теста с Inline-кнопками."""
    question = QUIZ_QUESTIONS[question_index]
    
    # Формируем Inline клавиатуру
    buttons = []
    labels = ["А", "Б", "В"]
    for i, opt in enumerate(question["options"]):
        buttons.append([InlineKeyboardButton(text=opt, callback_data=f"quiz_ans:{i}")])
        
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    text = (
        f"<b>Вопрос {question_index + 1} из 10</b>\n\n"
        f"{question['text']}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@router.message(F.text == "📝 Экспресс-тест")
async def start_quiz(message: Message, state: FSMContext):
    # Отменяем любые автодогревы
    db.cancel_pending_drips(message.from_user.id, "quiz_invite")
    
    await state.set_state(QuizState.answering)
    await state.update_data(current_q=0, score=0)
    
    await message.answer(
        "🚀 <b>Начинаем экспресс-тест 'От заявки до встречи'!</b>\n\n"
        "Тест состоит из 10 вопросов. Он поможет выявить зоны роста в твоих телефонных переговорах.\n"
        "Выбирай варианты кнопками под вопросами. Поехали!",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await send_quiz_question(message, state, 0)

@router.callback_query(QuizState.answering, F.data.startswith("quiz_ans:"))
async def handle_quiz_answer(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_q = user_data.get("current_q", 0)
    score = user_data.get("score", 0)
    
    selected_ans = int(callback.data.split(":")[1])
    question = QUIZ_QUESTIONS[current_q]
    
    # Проверка правильности
    is_correct = (selected_ans == question["correct"])
    if is_correct:
        score += 1
        feedback = "✅ <b>Правильно!</b>"
    else:
        feedback = f"❌ <b>Неверно.</b> Правильный ответ: <i>{question['options'][question['correct']]}</i>"
        
    feedback_text = (
        f"{feedback}\n\n"
        f"ℹ️ {question['comment']}\n\n"
        f"⭐ Текущий счет: {score} из {current_q + 1}"
    )
    
    # Удаляем кнопки старого вопроса и присылаем вердикт
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(feedback_text, parse_mode="HTML")
    await callback.answer()
    
    # Следующий шаг
    current_q += 1
    if current_q < 10:
        await state.update_data(current_q=current_q, score=score)
        await asyncio.sleep(1.0)
        await send_quiz_question(callback.message, state, current_q)
    else:
        # Тест завершен
        db.save_quiz_result(callback.from_user.id, score)
        await state.clear()
        
        # Подведение итогов
        if score >= 9:
            rating = "🏆 <b>Отлично! (9-10 баллов)</b>\nВы полностью усвоили методологию «Навигатор» и отлично держите сильную экспертную позицию перед клиентом."
        elif score >= 6:
            rating = "📈 <b>Хорошо (6-8 баллов)</b>\nВы понимаете базу, но в нюансах квалификации и позиционирования есть зоны роста, из-за которых могут сливаться сделки."
        else:
            rating = "⚠️ <b>Требуется повторение (менее 6 баллов)</b>\nВы часто скатываетесь в роль 'справочного бюро' и рискуете работать на клиента бесплатно. Рекомендуем внимательно перечитать методички."
            
        final_text = (
            f"🏁 <b>Тестирование завершено!</b>\n\n"
            f"Твой результат: <b>{score} из 10 правильных ответов</b>.\n\n"
            f"{rating}\n\n"
            f"🔥 <b>Специальное предложение от Антона:</b>\n"
            f"Каждую неделю Антон отбирает ровно 3-х агентов на <b>личный бесплатный аудит реального звонка</b>. "
            f"Мы прослушаем твою запись разговора, найдем точки слива клиентов и пересоберем сценарий под твои сделки.\n\n"
            f"Хочешь попасть на разбор?"
        )
        
        offer_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Записаться на аудит звонка", callback_data="request_audit")],
            [InlineKeyboardButton(text="❌ Спасибо, достаточно материалов", callback_data="quiz_close")]
        ])
        
        await asyncio.sleep(1.0)
        await callback.message.answer(final_text, parse_mode="HTML", reply_markup=get_main_keyboard())
        await callback.message.answer("Забронируй место на разбор:", reply_markup=offer_kb)

@router.callback_query(F.data == "request_audit")
async def cb_request_audit(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(SupportState.chatting)
    await callback.message.answer(
        "💬 <b>Отлично! Ты в режиме записи на аудит звонка.</b>\n\n"
        "Отправь аудиозапись твоего звонка (как файл, голосовое или ссылку) прямо сюда. "
        "Антон прослушает ее и ответит тебе здесь в ближайшее время!",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "quiz_close")
async def cb_quiz_close(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Окей! Если передумаешь — кнопка записи на разбор всегда доступна в меню.", reply_markup=get_main_keyboard())
    await callback.answer()

# Клик по кнопке drip-сообщения
@router.callback_query(F.data == "start_quiz_drip")
async def cb_start_quiz_drip(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await start_quiz(callback.message, state)
    await callback.answer()

# --- АДМИН-КОМАНДЫ ---

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    admin_text = (
        "⚙️ <b>Панель Администратора @{bot_name}</b>\n\n"
        "Команды управления:\n"
        "📊 /leads — выгрузить список всех зарегистрированных агентов с результатами тестов в CSV.\n"
        "📢 /broadcast — сделать рассылку по базе.\n"
        "📈 /stats — статистика использования бота."
    )
    await message.answer(admin_text, parse_mode="HTML")

@router.message(Command("leads"))
async def cmd_leads(message: Message, bot: Bot):
    if message.from_user.id != config.ADMIN_ID:
        return
        
    leads = db.get_leads_csv_data()
    if not leads:
        await message.answer("Агентов в базе данных пока нет.")
        return
        
    csv_path = os.path.join(config.DATA_DIR, "agents_export.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["Telegram ID", "Юзернейм", "Имя в Telegram", "Подписан на канал", "Балл за тест (из 10)", "Дата регистрации"])
        for row in leads:
            is_sub = "Да" if row[3] == 1 else "Нет"
            score = row[4] if row[4] is not None else "Не проходил"
            writer.writerow([row[0], row[1], row[2], is_sub, score, row[5]])
            
    doc = FSInputFile(csv_path)
    await bot.send_document(chat_id=config.ADMIN_ID, document=doc, caption="📊 Список агентов в базе бота")
    os.remove(csv_path)

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id != config.ADMIN_ID:
        return
        
    stats = db.get_stats()
    text = (
        "📈 <b>Статистика Главного Бота:</b>\n\n"
        f"👥 Всего зарегистрировано агентов: <b>{stats['total_users']}</b>\n"
        f"📝 Прошли экспресс-тестирование: <b>{stats['total_quizzes']}</b>\n"
        f"⭐ Средний балл по тесту: <b>{stats['avg_score']} из 10</b>\n\n"
        "🏆 <b>Топ скачиваний лид-магнитов:</b>\n"
    )
    
    if stats["downloads_by_keyword"]:
        for kw, cnt in stats["downloads_by_keyword"]:
            text += f"🔹 <b>{kw}</b>: {cnt} скачиваний\n"
    else:
        text += "Нет скачиваний."
        
    await message.answer(text, parse_mode="HTML")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        return
    await state.set_state(AdminState.waiting_for_broadcast)
    await message.answer(
        "📢 <b>Режим рассылки сообщений</b>\n\n"
        "Введите текст рассылки. Вы можете отформатировать его, вставить ссылки, "
        "прикрепить фото или документ. Сообщение будет полностью скопировано пользователям.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(AdminState.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Рассылка отменена.", reply_markup=get_main_keyboard())
        return
        
    await state.clear()
    
    # Запрос выбора сегмента
    segment_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Всем агентам", callback_data="run_bc:all")],
        [InlineKeyboardButton(text="✅ Прошедшим тест", callback_data="run_bc:quiz_completed")],
        [InlineKeyboardButton(text="❌ Не проходившим тест", callback_data="run_bc:quiz_pending")]
    ])
    
    # Сохраняем сообщение рассылки во временном контексте, пересылая его админу
    await state.update_data(bc_msg_id=message.message_id, bc_chat_id=message.chat.id)
    await message.answer("Выберите сегмент получателей рассылки:", reply_markup=segment_kb)

@router.callback_query(F.data.startswith("run_bc:"))
async def cb_run_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    segment = callback.data.split(":")[1]
    user_data = await state.get_data()
    bc_msg_id = user_data.get("bc_msg_id")
    bc_chat_id = user_data.get("bc_chat_id")
    
    await callback.message.delete()
    
    if not bc_msg_id or not bc_chat_id:
        await callback.answer("Ошибка: сообщение для рассылки не найдено.", show_alert=True)
        await state.clear()
        return
        
    await state.clear()
    
    users = db.get_all_users_for_broadcast(segment)
    if not users:
        await callback.message.answer("Нет пользователей в выбранном сегменте.")
        return
        
    status_msg = await callback.message.answer(f"⏳ Запускаю рассылку для {len(users)} агентов...")
    
    success = 0
    blocked = 0
    failed = 0
    
    for uid in users:
        if uid == config.ADMIN_ID:
            continue
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=bc_chat_id, message_id=bc_msg_id)
            success += 1
            await asyncio.sleep(0.05) # Лимиты ТГ (20 сообщений в сек)
        except TelegramForbiddenError:
            blocked += 1
            db.update_subscription(uid, False)
        except Exception as e:
            failed += 1
            logger.error(f"Не удалось отправить рассылку {uid}: {e}")
            
    await status_msg.edit_text(
        f"📢 <b>Рассылка завершена!</b>\n\n"
        f"✅ Успешно доставлено: <b>{success}</b>\n"
        f"🚷 Заблокировали бота: <b>{blocked}</b>\n"
        f"❌ Ошибки отправки: <b>{failed}</b>",
        parse_mode="HTML"
    )
    await callback.answer()

# --- ЛОГИКА ДВУСТОРОННЕГО ЧАТА (ФИДБЕК / РАЗБОРЫ) ---

@router.message(F.text)
async def handle_text_messages(message: Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()
    if current_state in [
        LeadForm.waiting_for_goal.state,
        LeadForm.waiting_for_dp.state,
        LeadForm.waiting_for_payment.state,
        LeadForm.waiting_for_contact.state
    ]:
        return

    # Если текст совпадает с кодовым словом
    keyword = map_param_to_keyword(message.text)
    if keyword:
        # Проверяем подписку
        user_id = message.from_user.id
        is_sub = await check_user_subscription(bot, user_id)
        if is_sub:
            await deliver_lead_magnet(bot, user_id, keyword)
        else:
            magnet = config.LEAD_MAGNETS[keyword]
            sub_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Подписаться на канал", url=config.CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ Проверить подписку", callback_data=f"check_sub:{keyword}")]
            ])
            await message.answer(
                f"Вы запросили материал: «<b>{magnet['title']}</b>».\n\n"
                f"Чтобы скачать его, подпишитесь на мой Telegram-канал. Каждую неделю я публикую там разборы реальных диалогов агентов:\n\n"
                f"👉 <a href='{config.CHANNEL_LINK}'>Канал Антона Цоя</a>\n\n"
                f"Подписались? Жмите кнопку ниже:",
                parse_mode="HTML",
                reply_markup=sub_kb
            )
        return

    # Логика обработки ответов Администратора (Антона)
    if message.from_user.id == config.ADMIN_ID:
        if message.reply_to_message:
            reply_text = message.reply_to_message.text or message.reply_to_message.caption
            if reply_text:
                match = re.search(r"🆔 ID пользователя:\s*(\d+)", reply_text)
                if match:
                    user_id = int(match.group(1))
                    try:
                        # Отправляем сообщение обратно агенту
                        await bot.send_message(chat_id=user_id, text=message.text)
                        await message.reply(f"✅ Ответ успешно отправлен агенту (ID: {user_id})")
                    except Exception as e:
                        await message.reply(f"❌ Не удалось отправить ответ: {e}")
                    return
        return

    # Если пользователь находится в режиме ввода вопроса или просто шлет сообщение
    current_state = await state.get_state()
    
    # Формируем карточку пересылки для Антона
    forward_header = (
        f"✉️ <b>Новое сообщение от агента в боте</b>\n\n"
        f"👤 <b>Имя:</b> {message.from_user.full_name}\n"
        f"✈️ <b>Юзернейм:</b> @{message.from_user.username or 'нет'}\n"
        f"🆔 <b>ID пользователя:</b> <code>{message.from_user.id}</code>\n\n"
        f"💬 <b>Текст сообщения:</b>\n<i>{message.text}</i>\n\n"
        f"👉 <i>Чтобы ответить, сделайте <b>Reply (Ответить)</b> на это сообщение.</i>"
    )
    
    try:
        await bot.send_message(chat_id=config.ADMIN_ID, text=forward_header, parse_mode="HTML")
        
        # Если агент отправлял вопрос целенаправленно из меню
        if current_state == SupportState.chatting:
            await state.clear()
            await message.answer(
                "Ваше сообщение отправлено Антону. Он ответит вам прямо в этом чате в ближайшее время.",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer("Сообщение переслано Антону. Ожидайте ответа прямо здесь.")
            
    except Exception as e:
        logger.error(f"Ошибка пересылки сообщения админу: {e}")
        await message.answer("Произошла ошибка при отправке сообщения. Попробуйте связаться позже.")

# Пересылка медиафайлов (голосовые, аудио, документы)
@router.message(F.voice | F.audio | F.document)
async def handle_media_messages(message: Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()
    if current_state in [
        LeadForm.waiting_for_goal.state,
        LeadForm.waiting_for_dp.state,
        LeadForm.waiting_for_payment.state,
        LeadForm.waiting_for_contact.state
    ]:
        await message.answer("⚠️ Пожалуйста, завершите расчет или отправьте номер телефона для продолжения.")
        return

    if message.from_user.id == config.ADMIN_ID:
        # Если админ отвечает файлом/голосовым
        if message.reply_to_message:
            reply_text = message.reply_to_message.text or message.reply_to_message.caption
            if reply_text:
                match = re.search(r"🆔 ID пользователя:\s*(\d+)", reply_text)
                if match:
                    user_id = int(match.group(1))
                    try:
                        # Копируем медиафайл пользователю
                        await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
                        await message.reply(f"✅ Медиафайл отправлен пользователю (ID: {user_id})")
                    except Exception as e:
                        await message.reply(f"❌ Ошибка отправки медиафайла: {e}")
                    return
        return

    # От пользователя к админу
    current_state = await state.get_state()
    media_type = "аудиозапись/файл"
    if message.voice:
        media_type = "голосовое сообщение"
    elif message.audio:
        media_type = f"аудиофайл '{message.audio.title or ''}'"
        
    forward_header = (
        f"✉️ <b>Новый медиафайл от агента в боте</b>\n\n"
        f"👤 <b>Имя:</b> {message.from_user.full_name}\n"
        f"✈️ <b>Юзернейм:</b> @{message.from_user.username or 'нет'}\n"
        f"🆔 <b>ID пользователя:</b> <code>{message.from_user.id}</code>\n"
        f"📁 <b>Тип медиа:</b> {media_type}\n\n"
        f"👉 <i>Чтобы ответить, сделайте <b>Reply (Ответить)</b> на пересылаемый следом файл.</i>"
    )
    
    try:
        # Сначала шлем заголовок
        await bot.send_message(chat_id=config.ADMIN_ID, text=forward_header, parse_mode="HTML")
        # Следом копируем медиафайл админу
        await bot.copy_message(chat_id=config.ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
        
        if current_state == SupportState.chatting:
            await state.clear()
            await message.answer(
                "Файл передан Антону Цою. Он прослушает его и пришлет обратную связь прямо сюда!",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer("Файл отправлен Антону.")
            
    except Exception as e:
        logger.error(f"Ошибка пересылки медиафайла админу: {e}")
        await message.answer("Не удалось отправить файл. Попробуйте еще раз.")

# --- ФОНОВЫЙ ШЕДУЛЕР DRIP-КАМПАНИИ ---

async def drip_scheduler_loop(bot: Bot):
    """Бесконечный цикл проверки очереди drip_schedule."""
    logger.info("Фоновый шедулер автодогрева запущен.")
    while True:
        try:
            pending = db.get_pending_drips()
            for drip_id, user_id, msg_type in pending:
                if msg_type == "quiz_invite":
                    try:
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="📝 Начать экспресс-тест", callback_data="start_quiz_drip")]
                        ])
                        text = (
                            "Привет! Вчера ты скачал полезный материал. Уверен, он уже помогает в работе. 📈\n\n"
                            "Чтобы точно понять, на каком этапе ты теряешь до 70% клиентов на старте, "
                            "пройди быстрый тест из 10 вопросов. Это займет всего 3 минуты, а пользы — на миллионы комиссионных!\n\n"
                            "<b>Готов проверить свои навыки первого контакта?</b>"
                        )
                        await bot.send_message(
                            chat_id=user_id,
                            text=text,
                            parse_mode="HTML",
                            reply_markup=kb
                        )
                        db.update_drip_status(drip_id, "sent")
                        logger.info(f"Drip-сообщение quiz_invite отправлено пользователю {user_id}")
                    except TelegramForbiddenError:
                        db.update_drip_status(drip_id, "blocked")
                        logger.warning(f"Пользователь {user_id} заблокировал бота. Статус изменен.")
                    except TelegramAPIError as e:
                        db.update_drip_status(drip_id, "failed")
                        logger.error(f"API Error sending drip to {user_id}: {e}")
                    except Exception as e:
                        db.update_drip_status(drip_id, "failed")
                        logger.error(f"Неожиданная ошибка рассылки drip к {user_id}: {e}")
                await asyncio.sleep(0.1) # Пауза между отправками
        except Exception as e:
            logger.error(f"Ошибка в цикле фонового шедулера: {e}")
        
        await asyncio.sleep(60) # Проверка каждую минуту

# --- ЗАПУСК БОТА ---

async def main():
    # Инициализация БД
    db.init_db()
    
    # Чтение прокси из переменной окружения
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        session = AiohttpSession(proxy=proxy_url)
        bot = Bot(token=config.BOT_TOKEN, session=session)
        logger.info(f"Запуск бота с прокси: {proxy_url}")
    else:
        bot = Bot(token=config.BOT_TOKEN)
        
    dp = Dispatcher()
    dp.include_router(router)
    
    # Запуск фонового шедулера drip-кампаний в asyncio task
    asyncio.create_task(drip_scheduler_loop(bot))
    
    logger.info("Главный бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
