"""
Обработчики оплаты через Telegram Stars.
"""

import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from bot.keyboards.inline import get_back_to_menu_kb, get_main_menu_kb
from bot.utils import get_api_client

logger = logging.getLogger(__name__)
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


@router.message(CommandStart(deep_link=True))
async def handle_deep_link_payment(message: Message, bot: Bot):
    """
    Обработчик deep link для прямой оплаты.

    Формат: t.me/BotName?start=pay_pro_abc123 или pay_enterprise_abc123
    """
    # Извлекаем аргумент из команды /start
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return

    deep_link_arg = args[1]

    # Проверяем, что это платёжная ссылка
    if not deep_link_arg.startswith("pay_"):
        return

    # Парсим аргумент: pay_pro_abc123 → plan=pro, payment_id=abc123
    parts = deep_link_arg.split("_", 2)  # ["pay", "pro", "abc123"]
    if len(parts) < 2:
        logger.warning(f"[PAYMENT] Некорректный deep link: {deep_link_arg}")
        await message.answer(
            "Некорректная ссылка для оплаты. Попробуйте выбрать план из меню.",
            reply_markup=get_main_menu_kb(),
        )
        return

    plan_name = parts[1]  # "pro" или "enterprise"
    payment_id = parts[2] if len(parts) > 2 else "direct"  # ID платежа для трекинга

    # Проверяем, что план существует
    if plan_name not in PRICES:
        logger.warning(f"[PAYMENT] Неизвестный план в deep link: {plan_name}")
        await message.answer(
            "Неизвестный тарифный план. Выберите из доступных.",
            reply_markup=get_main_menu_kb(),
        )
        return

    plan = PRICES[plan_name]

    logger.info(
        f"[PAYMENT] Deep link оплата: user={message.from_user.id}, plan={plan_name}, ref={payment_id}"
    )

    # Отправляем инвойс
    await bot.send_invoice(
        chat_id=message.chat.id,
        title=plan["name"],
        description=plan["description"],
        payload=f"subscription_{plan_name}_30_{payment_id}",  # Добавляем payment_id для трекинга
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=plan["name"], amount=plan["stars"])],
    )

    # Отправляем сообщение с инструкцией
    await message.answer(
        f"Счёт на оплату подписки <b>{plan['name']}</b> отправлен выше.\n\n"
        f"После оплаты подписка активируется автоматически.",
        parse_mode="HTML",
    )


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
    """
    Pre-checkout валидация перед оплатой.

    Проверяем:
    - Корректность payload
    - Доступность Backend API
    - Возможность активации подписки для пользователя
    """
    payload = pre_checkout_query.invoice_payload
    user_id = pre_checkout_query.from_user.id

    logger.info(f"[PAYMENT] Pre-checkout: user={user_id}, payload={payload}")

    # Базовая валидация payload
    if not payload or "subscription" not in payload:
        logger.warning(f"[PAYMENT] Некорректный payload в pre-checkout: {payload}")
        await pre_checkout_query.answer(
            ok=False,
            error_message="Некорректные данные платежа. Попробуйте снова.",
        )
        return

    # Проверяем доступность Backend API
    api = get_api_client()
    api_available = await api.health_check()

    if not api_available:
        logger.error(f"[PAYMENT] Backend API недоступен при pre-checkout для user={user_id}")
        await pre_checkout_query.answer(
            ok=False,
            error_message="Сервис временно недоступен. Попробуйте через несколько минут.",
        )
        return

    # Всё в порядке, разрешаем оплату
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    """
    Обработка успешной оплаты через Telegram Stars.

    После получения payment от Telegram:
    1. Парсим payload для определения плана
    2. Вызываем Backend API для активации подписки
    3. Отправляем подтверждение пользователю
    """
    payment = message.successful_payment
    payload = payment.invoice_payload

    logger.info(
        f"[PAYMENT] Получена оплата: user={message.from_user.id}, "
        f"amount={payment.total_amount} Stars, payload={payload}"
    )

    # Парсим payload: "subscription_pro_30" или "subscription_pro_30_abc123"
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
        logger.error(f"[PAYMENT] Неизвестный payload: {payload}")
        plan_name = "unknown"
        plan_display = "Unknown"
        days = 0

    # Активируем подписку через Backend API
    api = get_api_client()

    try:
        result = await api.activate_subscription(
            telegram_id=message.from_user.id,
            plan=plan_name,
            duration_days=days,
            telegram_payment_charge_id=payment.telegram_payment_charge_id,
            provider_payment_charge_id=payment.provider_payment_charge_id,
            total_amount=payment.total_amount,
        )

        if result and result.get("success"):
            logger.info(
                f"[PAYMENT] Подписка активирована: user={message.from_user.id}, plan={plan_name}"
            )

            success_text = f"""
<b>Оплата успешна!</b>

Подписка: {plan_display}
Срок: {days} дней
Оплачено: {payment.total_amount} Stars

Спасибо за покупку! Ваши новые лимиты уже активны.
"""
        else:
            # API вернул ошибку или не смог активировать
            logger.warning(
                f"[PAYMENT] Ошибка активации через API: user={message.from_user.id}, "
                f"result={result}"
            )

            success_text = f"""
<b>Оплата получена!</b>

Подписка: {plan_display}
Сумма: {payment.total_amount} Stars

Ваша подписка будет активирована в течение нескольких минут.
Если этого не произошло, обратитесь в поддержку: @KleyKodSupport

ID платежа: <code>{payment.telegram_payment_charge_id}</code>
"""

    except Exception as e:
        # Непредвиденная ошибка при обращении к API
        logger.error(
            f"[PAYMENT] Исключение при активации подписки: user={message.from_user.id}, "
            f"error={str(e)}",
            exc_info=True,
        )

        success_text = f"""
<b>Оплата получена!</b>

Подписка: {plan_display}
Сумма: {payment.total_amount} Stars

Произошла ошибка при активации подписки. Наша команда уже уведомлена.
Ваша подписка будет активирована вручную в ближайшее время.

Обратитесь в поддержку: @KleyKodSupport
ID платежа: <code>{payment.telegram_payment_charge_id}</code>
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
