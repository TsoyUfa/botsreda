"""Start handler + authentication flow (invite codes, roles)."""
from __future__ import annotations

from datetime import datetime

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.db import async_session
from bot.models import User, Student, InviteCode, Group
from bot.config import ADMIN_IDS
from bot.states import AuthStates
from bot.keyboards import (
    student_main_menu, admin_main_menu, back_button,
)

router = Router(name="start")


# ---- Helpers ----

async def get_or_create_user(telegram_id: int, username: str | None, full_name: str | None) -> User:
    """Get existing user or create a new empty one."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                role="student",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Update username/name if changed
            changed = False
            if username and user.username != username:
                user.username = username
                changed = True
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                changed = True
            if changed:
                await session.commit()
        return user


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


async def show_main_menu(event_or_call):
    """Show the right menu based on role."""
    # This is called from various places; determine user from the callback
    pass


# ---- /start command ----

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    user = await get_or_create_user(telegram_id, username, full_name)

    # Admin check
    if is_admin(telegram_id):
        # Ensure role is admin in DB
        async with async_session() as session:
            db_user = await session.get(User, user.id)
            if db_user.role != "admin":
                db_user.role = "admin"
                await session.commit()
        await message.answer(
            "\U0001F3E0 <b>Админ-панель</b>\n\n"
            "Добро пожаловать! Вы вошли как администратор.\n"
            "Выберите раздел:",
            reply_markup=admin_main_menu(),
        )
        return

    # Student check: does student profile exist?
    async with async_session() as session:
        stu_result = await session.execute(
            select(Student).where(Student.user_id == user.id)
        )
        student = stu_result.scalar_one_or_none()

    if student is not None:
        # Existing student
        if student.status == "blocked":
            await message.answer(
                "\u26d4 Ваш доступ приостановлен.\n"
                "Свяжитесь с куратором."
            )
            return
        await message.answer(
            f"\U0001F44B С возвращением, <b>{student.full_name_ru or full_name}</b>!\n\n"
            "Выберите раздел:",
            reply_markup=student_main_menu(),
        )
        return

    # New user → ask for invite code
    await state.set_state(AuthStates.waiting_for_code)
    await message.answer(
        "\U0001F511 <b>Вход в Академию</b>\n\n"
        "Введите пригласительный код, который выдал куратор.\n\n"
        "<i>Нет кода? Обратитесь к куратору.</i>"
    )


# ---- Invite code input ----

@router.message(AuthStates.waiting_for_code)
async def process_invite_code(message: Message, state: FSMContext):
    code_text = message.text.strip().upper() if message.text else ""

    async with async_session() as session:
        result = await session.execute(
            select(InviteCode).where(InviteCode.code == code_text)
        )
        invite = result.scalar_one_or_none()

    if invite is None:
        await message.answer(
            "\u274C Код не найден. Проверьте правильность ввода.\n\n"
            "Введите код ещё раз или обратитесь к куратору."
        )
        return

    if not invite.active:
        await message.answer("\u274C Этот код больше не активен. Обратитесь к куратору.")
        return

    if invite.used_count >= invite.max_uses:
        await message.answer("\u274C Этот код исчерпан. Обратитесь к куратору за новым кодом.")
        return

    if invite.expires_at and invite.expires_at < datetime.utcnow():
        await message.answer("\u274C Срок действия кода истёк. Обратитесь к куратору.")
        return

    # Code is valid → register student
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    async with async_session() as session:
        # Increment usage
        invite_db = await session.get(InviteCode, invite.id)
        invite_db.used_count += 1

        # Create student profile
        student = Student(
            user_id=user.id,
            group_id=invite.group_id,
            status="active",
            full_name_ru=None,  # will ask next
        )
        session.add(student)
        await session.commit()

    # Ask for full name
    await state.set_state(AuthStates.waiting_for_name)
    await state.update_data(student_user_id=user.id)
    await message.answer(
        "\u2705 Код принят!\n\n"
        "\U0001F464 Как вас зовут? Введите ФИО (например: Иван Иванов)."
    )


@router.message(AuthStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""
    if not name or len(name) < 2:
        await message.answer("Пожалуйста, введите корректное имя (минимум 2 символа).")
        return

    data = await state.get_data()
    user_id = data.get("student_user_id")

    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.user_id == user_id)
        )
        student = result.scalar_one_or_none()
        if student:
            student.full_name_ru = name
            await session.commit()

    await state.clear()
    await message.answer(
        f"\U0001F389 Добро пожаловать, <b>{name}</b>!\n\n"
        "Вы успешно зарегистрированы в Академии новостроек.\n"
        "Выберите раздел для начала обучения:",
        reply_markup=student_main_menu(),
    )


# ---- Back to main menu (callback) ----

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    telegram_id = call.from_user.id
    user = await get_or_create_user(telegram_id, call.from_user.username, call.from_user.full_name)

    if is_admin(telegram_id):
        await call.message.edit_text(
            "\U0001F3E0 <b>Админ-панель</b>\n\nВыберите раздел:",
            reply_markup=admin_main_menu(),
        )
    else:
        async with async_session() as session:
            stu_result = await session.execute(
                select(Student).where(Student.user_id == user.id)
            )
            student = stu_result.scalar_one_or_none()

        if student and student.status != "blocked":
            name = student.full_name_ru or call.from_user.full_name
            await call.message.edit_text(
                f"\U0001F44B <b>{name}</b>, выберите раздел:",
                reply_markup=student_main_menu(),
            )
        else:
            await call.message.edit_text(
                "\u26d4 Доступ приостановлен. Свяжитесь с куратором."
            )
    await call.answer()


# ---- Help ----

@router.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery):
    await call.message.edit_text(
        "\u2753 <b>Помощь</b>\n\n"
        "\U0001F4DA <b>База знаний</b> - теория по модулям\n"
        "\U0001F4DD <b>Тесты</b> - проверка знаний\n"
        "\U0001F4CA <b>Мой прогресс</b> - ваши результаты\n\n"
        "Вопросы? Напишите куратору.",
        reply_markup=back_button(),
    )
    await call.answer()
