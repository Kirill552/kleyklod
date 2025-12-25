"""
Обработчики профиля и статистики.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import get_plans_kb, get_profile_kb
from bot.utils import get_api_client

router = Router(name="profile")


# Тексты
PROFILE_TEXT = """
<b>Ваш профиль</b>

<b>Тариф:</b> {plan_name}
<b>Лимит:</b> {used}/{limit} этикеток сегодня

<b>Статистика:</b>
• Всего сгенерировано: {total_labels}
• Успешных генераций: {success_count}
• Pre-flight ошибок: {preflight_errors}

<b>Дата регистрации:</b> {registered_at}
"""

PLANS_TEXT = """
<b>Тарифные планы</b>

<b>Free</b> — Бесплатно
• 50 этикеток в день
• Базовый Pre-flight
• Поддержка в чате

<b>Pro</b> — 490 ₽/мес
• 500 этикеток в день
• Расширенный Pre-flight
• Приоритетная поддержка
• История генераций

<b>Enterprise</b> — 1990 ₽/мес
• Безлимит этикеток
• API доступ
• Персональный менеджер
• SLA 99.9%

Для покупки подписки нажмите кнопку ниже.
"""


async def get_profile_data(user_id: int) -> dict:
    """Получить данные профиля из API."""
    api = get_api_client()
    user_data = await api.get_user_profile(user_id)

    if not user_data:
        return {
            "plan_name": "Free",
            "used": 0,
            "limit": 50,
            "total_labels": 0,
            "success_count": 0,
            "preflight_errors": 0,
            "registered_at": "Сегодня",
        }

    return {
        "plan_name": user_data.get("plan", "Free").title(),
        "used": user_data.get("used_today", 0),
        "limit": user_data.get("daily_limit", 50),
        "total_labels": user_data.get("total_generated", 0),
        "success_count": user_data.get("success_count", 0),
        "preflight_errors": user_data.get("preflight_errors", 0),
        "registered_at": user_data.get("registered_at", "Сегодня")[:10],
    }


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Команда /profile."""
    profile_data = await get_profile_data(message.from_user.id)

    await message.answer(
        PROFILE_TEXT.format(**profile_data),
        reply_markup=get_profile_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    """Callback для кнопки Профиль."""
    profile_data = await get_profile_data(callback.from_user.id)

    await callback.message.edit_text(
        PROFILE_TEXT.format(**profile_data),
        reply_markup=get_profile_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("plans"))
async def cmd_plans(message: Message):
    """Команда /plans."""
    await message.answer(
        PLANS_TEXT,
        reply_markup=get_plans_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "plans")
async def cb_plans(callback: CallbackQuery):
    """Callback для кнопки Тарифы."""
    await callback.message.edit_text(
        PLANS_TEXT,
        reply_markup=get_plans_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.text == "Профиль")
async def text_profile(message: Message):
    """Текстовая команда Профиль."""
    profile_data = await get_profile_data(message.from_user.id)

    await message.answer(
        PROFILE_TEXT.format(**profile_data),
        reply_markup=get_profile_kb(),
        parse_mode="HTML",
    )
