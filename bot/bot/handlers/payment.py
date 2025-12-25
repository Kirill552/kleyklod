"""
Обработчики оплаты через Telegram Stars.
"""

from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from bot.keyboards.inline import get_back_to_menu_kb, get_main_menu_kb
from bot.utils import get_api_client

router = Router(name="payment")


# Цены в Stars (1 Star ≈ 1.3₽)
PRICES = {
    "pro": {
        "name": "Pro подписка",
        "description": "500 этикеток/день, расширенный Pre-flight",
        "stars": 377,  # ~490₽
        "duration_days": 30,
    },
    "enterprise": {
        "name": "Enterprise подписка",
        "description": "Безлимит, API доступ, SLA 99.9%",
        "stars": 1531,  # ~1990₽
        "duration_days": 30,
    },
}


@router.callback_query(F.data == "buy_pro")
async def cb_buy_pro(callback: CallbackQuery, bot: Bot):
    """Покупка Pro подписки."""
    plan = PRICES["pro"]

    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=plan["name"],
        description=plan["description"],
        payload="subscription_pro_30",
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=plan["name"], amount=plan["stars"])],
    )
    await callback.answer()


@router.callback_query(F.data == "buy_enterprise")
async def cb_buy_enterprise(callback: CallbackQuery, bot: Bot):
    """Покупка Enterprise подписки."""
    plan = PRICES["enterprise"]

    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=plan["name"],
        description=plan["description"],
        payload="subscription_enterprise_30",
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=plan["name"], amount=plan["stars"])],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Pre-checkout валидация."""
    # TODO: Проверить, что пользователь может купить подписку
    # TODO: Проверить лимиты и ограничения

    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    """Успешная оплата."""
    payment = message.successful_payment
    payload = payment.invoice_payload

    # Определяем тип подписки
    if "pro" in payload:
        plan_name = "pro"
        plan_display = "Pro"
        days = 30
    elif "enterprise" in payload:
        plan_name = "enterprise"
        plan_display = "Enterprise"
        days = 30
    else:
        plan_name = "unknown"
        plan_display = "Unknown"
        days = 0

    # Активируем подписку через API
    api = get_api_client()
    result = await api.activate_subscription(
        telegram_id=message.from_user.id,
        plan=plan_name,
        duration_days=days,
        telegram_payment_charge_id=payment.telegram_payment_charge_id,
        provider_payment_charge_id=payment.provider_payment_charge_id,
        total_amount=payment.total_amount,
    )

    if result and result.get("success"):
        success_text = f"""
<b>Оплата успешна!</b>

Подписка: {plan_display}
Срок: {days} дней

Спасибо за покупку! Ваши новые лимиты уже активны.
"""
    else:
        success_text = f"""
<b>Оплата получена!</b>

Подписка: {plan_display}

Ваша подписка будет активирована в течение нескольких минут.
Если этого не произошло, обратитесь в поддержку: @KleyKodSupport
"""

    await message.answer(
        success_text,
        reply_markup=get_main_menu_kb(),
        parse_mode="HTML",
    )


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

            if status == "completed":
                status_icon = "[OK]"
            elif status == "pending":
                status_icon = "[...]"
            else:
                status_icon = "[X]"

            lines.append(f"{status_icon} {date} - {plan} ({amount} Stars)")

        history_text = "\n".join(lines)

    await callback.message.edit_text(
        history_text,
        reply_markup=get_back_to_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()
