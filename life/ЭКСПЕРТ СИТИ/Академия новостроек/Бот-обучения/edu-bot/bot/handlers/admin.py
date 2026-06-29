"""Admin handlers: invite codes, students, content management."""
from __future__ import annotations

import secrets
import csv
import io

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func

from bot.db import async_session
from bot.models import (
    User, Student, InviteCode, Group, Module, Lesson, Test, TestAttempt,
)
from bot.config import ADMIN_IDS
from bot.states import AdminStates
from bot.keyboards import admin_main_menu, back_button

router = Router(name="admin")


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


# ---- Students list ----

@router.callback_query(F.data == "admin_students")
async def cb_admin_students(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(Student).order_by(Student.started_at.desc())
        )
        students = result.scalars().all()

    if not students:
        await call.message.edit_text(
            "\U0001F465 <b>Ученики</b>\n\nУчеников пока нет.",
            reply_markup=back_button("main_menu"),
        )
        await call.answer()
        return

    lines = [f"\U0001F465 <b>Ученики ({len(students)}):</b>\n"]
    status_emoji = {
        "active": "\U0001F7E2",
        "paused": "\U0001F7E1",
        "finished": "\u2705",
        "blocked": "\U0001F534",
    }
    for s in students:
        e = status_emoji.get(s.status, "\u26ab")
        lines.append(f"{e} <b>{s.full_name_ru or 'Без имени'}</b> - {s.status}")

    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=back_button("main_menu"),
    )
    await call.answer()


# ---- Invite codes: generate ----

@router.callback_query(F.data == "admin_codes")
async def cb_admin_codes(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(InviteCode).order_by(InviteCode.id.desc()).limit(20)
        )
        codes = result.scalars().all()

    lines = ["\U0001F511 <b>Коды доступа</b>\n"]
    if codes:
        for c in codes:
            status = "\u2705" if c.active and c.used_count < c.max_uses else "\u274c"
            lines.append(f"{status} <code>{c.code}</code> - {c.used_count}/{c.max_uses} исп.")
    else:
        lines.append("Кодов пока нет.")

    lines.append("\n\nДля создания нового кода используйте команду:\n<code>/newcode</code>")

    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=back_button("main_menu"),
    )
    await call.answer()


@router.message(F.text == "/newcode")
async def cmd_newcode(message: Message):
    if not is_admin(message.from_user.id):
        return

    code = "SREDA-" + secrets.token_hex(4).upper()

    async with async_session() as session:
        # Get or create default group
        grp = await session.execute(select(Group).limit(1))
        group = grp.scalar_one_or_none()
        group_id = group.id if group else None

        invite = InviteCode(
            code=code,
            group_id=group_id,
            max_uses=1,
            used_count=0,
            active=True,
        )
        session.add(invite)
        await session.commit()

    await message.answer(
        f"\u2705 Создан новый код доступа:\n\n"
        f"<code>{code}</code>\n\n"
        f"Передайте его ученику. Код одноразовый."
    )


# ---- Content management (modules) ----

@router.callback_query(F.data == "admin_content")
async def cb_admin_content(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(Module).order_by(Module.order))
        modules = result.scalars().all()

    lines = ["\U0001F4DA <b>Управление контентом</b>\n"]
    if modules:
        for m in modules:
            lines.append(f"\U0001F4C1 <b>{m.title}</b>")
    else:
        lines.append("Модулей пока нет.")

    lines.append("\n\nКоманды:")
    lines.append("<code>/addmodule</code> - добавить модуль")
    lines.append("<code>/addlesson</code> - добавить урок")

    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=back_button("main_menu"),
    )
    await call.answer()


@router.message(F.text == "/addmodule")
async def cmd_addmodule_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_module_title)
    await message.answer(
        "\U0001F4C1 <b>Новый модуль</b>\n\n"
        "Введите название модуля (например: Модуль 1: Рынок новостроек):"
    )


@router.message(AdminStates.waiting_for_module_title)
async def cmd_addmodule_save(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("Введите корректное название.")
        return

    async with async_session() as session:
        max_order = await session.execute(
            select(func.max(Module.order))
        )
        next_order = (max_order.scalar() or 0) + 1

        module = Module(title=title, order=next_order)
        session.add(module)
        await session.commit()

    await state.clear()
    await message.answer(
        f"\u2705 Модуль «{title}» создан!\n\n"
        f"Теперь можно добавить уроки командой <code>/addlesson</code>."
    )


@router.message(F.text == "/addlesson")
async def cmd_addlesson_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    async with async_session() as session:
        result = await session.execute(select(Module).order_by(Module.order))
        modules = result.scalars().all()

    if not modules:
        await message.answer(
            "\u274C Сначала создайте модуль командой <code>/addmodule</code>."
        )
        return

    lines = ["\U0001F4C4 <b>Добавить урок</b>\n\nВыберите модуль (введите его номер):\n"]
    for i, m in enumerate(modules, 1):
        lines.append(f"{i}. {m.title}")

    # Store module mapping in state
    module_map = {str(i): m.id for i, m in enumerate(modules, 1)}
    await state.set_state(AdminStates.waiting_for_lesson_module)
    await state.update_data(module_map=module_map)

    await message.answer("\n".join(lines))


@router.message(AdminStates.waiting_for_lesson_module)
async def cmd_addlesson_module(message: Message, state: FSMContext):
    num = message.text.strip()
    data = await state.get_data()
    module_map = data.get("module_map", {})

    if num not in module_map:
        await message.answer("Введите корректный номер модуля из списка.")
        return

    await state.set_state(AdminStates.waiting_for_lesson_title)
    await state.update_data(module_id=module_map[num])
    await message.answer("Введите название урока:")


@router.message(AdminStates.waiting_for_lesson_title)
async def cmd_addlesson_title(message: Message, state: FSMContext):
    title = message.text.strip()
    await state.set_state(AdminStates.waiting_for_lesson_content)
    await state.update_data(title=title)
    await message.answer(
        "Теперь введите текст урока (можно с разметкой HTML, эмодзи):\n\n"
        "<i>Поддерживаются теги: b, i, u, s, code, pre</i>"
    )


@router.message(AdminStates.waiting_for_lesson_content)
async def cmd_addlesson_save(message: Message, state: FSMContext):
    content = message.text or ""
    data = await state.get_data()
    module_id = data["module_id"]
    title = data["title"]

    async with async_session() as session:
        max_order = await session.execute(
            select(func.max(Lesson.order)).where(Lesson.module_id == module_id)
        )
        next_order = (max_order.scalar() or 0) + 1

        lesson = Lesson(
            module_id=module_id,
            title=title,
            content=content,
            order=next_order,
        )
        session.add(lesson)
        await session.commit()

    await state.clear()
    await message.answer(
        f"\u2705 Урок «{title}» добавлен!\n\n"
        f"Он уже доступен ученикам в базе знаний."
    )


# ---- Analytics (stub) ----

@router.callback_query(F.data == "admin_analytics")
async def cb_admin_analytics(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    async with async_session() as session:
        total_students = await session.scalar(
            select(func.count(Student.id))
        )
        active_students = await session.scalar(
            select(func.count(Student.id)).where(Student.status == "active")
        )
        total_attempts = await session.scalar(
            select(func.count(TestAttempt.id))
        )

    await call.message.edit_text(
        "\U0001F4CA <b>Аналитика</b>\n\n"
        f"\U0001F465 Учеников всего: <b>{total_students or 0}</b>\n"
        f"\U0001F7E2 Активных: <b>{active_students or 0}</b>\n"
        f"\U0001F4DD Пройдено тестов: <b>{total_attempts or 0}</b>\n\n"
        f"<i>Детальная аналитика будет добавлена в Фазе 4.</i>",
        reply_markup=back_button("main_menu"),
    )
    await call.answer()


# ---- Broadcast (stub) ----

@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    await call.message.edit_text(
        "\U0001F4E3 <b>Рассылка</b>\n\n"
        "Раздел будет добавлен в Фазе 6.\n"
        "Здесь будет: массовая рассылка, отложенная отправка, отчёты о доставке.",
        reply_markup=back_button("main_menu"),
    )
    await call.answer()


# ---- Tests management (stub) ----

@router.callback_query(F.data == "admin_tests")
async def cb_admin_tests(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    await call.message.edit_text(
        "\U0001F4DD <b>Управление тестами</b>\n\n"
        "Создание тестов будет в Фазе 3.\n"
        "Здесь будет: конструктор вопросов, настройка баллов, автопроверка.",
        reply_markup=back_button("main_menu"),
    )
    await call.answer()
