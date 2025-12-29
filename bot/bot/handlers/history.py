"""
Обработчик истории генераций.

Команда /history показывает список генераций с пагинацией.
Pro и Enterprise пользователи могут видеть и скачивать свои файлы.
"""

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.keyboards.inline import get_back_to_menu_kb, get_history_kb
from bot.utils import get_api_client

router = Router(name="history")
logger = logging.getLogger(__name__)

# Количество генераций на странице
PAGE_SIZE = 5


# Тексты
HISTORY_EMPTY_TEXT = """
<b>История генераций пуста</b>

Создайте первую генерацию!
"""

HISTORY_FREE_TEXT = """
<b>История генераций</b>

История генераций доступна на тарифах <b>Pro</b> и <b>Enterprise</b>.

<b>Pro</b> — история 7 дней
<b>Enterprise</b> — история 30 дней

Оформите подписку для доступа к истории.
"""

FILE_EXPIRED_TEXT = """
Файл больше недоступен. Срок хранения истёк.
"""

HISTORY_ERROR_TEXT = """
Не удалось загрузить историю генераций. Попробуйте позже.
"""


def format_generation_item(gen: dict, index: int) -> str:
    """
    Форматировать элемент генерации для отображения.

    Args:
        gen: Данные генерации из API
        index: Порядковый номер в списке

    Returns:
        Отформатированная строка
    """
    # Парсим дату
    created_at = gen.get("created_at", "")
    if created_at:
        try:
            # Убираем микросекунды и timezone для парсинга
            dt_str = created_at.replace("Z", "+00:00")
            if "." in dt_str:
                dt_str = dt_str.split(".")[0] + "+00:00"
            dt = datetime.fromisoformat(dt_str)
            date_str = dt.strftime("%d.%m.%Y, %H:%M")
        except (ValueError, TypeError):
            date_str = created_at[:16].replace("T", ", ")
    else:
        date_str = "Неизвестно"

    labels_count = gen.get("labels_count", 0)
    preflight_passed = gen.get("preflight_passed", False)

    # Статус проверки качества
    if preflight_passed:
        status_icon = "Проверка пройдена"
    else:
        status_icon = "С предупреждениями"

    return f"{index}. {date_str}\n   {labels_count} этикеток • {status_icon}"


def format_history_message(generations: list, page: int, total: int) -> str:
    """
    Форматировать сообщение с историей генераций.

    Args:
        generations: Список генераций
        page: Текущая страница
        total: Общее количество генераций

    Returns:
        Отформатированное сообщение
    """
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    if total_pages == 0:
        total_pages = 1

    lines = ["<b>История генераций</b>\n"]

    for i, gen in enumerate(generations, start=1):
        # Номер с учётом страницы
        global_index = (page - 1) * PAGE_SIZE + i
        lines.append(format_generation_item(gen, global_index))

    lines.append(f"\nСтраница {page} из {total_pages}")

    return "\n".join(lines)


@router.message(Command("history"))
async def cmd_history(message: Message):
    """Команда /history — показать историю генераций."""
    telegram_id = message.from_user.id
    api = get_api_client()

    # Сначала проверяем план пользователя
    profile = await api.get_user_profile(telegram_id)

    if not profile:
        await message.answer(
            HISTORY_ERROR_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        return

    plan = profile.get("plan", "free").lower()

    # Free пользователям история недоступна
    if plan == "free":
        await message.answer(
            HISTORY_FREE_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        return

    # Запрашиваем историю
    result = await api.get_generations(telegram_id, limit=PAGE_SIZE, offset=0)

    if not result or not result.get("success"):
        await message.answer(
            HISTORY_ERROR_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        return

    items = result.get("data", {}).get("items", [])
    total = result.get("data", {}).get("total", 0)

    if not items:
        await message.answer(
            HISTORY_EMPTY_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        return

    # Формируем сообщение с историей
    text = format_history_message(items, page=1, total=total)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    await message.answer(
        text,
        reply_markup=get_history_kb(items, current_page=1, total_pages=total_pages),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "history")
async def cb_history(callback: CallbackQuery):
    """Callback для кнопки История."""
    telegram_id = callback.from_user.id
    api = get_api_client()

    # Сначала проверяем план пользователя
    profile = await api.get_user_profile(telegram_id)

    if not profile:
        await callback.message.edit_text(
            HISTORY_ERROR_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    plan = profile.get("plan", "free").lower()

    # Free пользователям история недоступна
    if plan == "free":
        await callback.message.edit_text(
            HISTORY_FREE_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    # Запрашиваем историю
    result = await api.get_generations(telegram_id, limit=PAGE_SIZE, offset=0)

    if not result or not result.get("success"):
        await callback.message.edit_text(
            HISTORY_ERROR_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    items = result.get("data", {}).get("items", [])
    total = result.get("data", {}).get("total", 0)

    if not items:
        await callback.message.edit_text(
            HISTORY_EMPTY_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    # Формируем сообщение с историей
    text = format_history_message(items, page=1, total=total)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    await callback.message.edit_text(
        text,
        reply_markup=get_history_kb(items, current_page=1, total_pages=total_pages),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("history_page:"))
async def history_pagination(callback: CallbackQuery):
    """Пагинация истории генераций."""
    telegram_id = callback.from_user.id
    api = get_api_client()

    # Парсим номер страницы из callback_data
    try:
        page = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("Ошибка пагинации")
        return

    if page < 1:
        page = 1

    # Вычисляем offset
    offset = (page - 1) * PAGE_SIZE

    # Запрашиваем историю
    result = await api.get_generations(telegram_id, limit=PAGE_SIZE, offset=offset)

    if not result or not result.get("success"):
        await callback.answer("Ошибка загрузки истории")
        return

    items = result.get("data", {}).get("items", [])
    total = result.get("data", {}).get("total", 0)

    if not items:
        await callback.answer("Нет записей на этой странице")
        return

    # Формируем сообщение с историей
    text = format_history_message(items, page=page, total=total)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    await callback.message.edit_text(
        text,
        reply_markup=get_history_kb(items, current_page=page, total_pages=total_pages),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("download_gen:"))
async def download_generation(callback: CallbackQuery):
    """Скачать файл генерации."""
    telegram_id = callback.from_user.id
    api = get_api_client()

    # Парсим generation_id из callback_data
    try:
        generation_id = callback.data.split(":")[1]
    except IndexError:
        await callback.answer("Ошибка: неверный ID генерации")
        return

    await callback.answer("Загружаю файл...")

    # Запрашиваем файл
    result = await api.download_generation(telegram_id, generation_id)

    if not result or not result.get("success"):
        error_msg = result.get("error", FILE_EXPIRED_TEXT) if result else FILE_EXPIRED_TEXT
        await callback.message.answer(
            f"<b>Ошибка</b>\n\n{error_msg}",
            parse_mode="HTML",
        )
        return

    # Получаем содержимое файла
    file_content = result.get("data")
    if not file_content:
        await callback.message.answer(
            f"<b>Ошибка</b>\n\n{FILE_EXPIRED_TEXT}",
            parse_mode="HTML",
        )
        return

    # Отправляем файл пользователю
    filename = f"labels_{generation_id[:8]}.pdf"
    document = BufferedInputFile(file_content, filename=filename)

    await callback.message.answer_document(
        document=document,
        caption="Ваши этикетки готовы!",
    )
