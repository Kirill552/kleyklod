"""
FSM состояния для процесса генерации этикеток.
"""

from aiogram.fsm.state import State, StatesGroup


class GenerateStates(StatesGroup):
    """
    Состояния процесса генерации этикеток.

    Workflow PDF:
    1. choosing_mode - выбор режима (PDF или Excel)
    2. waiting_pdf - ожидание PDF от Wildberries
    3. waiting_codes - ожидание CSV/Excel с кодами ЧЗ
    4. choosing_format - выбор формата этикеток (объединённые/раздельные)
    5. processing - генерация в процессе
    6. waiting_feedback - ожидание текста обратной связи

    Workflow Excel:
    1. choosing_mode - выбор режима (PDF или Excel)
    2. waiting_excel - ожидание Excel с баркодами
    3. confirming_column - подтверждение автоопределённой колонки (HITL)
    4. selecting_column - ручной выбор колонки
    5. waiting_codes - ожидание CSV/Excel с кодами ЧЗ
    6. choosing_format - выбор формата этикеток
    7. processing - генерация в процессе
    """

    # Выбор режима загрузки
    choosing_mode = State()  # PDF или Excel

    # PDF режим (существующий)
    waiting_pdf = State()  # Ожидание PDF файла от WB

    # Excel режим (новый)
    waiting_excel = State()  # Ожидание Excel с баркодами
    confirming_column = State()  # Подтверждение колонки (HITL)
    selecting_column = State()  # Ручной выбор колонки

    # Общие состояния
    waiting_codes = State()  # Ожидание CSV/Excel с кодами
    choosing_format = State()  # Выбор формата этикеток
    confirming = State()  # Подтверждение генерации (deprecated)
    processing = State()  # Генерация в процессе
    waiting_feedback = State()  # Ожидание текста обратной связи
