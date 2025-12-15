from __future__ import annotations

from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class BroadcastState(StatesGroup):
    wait_msg = State()
    confirm = State()
