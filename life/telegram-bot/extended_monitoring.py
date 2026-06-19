from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Импортируем нашу аналитику и мониторинг
import analytics_db as adb
from student_monitoring import get_student_responses, get_recent_voice_messages

# =======================
# ДОПОЛНИТЕЛЬНЫЕ ОБРАБОТЧИКИ МОНИТОРИНГА
# =======================

async def monitor_new_answers_handler(callback: types.CallbackQuery):
    """Последние ответы студентов."""
    # Получаем последние ответы из базы
    import aiosqlite
    from config import DB_PATH
    
    async with aiosqlite.connect(DB_PATH) as db:
        responses = await db.execute("""
            SELECT sr.*, u.first_name, u.username 
            FROM student_responses sr
            JOIN users u ON sr.user_id = u.user_id
            ORDER BY sr.created_at DESC 
            LIMIT 15
        """)
        responses_data = await responses.fetchall()
    
    text = "📝 <b>ПОСЛЕДНИЕ ОТВЕТЫ СТУДЕНТОВ</b>\n\n"
    
    for response in responses_data:
        user_id, module_id, q_type, question, answer, is_correct, score, ai_feedback, voice_file_id, voice_duration, created_at, first_name, username = response
        
        # Форматируем время
        response_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        time_ago = (datetime.now() - response_time).seconds // 60
        
        if time_ago < 1:
            time_str = "только что"
        elif time_ago < 60:
            time_str = f"{time_ago} мин назад"
        else:
            hours = time_ago // 60
            time_str = f"{hours} ч назад"
        
        text += f"👤 <b>{first_name}</b> — {time_str}\n"
        
        if q_type == 'voice':
            text += f"🎙️ Голосовое сообщение ({voice_duration} сек)\n"
        elif q_type == 'free_text':
            text += f"📝 Текстовый ответ ({'✅' if is_correct else '❌'})\n"
            # Обрезаем длинные ответы
            answer_preview = answer[:100] + "..." if len(answer) > 100 else answer
            text += f"«{answer_preview}»\n"
        else:  # choice
            text += f"❓ Выбор варианта ({'✅' if is_correct else '❌'})\n"
        
        text += f"Блок {module_id} | ID: <code>{user_id}</code>\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔄 Обновить", callback_data="monitor_new_answers")],
        [InlineKeyboardButton("◀️ Назад", callback_data="monitor_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def monitor_voice_messages_handler(callback: types.CallbackQuery):
    """Голосовые сообщения студентов."""
    voice_messages = await get_recent_voice_messages(10)
    
    text = "🎙️ <b>ГОЛОСОВЫЕ СООБЩЕНИЯ СТУДЕНТОВ</b>\n\n"
    
    if not voice_messages:
        text += "Пока нет голосовых сообщений\n"
    else:
        for msg in voice_messages:
            user_id, first_name, username = msg['user_id'], msg['first_name'], msg['username']
            voice_duration = msg['voice_duration']
            created_at = msg['created_at']
            
            # Форматируем время
            msg_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            time_ago = (datetime.now() - msg_time).seconds // 60
            
            if time_ago < 1:
                time_str = "только что"
            elif time_ago < 60:
                time_str = f"{time_ago} мин назад"
            else:
                hours = time_ago // 60
                time_str = f"{hours} ч назад"
            
            text += f"👤 <b>{first_name}</b> (@{username or 'нет'})\n"
            text += f"🎙️ Голосовое ({voice_duration} сек) — {time_str}\n"
            text += f"ID: <code>{user_id}</code>\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔄 Обновить", callback_data="monitor_voice_messages")],
        [InlineKeyboardButton("◀️ Назад", callback_data="monitor_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def monitor_student_full_answers_handler(callback: types.CallbackQuery):
    """Полные ответы студента (улучшенная версия)."""
    user_id = int(callback.data.split("_")[-1])
    
    # Получаем все ответы студента
    responses = await get_student_responses(user_id, limit=50)
    
    if not responses:
        await callback.answer("❌ У этого студента пока нет ответов", show_alert=True)
        return
    
    # Группируем по типам ответов
    text_responses = [r for r in responses if r['question_type'] in ['free_text', 'choice']]
    voice_responses = [r for r in responses if r['question_type'] == 'voice']
    
    text = f"📝 <b>ПОЛНЫЕ ОТВЕТЫ СТУДЕНТА {user_id}</b>\n\n"
    
    # Текстовые ответы
    if text_responses:
        text += f"📝 <b>Текстовые ответы ({len(text_responses)}):</b>\n\n"
        
        for resp in text_responses[:10]:  # Показываем только первые 10
            q_type = "📝 Текст" if resp['question_type'] == 'free_text' else "❓ Выбор"
            status = "✅" if resp['is_correct'] else "❌"
            
            text += f"{q_type} {status} | Блок {resp['module_id']}\n"
            text += f"Вопрос: {resp['question'][:50]}...\n"
            
            if resp['question_type'] == 'free_text':
                answer_preview = resp['answer'][:100] + "..." if len(resp['answer']) > 100 else resp['answer']
                text += f"Ответ: «{answer_preview}»\n"
            else:
                text += f"Ответ: {resp['answer']}\n"
            
            if resp['ai_feedback']:
                text += f"ИИ-оценка: {resp['score']*100}%\n"
            
            text += "\n"
    
    # Голосовые сообщения
    if voice_responses:
        text += f"\n🎙️ <b>Голосовые сообщения ({len(voice_responses)}):</b>\n\n"
        
        for resp in voice_responses[:5]:  # Показываем только первые 5
            text += f"🎙️ Голос ({resp['voice_duration']} сек) | Блок {resp['module_id']}\n"
            text += f"Дата: {resp['created_at'][:16]}\n"
            
            if resp['answer']:  # Если есть расшифровка
                text += f"Расшифровка: {resp['answer'][:100]}...\n"
            
            text += "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📤 Экспорт все данные", callback_data=f"export_student_{user_id}")],
        [InlineKeyboardButton("◀️ Назад к студенту", callback_data=f"student_detail_{user_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="monitor_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# =======================
# ДОБАВЛЕНИЕ В ОСНОВНУЮ ПАНЕЛЬ
# =======================

def add_additional_monitoring_handlers(dp, bot):
    """Добавляет дополнительные обработчики мониторинга."""
    
    # Обновляем существующую функцию для поддержки новых кнопок
    @dp.callback_query(F.data.startswith("monitor_"))
    async def enhanced_monitor_callback_handler(callback: types.CallbackQuery):
        action = callback.data.split("_")[1]
        
        if action == "dashboard":
            await monitor_dashboard_handler(callback)
        elif action == "all":
            await monitor_all_students_handler(callback)
        elif action == "search":
            await monitor_search_handler(callback)
        elif action == "new":
            await monitor_new_answers_handler(callback)
        elif action == "voice":
            await monitor_voice_messages_handler(callback)
        elif action == "today":
            await callback.answer("📈 Аналитика за сегодня в разработке")
        elif action == "back":
            from simple_admin import SimpleAdminPanel
            admin_panel = SimpleAdminPanel("dummy")  # Временное решение
            await admin_panel.send_monitoring_menu(callback.from_user.id)
    
    # Обработчик для полных ответов студента
    @dp.callback_query(F.data.startswith("student_full_answers_"))
    async def student_full_answers_handler_wrapper(callback: types.CallbackQuery):
        await monitor_student_full_answers_handler(callback)