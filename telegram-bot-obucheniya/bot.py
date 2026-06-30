"""Основной файл Telegram-бота для обучения агентов «Среда обучения 2.0»."""
import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import config
import db
import lessons

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bot")

# Состояния для машины состояний
class RegistrationStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()

class HomeworkStates(StatesGroup):
    waiting_for_homework = State()

class CuratorStates(StatesGroup):
    entering_rejection_reason = State()

class BookingStates(StatesGroup):
    choosing_building = State()
    entering_apartment_info = State()
    entering_customer_name = State()
    entering_customer_phone = State()

class AdminStates(StatesGroup):
    choosing_broadcast_type = State()
    entering_broadcast_message = State()

# Инициализация бота с поддержкой HTML по умолчанию
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Reply-клавиатура главного меню с поддержкой Telegram Web App (TWA)
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎓 Открыть обучение", web_app=types.WebAppInfo(url=config.TWA_URL))
    builder.button(text="🏠 Бронирование")
    builder.button(text="❓ Поддержка")
    builder.adjust(1, 2)
    return builder.as_markup(resize_keyboard=True)

# Проверка прав администратора
def is_admin(user_id: int) -> bool:
    return config.is_admin(user_id)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработка команды /start"""
    user_id = message.from_user.id
    
    # Проверяем, существует ли пользователь
    user = await db.get_user(user_id)
    
    if not user:
        # Новый пользователь - запускаем регистрацию по ТЗ
        await state.clear()
        
        reply_builder = ReplyKeyboardBuilder()
        reply_builder.button(text="📱 Поделиться номером телефона", request_contact=True)
        
        await message.answer(
            "👋 <b>Добро пожаловать в систему обучения агентов СРЕДА 2.0!</b>\n\n"
            "Этот бот поможет вам освоить методологию «Агент-Навигатор» и автоматизировать вашу работу с новостройками.\n\n"
            "Для начала регистрации, пожалуйста, поделитесь номером телефона, нажав на кнопку ниже:",
            reply_markup=reply_builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
        )
        await state.set_state(RegistrationStates.waiting_for_phone)
        return
    
    # Существующий пользователь
    inline_builder = InlineKeyboardBuilder()
    inline_builder.button(text="🎓 Открыть Среду Обучения", web_app=types.WebAppInfo(url=config.TWA_URL))
    
    await message.answer(
        f"👋 <b>С возвращением, {user['full_name']}!</b>\n\n"
        "Рады видеть вас снова. Нажмите кнопку ниже, чтобы открыть обучение в Web App:",
        reply_markup=inline_builder.as_markup()
    )
    
    await message.answer("Или используйте меню ниже:", reply_markup=get_main_keyboard())

# Шаг 1 регистрации: Получение телефона
@dp.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    """Получение телефона"""
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        # Базовая проверка
        phone = message.text.strip()
    
    if not phone:
        await message.answer("Пожалуйста, нажмите на кнопку <b>📱 Поделиться номером телефона</b> или отправьте номер текстом.")
        return
        
    await state.update_data(phone=phone)
    await message.answer(
        "Спасибо! Теперь, пожалуйста, отправьте ваши <b>Имя и Фамилию</b> текстом (например: Иван Петров):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(RegistrationStates.waiting_for_name)

# Шаг 2 регистрации: Получение имени и финал
@dp.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Получение имени и завершение регистрации"""
    full_name = message.text.strip()
    
    if len(full_name) < 3 or " " not in full_name:
        await message.answer("Пожалуйста, введите корректные Имя и Фамилию (через пробел):")
        return
        
    data = await state.get_data()
    phone = data.get("phone")
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    # Создаем пользователя в БД
    await db.create_user(
        user_id=user_id,
        username=username,
        full_name=full_name,
        phone=phone
    )
    # На всякий случай обновляем поля, если юзер уже был в INSERT OR IGNORE
    await db.update_user_name(user_id, full_name)
    await db.update_user_phone(user_id, phone)
    await db.update_user_status(user_id, "active")
    await db.update_user_block(user_id, 1)
    await db.update_user_lesson(user_id, "1.1")
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Регистрация успешно завершена, {full_name}!</b>\n\n"
        "Вы получили доступ к обучающим блокам «Методичка 2.0». Вам доступно постоянное меню внизу экрана.\n\n"
        "Рекомендуем проходить обучение через наш интерактивный Web App!",
        reply_markup=get_main_keyboard()
    )
    
    # Сразу предлагаем открыть курс в Web App
    inline_builder = InlineKeyboardBuilder()
    inline_builder.button(text="🎓 Открыть Среду Обучения", web_app=types.WebAppInfo(url=config.TWA_URL))
    
    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть первый урок и оцифровать Точку А в Web App:",
        reply_markup=inline_builder.as_markup()
    )

def is_menu_button(text: str) -> bool:
    return text in ["🎓 Открыть обучение", "🏠 Бронирование", "❓ Поддержка"]
@dp.callback_query(F.data.regexp(r"^script_help_(\d)$"))
async def callback_script_help(callback: types.CallbackQuery):
    """Показать помощь по скрипту"""
    block = int(callback.data.split("_")[2])
    help_text = lessons.get_homework_script_help(block)
    
    if help_text:
        await callback.message.answer(help_text)
    await callback.answer()

# Автоматический прием голосовых ДЗ вне FSM-состояния
@dp.message(F.voice | F.audio)
async def handle_voice_homework(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        return
        
    # Проверяем, что нет активного состояния FSM (например, бронирование или регистрация)
    current_state = await state.get_state()
    if current_state is not None:
        return
        
    status = user["status"]
    block = user["current_block"]
    
    # Голосовые домашние задания требуются только для блоков 1 и 4
    hw_type = lessons.get_homework_type(block)
    
    if status == "active" and hw_type == "voice" and block <= 6:
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        
        # 1. Сохраняем в БД
        hw_id = await db.create_homework(user_id, block, "voice", file_id)
        # 2. Обновляем статус
        await db.update_user_status(user_id, "awaiting_review")
        
        # 3. Отправляем куратору
        curator_builder = InlineKeyboardBuilder()
        curator_builder.button(text="✅ Одобрить", callback_data=f"approve_hw_{hw_id}")
        curator_builder.button(text="❌ Отклонить", callback_data=f"reject_hw_{hw_id}")
        curator_builder.adjust(2)
        
        caption_text = (
            f"🔔 <b>Новое ДЗ по Блоку {block} (голосовое)!</b>\n\n"
            f"👤 <b>Студент:</b> {user['full_name']} (@{user['username'] or 'нет'})\n"
            f"🎙️ <b>Формат:</b> Голосовое сообщение"
        )
        
        try:
            await bot.send_voice(
                chat_id=config.CURATOR_CHAT_ID,
                voice=file_id,
                caption=caption_text,
                reply_markup=curator_builder.as_markup()
            )
        except Exception as e:
            logger.error(f"Ошибка при пересылке аудио куратору: {e}")
            await bot.send_message(
                chat_id=config.ADMIN_IDS[0],
                text=f"{caption_text}\n\n⚠️ Не удалось переслать аудио в групповой чат кураторов."
            )
            await bot.send_voice(chat_id=config.ADMIN_IDS[0], voice=file_id, reply_markup=curator_builder.as_markup())
            
        await message.answer(
            "✅ <b>Ваше голосовое домашнее задание принято на проверку куратором.</b>\n\n"
            "Вы можете следить за статусом проверки в Web App. Обычно проверка занимает не более 4 часов.",
            reply_markup=get_main_keyboard()
        )
    else:
        # Если статус ожидания проверки или ДЗ текстовое
        if status == "awaiting_review":
            await message.answer(
                "⏳ <b>Ваше задание уже на проверке.</b>\n\n"
                "Ожидайте ответа куратора перед отправкой новых материалов."
            )
        elif hw_type == "text" and status == "active":
            await message.answer(
                "⚠️ <b>Для текущего блока требуется текстовое ДЗ.</b>\n\n"
                "Пожалуйста, откройте Web App и введите ответ в поле задания."
            )
        else:
            await message.answer(
                "🎙️ Спасибо за голосовое сообщение! Если у вас есть вопросы по обучению, напишите куратору @anton_tsoy."
            )

# Callback-обработчик куратора: Одобрить ДЗ
@dp.callback_query(F.data.regexp(r"^approve_hw_(\d+)$"))
async def callback_curator_approve(callback: types.CallbackQuery):
    """Одобрение ДЗ куратором"""
    hw_id = int(callback.data.split("_")[2])
    hw = await db.get_homework(hw_id)
    
    if not hw:
        await callback.answer("Задание не найдено", show_alert=True)
        return
        
    if hw["status"] != "pending":
        await callback.answer("Это задание уже проверено!", show_alert=True)
        return
        
    # 1. Обновляем статус ДЗ в базе
    await db.approve_homework(hw_id)
    
    student_id = hw["user_id"]
    old_block = hw["block_number"]
    new_block = old_block + 1
    
    # 2. Обновляем статус ученика
    if new_block > 6:
        # Курс полностью завершен
        await db.update_user_status(student_id, "completed")
        await db.update_user_block(student_id, 7)
        
        # Уведомляем студента
        try:
            await bot.send_message(
                chat_id=student_id,
                text="🎉 <b>Поздравляем! Ваше финальное домашнее задание одобрено куратором!</b>\n\n"
                     "Вы успешно завершили программу обучения «Агент-Навигатор 2.0» и прошли весь курс! 🎓\n"
                     "Теперь вы являетесь сертифицированным навигатором. Успешных вам сделок!"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление студенту: {e}")
    else:
        # Открываем следующий блок
        await db.update_user_status(student_id, "active")
        await db.update_user_block(student_id, new_block)
        await db.update_user_lesson(student_id, f"{new_block}.1")
        
        # Уведомляем студента и шлем первый урок нового блока
        try:
            await bot.send_message(
                chat_id=student_id,
                text=f"🎉 <b>Ваше домашнее задание по Блоку {old_block} одобрено куратором!</b>\n\n"
                     f"Вам открыт следующий блок обучения."
            )
            # Автоматическая отправка первого урока нового блока
            content = lessons.get_lesson_content(new_block, 1)
            builder = InlineKeyboardBuilder()
            builder.button(text=f"▶️ Перейти к уроку {new_block}.2", callback_data=f"show_lesson_{new_block}_2")
            await bot.send_message(chat_id=student_id, text=content, reply_markup=builder.as_markup())
        except Exception as e:
            logger.error(f"Не удалось отправить урок студенту: {e}")
            
    # 3. Обновляем сообщение в чате кураторов
    curator_name = callback.from_user.full_name
    
    if callback.message.caption:
        new_caption = f"✅ <b>ДЗ ОДОБРЕНО куратором {curator_name}</b>\n\n{callback.message.caption}"
        await callback.message.edit_caption(caption=new_caption, reply_markup=None)
    else:
        new_text = f"✅ <b>ДЗ ОДОБРЕНО куратором {curator_name}</b>\n\n{callback.message.text}"
        await callback.message.edit_text(text=new_text, reply_markup=None)
        
    await callback.answer("Задание успешно одобрено!")

# Callback-обработчик куратора: Отклонить ДЗ (Запрос причины)
@dp.callback_query(F.data.regexp(r"^reject_hw_(\d+)$"))
async def callback_curator_reject(callback: types.CallbackQuery, state: FSMContext):
    """Клик на Отклонить - запрос причины отклонения"""
    hw_id = int(callback.data.split("_")[2])
    hw = await db.get_homework(hw_id)
    
    if not hw:
        await callback.answer("Задание не найдено", show_alert=True)
        return
        
    if hw["status"] != "pending":
        await callback.answer("Это задание уже проверено!", show_alert=True)
        return
        
    await state.update_data(hw_id=hw_id, curator_message_id=callback.message.message_id)
    await callback.message.answer(
        f"✍️ <b>Введите причину отклонения ДЗ для студента {hw['full_name']}:</b>\n"
        "(комментарий будет отправлен студенту в чат)"
    )
    await state.set_state(CuratorStates.entering_rejection_reason)
    await callback.answer()

# Ввод куратором причины отклонения
@dp.message(CuratorStates.entering_rejection_reason)
async def process_rejection_reason(message: types.Message, state: FSMContext):
    """Обработка причины отклонения от куратора"""
    comment = message.text.strip()
    data = await state.get_data()
    hw_id = data.get("hw_id")
    curator_message_id = data.get("curator_message_id")
    
    hw = await db.get_homework(hw_id)
    if not hw:
        await message.answer("Ошибка: ДЗ не найдено.")
        await state.clear()
        return
        
    # 1. Меняем статус ДЗ в базе
    await db.reject_homework(hw_id, comment)
    
    student_id = hw["user_id"]
    block = hw["block_number"]
    
    # 2. Возвращаем студента в режим active (но он остается на том же блоке и уроке X.2)
    await db.update_user_status(student_id, "active")
    
    # Отправляем сообщение студенту
    try:
        await bot.send_message(
            chat_id=student_id,
            text=f"⚠️ <b>Ваше домашнее задание по Блоку {block} было отклонено куратором.</b>\n\n"
                 f"💬 <b>Комментарий куратора:</b>\n<blockquote>{comment}</blockquote>\n\n"
                 "Пожалуйста, выполните требования куратора и отправьте домашнее задание заново."
        )
    except Exception as e:
        logger.error(f"Не удалось отправить отказ студенту: {e}")
        
    # 3. Обновляем исходное сообщение в чате кураторов
    curator_name = message.from_user.full_name
    
    try:
        # Нам нужно достать сообщение по curator_message_id
        # Пробуем отредактировать
        new_caption_or_text = f"❌ <b>ДЗ ОТКЛОНЕНО куратором {curator_name}</b>\n💬 Причина: {comment}\n\n"
        
        # Так как мы не знаем наверняка, текстовое это или аудиосообщение, пробуем отредактировать caption или text
        # Проще всего отправить новое уведомление в этот же чат, но красивее убрать кнопки.
        # В aiogram можно отредактировать разметку сообщения без текста:
        await bot.edit_message_reply_markup(
            chat_id=config.CURATOR_CHAT_ID,
            message_id=curator_message_id,
            reply_markup=None
        )
        
        # Дополнительно пишем в чат о статусе
        await bot.send_message(
            chat_id=config.CURATOR_CHAT_ID,
            text=f"❌ ДЗ студента {hw['full_name']} по Блоку {block} отклонено куратором {curator_name}.\nКомментарий: <i>{comment}</i>"
        )
    except Exception as e:
        logger.error(f"Не удалось отредактировать сообщение кураторов: {e}")
        
    await message.answer("✅ Комментарий сохранен и успешно отправлен студенту.")
    await state.clear()


# ==========================================
# ОСТАВШИЕСЯ ФУНКЦИИ ИЗ СТАРОЙ ВЕРСИИ БОТА (ДЛЯ СОВМЕСТИМОСТИ И БРОНИРОВАНИЙ)
# ==========================================

# Обработчик кнопки бронирования
@dp.message(F.text == "🏠 Бронирование")
async def booking_menu_message(message: types.Message, state: FSMContext):
    """Показ меню бронирования через Reply"""
    await state.clear()
    await show_booking_menu_text(message)

# Обработчик кнопки поддержки
@dp.message(F.text == "❓ Поддержка")
async def support_message(message: types.Message, state: FSMContext):
    """Показ контактов поддержки"""
    await state.clear()
    await message.answer(
        "❓ <b>Поддержка и контакты</b>\n\n"
        "По всем техническим вопросам работы бота, сложностям с прохождением уроков или сдачей домашних заданий пишите напрямую куратору: @anton_tsoy.\n\n"
        "Отвечаем в течение рабочего дня.",
        reply_markup=get_main_keyboard()
    )

async def show_booking_menu_text(message: types.Message):
    builder = InlineKeyboardBuilder()
    for building_code, building_info in config.BUILDINGS.items():
        builder.button(text=f"🏢 {building_info['name']}", callback_data=f"building_{building_code}")
    builder.button(text="📝 Мои бронирования", callback_data="my_bookings")
    builder.adjust(1)
    await message.answer(
        "<b>🏠 Бронирование новостроек:</b>\n\nВы можете забронировать объекты для клиентов. Выберите новостройку из списка:",
        reply_markup=builder.as_markup()
    )

# Ниже методы бронирования из старого bot.py для совместимости
@dp.callback_query(F.data == "booking_menu")
async def booking_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await show_booking_menu_text(callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("building_"))
async def select_building(callback: types.CallbackQuery, state: FSMContext):
    building_code = callback.data.split("_")[1]
    building_info = config.BUILDINGS.get(building_code)
    
    if not building_info:
        await callback.answer("Новостройка не найдена", show_alert=True)
        return
        
    await state.update_data(building_code=building_code)
    await callback.message.answer(
        f"<b>🏢 {building_info['name']}</b>\n\n"
        f"💰 Цена от: {building_info['price_from']}\n"
        f"📍 {building_info['location']}\n\n"
        f"{building_info['description']}\n\n"
        "Пожалуйста, введите информацию о квартире, которую хотите забронировать:\n"
        "(номер, этаж, площадь, планировка и т.д.)"
    )
    await state.set_state(BookingStates.entering_apartment_info)
    await callback.answer()

@dp.message(BookingStates.entering_apartment_info)
async def process_apartment_info(message: types.Message, state: FSMContext):
    await state.update_data(apartment_info=message.text)
    await message.answer("Отлично! Теперь введите <b>имя клиента</b>, для которого делается бронирование:")
    await state.set_state(BookingStates.entering_customer_name)

@dp.message(BookingStates.entering_customer_name)
async def process_customer_name(message: types.Message, state: FSMContext):
    await state.update_data(customer_name=message.text)
    await message.answer("Отлично! Теперь введите <b>телефон клиента</b> в формате +7XXXYYYZZZZ:")
    await state.set_state(BookingStates.entering_customer_phone)

@dp.message(BookingStates.entering_customer_phone)
async def process_customer_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    
    await db.create_booking(
        user_id=user_id,
        building_code=data["building_code"],
        apartment_info=data["apartment_info"],
        customer_name=data["customer_name"],
        customer_phone=message.text
    )
    
    building_info = config.BUILDINGS.get(data["building_code"])
    
    await message.answer(
        f"✅ <b>Бронирование успешно создано!</b>\n\n"
        f"🏢 Новостройка: {building_info['name']}\n"
        f"📝 Квартира: {data['apartment_info']}\n"
        f"👤 Клиент: {data['customer_name']}\n"
        f"📞 Телефон: {message.text}\n\n"
        f"С вами свяжется менеджер для подтверждения бронирования.",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

@dp.callback_query(F.data == "my_bookings")
async def show_my_bookings(callback: types.CallbackQuery):
    bookings = await db.get_user_bookings(callback.from_user.id)
    if not bookings:
        text = "<b>📝 Мои бронирования:</b>\n\nУ вас пока нет бронирований."
    else:
        text = "<b>📝 Мои бронирования:</b>\n\n"
        for booking in bookings:
            building_code = booking[2]
            building_info = config.BUILDINGS.get(building_code, {})
            text += f"🏢 {building_info.get('name', building_code)}\n"
            text += f"📝 {booking[3]}\n"
            text += f"👤 {booking[4]}\n"
            text += f"📞 {booking[5]}\n"
            text += f"📊 Статус: {booking[6]}\n\n"
            
    await callback.message.answer(text, reply_markup=get_main_keyboard())
    await callback.answer()

# Административные функции (сохранено с адаптацией под Среду 2.0)
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Команда доступна только администраторам.")
        return
        
    total_users = await db.count_users()
    
    text = (
        f"🔐 <b>Админ-панель СРЕДА 2.0</b>\n\n"
        f"👥 Всего учеников зарегистрировано: {total_users}\n\n"
        f"Выберите раздел:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Список учеников", callback_data="admin_users")
    builder.button(text="📊 Прогресс по блокам", callback_data="admin_progress")
    builder.button(text="🏠 Бронирования", callback_data="admin_bookings")
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
        
    users = await db.get_all_users()
    text = "<b>👥 Список учеников:</b>\n\n"
    for user in users[:20]:
        user_id, username, full_name, is_premium, created_at = user
        # Для обратной совместимости или если имя пустое
        name_display = full_name if full_name else f"Юзер {user_id}"
        text += f"👤 {name_display} (@{username or 'нет'})\n"
        text += f"   ID: {user_id} | Рег: {created_at[:10]}\n\n"
        
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="admin_panel")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "admin_progress")
async def admin_progress(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
        
    # Возвращаем общую статистику
    progress = await db.get_progress_overview()
    text = "<b>📊 Прогресс по блокам:</b>\n\n"
    for row in progress:
        module_id, completions, avg_score = row
        module_info = config.MODULES.get(module_id, {})
        text += f"📚 {module_info.get('title', f'Блок {module_id}')}\n"
        text += f"   ✅ Пройдено учениками: {completions}\n\n"
        
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="admin_panel")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "admin_bookings")
async def admin_bookings(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
        
    bookings = await db.get_recent_bookings()
    text = "<b>🏠 Недавние бронирования:</b>\n\n"
    for booking in bookings[:10]:
        booking_id, user_id, building_code, apartment_info, customer_name, customer_phone, status, created_at, agent_name = booking
        building_info = config.BUILDINGS.get(building_code, {})
        text += f"🏢 {building_info.get('name', building_code)}\n"
        text += f"👤 Клиент: {customer_name} (Агент: {agent_name})\n"
        text += f"📞 {customer_phone} | Статус: {status}\n\n"
        
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="admin_panel")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "admin_panel")
async def back_to_admin_panel(callback: types.CallbackQuery):
    total_users = await db.count_users()
    text = (
        f"🔐 <b>Админ-панель СРЕДА 2.0</b>\n\n"
        f"👥 Всего учеников зарегистрировано: {total_users}\n\n"
        f"Выберите раздел:"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Список учеников", callback_data="admin_users")
    builder.button(text="📊 Прогресс по блокам", callback_data="admin_progress")
    builder.button(text="🏠 Бронирования", callback_data="admin_bookings")
    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# --- КЛАССЫ СОСТОЯНИЙ ДЛЯ НОВОГО ФУНКЦИОНАЛА ---

class CalcStates(StatesGroup):
    waiting_for_price = State()
    waiting_for_down_payment = State()

class QuizStates(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ РАСЧЕТОВ И RAG ---

def calculate_annuity(principal, rate_annual, term_months):
    """Метод аннуитетных расчетов"""
    if principal <= 0 or term_months <= 0:
        return 0.0
    if rate_annual <= 0:
        return round(principal / term_months, 2)
    r = rate_annual / 12 / 100
    payment = principal * (r * (1 + r)**term_months) / ((1 + r)**term_months - 1)
    return round(payment, 2)

def call_gemini_api(prompt, system_instruction=None):
    """Прямой HTTP-запрос к Gemini API"""
    import requests
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={config.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [
                {"text": system_instruction}
            ]
        }
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    res_data = response.json()
    return res_data["candidates"][0]["content"]["parts"][0]["text"]

def search_local_obsidian(query: str, search_path: str = "/Users/anton_tsoy/Desktop/Обсидиан/6. обучения агентов") -> List[Dict]:
    """Локальный поиск по файлам Obsidian в Уфе по ключевым словам"""
    import glob
    import re
    if not os.path.exists(search_path):
        # Если папка переименована, попробуем поискать относительно корня workspace
        alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "6. обучения агентов")
        if os.path.exists(alt_path):
            search_path = alt_path
        else:
            return []
        
    words = [w.lower() for w in re.findall(r'[а-яА-Яa-zA-Z0-9]+', query) if len(w) > 2]
    stop_words = {"как", "что", "это", "для", "или", "если", "при", "был", "всей", "всех", "под", "над"}
    words = [w for w in words if w not in stop_words]
    
    if not words:
        return []
        
    chunks = []
    for filepath in glob.glob(os.path.join(search_path, "**/*.md"), recursive=True):
        if ".obsidian" in filepath or ".git" in filepath:
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            paragraphs = content.split("\n\n")
            filename = os.path.basename(filepath)
            for p in paragraphs:
                p_clean = p.strip()
                if len(p_clean) < 40:
                    continue
                score = 0
                for word in words:
                    matches = len(re.findall(r'\b' + re.escape(word) + r'\b', p_clean.lower()))
                    score += matches * 2
                    if word in p_clean.lower():
                        score += 1
                if score > 0:
                    chunks.append({
                        "filename": filename,
                        "text": p_clean,
                        "score": score
                    })
        except Exception:
            pass
            
    chunks.sort(key=lambda x: x["score"], reverse=True)
    return chunks[:3]

def generate_fallback_response(query: str, chunks: List[Dict]) -> str:
    """Заглушка ответа ИИ в ToV"""
    if not chunks:
        return (
            "🤖 **ИИ-Навигатор (Инфорежим):**\n\n"
            "Привет, коллега! Я пока не нашел точного совпадения по этой теме в файлах Obsidian.\n"
            "Напомню наше золотое правило: сначала **Финансы (бюджет и платеж)**, потом **Локация**, потом **ЖК**, и только в конце — **Квартира**.\n\n"
            "💡 *Для включения полноценного ИИ-синтеза, укажите действующий GEMINI_API_KEY в файле .env.*"
        )
    top_chunk = chunks[0]
    return (
        f"🤖 **ИИ-Навигатор (Найдено в Obsidian — {top_chunk['filename']}):**\n\n"
        f"{top_chunk['text']}\n\n"
        f"💡 *Интеграция работает по локальному индексу базы знаний.*"
    )

def answer_question_rag_sync(user_id: int, query: str) -> Tuple[str, List[str]]:
    """Логика RAG: поиск в Obsidian + генерация в Gemini"""
    import json
    from typing import Tuple
    chunks = search_local_obsidian(query)
    sources = [c["filename"] for c in chunks]
    
    context = ""
    if chunks:
        context = "\n\n".join([f"Файл: {c['filename']}\n{c['text']}" for c in chunks])
        
    system_instruction = (
        "Ты — ИИ-коуч в роли Антона Цоя. Твой ToV: прямо, по делу, без пафоса и давления. "
        "Помогай агентам решать задачи по недвижимости и объяснять клиентам сложные финансовые выгоды (рассрочки, транши, субсидии)."
    )
    
    prompt = f"Вопрос агента: {query}\n\n"
    if context:
        prompt += f"Контекст из базы знаний Obsidian:\n{context}\n\nСформулируй ответ на русском языке."
    else:
        prompt += "Ответь кратко на вопрос на основе методологии Навигатора."
        
    response_text = ""
    if config.GEMINI_API_KEY:
        try:
            response_text = call_gemini_api(prompt, system_instruction)
        except Exception as e:
            logger.error(f"Gemini API Call error: {e}")
            response_text = generate_fallback_response(query, chunks)
    else:
        response_text = generate_fallback_response(query, chunks)
        
    # Запуск асинхронной записи лога в базу данных
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(db.log_ai_chat(user_id, query, response_text, json.dumps(sources, ensure_ascii=False)))
    except Exception:
        pass
        
    return response_text, sources


# --- ОБРАБОТЧИКИ НОВЫХ КОМАНД БОТА ---

# 1. Интерактивный калькулятор (/calc)
@dp.message(Command("calc"))
async def cmd_calc(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🧮 <b>Финансовый Калькулятор Навигатора</b>\n\nВведите общую стоимость квартиры в рублях (например: 8000000):")
    await state.set_state(CalcStates.waiting_for_price)

@dp.message(CalcStates.waiting_for_price)
async def process_calc_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(" ", "").strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительное число стоимости:")
        return
        
    await state.update_data(price=price)
    await message.answer("Отлично. Теперь введите сумму первоначального взноса в рублях (например: 1500000):")
    await state.set_state(CalcStates.waiting_for_down_payment)

@dp.message(CalcStates.waiting_for_down_payment)
async def process_calc_dp(message: types.Message, state: FSMContext):
    try:
        dp_val = float(message.text.replace(" ", "").strip())
        if dp_val < 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительное число первоначального взноса:")
        return
        
    data = await state.get_data()
    price = data["price"]
    
    if dp_val >= price:
        await message.answer("Первоначальный взнос не может быть больше или равен стоимости лота! Введите взнос заново:")
        return
        
    await state.clear()
    
    # Расчет параметров
    loan = price - dp_val
    term_months = 360 # 30 лет
    
    payment_std = calculate_annuity(loan, 18.0, term_months)
    payment_sub = calculate_annuity(loan * 1.15, 6.0, term_months) # Субсидия: 15% удорожание, ставка 6%
    payment_tr1 = calculate_annuity(loan * 0.15, 6.0, term_months) # Трашн 1: 15% от кредита до сдачи
    payment_tr2 = calculate_annuity(loan, 6.0, term_months - 24) # Транш 2: через 24 мес.
    
    ans = (
        f"📊 <b>Результаты расчета (Стоимость: {price:,.0f} ₽, Взнос: {dp_val:,.0f} ₽)</b>\n\n"
        f"🔴 <b>1. Стандартная ипотека (18%):</b>\n"
        f"   • Платеж: <b>{payment_std:,.2f} ₽/мес.</b>\n"
        f"   • Сумма кредита: {loan:,.0f} ₽\n\n"
        f"🟢 <b>2. Субсидия (6% + удорожание 15%):</b>\n"
        f"   • Платеж: <b>{payment_sub:,.2f} ₽/мес.</b>\n"
        f"   • Кредит с удорожанием: {loan*1.15:,.0f} ₽\n"
        f"   • Экономия в месяц: <b>{(payment_std - payment_sub):,.2f} ₽</b>\n\n"
        f"🔵 <b>3. Траншевая ипотека (6% до сдачи):</b>\n"
        f"   • В первые 2 года: <b>{payment_tr1:,.2f} ₽/мес.</b> (кредит на транш {loan*0.15:,.0f} ₽)\n"
        f"   • После сдачи: <b>{payment_tr2:,.2f} ₽/мес.</b> (кредит на полную сумму)\n"
    )
    await message.answer(ans, reply_markup=get_main_keyboard())


# 2. ИИ-помощник (/ask)
@dp.message(Command("ask"))
async def cmd_ask(message: types.Message):
    query = message.text[len("/ask "):].strip()
    if not query:
        await message.answer("Используйте команду в формате: `/ask [ваш вопрос]` (например: `/ask как отработать депозит` или `/ask правила очередности`)")
        return
        
    waiting_msg = await message.answer("🤖 <i>ИИ-Навигатор анализирует базу знаний Obsidian...</i>")
    
    # Запуск RAG-поиска
    response, sources = answer_question_rag_sync(message.from_user.id, query)
    
    source_text = ""
    if sources:
        source_text = f"\n\n📂 <b>Источники:</b> " + ", ".join(sources)
        
    await waiting_msg.edit_text(response + source_text)


# 3. Витрина лотов (/lots)
@dp.message(Command("lots"))
async def cmd_lots(message: types.Message):
    lots = await db.get_all_lots()
    if not lots:
        # Если лотов в базе нет, добавляем демо-лоты для прототипа
        await db.create_lot("ЖК Центральный парк, 2-комн", "ГлавЗастройщик", "2-к", 60.5, 9500000, "", True)
        await db.create_lot("ЖК Уфимский Кремль, Студия", "РегионДевелопмент", "Студия", 28.0, 5200000, "", False)
        lots = await db.get_all_lots()
        
    text = "🏠 <b>Уникальные лоты и спецпредложения:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for lot in lots:
        uniq = "💎 [ЭКСКЛЮЗИВ] " if lot["is_unique"] else "🏢 "
        text += f"{uniq}<b>{lot['title']}</b>\n"
        text += f"   • Застройщик: {lot['developer_name']}\n"
        text += f"   • Площадь: {lot['area']} кв.м.\n"
        text += f"   • Базовая цена: <b>{lot['base_price']:,.0f} ₽</b>\n\n"
        builder.button(text=f"Забронировать {lot['title']}", callback_data=f"book_lot_{lot['id']}")
        
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("book_lot_"))
async def process_book_lot(callback: types.CallbackQuery, state: FSMContext):
    lot_id = int(callback.data.split("_")[2])
    # Переводим в состояние бронирования
    await state.clear()
    await state.update_data(building_code=f"LOT_ID_{lot_id}")
    await callback.message.answer("Запуск процесса бронирования. Введите ФИО клиента:")
    await state.set_state(BookingStates.entering_apartment_info) # Используем существующие FSM-состояния
    await callback.answer()


# 4. Мероприятия (/events)
@dp.message(Command("events"))
async def cmd_events(message: types.Message):
    events = await db.get_all_events()
    if not events:
        # Добавим демо-события
        await db.create_event("Офлайн-практикум: Финансовый инжиниринг", "Разбираем траншевые схемы и рассрочки.", "offline", "2026-07-15 18:00:00", "Конференц-зал Азимут, Уфа", 25)
        await db.create_event("Zoom-разбор: Отработка возражений 2026", "Антон Цой разбирает звонки агентов в прямом эфире.", "online", "2026-07-22 19:00:00", "https://zoom.us/j/sreda20", 100)
        events = await db.get_all_events()
        
    text = "📅 <b>Расписание мероприятий:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for ev in events:
        emoji = "👥" if ev["event_type"] == "offline" else "💻"
        text += f"{emoji} <b>{ev['title']}</b>\n"
        text += f"   • Дата: {ev['event_date']}\n"
        text += f"   • Формат: {ev['event_type'].upper()} ({ev['location']})\n"
        text += f"   • Мест: {ev['registered_count']} / {ev['max_seats']}\n\n"
        builder.button(text=f"Записаться на {ev['title']}", callback_data=f"reg_event_{ev['id']}")
        
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("reg_event_"))
async def process_reg_event(callback: types.CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    success = await db.register_for_event(event_id, callback.from_user.id)
    if success:
        await callback.message.answer("🎉 Вы успешно записались на мероприятие! Бот пришлет напоминание за 1 час до начала.")
    else:
        await callback.message.answer("⚠️ Не удалось записаться: либо вы уже зарегистрированы, либо закончились свободные места.")
    await callback.answer()


# 5. Интерактивное тестирование (/test)
@dp.message(Command("test"))
async def cmd_test(message: types.Message, state: FSMContext):
    await state.clear()
    text = (
        "✍️ <b>Диагностика знаний: Модуль Финансового Инжиниринга</b>\n\n"
        "Пройдите тест из 3 вопросов, чтобы оценить ваши навыки составления схем.\n\n"
        "<b>Вопрос 1:</b> Какое золотое правило очередности подбора лотов Навигатора?\n"
        "1. Планировка -> ЖК -> Локация -> Бюджет\n"
        "2. Бюджет (Финансы) -> Локация -> ЖК -> Планировка\n"
        "3. Локация -> Бюджет -> ЖК -> Планировка\n\n"
        "Отправьте цифру с вашим ответом (1, 2 или 3):"
    )
    await message.answer(text)
    await state.set_state(QuizStates.q1)

@dp.message(QuizStates.q1)
async def process_q1(message: types.Message, state: FSMContext):
    ans = message.text.strip()
    if ans not in ["1", "2", "3"]:
        await message.answer("Пожалуйста, введите только цифру 1, 2 или 3:")
        return
    await state.update_data(q1=ans)
    
    text = (
        "<b>Вопрос 2:</b> Что является главным преимуществом траншевой ипотеки?\n"
        "1. Полное отсутствие процентов до сдачи дома\n"
        "2. Начисление процентов только на выданную часть (транш), что снижает платеж до сдачи дома\n"
        "3. Возможность купить квартиру вообще без первоначального взноса\n\n"
        "Отправьте цифру с вашим ответом (1, 2 или 3):"
    )
    await message.answer(text)
    await state.set_state(QuizStates.q2)

@dp.message(QuizStates.q2)
async def process_q2(message: types.Message, state: FSMContext):
    ans = message.text.strip()
    if ans not in ["1", "2", "3"]:
        await message.answer("Пожалуйста, введите только цифру 1, 2 или 3:")
        return
    await state.update_data(q2=ans)
    
    text = (
        "<b>Вопрос 3:</b> В чем скрытая ловушка стратегии ожидания на депозите под 19%?\n"
        "1. Налоги съедят большую часть прибыли со вклада\n"
        "2. Рост цен на недвижимость при снижении ставок нивелирует доходность от процентов\n"
        "3. Банки заморозят депозиты при снижении ключевой ставки\n\n"
        "Отправьте цифру с вашим ответом (1, 2 или 3):"
    )
    await message.answer(text)
    await state.set_state(QuizStates.q3)

@dp.message(QuizStates.q3)
async def process_q3(message: types.Message, state: FSMContext):
    import json
    ans = message.text.strip()
    if ans not in ["1", "2", "3"]:
        await message.answer("Пожалуйста, введите только цифру 1, 2 или 3:")
        return
        
    data = await state.get_data()
    q1 = data["q1"]
    q2 = data["q2"]
    q3 = ans
    await state.clear()
    
    # Проверка ответов
    score = 0
    feedback = []
    
    if q1 == "2":
        score += 1
    else:
        feedback.append("❌ Ошибка в очередности подбора. Помни: сперва утверждаем бюджет и лимиты, а не планировки!")
        
    if q2 == "2":
        score += 1
    else:
        feedback.append("❌ Ошибка по траншевой ипотеке. Траншевая ипотека снижает платеж до сдачи за счет начисления процентов только на выданную сумму.")
        
    if q3 == "2":
        score += 1
    else:
        feedback.append("❌ Ошибка по депозитам. Рост цен на новостройки при падении ключевой ставки съедает накопленное на депозите.")
        
    # Сохраняем результат
    user_id = message.from_user.id
    passed = (score == 3)
    
    await db.save_test_result(
        user_id=user_id,
        module_id=4, # Модуль 4: Финансовый инжиниринг
        test_id=1,
        score=score / 3.0,
        is_passed=passed,
        answers=json.dumps({"q1": q1, "q2": q2, "q3": q3})
    )
    
    # Формируем ИИ-выводы
    feedback_str = "\n".join(feedback) if feedback else "🎉 Отличная работа! Все ответы верны. Вы овладели базой финансового инжиниринга."
    conclusion = (
        f"🏁 <b>Тестирование завершено! Ваш результат: {score}/3</b>\n\n"
        f"📝 <b>Анализ ошибок:</b>\n{feedback_str}\n\n"
        f"🤖 <b>Рекомендация ИИ:</b> "
    )
    if score == 3:
        conclusion += "Вы готовы применять субсидии и транши на встречах. Рекомендуем использовать команду `/calc` для расчетов с клиентами."
    elif score >= 1:
        conclusion += "Хороший результат, но есть пробелы в логике. Изучите урок 4.1 и карточки ролевых игр в Obsidian."
    else:
        conclusion += "Вам требуется повторно пройти Блок 4. Ошибки в базовой математике сделки критичны для работы Навигатора."
        
    await message.answer(conclusion, reply_markup=get_main_keyboard())


# Основная функция запуска

async def main():
    """Основная функция запуска бота"""
    if not config.is_configured():
        logger.error("Бот не настроен. Проверьте .env файл")
        return
    
    # Создаем директорию для базы данных
    os.makedirs("data", exist_ok=True)
    
    # Инициализируем базу данных
    await db.init_db()
    logger.info("База данных инициализирована")
    
    # Удаляем вебхук
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем polling
    logger.info("Бот Среда 2.0 успешно запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        sys.exit(1)