"""FSM states for the bot."""
from aiogram.fsm.state import State, StatesGroup


class AuthStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_name = State()


class AdminStates(StatesGroup):
    waiting_for_code_name = State()       # create invite: enter code text
    waiting_for_module_title = State()     # add module
    waiting_for_module_desc = State()
    waiting_for_lesson_title = State()     # add lesson
    waiting_for_lesson_content = State()
    waiting_for_lesson_module = State()


class TestStates(StatesGroup):
    answering = State()
