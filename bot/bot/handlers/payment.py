"""
Обработчики оплаты через ЮКассу.
"""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.inline import get_back_to_menu_kb
from bot.utils import get_api_client

logger = logging.getLogger(__name__)
router = Router(name="payment")


# Тарифы в рублях
PLANS = {
    "pro": {"name": "Pro", "price": 490, "days": 30},
    "enterprise": {"name": "Enterprise", "price": 1990, "days": 30},
}


async def _initiate_payment(callback: CallbackQuery, plan: str):
    """
    Инициализация платежа через ЮКассу.

    Args:
        callback: Callback query от пользователя
        plan: Название тарифа (pro / enterprise)
    """
    user_id = callback.from_user.id
    plan_info = PLANS[plan]

    await callback.message.edit_text(
        f"Создаю платёж для подписки {plan_info['name']}...",
    )

    api = get_api_client()
    result = await api.create_yookassa_payment(
        plan=plan,
        telegram_id=user_id,
    )

    if not result or not result.get("confirmation_url"):
        await callback.message.edit_text(
            "Ошибка создания платежа. Попробуйте позже.",
            reply_markup=get_back_to_menu_kb(),
        )
        return

    # Кнопка со ссылкой на оплату
    kb = InlineKeyboardBuilder()
    kb.button(text=f"Оплатить {plan_info['price']} руб.", url=result["confirmation_url"])
    kb.button(text="Назад к тарифам", callback_data="plans")
    kb.adjust(1)

    await callback.message.edit_text(
        f"<b>Подписка {plan_info['name']}</b>\n\n"
        f"Стоимость: {plan_info['price']} руб./месяц\n"
        f"Срок: {plan_info['days']} дней\n\n"
        "Нажмите кнопку ниже для перехода на страницу оплаты.\n"
        "После оплаты подписка активируется автоматически.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "buy_pro")
async def cb_buy_pro(callback: CallbackQuery):
    """Покупка Pro подписки."""
    await _initiate_payment(callback, "pro")


@router.callback_query(F.data == "buy_enterprise")
async def cb_buy_enterprise(callback: CallbackQuery):
    """Покупка Enterprise подписки."""
    await _initiate_payment(callback, "enterprise")


@router.callback_query(F.data == "payment_history")
async def cb_payment_history(callback: CallbackQuery):
    """История платежей."""
    api = get_api_client()
    history = await api.get_payment_history(callback.from_user.id)

    if not history:
        history_text = """
<b>История платежей</b>

У вас пока нет платежей.

Оформите подписку Pro или Enterprise для расширенных возможностей!
"""
    else:
        lines = ["<b>История платежей</b>\n"]
        for payment in history[:10]:  # Последние 10
            date = payment.get("created_at", "")[:10]
            amount = payment.get("amount", 0)
            plan = payment.get("plan", "").title()
            status = payment.get("status", "")

            if status == "succeeded":
                status_icon = "✅"
            elif status == "pending":
                status_icon = "⏳"
            elif status == "canceled":
                status_icon = "❌"
            else:
                status_icon = "❓"

            lines.append(f"{status_icon} {date} - {plan} ({amount} руб.)")

        history_text = "\n".join(lines)

    await callback.message.edit_text(
        history_text,
        reply_markup=get_back_to_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()
