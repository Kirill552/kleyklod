"""
Обработчики команды /support — чат с поддержкой.

Сообщения пересылаются в VK личку админа, ответы приходят обратно в Telegram.
"""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import get_back_to_menu_kb, get_cancel_kb
from bot.states import SupportStates
from bot.utils.api_client import get_api_client

logger = logging.getLogger(__name__)

router = Router(name="support")


# Тексты
SUPPORT_START_TEXT = """
<b>Поддержка KleyKod</b>

Напишите ваш вопрос — мы ответим в ближайшее время.

Ответ придёт прямо сюда, в Telegram.
"""

SUPPORT_SENT_TEXT = """
<b>Сообщение отправлено!</b>

Мы ответим в ближайшее время.
Ответ придёт прямо сюда, в Telegram.
"""

SUPPORT_ERROR_TEXT = """
<b>Ошибка отправки</b>

Попробуйте позже или напишите на support@kleykod.ru
"""


@router.message(Command("support"))
async def cmd_support(message: Message, state: FSMContext):
    """Команда /support — начало диалога с поддержкой."""
    await state.set_state(SupportStates.waiting_message)

    await message.answer(
        SUPPORT_START_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "support")
async def cb_support(callback: CallbackQuery, state: FSMContext):
    """Callback для кнопки Поддержка."""
    await state.set_state(SupportStates.waiting_message)

    await callback.message.edit_text(
        SUPPORT_START_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SupportStates.waiting_message, F.text)
async def receive_support_message(message: Message, state: FSMContext):
    """Получение сообщения для поддержки."""
    telegram_id = message.from_user.id
    text = message.text.strip()

    # Отправляем через API
    api_client = get_api_client()
    result = await api_client.send_support_message(telegram_id, text)

    if result.success:
        logger.info(f"[SUPPORT] Сообщение от {telegram_id} отправлено")
        await message.answer(
            SUPPORT_SENT_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
    else:
        logger.error(f"[SUPPORT] Ошибка отправки от {telegram_id}: {result.error}")
        await message.answer(
            SUPPORT_ERROR_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )

    await state.clear()
