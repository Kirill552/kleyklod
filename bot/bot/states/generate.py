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
    5. waiting_organization - ожидание названия организации (первая генерация)
    6. waiting_inn - ожидание ИНН (опционально)
    7. processing - генерация в процессе
    8. waiting_feedback - ожидание текста обратной связи
    """

    # Excel режим
    waiting_excel = State()  # Ожидание Excel с баркодами
    confirming_column = State()  # Подтверждение колонки (HITL)
    selecting_column = State()  # Ручной выбор колонки

    # Общие состояния
    waiting_codes = State()  # Ожидание CSV/Excel с кодами

    # Первая генерация — сбор данных организации
    waiting_organization = State()  # Ожидание названия организации
    waiting_inn = State()  # Ожидание ИНН (опционально)

    processing = State()  # Генерация в процессе
    waiting_feedback = State()  # Ожидание текста обратной связи


class SettingsStates(StatesGroup):
    """
    Состояния редактирования настроек пользователя.

    Используется в /settings для изменения организации и ИНН.
    """

    waiting_organization = State()  # Ожидание новой организации
    waiting_inn = State()  # Ожидание нового ИНН
