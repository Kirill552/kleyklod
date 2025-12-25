"""
Inline-клавиатуры для бота.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню бота."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Создать этикетки",
            callback_data="generate",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Мой профиль",
            callback_data="profile",
        ),
        InlineKeyboardButton(
            text="Тарифы",
            callback_data="plans",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Помощь",
            callback_data="help",
        ),
        InlineKeyboardButton(
            text="О сервисе",
            callback_data="about",
        ),
    )

    return builder.as_markup()


def get_cancel_kb() -> InlineKeyboardMarkup:
    """Клавиатура отмены операции."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Отменить",
            callback_data="cancel",
        )
    )

    return builder.as_markup()


def get_confirm_kb(labels_count: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения генерации."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"Сгенерировать {labels_count} этикеток",
            callback_data="confirm_generate",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Отменить",
            callback_data="cancel",
        )
    )

    return builder.as_markup()


def get_format_choice_kb() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора формата этикеток.

    - combined: WB + DataMatrix на одной этикетке
    - separate: WB и DataMatrix на отдельных листах
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Объединённые (WB + ЧЗ на одной)",
            callback_data="format_combined",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Раздельные (WB и ЧЗ отдельно)",
            callback_data="format_separate",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Отменить",
            callback_data="cancel",
        )
    )

    return builder.as_markup()


def get_plans_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора тарифа."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Free (50 шт/день)",
            callback_data="plan_free",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Pro - 490 руб/мес",
            callback_data="plan_pro",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Enterprise - 1990 руб/мес",
            callback_data="plan_enterprise",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="back_to_menu",
        )
    )

    return builder.as_markup()


def get_payment_kb(plan: str, price_stars: int) -> InlineKeyboardMarkup:
    """Клавиатура оплаты через Stars."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"Оплатить {price_stars} Stars",
            callback_data=f"pay_stars_{plan}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад к тарифам",
            callback_data="plans",
        )
    )

    return builder.as_markup()


def get_back_to_menu_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="В главное меню",
            callback_data="back_to_menu",
        )
    )

    return builder.as_markup()


def get_consent_kb() -> InlineKeyboardMarkup:
    """Клавиатура согласия на обработку ПДн (152-ФЗ)."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Принимаю условия",
            callback_data="consent_accept",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Политика конфиденциальности",
            url="https://kleykod.ru/privacy",
        )
    )

    return builder.as_markup()


def get_profile_kb() -> InlineKeyboardMarkup:
    """Клавиатура профиля пользователя."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Купить Pro",
            callback_data="buy_pro",
        ),
        InlineKeyboardButton(
            text="Enterprise",
            callback_data="buy_enterprise",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="История платежей",
            callback_data="payment_history",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="В главное меню",
            callback_data="back_to_menu",
        )
    )

    return builder.as_markup()
