from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Импортируем нашу аналитику и мониторинг
import analytics_db as adb
from student_monitoring import get_student_responses, get_recent_voice_messages
from extended_monitoring import (
    monitor_new_answers_handler,
    monitor_voice_messages_handler,
    monitor_student_full_answers_handler,
    add_additional_monitoring_handlers
)

# =======================
# УЛУЧШЕННАЯ АДМИН-ПАНЕЛЬ ДЛЯ МОНИТОРИНГА
# =======================

class SimpleAdminPanel:
    """Упрощенная админ-панель для мониторинга студентов."""
    
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.admin_user_id = 5690724590  # Telegram ID Антона
    
    async def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь админом."""
        return user_id == self.admin_user_id
    
    async def send_monitoring_menu(self, user_id: int):
        """Отправляет главное меню мониторинга."""
        if not await self.is_admin(user_id):
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("📊 Дашборд", callback_data="monitor_dashboard")],
            [InlineKeyboardButton("👥 Все студенты", callback_data="monitor_all_students")],
            [InlineKeyboardButton("🔍 Поиск студента", callback_data="monitor_search")],
            [InlineKeyboardButton("📝 Новые ответы", callback_data="monitor_new_answers")],
            [InlineKeyboardButton("🎙️ Голосовые сообщения", callback_data="monitor_voice_messages")],
            [InlineKeyboardButton("📈 Активность сегодня", callback_data="monitor_today")]
        ])
        
        text = (
            "🔍 <b>МОНИТОРИНГ СТУДЕНТОВ</b> 🔍\n\n"
            "Полная информация по всем ученикам в одном месте"
        )
        
        await self.bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="HTML")

async def monitor_dashboard_handler(callback: types.CallbackQuery):
    """Обработчик дашборда с ключевой статистикой."""
    stats = await adb.get_admin_dashboard()
    
    text = (
        "📊 <b>ДАШБОРД МОНИТОРИНГА</b>\n\n"
        f"👥 <b>Студенты:</b>\n"
        f"• Всего: <b>{stats['total_users']}</b>\n"
        f"• Активные (7 дней): <b>{stats['active_users']}</b>\n"
        f"• Новые (30 дней): <b>{stats['new_users_30d']}</b>\n"
        f"• Процент активности: <b>{round(stats['active_users']/max(stats['total_users'],1)*100, 1)}%</b>\n\n"
        f"🎓 <b>Обучение:</b>\n"
        f"• Завершено уроков: <b>{stats['completed_lessons']}</b>\n"
        f"• Сертифицированных: <b>{stats['certified_agents']}</b>\n"
        f"• Сессий сегодня: <b>{stats['today_sessions']}</b>\n\n"
        f"🔥 <b>Популярные модули:</b>\n"
    )
    
    for i, module in enumerate(stats['popular_modules'][:3], 1):
        text += f"{i}. Блок {module['module_id']} - {module['views']} просмотров\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔄 Обновить", callback_data="monitor_dashboard")],
        [InlineKeyboardButton("👥 Перейти к студентам", callback_data="monitor_all_students")],
        [InlineKeyboardButton("◀️ Назад", callback_data="monitor_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def monitor_all_students_handler(callback: types.CallbackQuery):
    """Обработчик списка всех студентов."""
    import aiosqlite
    from config import DB_PATH
    
    async with aiosqlite.connect(DB_PATH) as db:
        students = await db.execute("""
            SELECT user_id, username, first_name, registration_date, last_activity 
            FROM users 
            ORDER BY last_activity DESC 
        """)
        students_data = await students.fetchall()
    
    text = "👥 <b>ВСЕ СТУДЕНТЫ (по активности)</b>\n\n"
    keyboard_buttons = []
    
    for student in students_data:
        user_id, username, first_name, reg_date, last_activity = student
        
        # Статус активности
        if last_activity:
            last_active = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S')
            days_inactive = (datetime.now() - last_active).days
            
            if days_inactive <= 1:
                status = "🟢 Сегодня"
            elif days_inactive <= 7:
                status = "🟡 Неделя"
            elif days_inactive <= 30:
                status = "🔴 Месяц"
            else:
                status = "⚪ Давно"
        else:
            status = "⚪ Новый"
        
        text += f"👤 <b>{first_name}</b> (@{username or 'нет'})\n"
        text += f"ID: <code>{user_id}</code> | {status}\n"
        text += f"Рег: {reg_date[:10]}\n\n"
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                f"{first_name} — детально", 
                callback_data=f"student_detail_{user_id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton("◀️ Назад", callback_data="monitor_back")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def monitor_student_detail_handler(callback: types.CallbackQuery):
    """Детальная информация о конкретном студенте."""
    user_id = int(callback.data.split("_")[-1])
    
    analytics = await adb.get_user_analytics(user_id)
    
    if not analytics:
        await callback.answer("❌ Студент не найден", show_alert=True)
        return
    
    user_info = analytics['user_info']
    progress = analytics['progress']
    quiz_stats = analytics['quiz_stats']
    
    text = (
        f"👤 <b>СТУДЕНТ: {user_info['first_name']}</b>\n\n"
        f"<b>🏷️ Информация:</b>\n"
        f"• Имя: {user_info['first_name']}\n"
        f"• Username: @{user_info['username'] or 'нет'}\n"
        f"• ID: <code>{user_info['user_id']}</code>\n"
        f"• Регистрация: {user_info['registration_date'][:10]}\n"
        f"• Последняя активность: {user_info['last_activity'][:16] if user_info['last_activity'] else 'нет'}\n"
        f"• Всего сессий: {user_info['total_sessions']}\n\n"
    )
    
    # Прогресс по модулям
    text += "<b>📚 Прогресс:</b>\n"
    completed_modules = sum(1 for p in progress if p['is_completed'])
    text += f"• Завершено модулей: {completed_modules}/7\n"
    
    for mod in progress:
        status_icon = "✅" if mod['is_completed'] else "🟡" if mod['started'] else "⚪"
        text += f"{status_icon} Блок {mod['module_id']}: "
        if mod['best_score']:
            text += f"{round(mod['best_score']*100)}%\n"
        else:
            text += "не начат\n"
    
    # Статистика по тестам
    text += f"\n<b>📊 Тесты:</b>\n"
    text += f"• Попыток: {quiz_stats['total_attempts']}\n"
    text += f"• Средний балл: {quiz_stats['avg_score']}%\n"
    text += f"• Правильных ответов: {quiz_stats['correct_answers']}\n"
    
    # Время обучения
    total_minutes = analytics['total_learning_time'] // 60
    text += f"\n<b>⏱️ Время в системе:</b> {total_minutes} мин"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📤 Экспорт данных", callback_data=f"export_student_{user_id}")],
        [InlineKeyboardButton("📝 Все ответы", callback_data=f"student_full_answers_{user_id}")],
        [InlineKeyboardButton("◀️ К списку", callback_data="monitor_all_students")],
        [InlineKeyboardButton("◀️ Назад", callback_data="monitor_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def monitor_student_answers_handler(callback: types.CallbackQuery):
    """Все ответы студента."""
    user_id = int(callback.data.split("_")[-1])
    
    # Здесь нужно добавить функцию для получения всех ответов студента
    # Временно показываем заглушку
    
    text = f"📝 <b>ОТВЕТЫ СТУДЕНТА {user_id}</b>\n\n"
    text += "⚠️ Функция в разработке\n\n"
    text += "Здесь будут отображаться:\n"
    text += "• Все тестовые ответы\n"
    text += "• Текстовые ответы с ИИ-проверкой\n"
    text += "• Голосовые сообщения\n"
    text += "• История обучения"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("◀️ Назад к студенту", callback_data=f"student_detail_{user_id}")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def monitor_search_handler(callback: types.CallbackQuery):
    """Поиск студента."""
    text = (
        "🔍 <b>ПОИСК СТУДЕНТА</b>\n\n"
        "Введите для поиска:\n"
        "• <b>ID пользователя</b> (цифры)\n"
        "• <b>Имя</b> (текст)\n"
        "• <b>Username</b> (с @)\n\n"
        "Примеры:\n"
        "• <code>5690724590</code>\n"
        "• <code>Антон</code>\n"
        "• <code>@anton_soy</code>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("◀️ Назад", callback_data="monitor_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# =======================
# ИНТЕГРАЦИЯ С ОСНОВНЫМ БОТОМ
# =======================

def register_simple_admin_handlers(dp: Dispatcher, admin_panel: SimpleAdminPanel):
    """Регистрирует обработчики упрощенной админ-панели."""
    
    # Команда для входа в мониторинг
    @dp.message(Command("monitor"))
    async def monitor_command(message: types.Message):
        if await admin_panel.is_admin(message.from_user.id):
            await admin_panel.send_monitoring_menu(message.from_user.id)
        else:
            await message.answer("❌ Доступ запрещен")
    
    # Обработчики кнопок мониторинга
    @dp.callback_query(F.data.startswith("monitor_"))
    async def monitor_callback_handler(callback: types.CallbackQuery):
        action = callback.data.split("_")[1]
        
        if action == "dashboard":
            await monitor_dashboard_handler(callback)
        elif action == "all":
            await monitor_all_students_handler(callback)
        elif action == "search":
            await monitor_search_handler(callback)
        elif action == "back":
            await admin_panel.send_monitoring_menu(callback.from_user.id)
        elif action == "today":
            # TODO: Реализовать отчет за сегодня
            await callback.answer("📈 В разработке")
    
    @dp.callback_query(F.data.startswith("student_detail_"))
    async def student_detail_handler(callback: types.CallbackQuery):
        await monitor_student_detail_handler(callback)
    
    @dp.callback_query(F.data.startswith("student_answers_"))
    async def student_answers_handler(callback: types.CallbackQuery):
        await monitor_student_full_answers_handler(callback)
    
    # Регистрируем дополнительные обработчики
    add_additional_monitoring_handlers(dp, None)  # bot не нужен для этих обработчиков
    
    @dp.callback_query(F.data.startswith("export_student_"))
    async def export_student_handler(callback: types.CallbackQuery):
        user_id = int(callback.data.split("_")[-1])
        export_data = await adb.export_user_data(user_id)
        
        # Отправка файла с данными
        from io import BytesIO
        
        file_data = BytesIO(export_data.encode('utf-8'))
        file_data.name = f"student_{user_id}_data.json"
        
        await callback.bot.send_document(
            callback.from_user.id,
            document=types.InputFile(file_data, filename=file_data.name),
            caption=f"📤 Данные студента {user_id}"
        )
        await callback.answer("Данные экспортированы")