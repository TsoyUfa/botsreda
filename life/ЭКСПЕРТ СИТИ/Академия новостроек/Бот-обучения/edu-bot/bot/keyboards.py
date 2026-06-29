"""Inline keyboards for the bot."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def student_main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="\U0001F4DA База знаний", callback_data="kb_menu")
    kb.button(text="\U0001F4DD Тесты", callback_data="tests_menu")
    kb.button(text="\U0001F4CA Мой прогресс", callback_data="my_progress")
    kb.button(text="\u2753 Помощь", callback_data="help")
    kb.adjust(1, 1, 2)
    return kb.as_markup()


def admin_main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="\U0001F465 Ученики", callback_data="admin_students")
    kb.button(text="\U0001F4DD Управление тестами", callback_data="admin_tests")
    kb.button(text="\U0001F4DA База знаний (контент)", callback_data="admin_content")
    kb.button(text="\U0001F511 Коды доступа", callback_data="admin_codes")
    kb.button(text="\U0001F4CA Аналитика", callback_data="admin_analytics")
    kb.button(text="\U0001F4E3 Рассылка", callback_data="admin_broadcast")
    kb.adjust(1, 1, 1, 1, 2)
    return kb.as_markup()


def back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="\u2b05\ufe0f Назад", callback_data=callback_data)
    return kb.as_markup()


def modules_list_kb(modules) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for m in modules:
        kb.button(text=m.title, callback_data=f"module_{m.id}")
    kb.button(text="\u2b05\ufe0f Назад", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def lessons_nav_kb(lesson, prev_id=None, next_id=None, module_id=None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    row = []
    if prev_id:
        kb.button(text="\u25c0\ufe0f Назад", callback_data=f"lesson_{prev_id}")
    if next_id:
        kb.button(text="\u25b6\ufe0f Далее", callback_data=f"lesson_{next_id}")
    kb.adjust(2)
    kb.button(text="\U0001F4DD Тест по модулю", callback_data=f"test_module_{module_id}")
    kb.button(text="\U0001F4DA К модулям", callback_data="kb_menu")
    kb.button(text="\U0001F3E0 Главное меню", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


def tests_list_kb(tests) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in tests:
        kb.button(text=t.title, callback_data=f"take_test_{t.id}")
    kb.button(text="\u2b05\ufe0f Назад", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()
