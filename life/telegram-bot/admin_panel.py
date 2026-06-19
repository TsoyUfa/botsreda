from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Импортируем нашу аналитику
import analytics_db as adb

# =======================
# АДМИН-ПАНЕЛЬ ДЛЯ УПРАВЛЕНИЯ
# =======================

class AdminPanel:
    """Класс для управления админ-панелью бота."""
    
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.admin_user_id = 5690724590  # Telegram ID Антона (заменить на ваш реальный ID)
    
    async def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь админом."""
        return user_id == self.admin_user_id
    
    async def send_admin_menu(self, user_id: int):
        """Отправляет главное меню админ-панели."""
        if not await self.is_admin(user_id):
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("📊 Общая статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Список агентов", callback_data="admin_agents")],
            [InlineKeyboardButton("🔍 Поиск агента", callback_data="admin_search")],
            [InlineKeyboardButton("📈 Аналитика за сегодня", callback_data="admin_daily")],
            [InlineKeyboardButton("📤 Экспорт данных", callback_data="admin_export")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")]
        ])
        
        stats = await adb.get_admin_dashboard()
        
        text = (
            "⚡ <b>АДМИН-ПАНЕЛЬ Р.О.С.Т.</b> ⚡\n\n"
            f"👥 Всего агентов: <b>{stats['total_users']}</b>\n"
            f"🟢 Активных (7 дней): <b>{stats['active_users']}</b>\n"
            f"📈 Новых (30 дней): <b>{stats['new_users_30d']}</b>\n"
            f"🎓 Сертифицированных: <b>{stats['certified_agents']}</b>\n"
            f"📚 Завершено уроков: <b>{stats['completed_lessons']}</b>\n"
            f"🔄 Сессий сегодня: <b>{stats['today_sessions']}</b>\n\n"
            "Выберите действие ниже:"
        )
        
        await self.bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="HTML")

async def admin_stats_handler(callback: types.CallbackQuery):
    """Обработчик кнопки статистики."""
    stats = await adb.get_admin_dashboard()
    
    text = (
        "📊 <b>ОБЩАЯ СТАТИСТИКА</b>\n\n"
        f"<b>👥 Пользователи:</b>\n"
        f"• Всего агентов: {stats['total_users']}\n"
        f"• Активные (последние 7 дней): {stats['active_users']}\n"
        f"• Новые регистрации (30 дней): {stats['new_users_30d']}\n"
        f"• Процент активности: {round(stats['active_users']/max(stats['total_users'],1)*100, 1)}%\n\n"
        f"<b>🎓 Обучение:</b>\n"
        f"• Завершено уроков: {stats['completed_lessons']}\n"
        f"• Сертифицированных агентов: {stats['certified_agents']}\n"
        f"• Активных сессий сегодня: {stats['today_sessions']}\n\n"
        f"<b>🔥 Популярные модули:</b>\n"
    )
    
    for i, module in enumerate(stats['popular_modules'][:3], 1):
        text += f"{i}. Блок {module['module_id']} - {module['views']} просмотров\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def admin_agents_list_handler(callback: types.CallbackQuery):
    """Обработчик списка агентов."""
    import aiosqlite
    from config import DB_PATH
    
    async with aiosqlite.connect(DB_PATH) as db:
        agents = await db.execute("""
            SELECT user_id, username, first_name, registration_date, last_activity 
            FROM users 
            ORDER BY last_activity DESC 
            LIMIT 20
        """)
        agents_data = await agents.fetchall()
    
    text = "👥 <b>СПИСОК АГЕНТОВ (последние 20 по активности)</b>\n\n"
    keyboard_buttons = []
    
    for agent in agents_data:
        user_id, username, first_name, reg_date, last_activity = agent
        
        # Определяем статус активности
        if last_activity:
            last_active = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S')
            days_inactive = (datetime.now() - last_active).days
            
            if days_inactive <= 7:
                status = "🟢 Активен"
            elif days_inactive <= 30:
                status = "🟡 Был(а) недавно"
            else:
                status = "🔴 Неактивен"
        else:
            status = "⚪ Новый"
        
        text += f"👤 <b>{first_name}</b> (@{username or 'нет'})\n"
        text += f"ID: <code>{user_id}</code> | {status}\n"
        text += f"Регистрация: {reg_date[:10]}\n\n"
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                f"{first_name} - детально", 
                callback_data=f"agent_detail_{user_id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton("◀️ Назад в меню", callback_data="admin_back")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def admin_agent_detail_handler(callback: types.CallbackQuery):
    """Обработчик детальной информации об агенте."""
    user_id = int(callback.data.split("_")[-1])
    
    analytics = await adb.get_user_analytics(user_id)
    
    if not analytics:
        await callback.answer("❌ Агент не найден", show_alert=True)
        return
    
    user_info = analytics['user_info']
    progress = analytics['progress']
    quiz_stats = analytics['quiz_stats']
    
    text = (
        f"👤 <b>ДЕТАЛИ АГЕНТА</b>\n\n"
        f"<b>🏷️ Информация:</b>\n"
        f"• Имя: {user_info['first_name']}\n"
        f"• Username: @{user_info['username'] or 'нет'}\n"
        f"• ID: <code>{user_info['user_id']}</code>\n"
        f"• Регистрация: {user_info['registration_date'][:10]}\n"
        f"• Последняя активность: {user_info['last_activity'][:16] if user_info['last_activity'] else 'нет'}\n"
        f"• Всего сессий: {user_info['total_sessions']}\n\n"
    )
    
    # Прогресс по модулям
    text += "<b>📚 Прогресс обучения:</b>\n"
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
    text += f"\n<b>📊 Статистика тестов:</b>\n"
    text += f"• Всего попыток: {quiz_stats['total_attempts']}\n"
    text += f"• Средний балл: {quiz_stats['avg_score']}%\n"
    text += f"• Правильных ответов: {quiz_stats['correct_answers']}\n"
    text += f"• Тестировано модулей: {quiz_stats['modules_tested']}\n"
    
    # Общее время обучения
    total_minutes = analytics['total_learning_time'] // 60
    text += f"\n<b>⏱️ Время в системе:</b> {total_minutes} минут"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📤 Экспорт данных агента", callback_data=f"export_agent_{user_id}")],
        [InlineKeyboardButton("◀️ К списку агентов", callback_data="admin_agents")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def admin_daily_report_handler(callback: types.CallbackQuery):
    """Обработчик ежедневного отчета."""
    report = await adb.export_daily_report()
    
    text = (
        f"📈 <b>ОТЧЕТ ЗА {report['date']}</b>\n\n"
        f"<b>👥 Пользователи:</b>\n"
        f"• Новых агентов: {report['new_users']}\n"
        f"• Всего действий: {report['total_actions']}\n\n"
        f"<b>🎓 Обучение:</b>\n"
        f"• Завершено уроков: {report['completed_lessons']}\n"
        f"• Средний балл тестов: {report['avg_quiz_score']}%\n\n"
        f"<b>📊 Активность:</b>\n"
    )
    
    # Добавляем сравнение с вчерашним днем
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_report = await adb.export_daily_report(yesterday)
    
    if yesterday_report:
        text += f"• По сравнению со вчерашним днем:\n"
        
        users_change = report['new_users'] - yesterday_report['new_users']
        text += f"  - Новые агенты: {users_change:+d}\n"
        
        actions_change = report['total_actions'] - yesterday_report['total_actions']
        text += f"  - Активность: {actions_change:+d}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin_daily")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def admin_search_handler(callback: types.CallbackQuery):
    """Обработчик поиска агента."""
    text = (
        "🔍 <b>ПОИСК АГЕНТА</b>\n\n"
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
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# =======================
# ИНТЕГРАЦИЯ С ОСНОВНЫМ БОТОМ
# =======================

def register_admin_handlers(dp: Dispatcher, admin_panel: AdminPanel):
    """Регистрирует обработчики админ-панели."""
    
    # Команда для входа в админ-панель
    @dp.message(Command("admin"))
    async def admin_command(message: types.Message):
        if await admin_panel.is_admin(message.from_user.id):
            await admin_panel.send_admin_menu(message.from_user.id)
        else:
            await message.answer("❌ Доступ запрещен")
    
    # Обработчики кнопок админ-панели
    @dp.callback_query(F.data.startswith("admin_"))
    async def admin_callback_handler(callback: types.CallbackQuery):
        action = callback.data.split("_")[1]
        
        if action == "stats":
            await admin_stats_handler(callback)
        elif action == "agents":
            await admin_agents_list_handler(callback)
        elif action == "daily":
            await admin_daily_report_handler(callback)
        elif action == "search":
            await admin_search_handler(callback)
        elif action == "back":
            await admin_panel.send_admin_menu(callback.from_user.id)
        elif action.startswith("agent_detail"):
            await admin_agent_detail_handler(callback)
        elif action.startswith("export_agent"):
            user_id = int(callback.data.split("_")[-1])
            export_data = await adb.export_user_data(user_id)
            
            # Отправка файла с данными
            from io import BytesIO
            import json
            
            file_data = BytesIO(export_data.encode('utf-8'))
            file_data.name = f"agent_{user_id}_data.json"
            
            await callback.bot.send_document(
                callback.from_user.id,
                document=types.InputFile(file_data, filename=file_data.name),
                caption=f"📤 Данные агента {user_id}"
            )
            await callback.answer("Данные экспортированы")

# =======================
# ИНИЦИАЛИЗАЦИЯ АНАЛИТИКИ
# =======================

async def init_analytics_integration():
    """Инициализация аналитики в основном боте."""
    # Инициализируем улучшенную базу данных
    await adb.init_analytics_db()
    
    print("✅ Аналитическая система успешно инициализирована")
    print("📊 Теперь доступно:")
    print("  • Логирование всех действий пользователей")
    print("  • Детальная статистика по каждому агенту") 
    print("  • Админ-панель для управления")
    print("  • Экспорт данных в JSON")
    print("  • Ежедневные отчеты")