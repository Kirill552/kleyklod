"""
FSM состояния для процесса генерации этикеток.
"""

from aiogram.fsm.state import State, StatesGroup


class GenerateStates(StatesGroup):
    """
    Состояния процесса генерации этикеток.

    Workflow:
    1. waiting_pdf - ожидание PDF от Wildberries
    2. waiting_codes - ожидание CSV/Excel с кодами ЧЗ
    3. choosing_format - выбор формата этикеток (объединённые/раздельные)
    4. confirming - подтверждение перед генерацией
    5. processing - генерация в процессе
    """

    waiting_pdf = State()  # Ожидание PDF файла от WB
    waiting_codes = State()  # Ожидание CSV/Excel с кодами
    choosing_format = State()  # Выбор формата этикеток
    confirming = State()  # Подтверждение генерации
    processing = State()  # Генерация в процессе
