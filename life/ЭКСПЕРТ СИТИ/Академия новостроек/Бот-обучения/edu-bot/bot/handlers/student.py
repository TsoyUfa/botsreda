"""Student handlers: knowledge base, tests menu, progress."""
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.db import async_session
from bot.models import Module, Lesson, Test, Student, User, TestAttempt, StudentAnswer
from bot.keyboards import (
    modules_list_kb, lessons_nav_kb, tests_list_kb, back_button,
)

router = Router(name="student")


# ---- Knowledge Base: modules list ----

@router.callback_query(F.data == "kb_menu")
async def cb_kb_menu(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Module).order_by(Module.order, Module.id)
        )
        modules = result.scalars().all()

    if not modules:
        await call.message.edit_text(
            "\U0001F4DA <b>База знаний</b>\n\n"
            "Модули пока не добавлены. Куратор скоро наполнит базу.",
            reply_markup=back_button(),
        )
        await call.answer()
        return

    await call.message.edit_text(
        "\U0001F4DA <b>База знаний</b>\n\nВыберите модуль:",
        reply_markup=modules_list_kb(modules),
    )
    await call.answer()


# ---- Module: lessons list ----

@router.callback_query(F.data.startswith("module_"))
async def cb_module(call: CallbackQuery):
    module_id = int(call.data.split("_")[1])

    async with async_session() as session:
        result = await session.execute(
            select(Lesson)
            .where(Lesson.module_id == module_id)
            .order_by(Lesson.order, Lesson.id)
        )
        lessons = result.scalars().all()

    if not lessons:
        await call.message.edit_text(
            "\U0001F4DA В этом модуле пока нет уроков.",
            reply_markup=back_button("kb_menu"),
        )
        await call.answer()
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    for lesson in lessons:
        kb.button(text=f"\U0001F4C4 {lesson.title}", callback_data=f"lesson_{lesson.id}")
    kb.button(text="\u2b05\ufe0f К модулям", callback_data="kb_menu")
    kb.adjust(1)

    await call.message.edit_text(
        "\U0001F4C4 <b>Уроки модуля</b>\n\nВыберите урок:",
        reply_markup=kb.as_markup(),
    )
    await call.answer()


# ---- Lesson detail ----

@router.callback_query(F.data.startswith("lesson_"))
async def cb_lesson(call: CallbackQuery):
    lesson_id = int(call.data.split("_")[1])

    async with async_session() as session:
        lesson = await session.get(Lesson, lesson_id)
        if lesson is None:
            await call.answer("Урок не найден", show_alert=True)
            return

        # Find prev and next lessons in same module
        result = await session.execute(
            select(Lesson)
            .where(Lesson.module_id == lesson.module_id)
            .order_by(Lesson.order, Lesson.id)
        )
        all_lessons = result.scalars().all()

    # Determine prev/next
    current_idx = None
    for i, l in enumerate(all_lessons):
        if l.id == lesson_id:
            current_idx = i
            break

    prev_id = all_lessons[current_idx - 1].id if current_idx and current_idx > 0 else None
    next_id = all_lessons[current_idx + 1].id if current_idx is not None and current_idx < len(all_lessons) - 1 else None

    text = f"\U0001F4C4 <b>{lesson.title}</b>\n\n{lesson.content}"

    await call.message.edit_text(
        text,
        reply_markup=lessons_nav_kb(lesson, prev_id, next_id, lesson.module_id),
    )
    await call.answer()


# ---- Tests menu ----

@router.callback_query(F.data == "tests_menu")
async def cb_tests_menu(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(Test).order_by(Test.id))
        tests = result.scalars().all()

    if not tests:
        await call.message.edit_text(
            "\U0001F4DD <b>Тесты</b>\n\n"
            "Тесты пока не добавлены.",
            reply_markup=back_button(),
        )
        await call.answer()
        return

    await call.message.edit_text(
        "\U0001F4DD <b>Тесты</b>\n\nВыберите тест для прохождения:",
        reply_markup=tests_list_kb(tests),
    )
    await call.answer()


# ---- Progress (stub) ----

@router.callback_query(F.data == "my_progress")
async def cb_progress(call: CallbackQuery):
    # Will be expanded in Phase 4
    await call.message.edit_text(
        "\U0001F4CA <b>Мой прогресс</b>\n\n"
        "Раздел в разработке. Здесь будет отображаться ваш прогресс по модулям и результаты тестов.",
        reply_markup=back_button(),
    )
    await call.answer()
