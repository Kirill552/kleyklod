"""
Reply-клавиатуры для бота.
"""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_reply_kb() -> ReplyKeyboardMarkup:
    """Основная reply-клавиатура."""
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="Создать этикетки"),
    )
    builder.row(
        KeyboardButton(text="Мой профиль"),
        KeyboardButton(text="Помощь"),
    )

    return builder.as_markup(resize_keyboard=True)


def get_cancel_reply_kb() -> ReplyKeyboardMarkup:
    """Reply-клавиатура с кнопкой отмены."""
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="Отмена"),
    )

    return builder.as_markup(resize_keyboard=True)
