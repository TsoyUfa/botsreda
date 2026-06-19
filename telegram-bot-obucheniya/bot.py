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