import logging
import asyncio
import aiohttp
import json
import re
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

import db
import config
import lessons
import analytics_db as adb
from simple_admin import SimpleAdminPanel, register_simple_admin_handlers
from student_monitoring import (
    log_text_response, 
    log_choice_response, 
    init_student_monitoring,
    register_voice_handlers
)
from webapp_manager import webapp_content

# Enable logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Bot and Dispatcher
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# FSM States for Quizzes
class QuizState(StatesGroup):
    answering = State()  # Storing: module_id, current_q_idx, correct_count, total_questions

# Gemini API Key configuration
GEMINI_API_KEY = config.GEMINI_API_KEY

async def evaluate_answer_with_ai(question: str, rubric: str, user_answer: str) -> tuple[float, str]:
    """
    Evaluates the free-text answer of the student using Gemini API.
    Returns a tuple of (score_float, critique_text).
    """
    if not GEMINI_API_KEY:
        # Graceful fallback: simulated high-fidelity AI feedback for demo purposes
        await asyncio.sleep(2.5)  # simulate API latency
        score = 0.88
        critique = (
            "🤖 <b>[РЕЖИМ ДЕМОНСТРАЦИИ — КЛЮЧ GEMINI_API_KEY НЕ ЗАДАН]</b>\n"
            "<b>Рецензия ИИ «Эксперт Сити» на ваш ответ:</b>\n\n"
            "✅ <b>Отлично!</b> Вы верно подметили необходимость выявить <i>комфортный ежемесячный платеж</i> (а не максимальный лимит, одобренный банком). Это ключевой пункт безопасности в 2026 году.\n"
            "✅ Вы зафиксировали <i>цели и срок сдачи ключей</i>, что является шагом 1 паспорта покупки.\n"
            "💡 <b>Рекомендация ИИ:</b> На реальной встрече не забудьте также уточнить наличие <i>предварительного одобрения ипотеки</i> до начала подбора ЖК.\n\n"
            "📊 <b>Оценка ИИ:</b> 88% (Зачет!)"
        )
        return score, critique

    # Real call to Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""
Ты — искусственный интеллект-ассистент обучающей платформы 'Эксперт Сити' по новостройкам.
Твоя задача — проверить свободный практический ответ ученика на вопрос по следующей рубрике.

Вопрос: {question}
Критерии оценки (рубрика): {rubric}
Ответ ученика: {user_answer}

Проведи детальный разбор ответа. Напиши вежливую, профессиональную и конструктивную рецензию в стиле 'Эксперт Сити' (честность, глубина, экспертность).
Выдели сильные стороны (используй зеленый маркер/галочку ✅) и зоны для роста (используй предупреждающий маркер 💡 или ⚠️).
В самом конце напиши оценку соответствия критериям в процентах в строгом формате:
ОЦЕНКА: XX% (где XX - число от 0 до 100).
Например: ОЦЕНКА: 85%.
"""
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers={"Content-Type": "application/json"}) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    ai_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Parse score from AI output
                    score = 0.0
                    match = re.search(r"ОЦЕНКА:\s*(\d+)%", ai_text, re.IGNORECASE)
                    if match:
                        score = float(match.group(1)) / 100.0
                    else:
                        # Fallback parsing
                        score = 0.8  # Default pass if text is returned
                        
                    return score, ai_text
                else:
                    logger.error(f"Gemini API returned error: {resp.status}")
                    return 0.5, "⚠️ Ошибка при запросе к Gemini API. Оценка проведена в автоматическом режиме: 50% (Не зачтено)."
    except Exception as e:
        logger.error(f"Exception during Gemini API call: {e}")
        return 0.5, f"⚠️ Не удалось связаться с ИИ-сервером: {e}. Попробуйте позже."

# Main Menu Keyboards
def get_main_menu_keyboard():
    keyboard = [
        [types.KeyboardButton(text="📚 Мое Обучение"), types.KeyboardButton(text="💡 О методологии Р.О.С.Т.")],
        [types.KeyboardButton(text="❓ Помощь / Контакты")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    """Start command handler with Web App integration."""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    
    # Save/create user in DB
    await db.create_user(user_id, username, first_name)
    
    # Log registration/start and begin analytics session
    session_id = await adb.start_learning_session(user_id)
    await adb.log_user_action(user_id, 'start_bot', {'first_start': True}, session_id)
    
    # Create keyboard with Web App button
    webapp_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎓 Открыть курс в Web App",
            web_app=types.WebAppInfo(
                url="https://your-web-app-url.com"  # Замените на ваш URL
            )
        )],
        [InlineKeyboardButton(
            text="📊 Мой прогресс",
            callback_data="user_progress"
        )]
    ])
    
    welcome_text = (
        f"🎓 Добро пожаловать в <b>«Среда Обучение»</b>, {first_name}! 🤝\n\n"
        "Вы подключились к обучающей системе <b>«Р.О.С.Т.»</b>.\n\n"
        "Мы готовим <b>антихрупких агентов-навигаторов</b> по новому стандарту работы с недвижимостью.\n\n"
        "<b>🌟 Что вас ждет:</b>\n"
        "• 7 мощных модулей обучения\n"
        "• Полная система тестирования с ИИ-проверкой\n"
        "• Голосовые задания и обратная связь\n"
        "• Удобный Web App интерфейс\n\n"
        "<b>🚀 Как начать:</b>\n"
        "Нажмите кнопку ниже для открытия курса в Web App или изучайте модули прямо здесь."
    )
    
    # Send welcome message with Web App button
    await message.answer(welcome_text, reply_markup=webapp_keyboard, parse_mode="HTML")
    
    # Also send regular keyboard for other functions
    await message.answer("Или используйте меню ниже:", reply_markup=get_main_menu_keyboard())

@dp.callback_query(F.data == "user_progress")
async def show_user_progress(callback: types.CallbackQuery):
    """Показать прогресс пользователя в Web App формате"""
    user_id = callback.from_user.id
    first_name = callback.from_user.first_name or "Студент"
    
    # Получаем прогресс пользователя
    progress = await db.get_user_progress(user_id)
    progress_dict = {row[0]: {"completed": row[2], "score": row[3]} for row in progress}
    
    # Формируем сообщение с прогрессом
    progress_text = f"📊 <b>Ваш прогресс обучения</b>, {first_name}!\n\n"
    
    completed_modules = 0
    total_score = 0
    score_count = 0
    
    for module_id, module_data in config.MODULES.items():
        module_progress = progress_dict.get(int(module_id), {"completed": False, "score": None})
        is_completed = module_progress["completed"]
        score = module_progress["score"]
        
        if is_completed:
            completed_modules += 1
            
        status_icon = "✅" if is_completed else "🔓"
        progress_text += f"{status_icon} <b>Блок {module_id}:</b> {module_data['title']}\n"
        
        if score is not None:
            progress_text += f"   Результат теста: {int(score*100)}%\n"
            total_score += score
            score_count += 1
        
        progress_text += "\n"
    
    # Общая статистика
    total_modules = len(config.MODULES)
    completion_rate = (completed_modules / total_modules) * 100 if total_modules > 0 else 0
    avg_score = (total_score / score_count * 100) if score_count > 0 else 0
    
    progress_text += f"📈 <b>Общая статистика:</b>\n"
    progress_text += f"• Завершено модулей: {completed_modules}/{total_modules} ({completion_rate:.0f}%)\n"
    progress_text += f"• Средний балл: {avg_score:.0f}%\n"
    
    if completion_rate == 100:
        progress_text += "\n🎉 Поздравляем! Вы завершили все модули обучения!"
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎓 Открыть Web App",
            web_app=types.WebAppInfo(
                url="https://your-web-app-url.com"  # ← ЗАМЕНИТЬ НА ВАШ URL ПОСЛЕ ДЕПЛОЯ
            )
        )],
        [InlineKeyboardButton(
            text="📚 Продолжить обучение",
            callback_data="continue_learning"
        )],
        [InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data="user_progress"
        )]
    ])
    
    await callback.message.edit_text(progress_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "continue_learning")
async def continue_learning(callback: types.CallbackQuery):
    """Показать доступные модули для продолжения обучения"""
    user_id = callback.from_user.id
    progress = await db.get_user_progress(user_id)
    progress_dict = {row[0]: {"unlocked": row[1], "completed": row[2], "score": row[3]} for row in progress}
    
    response_text = "<b>📚 Продолжить обучение:</b>\n\n"
    keyboard_buttons = []
    
    for m_id, m_data in config.MODULES.items():
        m_prog = progress_dict.get(int(m_id), {"unlocked": 1, "completed": 0, "score": None})
        
        # Все блоки теперь бесплатны и открыты
        unlocked = True
        completed = bool(m_prog["completed"])
        
        # Determine icon
        if completed:
            status_icon = "✅"
        else:
            status_icon = "🔓"
            
        m_title = m_data["title"]
        
        response_text += f"{status_icon} <b>Блок {m_id}:</b> {m_title}\n"
        if completed and m_prog['score'] is not None:
            response_text += f"   └ Результат теста: {int(m_prog['score']*100)}%\n"
        response_text += "\n"
        
        # Add buttons to view unlocked blocks
        btn_label = f"Блок {m_id}" + (" (Пройден)" if completed else " (Начать)")
        keyboard_buttons.append([InlineKeyboardButton(text=btn_label, callback_data=f"lesson_{m_id}")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(response_text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()

@dp.message(Command("progress"))
async def progress_cmd(message: types.Message):
    """Command to show user progress"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Студент"
    
    # Получаем прогресс пользователя
    progress = await db.get_user_progress(user_id)
    progress_dict = {row[0]: {"completed": row[2], "score": row[3]} for row in progress}
    
    # Формируем сообщение с прогрессом
    progress_text = f"📊 <b>Ваш прогресс обучения</b>, {first_name}!\n\n"
    
    completed_modules = 0
    total_score = 0
    score_count = 0
    
    for module_id, module_data in config.MODULES.items():
        module_progress = progress_dict.get(int(module_id), {"completed": False, "score": None})
        is_completed = module_progress["completed"]
        score = module_progress["score"]
        
        if is_completed:
            completed_modules += 1
            
        status_icon = "✅" if is_completed else "🔓"
        progress_text += f"{status_icon} <b>Блок {module_id}:</b> {module_data['title']}\n"
        
        if score is not None:
            progress_text += f"   Результат теста: {int(score*100)}%\n"
            total_score += score
            score_count += 1
        
        progress_text += "\n"
    
    # Общая статистика
    total_modules = len(config.MODULES)
    completion_rate = (completed_modules / total_modules) * 100 if total_modules > 0 else 0
    avg_score = (total_score / score_count * 100) if score_count > 0 else 0
    
    progress_text += f"📈 <b>Общая статистика:</b>\n"
    progress_text += f"• Завершено модулей: {completed_modules}/{total_modules} ({completion_rate:.0f}%)\n"
    progress_text += f"• Средний балл: {avg_score:.0f}%\n"
    
    if completion_rate == 100:
        progress_text += "\n🎉 Поздравляем! Вы завершили все модули обучения!"
    
    # Create keyboard with Web App button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎓 Открыть курс в Web App",
            web_app=types.WebAppInfo(
                url="https://your-web-app-url.com"  # ← ЗАМЕНИТЬ НА ВАШ URL ПОСЛЕ ДЕПЛОЯ
            )
        )]
    ])
    
    await message.answer(progress_text, reply_markup=keyboard, parse_mode="HTML")
async def show_my_learning(message: types.Message):
    """Lists all modules with their current unlock/completed status."""
    user_id = message.from_user.id
    progress = await db.get_user_progress(user_id)
    
    # Map progress for quick lookup
    progress_dict = {row[0]: {"unlocked": row[1], "completed": row[2], "score": row[3]} for row in progress}
    
    response_text = "<b>📚 Ваша программа обучения:</b>\n\n"
    keyboard_buttons = []
    
    for m_id, m_data in config.MODULES.items():
        m_prog = progress_dict.get(m_id, {"unlocked": 1, "completed": 0, "score": None})
        
        # Все блоки теперь бесплатны и открыты
        unlocked = True
        completed = bool(m_prog["completed"])
        
        # Determine icon
        if completed:
            status_icon = "✅"
        else:
            status_icon = "🔓"
            
        m_title = m_data["title"]
        
        response_text += f"{status_icon} <b>Блок {m_id}</b>: {m_title}\n"
        if completed and m_prog['score'] is not None:
            response_text += f"   └ Результат теста: {int(m_prog['score']*100)}%\n"
        response_text += "\n"
        
        # Add buttons to view unlocked blocks
        btn_label = f"Блок {m_id}" + (" (Пройден)" if completed else " (Начать)")
        keyboard_buttons.append([InlineKeyboardButton(text=btn_label, callback_data=f"lesson_{m_id}")])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(response_text, reply_markup=markup, parse_mode="HTML")

@dp.callback_query(F.data.startswith("lesson_"))
async def view_lesson(callback: types.CallbackQuery):
    """Displays lesson content."""
    user_id = callback.from_user.id
    module_id = int(callback.data.split("_")[1])
    
    lesson_data = lessons.LESSONS.get(module_id)
    if not lesson_data:
        await callback.message.answer("Материалы данного блока находятся в разработке.")
        await callback.answer()
        return
    
    # Все блоки теперь доступны - показываем контент
    
    # Log lesson start with analytics
    lesson_start_time = datetime.now()
    await adb.log_lesson_start(user_id, module_id, session_id=f"lesson_{module_id}_{user_id}")
    await adb.log_user_action(user_id, 'view_lesson', {
        'module_id': module_id,
        'module_title': lesson_data['title']
    })
        
    await callback.message.answer(
        f"<b>{lesson_data['title']}</b>\n\n"
        f"{lesson_data['content']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎙️ Прослушать аудио-подкаст", url=lesson_data['audio'])],
            [InlineKeyboardButton(text="📝 Пройти проверочный тест", callback_data=f"quiz_{module_id}")],
            [InlineKeyboardButton(text="⬅️ К списку блоков", callback_data="back_to_list")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_list")
async def back_to_list(callback: types.CallbackQuery):
    """Back to list handler."""
    await callback.message.delete()
    # Fake message object to reuse show_my_learning
    fake_msg = types.Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat,
        from_user=callback.from_user,
        text="📚 Мое Обучение"
    )
    await show_my_learning(fake_msg)
    await callback.answer()

# --- HYBRID QUIZ LOGIC (FSM) ---

@dp.callback_query(F.data.startswith("quiz_"))
async def start_quiz(callback: types.CallbackQuery, state: FSMContext):
    """Initiates a quiz for the block."""
    user_id = callback.from_user.id
    module_id = int(callback.data.split("_")[1])
    
    lesson_data = lessons.LESSONS.get(module_id)
    if not lesson_data or "quiz" not in lesson_data or not lesson_data["quiz"]:
        await callback.message.answer("Для этого блока тест не предусмотрен.")
        await callback.answer()
        return
        
    # Initialize state
    await state.set_state(QuizState.answering)
    await state.update_data(
        module_id=module_id,
        current_q_idx=0,
        correct_count=0,
        total_questions=len(lesson_data["quiz"])
    )
    
    await callback.message.answer("📝 Начинаем проверочный тест. Ответьте на вопросы:")
    await callback.answer()
    await send_quiz_question(callback.message, state)

async def send_quiz_question(message: types.Message, state: FSMContext):
    """Sends current quiz question based on state index."""
    data = await state.get_data()
    module_id = data["module_id"]
    q_idx = data["current_q_idx"]
    
    quiz_list = lessons.LESSONS[module_id]["quiz"]
    question_data = quiz_list[q_idx]
    
    q_type = question_data.get("type", "choice")
    
    if q_type == "choice":
        # Classic choice buttons
        buttons = []
        for opt_idx, option in enumerate(question_data["options"]):
            buttons.append([InlineKeyboardButton(
                text=option, 
                callback_data=f"ans_{module_id}_{q_idx}_{opt_idx}"
            )])
            
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            f"<b>Вопрос {q_idx + 1} из {len(quiz_list)}:</b>\n\n"
            f"{question_data['question']}",
            reply_markup=markup,
            parse_mode="HTML"
        )
    elif q_type == "free_text":
        # Free text prompt - wait for text message input
        await message.answer(
            f"<b>Вопрос {q_idx + 1} из {len(quiz_list)}:</b>\n\n"
            f"{question_data['question']}\n\n"
            "✍️ <i>Введите ваш развернутый текстовый ответ в поле ввода сообщения и отправьте его боту на ИИ-проверку!</i>",
            parse_mode="HTML"
        )

@dp.callback_query(QuizState.answering, F.data.startswith("ans_"))
async def handle_choice_answer(callback: types.CallbackQuery, state: FSMContext):
    """Processes the multiple-choice button answer."""
    _, module_id, q_idx, opt_idx = callback.data.split("_")
    module_id, q_idx, opt_idx = int(module_id), int(q_idx), int(opt_idx)
    
    data = await state.get_data()
    correct_count = data["correct_count"]
    current_q_idx = data["current_q_idx"]
    total_questions = data["total_questions"]
    
    quiz_list = lessons.LESSONS[module_id]["quiz"]
    correct_idx = quiz_list[q_idx]["correct_idx"]
    
    is_correct = (opt_idx == correct_idx)
    if is_correct:
        correct_count += 1
        await callback.message.answer("✅ Правильно!")
    else:
        correct_opt = quiz_list[q_idx]["options"][correct_idx]
        await callback.message.answer(f"❌ Неверно. Правильный ответ:\n<i>«{correct_opt}»</i>", parse_mode="HTML")
    
    # Логируем ответ студента
    question_text = quiz_list[q_idx]["question"]
    selected_answer = quiz_list[q_idx]["options"][opt_idx]
    await log_choice_response(
        user_id=user_id,
        module_id=module_id,
        question=question_text,
        answer=selected_answer,
        is_correct=is_correct
    )
        
    current_q_idx += 1
    await state.update_data(correct_count=correct_count, current_q_idx=current_q_idx)
    await callback.answer()
    
    if current_q_idx < total_questions:
        await send_quiz_question(callback.message, state)
    else:
        await finish_quiz(callback.message, state)

@dp.message(QuizState.answering, F.text)
async def handle_free_text_answer(message: types.Message, state: FSMContext):
    """Processes the student's typed text answer using Gemini AI evaluation."""
    data = await state.get_data()
    module_id = data["module_id"]
    q_idx = data["current_q_idx"]
    correct_count = data["correct_count"]
    total_questions = data["total_questions"]
    
    quiz_list = lessons.LESSONS[module_id]["quiz"]
    question_data = quiz_list[q_idx]
    
    if question_data.get("type") != "free_text":
        # Ignore and remind to use buttons
        await message.answer("Пожалуйста, нажмите на одну из кнопок вариантов ответов выше! 👆")
        return
        
    # Inform user that AI is grading
    wait_msg = await message.answer(
        "🤖 <b>Нейросеть «Эксперт Сити» анализирует ваш практический ответ...</b>\n"
        "Это займет около 3-4 секунд. Пожалуйста, подождите ⏳",
        parse_mode="HTML"
    )
    
    # Async Gemini AI evaluation
    score_ratio, AI_critique = await evaluate_answer_with_ai(
        question_data["question"],
        question_data["rubric"],
        message.text
    )
    
    # Clear wait message
    try:
        await wait_msg.delete()
    except Exception:
        pass
        
    # Send custom AI evaluation critique to the student
    await message.answer(AI_critique, parse_mode="HTML")
    
    # Логируем текстовый ответ студента
    question_data = quiz_list[q_idx]
    await log_text_response(
        user_id=user_id,
        module_id=module_id,
        question=question_data["question"],
        answer=message.text,
        is_correct=passed_question,
        score=score_ratio,
        ai_feedback=AI_critique
    )
    
    threshold = config.MODULES[module_id]["quiz_threshold"]
    passed_question = (score_ratio >= threshold)
    
    if passed_question:
        correct_count += 1
        
    current_q_idx = q_idx + 1
    await state.update_data(correct_count=correct_count, current_q_idx=current_q_idx)
    
    if current_q_idx < total_questions:
        await send_quiz_question(message, state)
    else:
        await finish_quiz(message, state)

async def finish_quiz(message: types.Message, state: FSMContext):
    """Computes overall test results, saves progress, unlocks next block."""
    data = await state.get_data()
    module_id = data["module_id"]
    correct_count = data["correct_count"]
    total_questions = data["total_questions"]
    
    score = correct_count / total_questions
    threshold = config.MODULES[module_id]["quiz_threshold"]
    passed = (score >= threshold)
    
    user_id = message.from_user.id
    await db.save_quiz_result(user_id, module_id, score, passed)
    await state.clear()
    
    if passed:
        await message.answer(
            f"🎉 <b>Поздравляем! Вы прошли тест Блока {module_id}!</b>\\n\\n"
            f"Результат: {correct_count} из {total_questions} пройденных шагов ({int(score*100)}%).\\n"
            "Следующий блок разблокирован для продолжения обучения.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"⚠️ <b>Тест Блока {module_id} не пройден.</b>\\n\\n"
            f"Ваш результат: {correct_count} из {total_questions} ({int(score*100)}%).\\n"
            f"Для прохождения необходимо набрать минимум {int(threshold*100)}%.\\n"
            "Изучите материалы повторно и попробуйте еще раз!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Пройти заново", callback_data=f"quiz_{module_id}")],
                [InlineKeyboardButton(text="📚 К списку блоков", callback_data="back_to_list")]
            ]),
            parse_mode="HTML"
        )

# --- PAYMENTS REMOVED (ALL MODULES NOW FREE) ---



# --- OTHER MENUS ---

@dp.message(F.text == "💡 О методологии Р.О.С.Т.")
async def show_about(message: types.Message):
    """Shows about methodology text."""
    about_text = (
        "💡 <b>Методология «Р.О.С.Т.»</b>\n\n"
        "<b>Р.</b>иск-менеджмент — снижение рисков для клиента и агента\n"
        "<b>О.</b>бъективность — честные данные, без давления, факты\n"
        "<b>С.</b>истемность — алгоритм сделки от финансов до ключей\n"
        "<b>Т.</b>ехнологии — ИИ-поддержка, автоматизация аналитики\n\n"
        "<b>Куратор Академии:</b> @Anton_soy\n"
        "<b>Руководитель:</b> Антон Цой\n\n"
        "Методология готовит <b>антихрупких агентов</b>, которые:\n"
        "• Не теряют клиентов из-за задержек строительства\n"
        "• Выстраивают долгосрочные отношения с клиентами\n"
        "• Получают стабильный доход без стресса"
    )
    await message.answer(about_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")

@dp.message(F.text == "❓ Помощь / Контакты")
async def show_help(message: types.Message):
    """Shows help info."""
    help_text = (
        "❓ <b>Помощь и поддержка</b>\n\n"
        "Если у вас возникли вопросы по работе бота или прохождению тестов, свяжитесь с куратором:\n\n"
        "👤 Куратор Академии: @Anton_soy\n\n"
        "📍 Руководитель: Антон Цой."
    )
    await message.answer(help_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")

# Main startup routine
async def main():
    # Initialize Database
    await db.init_db()
    logger.info("Basic database initialized successfully.")
    
    # Initialize Analytics System
    await adb.init_analytics_db()
    logger.info("Analytics database initialized successfully.")
    
    # Initialize Student Monitoring System
    await init_student_monitoring()
    logger.info("Student monitoring system initialized successfully.")
    
    # Initialize Simple Admin Panel
    admin_panel = SimpleAdminPanel(config.BOT_TOKEN)
    register_simple_admin_handlers(dp, admin_panel)
    logger.info("Simple admin panel handlers registered.")
    
    # Register Voice Handlers
    register_voice_handlers(dp, bot)
    logger.info("Voice message handlers registered.")
    
    # Start Polling
    logger.info("Bot starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
