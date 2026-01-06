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
            text="Настройки",
            callback_data="settings",
        ),
        InlineKeyboardButton(
            text="Личный кабинет",
            url="https://kleykod.ru/app",
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
            text="Купить Pro - 490 руб/мес",
            callback_data="buy_pro",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Купить Enterprise - 1990 руб/мес",
            callback_data="buy_enterprise",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Личный кабинет на сайте",
            url="https://kleykod.ru/app",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад",
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

    # Кнопка "Поделиться ботом" с switch_inline_query
    builder.row(
        InlineKeyboardButton(
            text="Поделиться ботом",
            switch_inline_query="Генерирую этикетки WB+ЧЗ бесплатно!",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Создать ещё",
            callback_data="generate",
        ),
        InlineKeyboardButton(
            text="В главное меню",
            callback_data="back_to_menu",
        ),
    )

    return builder.as_markup()


def get_upgrade_kb() -> InlineKeyboardMarkup:
    """Клавиатура для апгрейда тарифа (показывается при исчерпании лимита)."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Купить Pro - 500 этикеток/день",
            callback_data="buy_pro",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Тарифы",
            callback_data="plans",
        ),
        InlineKeyboardButton(
            text="В главное меню",
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


def get_settings_kb() -> InlineKeyboardMarkup:
    """Клавиатура управления настройками пользователя."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Изменить организацию",
            callback_data="settings_org",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Изменить ИНН",
            callback_data="settings_inn",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Очистить все",
            callback_data="settings_clear",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="В главное меню",
            callback_data="back_to_menu",
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

    # Кнопка возврата в меню
    builder.row(
        InlineKeyboardButton(
            text="В главное меню",
            callback_data="back_to_menu",
        )
    )

    return builder.as_markup()
