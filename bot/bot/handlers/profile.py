"""
Обработчики профиля и статистики.
"""

from datetime import UTC, datetime, timedelta

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
<b>Сегодня:</b> {limit_text}
{progress_bar}

<b>Всего создано:</b> {total_labels} этикеток
<b>Экономия:</b> ~{saved_money}

<b>На сайте доступно:</b>
- База ваших товаров ({products_count} шт)
- История генераций (PRO){trial_warning}
"""

TRIAL_ENDING_WARNING = """
<b>Trial заканчивается через {days_left} дней!</b>"""

PLANS_TEXT = """
<b>Тарифные планы</b>

<b>FREE</b> — бесплатно
- 50 этикеток в день
- Проверка качества

<b>PRO</b> — 490 руб/мес
- 500 этикеток в день
- История 7 дней
- База товаров (100 шт)

<b>ENTERPRISE</b> — 1990 руб/мес
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
        limit: Дневной лимит
        width: Ширина бара в символах

    Returns:
        "████████░░ 76%" или "∞ Безлимит" для Enterprise
    """
    if limit == 0:
        return ""

    percent = min(used / limit, 1.0)
    filled = int(width * percent)
    empty = width - filled

    bar = "█" * filled + "░" * empty
    percent_text = f"{int(percent * 100)}%"

    return f"{bar} {percent_text}"


def get_trial_days_left(trial_ends_at: str | None) -> int | None:
    """
    Вычислить сколько дней осталось до конца trial.

    Args:
        trial_ends_at: ISO дата окончания trial или None

    Returns:
        Количество дней или None если trial не активен
    """
    if not trial_ends_at:
        return None

    try:
        if "T" in trial_ends_at:
            trial_end = datetime.fromisoformat(trial_ends_at.replace("Z", "+00:00"))
        else:
            trial_end = datetime.strptime(trial_ends_at[:10], "%Y-%m-%d").replace(tzinfo=UTC)

        now = datetime.now(UTC)
        time_left = trial_end - now

        if time_left <= timedelta(0):
            return None

        return time_left.days
    except (ValueError, TypeError):
        return None


def check_trial_ending(trial_ends_at: str | None) -> bool:
    """
    Проверить, заканчивается ли trial в течение суток.

    Args:
        trial_ends_at: ISO дата окончания trial или None

    Returns:
        True если trial заканчивается менее чем через сутки
    """
    if not trial_ends_at:
        return False

    try:
        # Парсим дату окончания trial
        if "T" in trial_ends_at:
            trial_end = datetime.fromisoformat(trial_ends_at.replace("Z", "+00:00"))
        else:
            trial_end = datetime.strptime(trial_ends_at[:10], "%Y-%m-%d").replace(tzinfo=UTC)

        now = datetime.now(UTC)
        time_left = trial_end - now

        # Если осталось меньше суток и trial ещё не закончился
        return timedelta(0) < time_left < timedelta(days=1)
    except (ValueError, TypeError):
        return False


async def get_profile_data(user_id: int) -> dict:
    """Получить данные профиля из API."""
    api = get_api_client()
    user_data = await api.get_user_profile(user_id)

    if not user_data:
        return {
            "plan_name": "Free",
            "limit_text": "50/50 этикеток",
            "progress_bar": get_progress_bar(0, 50),
            "total_labels": 0,
            "saved_money": "0 руб",
            "products_count": 0,
            "trial_warning": "",
        }

    total_labels = user_data.get("total_generated", 0)
    trial_ends_at = user_data.get("trial_ends_at")
    used = user_data.get("used_today", 0)
    limit = user_data.get("daily_limit", 50)
    plan = user_data.get("plan", "free").lower()

    # Названия тарифов с эмодзи
    plan_names = {
        "free": "Free",
        "pro": "Pro",
        "enterprise": "Enterprise",
    }
    plan_name = plan_names.get(plan, "Free")

    # Лимит и прогресс-бар
    if limit == 0:  # Enterprise — безлимит
        limit_text = "Безлимит"
        progress_bar = ""
    else:
        remaining = max(0, limit - used)
        limit_text = f"{remaining}/{limit} этикеток"
        progress_bar = get_progress_bar(used, limit)

    # Предупреждение о trial
    trial_warning = ""
    days_left = get_trial_days_left(trial_ends_at)
    if days_left is not None and days_left <= 7:
        if days_left == 0:
            trial_warning = "\n\n<b>Trial заканчивается сегодня!</b>"
        elif days_left == 1:
            trial_warning = "\n\n<b>Trial заканчивается завтра!</b>"
        else:
            trial_warning = "\n" + TRIAL_ENDING_WARNING.format(days_left=days_left)

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
        "trial_warning": trial_warning,
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
