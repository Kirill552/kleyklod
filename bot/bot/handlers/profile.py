"""
Обработчики профиля и статистики.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import get_plans_kb, get_profile_kb
from bot.utils import get_api_client

router = Router(name="profile")

# Порог для отображения безлимита (Enterprise = 999999 в backend)
UNLIMITED_THRESHOLD = 100000


def is_unlimited(limit: int) -> bool:
    """Проверка безлимитного тарифа."""
    return limit >= UNLIMITED_THRESHOLD


# Тексты
PROFILE_TEXT = """
<b>Ваш профиль</b>

<b>Тариф:</b> {plan_name}
<b>Баланс:</b> {limit_text}
{progress_bar}

<b>Всего создано:</b> {total_labels} этикеток
<b>Экономия:</b> ~{saved_money}

<b>На сайте доступно:</b>
- База ваших товаров ({products_count} шт)
- История генераций
"""

PLANS_TEXT = """
<b>Тарифные планы</b>

<b>Старт</b> — бесплатно
- 50 этикеток в месяц
- Проверка качества

<b>Про</b> — 490 руб/мес
- 2000 этикеток в месяц
- Накопление до 10 000 шт
- История 7 дней
- База товаров

<b>Бизнес</b> — 1990 руб/мес
- Безлимит этикеток
- История 30 дней
- База товаров (безлимит)
- API для интеграций

Все тарифы включают:
- Проверку качества DataMatrix
- Все возможности сайта
"""


def calculate_saved_money(total_labels: int) -> str:
    """
    Рассчитать сэкономленные деньги.

    Расчёт: total_labels * 1.5 рубля (средняя цена у конкурентов).
    """
    saved = total_labels * 1.5
    if saved >= 1000:
        return f"{saved / 1000:.1f}K руб"
    return f"{int(saved)} руб"


def get_progress_bar(used: int, limit: int, width: int = 10) -> str:
    """
    Генерирует текстовый прогресс-бар использования лимита.

    Args:
        used: Использовано этикеток
        limit: Месячный лимит
        width: Ширина бара в символах

    Returns:
        "████████░░ 76%" или "" для безлимита (Бизнес)
    """
    if limit == 0 or is_unlimited(limit):
        return ""

    percent = min(used / limit, 1.0)
    filled = int(width * percent)
    empty = width - filled

    bar = "█" * filled + "░" * empty
    percent_text = f"{int(percent * 100)}%"

    return f"{bar} {percent_text}"


async def get_profile_data(user_id: int) -> dict:
    """Получить данные профиля из API."""
    api = get_api_client()
    user_data = await api.get_user_profile(user_id)

    if not user_data:
        return {
            "plan_name": "Старт",
            "limit_text": "50/50 этикеток",
            "progress_bar": get_progress_bar(0, 50),
            "total_labels": 0,
            "saved_money": "0 руб",
            "products_count": 0,
        }

    total_labels = user_data.get("total_generated", 0)
    used = user_data.get("used_today", 0)
    limit = user_data.get("daily_limit", 50)
    plan = user_data.get("plan", "free").lower()

    # Названия тарифов с эмодзи
    plan_names = {
        "free": "Старт",
        "pro": "Про",
        "enterprise": "Бизнес",
    }
    plan_name = plan_names.get(plan, "Старт")

    # Лимит и прогресс-бар
    if limit == 0 or is_unlimited(limit):  # Enterprise — безлимит
        limit_text = "∞ Безлимит"
        progress_bar = ""
    else:
        remaining = max(0, limit - used)
        limit_text = f"{remaining}/{limit} этикеток"
        progress_bar = get_progress_bar(used, limit)

    # Количество товаров в базе (только для PRO/ENTERPRISE)
    products_count = 0
    if plan in ("pro", "enterprise"):
        products_count = await api.get_products_count(user_id)

    return {
        "plan_name": plan_name,
        "limit_text": limit_text,
        "progress_bar": progress_bar,
        "total_labels": total_labels,
        "saved_money": calculate_saved_money(total_labels),
        "products_count": products_count,
    }


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Команда /profile."""
    profile_data = await get_profile_data(message.from_user.id)

    # Формируем текст профиля
    profile_text = PROFILE_TEXT.format(**profile_data)

    # Определяем is_paid
    plan_name = profile_data.get("plan_name", "Free")
    is_paid = "pro" in plan_name.lower() or "enterprise" in plan_name.lower()

    await message.answer(
        profile_text,
        reply_markup=get_profile_kb(is_paid=is_paid),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    """Callback для кнопки Профиль."""
    profile_data = await get_profile_data(callback.from_user.id)

    # Формируем текст профиля
    profile_text = PROFILE_TEXT.format(**profile_data)

    # Определяем is_paid
    plan_name = profile_data.get("plan_name", "Free")
    is_paid = "pro" in plan_name.lower() or "enterprise" in plan_name.lower()

    await callback.message.edit_text(
        profile_text,
        reply_markup=get_profile_kb(is_paid=is_paid),
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

    # Формируем текст профиля
    profile_text = PROFILE_TEXT.format(**profile_data)

    # Определяем is_paid
    plan_name = profile_data.get("plan_name", "Free")
    is_paid = "pro" in plan_name.lower() or "enterprise" in plan_name.lower()

    await message.answer(
        profile_text,
        reply_markup=get_profile_kb(is_paid=is_paid),
        parse_mode="HTML",
    )
