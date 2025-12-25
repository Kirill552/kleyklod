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
    3. confirming - подтверждение перед генерацией
    4. processing - генерация в процессе
    """

    waiting_pdf = State()      # Ожидание PDF файла от WB
    waiting_codes = State()    # Ожидание CSV/Excel с кодами
    confirming = State()       # Подтверждение генерации
    processing = State()       # Генерация в процессе
