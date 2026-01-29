"""
Inline-клавиатуры для бота.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню бота (4 кнопки)."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Создать этикетки",
            callback_data="generate",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Профиль",
            callback_data="profile",
        ),
        InlineKeyboardButton(
            text="Тарифы",
            callback_data="plans",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Открыть сайт →",
            url="https://kleykod.ru/app",
        )
    )

    return builder.as_markup()


def get_help_kb() -> InlineKeyboardMarkup:
    """Клавиатура для /help."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Создать этикетки",
            callback_data="generate",
        ),
        InlineKeyboardButton(
            text="Открыть сайт →",
            url="https://kleykod.ru/app",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Главное меню",
            callback_data="back_to_menu",
        )
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


def get_excel_step_kb() -> InlineKeyboardMarkup:
    """Клавиатура для шага загрузки Excel (с кнопкой примера)."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="📥 Скачать пример файла",
            callback_data="download_example",
        )
    )
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


def get_plans_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора тарифа."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Купить Про",
            callback_data="buy_pro",
        ),
        InlineKeyboardButton(
            text="Купить Бизнес",
            callback_data="buy_enterprise",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Главное меню",
            callback_data="back_to_menu",
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


def get_profile_kb(is_paid: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура профиля пользователя."""
    builder = InlineKeyboardBuilder()

    if is_paid:
        builder.row(
            InlineKeyboardButton(
                text="История",
                callback_data="history",
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="Улучшить тариф",
                callback_data="plans",
            ),
            InlineKeyboardButton(
                text="История",
                callback_data="history",
            ),
        )
    builder.row(
        InlineKeyboardButton(
            text="Открыть сайт",
            url="https://kleykod.ru/app",
        ),
        InlineKeyboardButton(
            text="Главное меню",
            callback_data="back_to_menu",
        ),
    )

    return builder.as_markup()


def get_feedback_kb() -> InlineKeyboardMarkup:
    """Клавиатура для опроса обратной связи."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Пропустить",
            callback_data="skip_feedback",
        )
    )

    return builder.as_markup()


def get_after_generation_kb() -> InlineKeyboardMarkup:
    """Клавиатура после успешной генерации этикеток."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Создать ещё",
            callback_data="generate",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Открыть сайт →",
            url="https://kleykod.ru/app",
        ),
        InlineKeyboardButton(
            text="Главное меню",
            callback_data="back_to_menu",
        ),
    )

    return builder.as_markup()


def get_upgrade_kb() -> InlineKeyboardMarkup:
    """Клавиатура при исчерпании лимита."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Купить Про — 490 ₽/мес",
            callback_data="buy_pro",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Все тарифы",
            callback_data="plans",
        ),
        InlineKeyboardButton(
            text="Главное меню",
            callback_data="back_to_menu",
        ),
    )

    return builder.as_markup()


def get_column_confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение автоопределённой колонки (HITL)."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Да, продолжить",
            callback_data="column_confirm",
        ),
        InlineKeyboardButton(
            text="🔄 Выбрать другую",
            callback_data="column_change",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel",
        )
    )

    return builder.as_markup()


def get_column_select_kb(columns: list[str]) -> InlineKeyboardMarkup:
    """
    Кнопки выбора колонки (максимум 6).

    Args:
        columns: Список колонок вида ["A: Артикул", "B: Баркод", ...]

    Returns:
        InlineKeyboardMarkup с кнопками по 2 в ряд
    """
    builder = InlineKeyboardBuilder()

    buttons = []
    for col in columns[:6]:
        # col = "B: Баркод" → callback = "col_B"
        col_letter = col.split(":")[0].strip()
        buttons.append(
            InlineKeyboardButton(
                text=col,
                callback_data=f"col_{col_letter}",
            )
        )

    # По 2 кнопки в ряд
    for i in range(0, len(buttons), 2):
        row_buttons = buttons[i : i + 2]
        builder.row(*row_buttons)

    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel",
        )
    )

    return builder.as_markup()


def get_settings_kb(
    has_auto_save: bool = False, auto_save_enabled: bool = False
) -> InlineKeyboardMarkup:
    """
    Клавиатура управления настройками.

    Args:
        has_auto_save: Доступна ли функция автосохранения (PRO/Enterprise)
        auto_save_enabled: Включено ли автосохранение
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Изменить шаблон",
            callback_data="settings_template",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Изменить организацию",
            callback_data="settings_org",
        ),
        InlineKeyboardButton(
            text="Изменить ИНН",
            callback_data="settings_inn",
        ),
    )

    if has_auto_save:
        status = "Вкл" if auto_save_enabled else "Выкл"
        action = "off" if auto_save_enabled else "on"
        builder.row(
            InlineKeyboardButton(
                text=f"Автосохранение: {status}",
                callback_data=f"settings_autosave:{action}",
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="Очистить всё",
            callback_data="settings_clear",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Открыть сайт →",
            url="https://kleykod.ru/app/settings",
        ),
        InlineKeyboardButton(
            text="Главное меню",
            callback_data="back_to_menu",
        ),
    )

    return builder.as_markup()


def get_truncation_confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение обрезки длинных полей (HITL)."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Продолжить с обрезкой",
            callback_data="truncation_confirm",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Отмена",
            callback_data="cancel",
        )
    )

    return builder.as_markup()


def get_history_kb(
    generations: list,
    current_page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """
    Клавиатура для истории генераций.

    Args:
        generations: Список генераций на текущей странице
        current_page: Номер текущей страницы
        total_pages: Общее количество страниц

    Returns:
        InlineKeyboardMarkup с кнопками скачивания и пагинации
    """
    builder = InlineKeyboardBuilder()

    # Кнопки скачивания для каждой генерации
    for gen in generations:
        gen_id = str(gen.get("id", ""))
        if gen_id:
            # Показываем только первые 8 символов UUID для краткости
            short_id = gen_id[:8]
            builder.row(
                InlineKeyboardButton(
                    text=f"Скачать #{short_id}",
                    callback_data=f"download_gen:{gen_id}",
                )
            )

    # Кнопки пагинации
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Назад",
                callback_data=f"history_page:{current_page - 1}",
            )
        )
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперёд",
                callback_data=f"history_page:{current_page + 1}",
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    # Сайт и меню
    builder.row(
        InlineKeyboardButton(
            text="Открыть сайт →",
            url="https://kleykod.ru/app/history",
        ),
        InlineKeyboardButton(
            text="Главное меню",
            callback_data="back_to_menu",
        ),
    )

    return builder.as_markup()


def get_numbering_kb(
    global_last: int | None = None,
    per_product_last: int | None = None,
    is_pro: bool = False,
) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора режима нумерации.

    Args:
        global_last: Глобальный счётчик (last_label_number)
        per_product_last: Per-product счётчик из карточек товаров
        is_pro: PRO/ENTERPRISE тариф

    Returns:
        InlineKeyboardMarkup с вариантами нумерации
    """
    builder = InlineKeyboardBuilder()

    # Базовые опции
    builder.row(
        InlineKeyboardButton(
            text="Без номеров",
            callback_data="numbering:none",
        ),
        InlineKeyboardButton(
            text="С 1",
            callback_data="numbering:from_1",
        ),
    )

    # По товару: 🔒 для FREE, активно для PRO
    if is_pro:
        builder.row(
            InlineKeyboardButton(
                text="По товару",
                callback_data="numbering:per_product",
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="По товару 🔒 Про",
                callback_data="numbering:locked",
            ),
        )

    # Продолжить (общая) — если есть глобальный счётчик
    if global_last and global_last > 0:
        builder.row(
            InlineKeyboardButton(
                text=f"Продолжить с {global_last + 1} (общая)",
                callback_data=f"numbering:continue:{global_last + 1}",
            ),
        )

    # Продолжить (по товару) — только PRO, если есть карточки
    if per_product_last and per_product_last > 0:
        if is_pro and per_product_last != global_last:
            builder.row(
                InlineKeyboardButton(
                    text=f"Продолжить с {per_product_last + 1} (по товару)",
                    callback_data=f"numbering:continue:{per_product_last + 1}",
                ),
            )
        elif not is_pro:
            builder.row(
                InlineKeyboardButton(
                    text="Продолжить (по товару) 🔒 Про",
                    callback_data="numbering:locked",
                ),
            )

    builder.row(
        InlineKeyboardButton(
            text="Отмена",
            callback_data="cancel",
        )
    )

    return builder.as_markup()


def get_range_kb(total_count: int) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора диапазона печати.

    Args:
        total_count: Общее количество кодов

    Returns:
        InlineKeyboardMarkup с вариантами диапазона
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"Все ({total_count} шт.)",
            callback_data="range:all",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Указать диапазон",
            callback_data="range:custom",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Отмена",
            callback_data="cancel",
        )
    )

    return builder.as_markup()


def get_template_select_kb(current: str = "basic") -> InlineKeyboardMarkup:
    """
    Клавиатура выбора шаблона этикетки.

    Args:
        current: Текущий выбранный шаблон

    Returns:
        InlineKeyboardMarkup с вариантами шаблонов
    """
    builder = InlineKeyboardBuilder()

    templates = [
        ("basic", "Базовый"),
        ("professional", "Профессиональный"),
        ("extended", "Расширенный"),
    ]

    for template_id, template_name in templates:
        mark = "✓ " if template_id == current else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{mark}{template_name}",
                callback_data=f"template:{template_id}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="← Назад",
            callback_data="settings",
        )
    )

    return builder.as_markup()


def get_products_menu_kb(count: int) -> InlineKeyboardMarkup:
    """
    Главное меню базы товаров.

    Args:
        count: Количество товаров в базе

    Returns:
        InlineKeyboardMarkup меню товаров
    """
    builder = InlineKeyboardBuilder()

    if count > 0:
        builder.row(
            InlineKeyboardButton(
                text="Показать все",
                callback_data="products:list:0",
            ),
            InlineKeyboardButton(
                text="Очистить базу",
                callback_data="products:clear_confirm",
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="Как добавить товары?",
                callback_data="products:help",
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="← В меню",
            callback_data="back_to_menu",
        )
    )

    return builder.as_markup()


def get_products_list_kb(
    products: list,
    offset: int,
    total: int,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    """
    Список товаров с пагинацией.

    Args:
        products: Список товаров на странице
        offset: Текущее смещение
        total: Общее количество товаров
        page_size: Размер страницы

    Returns:
        InlineKeyboardMarkup со списком и пагинацией
    """
    builder = InlineKeyboardBuilder()

    # Кнопки товаров
    for product in products:
        barcode = product.get("barcode", "")
        name = product.get("name", "Без названия")[:20]
        builder.row(
            InlineKeyboardButton(
                text=f"{barcode} — {name}",
                callback_data=f"product:{barcode}",
            )
        )

    # Пагинация
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="← Назад",
                callback_data=f"products:list:{offset - page_size}",
            )
        )
    if offset + page_size < total:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперёд →",
                callback_data=f"products:list:{offset + page_size}",
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text="← К базе товаров",
            callback_data="products",
        )
    )

    return builder.as_markup()


def get_product_view_kb(barcode: str) -> InlineKeyboardMarkup:
    """
    Просмотр карточки товара.

    Args:
        barcode: Баркод товара

    Returns:
        InlineKeyboardMarkup с действиями над товаром
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Удалить",
            callback_data=f"product:delete_confirm:{barcode}",
        ),
        InlineKeyboardButton(
            text="← Назад",
            callback_data="products:list:0",
        ),
    )

    return builder.as_markup()


def get_product_delete_confirm_kb(barcode: str) -> InlineKeyboardMarkup:
    """Подтверждение удаления товара."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да, удалить",
            callback_data=f"product:delete:{barcode}",
        ),
        InlineKeyboardButton(
            text="Отмена",
            callback_data=f"product:{barcode}",
        ),
    )

    return builder.as_markup()


def get_clear_products_confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение очистки базы товаров."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да, очистить всё",
            callback_data="products:clear",
        ),
        InlineKeyboardButton(
            text="Отмена",
            callback_data="products",
        ),
    )

    return builder.as_markup()


def get_save_products_kb() -> InlineKeyboardMarkup:
    """Клавиатура для сохранения новых товаров после генерации."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Да, сохранить",
            callback_data="save_products:yes",
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data="save_products:no",
        ),
    )

    return builder.as_markup()


def generation_mode_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора режима генерации."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Только WB", callback_data="gen_mode:wb_only")],
            [InlineKeyboardButton(text="🏷️ Только ЧЗ", callback_data="gen_mode:chz_only")],
            [
                InlineKeyboardButton(
                    text="🔗 Объединение WB + ЧЗ", callback_data="gen_mode:combined"
                )
            ],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_menu")],
        ]
    )


def wb_only_upsell_keyboard() -> InlineKeyboardMarkup:
    """Апсейл после WB-only генерации."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Попробовать объединение", callback_data="gen_mode:combined"
                )
            ],
            [InlineKeyboardButton(text="📦 Ещё WB этикетки", callback_data="gen_mode:wb_only")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")],
        ]
    )


def chz_only_upsell_keyboard() -> InlineKeyboardMarkup:
    """Апсейл после ЧЗ-only генерации."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Добавить штрихкод WB", callback_data="gen_mode:combined"
                )
            ],
            [InlineKeyboardButton(text="🏷️ Ещё ЧЗ этикетки", callback_data="gen_mode:chz_only")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")],
        ]
    )


def label_size_keyboard() -> InlineKeyboardMarkup:
    """Выбор размера этикетки."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="58×40 мм", callback_data="size:58x40")],
            [InlineKeyboardButton(text="58×30 мм", callback_data="size:58x30")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_mode_select")],
        ]
    )
