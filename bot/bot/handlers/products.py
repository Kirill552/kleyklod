"""
Обработчики для работы с базой товаров.

Команда /products — просмотр, поиск и удаление товаров.
"""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    get_back_to_menu_kb,
    get_clear_products_confirm_kb,
    get_product_delete_confirm_kb,
    get_product_view_kb,
    get_products_list_kb,
    get_products_menu_kb,
)
from bot.states import ProductsStates
from bot.utils import get_api_client

logger = logging.getLogger(__name__)

router = Router(name="products")

PAGE_SIZE = 5

# Тексты
PRODUCTS_MENU_TEXT = """
📦 <b>База товаров</b>

Сохранено: <b>{count}</b> карточек

Поиск по баркоду — отправьте номер
"""

PRODUCTS_EMPTY_TEXT = """
📦 <b>База товаров</b>

База пуста. Товары сохраняются автоматически после генерации этикеток (PRO/Enterprise).
"""

PRODUCTS_UNAVAILABLE_TEXT = """
📦 <b>База товаров</b>

База товаров доступна на тарифах PRO и Enterprise.

Улучшите тариф, чтобы:
• Автоматически сохранять товары
• Быстрое автозаполнение при генерации
• До 1000 карточек в базе
"""

PRODUCT_VIEW_TEXT = """
📦 <b>Товар</b>

<b>Баркод:</b> <code>{barcode}</code>
<b>Название:</b> {name}
<b>Артикул:</b> {article}
<b>Размер:</b> {size} | <b>Цвет:</b> {color}

Редактирование на сайте: kleykod.ru/app/products
"""

PRODUCT_NOT_FOUND_TEXT = """
Товар с баркодом <code>{barcode}</code> не найден.
"""

PRODUCT_DELETED_TEXT = """
✅ Товар <code>{barcode}</code> удалён.
"""

PRODUCTS_CLEARED_TEXT = """
✅ База товаров очищена.

Удалено {count} карточек.
"""

CLEAR_CONFIRM_TEXT = """
⚠️ <b>Очистить всю базу товаров?</b>

Будет удалено {count} карточек.
Это действие необратимо.
"""


@router.message(Command("products"))
async def cmd_products(message: Message, state: FSMContext):
    """Показать главное меню базы товаров."""
    await state.clear()
    telegram_id = message.from_user.id

    api = get_api_client()

    # Проверяем профиль пользователя
    profile = await api.get_user_profile(telegram_id)
    plan = profile.get("plan", "free") if profile else "free"

    if plan == "free":
        await message.answer(
            PRODUCTS_UNAVAILABLE_TEXT,
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        return

    # Получаем количество товаров
    count = await api.get_products_count(telegram_id)

    if count == 0:
        await message.answer(
            PRODUCTS_EMPTY_TEXT,
            reply_markup=get_products_menu_kb(0),
            parse_mode="HTML",
        )
    else:
        await state.set_state(ProductsStates.browsing)
        await message.answer(
            PRODUCTS_MENU_TEXT.format(count=count),
            reply_markup=get_products_menu_kb(count),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "products")
async def cb_products_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню товаров."""
    await state.clear()
    telegram_id = callback.from_user.id

    api = get_api_client()
    count = await api.get_products_count(telegram_id)

    if count == 0:
        await callback.message.edit_text(
            PRODUCTS_EMPTY_TEXT,
            reply_markup=get_products_menu_kb(0),
            parse_mode="HTML",
        )
    else:
        await state.set_state(ProductsStates.browsing)
        await callback.message.edit_text(
            PRODUCTS_MENU_TEXT.format(count=count),
            reply_markup=get_products_menu_kb(count),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(F.data.startswith("products:list:"))
async def cb_products_list(callback: CallbackQuery, state: FSMContext):
    """Показать список товаров с пагинацией."""
    telegram_id = callback.from_user.id
    offset = int(callback.data.split(":")[2])

    api = get_api_client()
    result = await api.get_products(telegram_id, limit=PAGE_SIZE, offset=offset)

    if not result.success:
        await callback.answer(result.error or "Ошибка загрузки", show_alert=True)
        return

    data = result.data or {}
    products = data.get("items", [])
    total = data.get("total", 0)

    if not products:
        await callback.message.edit_text(
            PRODUCTS_EMPTY_TEXT,
            reply_markup=get_products_menu_kb(0),
            parse_mode="HTML",
        )
    else:
        await state.set_state(ProductsStates.browsing)
        await callback.message.edit_text(
            f"📦 <b>Товары</b> ({offset + 1}-{min(offset + PAGE_SIZE, total)} из {total})",
            reply_markup=get_products_list_kb(products, offset, total, PAGE_SIZE),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(F.data.startswith("product:") & ~F.data.contains("delete"))
async def cb_product_view(callback: CallbackQuery, state: FSMContext):
    """Показать карточку товара."""
    telegram_id = callback.from_user.id
    barcode = callback.data.split(":")[1]

    api = get_api_client()
    result = await api.get_product_by_barcode(telegram_id, barcode)

    if not result.success:
        await callback.answer(result.error or "Товар не найден", show_alert=True)
        return

    product = result.data or {}

    await state.set_state(ProductsStates.viewing_product)
    await state.update_data(current_barcode=barcode)

    await callback.message.edit_text(
        PRODUCT_VIEW_TEXT.format(
            barcode=product.get("barcode", barcode),
            name=product.get("name", "—"),
            article=product.get("article", "—"),
            size=product.get("size", "—"),
            color=product.get("color", "—"),
        ),
        reply_markup=get_product_view_kb(barcode),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:delete_confirm:"))
async def cb_product_delete_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления товара."""
    barcode = callback.data.split(":")[2]

    await state.set_state(ProductsStates.confirming_delete)
    await callback.message.edit_text(
        f"Удалить товар <code>{barcode}</code>?",
        reply_markup=get_product_delete_confirm_kb(barcode),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:delete:"))
async def cb_product_delete(callback: CallbackQuery, state: FSMContext):
    """Удаление товара."""
    telegram_id = callback.from_user.id
    barcode = callback.data.split(":")[2]

    api = get_api_client()
    result = await api.delete_product(telegram_id, barcode)

    if result.success:
        await callback.message.edit_text(
            PRODUCT_DELETED_TEXT.format(barcode=barcode),
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        logger.info(f"[PRODUCTS] Товар {barcode} удалён пользователем {telegram_id}")
    else:
        await callback.answer(result.error or "Ошибка удаления", show_alert=True)

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "products:clear_confirm")
async def cb_clear_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение очистки базы."""
    telegram_id = callback.from_user.id

    api = get_api_client()
    count = await api.get_products_count(telegram_id)

    await state.set_state(ProductsStates.confirming_clear)
    await callback.message.edit_text(
        CLEAR_CONFIRM_TEXT.format(count=count),
        reply_markup=get_clear_products_confirm_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "products:clear")
async def cb_clear_products(callback: CallbackQuery, state: FSMContext):
    """Очистка базы товаров."""
    telegram_id = callback.from_user.id

    api = get_api_client()

    # Сначала получаем количество для сообщения
    count = await api.get_products_count(telegram_id)

    result = await api.clear_products(telegram_id)

    if result.success:
        await callback.message.edit_text(
            PRODUCTS_CLEARED_TEXT.format(count=count),
            reply_markup=get_back_to_menu_kb(),
            parse_mode="HTML",
        )
        logger.info(f"[PRODUCTS] База очищена для пользователя {telegram_id}")
    else:
        await callback.answer(result.error or "Ошибка очистки", show_alert=True)

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "products:help")
async def cb_products_help(callback: CallbackQuery):
    """Справка по добавлению товаров."""
    await callback.message.edit_text(
        """
<b>Как добавить товары в базу?</b>

Товары добавляются автоматически после генерации этикеток.

1. Создайте этикетки как обычно
2. После генерации бот предложит сохранить новые товары
3. Нажмите «Да, сохранить»

При следующей генерации данные подставятся автоматически!

<b>Также можно:</b>
• Добавить товары на сайте: kleykod.ru/app/products
• Импортировать из Excel
""",
        reply_markup=get_back_to_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ProductsStates.browsing, F.text)
async def search_by_barcode(message: Message, state: FSMContext):
    """Поиск товара по баркоду."""
    telegram_id = message.from_user.id
    barcode = message.text.strip()

    # Проверяем, похоже ли на баркод (только цифры)
    if not barcode.isdigit():
        await message.answer(
            "Отправьте баркод (только цифры) для поиска.",
            parse_mode="HTML",
        )
        return

    api = get_api_client()
    result = await api.get_product_by_barcode(telegram_id, barcode)

    if not result.success:
        await message.answer(
            PRODUCT_NOT_FOUND_TEXT.format(barcode=barcode),
            reply_markup=get_products_menu_kb(await api.get_products_count(telegram_id)),
            parse_mode="HTML",
        )
        return

    product = result.data or {}

    await state.set_state(ProductsStates.viewing_product)
    await state.update_data(current_barcode=barcode)

    await message.answer(
        PRODUCT_VIEW_TEXT.format(
            barcode=product.get("barcode", barcode),
            name=product.get("name", "—"),
            article=product.get("article", "—"),
            size=product.get("size", "—"),
            color=product.get("color", "—"),
        ),
        reply_markup=get_product_view_kb(barcode),
        parse_mode="HTML",
    )
