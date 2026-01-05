"""
FSM состояния для процесса генерации этикеток.
"""

from aiogram.fsm.state import State, StatesGroup


class GenerateStates(StatesGroup):
    """
    Состояния процесса генерации этикеток.

    Workflow:
    1. waiting_excel - ожидание Excel с баркодами
    2. confirming_column - подтверждение автоопределённой колонки (HITL)
    3. selecting_column - ручной выбор колонки
    4. waiting_codes - ожидание CSV/Excel с кодами ЧЗ
    5. processing - генерация в процессе
    6. waiting_feedback - ожидание текста обратной связи
    """

    # Excel режим
    waiting_excel = State()  # Ожидание Excel с баркодами
    confirming_column = State()  # Подтверждение колонки (HITL)
    selecting_column = State()  # Ручной выбор колонки

    # Общие состояния
    waiting_codes = State()  # Ожидание CSV/Excel с кодами
    processing = State()  # Генерация в процессе
    waiting_feedback = State()  # Ожидание текста обратной связи
