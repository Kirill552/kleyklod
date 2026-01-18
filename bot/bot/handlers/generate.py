"""
Обработчики генерации этикеток.

Workflow:
1. Пользователь нажимает «Создать этикетки»
2. Отправляет Excel с баркодами WB
3. Отправляет PDF с кодами ЧЗ (только PDF содержит криптоподпись)
4. (Первая генерация) Вводит название организации и ИНН
5. Получает готовый PDF
"""

import io

import sentry_sdk
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.config import get_bot_settings
from bot.keyboards import (
    get_after_generation_kb,
    get_cancel_kb,
    get_column_confirm_kb,
    get_column_select_kb,
    get_excel_step_kb,
    get_feedback_kb,
    get_main_menu_kb,
    get_numbering_kb,
    get_range_kb,
    get_template_select_kb,
    get_truncation_confirm_kb,
    get_upgrade_kb,
)
from bot.states import GenerateStates
from bot.utils import get_api_client, get_user_settings_async

router = Router(name="generate")

# Порог для отображения безлимита (Enterprise = 999999 в backend)
UNLIMITED_THRESHOLD = 100000


def is_unlimited(limit: int) -> bool:
    """Проверка безлимитного тарифа."""
    return limit >= UNLIMITED_THRESHOLD


# Тексты
SEND_EXCEL_TEXT = """
<b>Шаг 1 из 2: Excel с баркодами</b>

Отправьте Excel файл (.xlsx) с баркодами товаров.

💡 Скачайте из ЛК WB: Товары → Карточки → Выгрузить
"""

CONFIRM_COLUMN_TEXT = """
<b>Проверьте данные</b>

Найдено <b>{count} баркодов</b> в колонке «{column}»

Примеры:
<code>{sample_1}</code>
<code>{sample_2}</code>

Это верно?
"""

SELECT_COLUMN_TEXT = """
<b>Выберите колонку с баркодами</b>

Не удалось определить автоматически.
Укажите, в какой колонке находятся штрихкоды:
"""

TOO_MANY_COLUMNS_TEXT = """
<b>Слишком сложный файл</b>

В Excel {count} колонок — сложно выбрать в чате.

Используйте веб-версию с удобным превью:
🌐 kleykod.ru/app
"""

SEND_CODES_TEXT = """
<b>Шаг 2 из 2: Коды Честного Знака</b>

Найдено <b>{barcodes_count} баркодов</b> в Excel.

Теперь отправьте <b>PDF файл</b> с кодами маркировки.

💡 Скачайте PDF из личного кабинета ЧЗ (crpt.ru)
"""

PROCESSING_TEXT = """
<b>Генерация этикеток...</b>

Объединяю штрихкоды WB и коды ЧЗ.
Это займёт несколько секунд.
"""

FEEDBACK_REQUEST_TEXT = """
Вы сгенерировали уже 3 партии этикеток!

Что бы вы хотели улучшить в сервисе?

Напишите свои идеи и пожелания (или нажмите «Пропустить»)
"""

FEEDBACK_THANKS_TEXT = "Спасибо за обратную связь! Мы учтём ваше мнение."

FEEDBACK_SKIP_TEXT = "Хорошо, спросим в следующий раз"

START_NUMBER_SET_TEXT = """
✅ Стартовый номер установлен: <b>{number}</b>

Этикетки будут пронумерованы начиная с этого номера.
Продолжайте загрузку файлов.
"""

START_NUMBER_ERROR_TEXT = """
❌ <b>Неверный формат</b>

Используйте: <code>/from 101</code>
Где 101 — стартовый номер (положительное число).
"""

ASK_ORGANIZATION_TEXT = """
🏢 <b>Укажите название организации для этикеток</b>

Например: ООО «Рога и Копыта»

Или отправьте /skip чтобы пропустить
"""

ASK_INN_TEXT = """
📋 <b>Укажите ИНН</b> (опционально)

Отправьте /skip чтобы пропустить
"""

SELECT_NUMBERING_TEXT = """
<b>Нумерация этикеток</b>

Выберите режим нумерации:
• <b>Без номеров</b> — только код ЧЗ
• <b>С 1</b> — нумерация с единицы
• <b>Продолжить</b> — продолжить с последнего номера
"""

SELECT_RANGE_TEXT = """
<b>Диапазон печати</b>

Найдено <b>{total}</b> кодов ЧЗ.

Напечатать все или указать диапазон?
(например: 5-15 из 50)
"""

ENTER_RANGE_TEXT = """
<b>Введите диапазон</b>

Формат: <code>5-15</code> или <code>1-10</code>

Всего кодов: {total}
"""

INVALID_RANGE_TEXT = """
Неверный формат диапазона.

Используйте: <code>5-15</code>
Где 5 — начало, 15 — конец.

Всего кодов: {total}
"""

SAVE_PRODUCTS_TEXT = """
<b>Сохранить новые товары?</b>

Найдено {count} новых товаров.
Сохранить их в базу для автозаполнения?
"""

LIMIT_EXCEEDED_TEXT = """
⚠️ <b>Дневной лимит исчерпан</b>

Использовано: {used} / {limit} этикеток
Лимит обновится завтра в 00:00

<b>Перейти на PRO:</b>
• 500 этикеток в день
• История генераций 7 дней
• База до 100 товаров
• 490 ₽/мес
"""

TRUNCATION_WARNING_TEXT = """
⚠️ <b>Некоторые данные слишком длинные:</b>

{warnings}

<b>Варианты:</b>
1. Сократите данные в Excel и отправьте снова
2. Продолжить — длинные тексты будут обрезаны
3. Используйте веб-версию с Extended шаблоном: kleykod.ru/app
"""

# Лимиты символов для Basic 58x40
FIELD_LIMITS = {
    "name": 56,  # 2 строки по ~28 символов
    "article": 25,
    "size": 12,
    "color": 12,
    "organization": 30,
}

# Русские названия полей для сообщений
FIELD_NAMES_RU = {
    "name": "Название",
    "article": "Артикул",
    "size": "Размер",
    "color": "Цвет",
    "organization": "Организация",
}


def check_field_limits(items: list[dict]) -> list[str]:
    """
    Проверяет длину полей и возвращает список предупреждений.

    Args:
        items: Список товаров с полями name, article, size, color

    Returns:
        Список строк с предупреждениями
    """
    warnings = []
    for i, item in enumerate(items, 1):
        for field, limit in FIELD_LIMITS.items():
            if field == "organization":
                continue  # Организация проверяется отдельно
            value = item.get(field, "")
            if value and len(str(value)) > limit:
                field_name = FIELD_NAMES_RU.get(field, field)
                warnings.append(
                    f"• Строка {i}: {field_name} слишком длинный "
                    f"({len(str(value))} символов, макс. {limit})"
                )
    return warnings


@router.callback_query(F.data == "generate")
async def cb_generate_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса генерации — сразу к Excel."""
    await state.set_state(GenerateStates.waiting_excel)
    await callback.message.edit_text(
        SEND_EXCEL_TEXT,
        reply_markup=get_excel_step_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.text == "Создать этикетки")
async def text_generate_start(message: Message, state: FSMContext):
    """Текстовая команда для начала генерации."""
    await state.set_state(GenerateStates.waiting_excel)
    await message.answer(
        SEND_EXCEL_TEXT,
        reply_markup=get_excel_step_kb(),
        parse_mode="HTML",
    )


@router.message(F.text.startswith("/from"))
async def cmd_from_number(message: Message, state: FSMContext):
    """
    Команда /from <number> — установить стартовый номер нумерации.

    Работает в любом состоянии генерации.
    Пример: /from 101
    """
    current_state = await state.get_state()

    # Команда работает только во время генерации
    if not current_state or not current_state.startswith("GenerateStates:"):
        await message.answer(
            "Команда /from работает только во время генерации этикеток.\n"
            "Нажмите «Создать этикетки» чтобы начать.",
        )
        return

    # Парсим номер из команды
    text = message.text.strip()
    parts = text.split(maxsplit=1)

    if len(parts) < 2:
        await message.answer(
            START_NUMBER_ERROR_TEXT,
            parse_mode="HTML",
        )
        return

    try:
        start_number = int(parts[1])
        if start_number < 1:
            raise ValueError("Номер должен быть >= 1")
    except ValueError:
        await message.answer(
            START_NUMBER_ERROR_TEXT,
            parse_mode="HTML",
        )
        return

    # Сохраняем в состояние
    await state.update_data(
        start_number=start_number,
        numbering_mode="continue",
    )

    await message.answer(
        START_NUMBER_SET_TEXT.format(number=start_number),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "download_example")
async def cb_download_example(callback: CallbackQuery):
    """Отправить пример Excel файла."""
    from pathlib import Path

    # Путь к примеру файла
    assets_dir = Path(__file__).parent.parent / "assets"
    example_path = assets_dir / "example.xlsx"

    if example_path.exists():
        await callback.message.answer_document(
            BufferedInputFile(
                example_path.read_bytes(),
                filename="kleykod_example.xlsx",
            ),
            caption="Пример файла с баркодами.\nЗаполните колонку «Баркод» своими данными.",
        )
    else:
        await callback.message.answer(
            "Пример файла временно недоступен. "
            "Создайте Excel с колонкой «Баркод» и номерами EAN-13."
        )

    await callback.answer()


# ===== Excel флоу =====


@router.message(GenerateStates.waiting_excel, F.document)
async def receive_excel(message: Message, state: FSMContext, bot: Bot):
    """Получение Excel файла с баркодами."""
    document = message.document
    filename = document.file_name or "barcodes.xlsx"

    # Валидация расширения
    if not filename.lower().endswith((".xlsx", ".xls")):
        await message.answer(
            "Отправьте Excel файл (.xlsx или .xls)",
            reply_markup=get_cancel_kb(),
        )
        return

    # Проверка размера
    settings = get_bot_settings()
    if document.file_size > settings.max_file_size_bytes:
        await message.answer(
            f"Файл слишком большой. Максимум: {settings.max_file_size_mb} МБ",
            reply_markup=get_cancel_kb(),
        )
        return

    # Показываем статус загрузки
    status_msg = await message.answer("Анализирую Excel файл...")

    # Скачиваем файл
    try:
        file = await bot.get_file(document.file_id)
        file_bytes_io = io.BytesIO()
        await bot.download_file(file.file_path, file_bytes_io)
        excel_bytes = file_bytes_io.getvalue()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        await status_msg.edit_text(
            f"Ошибка загрузки файла: {e}",
            reply_markup=get_cancel_kb(),
        )
        return

    # Парсим Excel через API
    api = get_api_client()
    result = await api.parse_excel_barcodes(excel_bytes, filename)

    if not result:
        await status_msg.edit_text(
            "Ошибка чтения Excel файла. Проверьте формат.",
            reply_markup=get_cancel_kb(),
        )
        return

    # Сохраняем данные в состояние
    # Backend возвращает: all_columns, total_rows, detected_column, sample_items
    detected_column = result.get("detected_column")
    # Если колонка определена — высокая уверенность
    confidence = 1.0 if detected_column else 0.0

    raw_columns = result.get("all_columns", [])
    total_count = result.get("total_rows", 0)
    sample_items = result.get("sample_items", [])

    # Форматируем колонки в формат "A: Название", "B: Название" для клавиатуры
    columns = []
    for idx, col_name in enumerate(raw_columns[:6]):
        col_letter = chr(ord("A") + idx)
        columns.append(f"{col_letter}: {col_name}")

    await state.update_data(
        excel_file_id=document.file_id,
        excel_filename=filename,
        excel_columns=columns,  # Используем отформатированные колонки
        detected_column=detected_column,
        confidence=confidence,
        barcodes_count=total_count,
        sample_items=sample_items,
    )

    # Решаем: подтверждение или выбор
    if confidence >= 0.8 and detected_column:
        # Высокая уверенность — просим подтвердить
        await state.set_state(GenerateStates.confirming_column)
        # sample_items — список объектов с полем barcode
        sample_1 = sample_items[0].get("barcode", "—") if sample_items else "—"
        sample_2 = sample_items[1].get("barcode", "—") if len(sample_items) > 1 else "—"
        await status_msg.edit_text(
            CONFIRM_COLUMN_TEXT.format(
                count=total_count,
                column=detected_column,
                sample_1=sample_1,
                sample_2=sample_2,
            ),
            reply_markup=get_column_confirm_kb(),
            parse_mode="HTML",
        )
    elif len(columns) <= 6:
        # Низкая уверенность, но мало колонок — показываем выбор
        await state.set_state(GenerateStates.selecting_column)
        await status_msg.edit_text(
            SELECT_COLUMN_TEXT,
            reply_markup=get_column_select_kb(columns),
            parse_mode="HTML",
        )
    else:
        # Слишком много колонок — redirect на сайт
        await status_msg.edit_text(
            TOO_MANY_COLUMNS_TEXT.format(count=len(columns)),
            reply_markup=get_main_menu_kb(),
            parse_mode="HTML",
        )
        await state.clear()


@router.message(GenerateStates.waiting_excel, ~F.document)
async def waiting_excel_wrong_type(message: Message):
    """Неверный тип сообщения при ожидании Excel."""
    await message.answer(
        "Пожалуйста, отправьте Excel файл (.xlsx) с баркодами.",
        reply_markup=get_cancel_kb(),
    )


@router.callback_query(GenerateStates.confirming_column, F.data == "column_confirm")
async def cb_column_confirm(callback: CallbackQuery, state: FSMContext):
    """Пользователь подтвердил автоопределённую колонку."""
    data = await state.get_data()
    await state.update_data(selected_column=data.get("detected_column"))
    barcodes_count = data.get("barcodes_count", 0)

    # Переходим к загрузке кодов ЧЗ
    await state.set_state(GenerateStates.waiting_codes)
    await callback.message.edit_text(
        SEND_CODES_TEXT.format(barcodes_count=barcodes_count),
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(GenerateStates.confirming_column, F.data == "column_change")
async def cb_column_change(callback: CallbackQuery, state: FSMContext):
    """Пользователь хочет выбрать другую колонку."""
    data = await state.get_data()
    columns = data.get("excel_columns", [])

    if len(columns) <= 6:
        await state.set_state(GenerateStates.selecting_column)
        await callback.message.edit_text(
            SELECT_COLUMN_TEXT,
            reply_markup=get_column_select_kb(columns),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            TOO_MANY_COLUMNS_TEXT.format(count=len(columns)),
            reply_markup=get_main_menu_kb(),
            parse_mode="HTML",
        )
        await state.clear()
    await callback.answer()


@router.callback_query(GenerateStates.selecting_column, F.data.startswith("col_"))
async def cb_column_selected(callback: CallbackQuery, state: FSMContext):
    """Пользователь выбрал колонку вручную."""
    col_letter = callback.data.replace("col_", "")
    data = await state.get_data()
    columns = data.get("excel_columns", [])

    # Находим полное название колонки
    selected = next((c for c in columns if c.startswith(col_letter)), col_letter)
    await state.update_data(selected_column=selected)

    # Получаем количество баркодов для предупреждения
    barcodes_count = data.get("barcodes_count", 0)

    # Переходим к загрузке кодов ЧЗ
    await state.set_state(GenerateStates.waiting_codes)
    await callback.message.edit_text(
        SEND_CODES_TEXT.format(barcodes_count=barcodes_count),
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(GenerateStates.waiting_codes, F.document)
async def receive_codes(message: Message, state: FSMContext, bot: Bot):
    """Получение PDF файла с кодами ЧЗ — проверяем настройки или запрашиваем."""
    document = message.document

    filename = document.file_name or "codes.pdf"
    extension = filename.lower().split(".")[-1] if "." in filename else ""

    # Проверка что это PDF
    is_pdf = document.mime_type == "application/pdf" or extension == "pdf"

    if not is_pdf:
        await message.answer(
            "Пожалуйста, отправьте <b>PDF файл</b> с кодами.\n\n"
            "CSV и Excel не содержат криптоподпись и не подходят для печати.\n\n"
            "💡 Скачайте PDF из личного кабинета ЧЗ (crpt.ru)",
            reply_markup=get_cancel_kb(),
            parse_mode="HTML",
        )
        return

    # Проверка размера
    settings = get_bot_settings()
    if document.file_size > settings.max_file_size_bytes:
        await message.answer(
            f"Файл слишком большой. Максимум: {settings.max_file_size_mb} МБ",
            reply_markup=get_cancel_kb(),
        )
        return

    # Сохраняем file_id в состояние
    data = await state.get_data()
    barcodes_count = data.get("barcodes_count", 0)

    await state.update_data(
        codes_file_id=document.file_id,
        codes_filename=filename,
        codes_count=barcodes_count,  # Используем количество баркодов как приблизительное
    )

    # Получаем telegram_id
    telegram_id = message.from_user.id if message.from_user else None

    if not telegram_id:
        await message.answer(
            "Ошибка идентификации пользователя. Попробуйте снова.",
            reply_markup=get_main_menu_kb(),
        )
        await state.clear()
        return

    # Проверяем длину полей в sample_items перед продолжением
    sample_items = data.get("sample_items", [])

    if sample_items:
        field_warnings = check_field_limits(sample_items)
        if field_warnings:
            # Ограничиваем количество предупреждений (максимум 10)
            if len(field_warnings) > 10:
                displayed_warnings = field_warnings[:10]
                displayed_warnings.append(f"... и ещё {len(field_warnings) - 10} предупреждений")
            else:
                displayed_warnings = field_warnings

            warnings_text = "\n".join(displayed_warnings)
            await state.update_data(field_warnings=field_warnings)
            await state.set_state(GenerateStates.confirming_truncation)
            await message.answer(
                TRUNCATION_WARNING_TEXT.format(warnings=warnings_text),
                reply_markup=get_truncation_confirm_kb(),
                parse_mode="HTML",
            )
            return

    # Если нет предупреждений — переходим к выбору нумерации
    await proceed_to_numbering(message, state)


async def proceed_after_codes(message: Message, state: FSMContext, bot: Bot, telegram_id: int):
    """Продолжение после проверки полей — настройки или генерация."""
    user_settings = await get_user_settings_async()
    has_settings = await user_settings.has_settings(telegram_id)

    if has_settings:
        # Настройки есть — сразу генерируем с ними
        await process_generation(message, state, bot, telegram_id)
    else:
        # Первая генерация — запрашиваем данные организации
        await state.set_state(GenerateStates.waiting_organization)
        await message.answer(
            ASK_ORGANIZATION_TEXT,
            reply_markup=get_cancel_kb(),
            parse_mode="HTML",
        )


async def proceed_to_numbering(message: Message, state: FSMContext):
    """Переход к выбору нумерации."""
    telegram_id = message.from_user.id if message.from_user else None

    global_last = None
    is_pro = False

    if telegram_id:
        api = get_api_client()
        profile = await api.get_user_profile(telegram_id)
        if profile:
            global_last = profile.get("last_label_number")
            plan = profile.get("plan", "free")
            is_pro = plan in ("pro", "enterprise")

    await state.set_state(GenerateStates.selecting_numbering)
    await message.answer(
        SELECT_NUMBERING_TEXT,
        reply_markup=get_numbering_kb(global_last=global_last, is_pro=is_pro),
        parse_mode="HTML",
    )


@router.callback_query(GenerateStates.selecting_numbering, F.data.startswith("numbering:"))
async def cb_numbering_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора режима нумерации."""
    data_parts = callback.data.split(":")

    # Заблокированная опция — показать сообщение о PRO
    if data_parts[1] == "locked":
        await callback.answer(
            "🔒 Эта функция доступна на тарифе PRO",
            show_alert=True,
        )
        return

    if data_parts[1] == "none":
        numbering_mode = "none"
        start_number = None
    elif data_parts[1] == "from_1":
        numbering_mode = "sequential"
        start_number = 1
    elif data_parts[1] == "per_product":
        numbering_mode = "per_product"
        start_number = None
    elif data_parts[1] == "continue" and len(data_parts) > 2:
        numbering_mode = "continue"
        start_number = int(data_parts[2])
    else:
        numbering_mode = "sequential"
        start_number = 1

    await state.update_data(
        numbering_mode=numbering_mode,
        start_number=start_number,
    )

    await callback.answer()

    # Проверяем количество кодов для диапазона
    fsm_data = await state.get_data()
    codes_count = fsm_data.get("codes_count", 0)

    if codes_count > 20:
        # Показываем выбор диапазона
        await state.set_state(GenerateStates.selecting_range)
        await callback.message.edit_text(
            SELECT_RANGE_TEXT.format(total=codes_count),
            reply_markup=get_range_kb(codes_count),
            parse_mode="HTML",
        )
    else:
        # Переходим к генерации
        await proceed_to_generation(callback.message, state, callback.from_user.id)


@router.callback_query(GenerateStates.selecting_range, F.data.startswith("range:"))
async def cb_range_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора диапазона."""
    action = callback.data.split(":")[1]

    if action == "all":
        # Все коды — переходим к генерации
        await callback.answer()
        await proceed_to_generation(callback.message, state, callback.from_user.id)
    elif action == "custom":
        # Запрашиваем ввод диапазона
        fsm_data = await state.get_data()
        codes_count = fsm_data.get("codes_count", 0)

        await callback.message.edit_text(
            ENTER_RANGE_TEXT.format(total=codes_count),
            reply_markup=get_cancel_kb(),
            parse_mode="HTML",
        )
        await callback.answer()


@router.message(GenerateStates.selecting_range, F.text)
async def receive_range_input(message: Message, state: FSMContext):
    """Получение ввода диапазона."""
    text = message.text.strip()
    fsm_data = await state.get_data()
    codes_count = fsm_data.get("codes_count", 0)

    # Парсим диапазон (формат: "5-15")
    try:
        if "-" in text:
            start_str, end_str = text.split("-", 1)
            range_start = int(start_str.strip())
            range_end = int(end_str.strip())
        else:
            await message.answer(
                INVALID_RANGE_TEXT.format(total=codes_count),
                reply_markup=get_cancel_kb(),
                parse_mode="HTML",
            )
            return

        # Валидация
        if range_start < 1 or range_end > codes_count or range_start > range_end:
            await message.answer(
                INVALID_RANGE_TEXT.format(total=codes_count),
                reply_markup=get_cancel_kb(),
                parse_mode="HTML",
            )
            return

        # Сохраняем диапазон
        await state.update_data(
            range_start=range_start,
            range_end=range_end,
        )

        # Переходим к генерации
        await proceed_to_generation(message, state, message.from_user.id)

    except ValueError:
        await message.answer(
            INVALID_RANGE_TEXT.format(total=codes_count),
            reply_markup=get_cancel_kb(),
            parse_mode="HTML",
        )


async def proceed_to_generation(message: Message, state: FSMContext, user_id: int):
    """Переход к проверке настроек и генерации."""
    # Проверяем, есть ли сохранённые настройки
    user_settings = await get_user_settings_async()
    has_settings = await user_settings.has_settings(user_id)

    if has_settings:
        # Настройки есть — запускаем генерацию

        # Получаем bot из контекста
        bot = message.bot
        await process_generation(message, state, bot, user_id)
    else:
        # Первая генерация — запрашиваем данные организации
        await state.set_state(GenerateStates.waiting_organization)
        await message.answer(
            ASK_ORGANIZATION_TEXT,
            reply_markup=get_cancel_kb(),
            parse_mode="HTML",
        )


@router.callback_query(GenerateStates.confirming_truncation, F.data == "truncation_confirm")
async def cb_truncation_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Пользователь подтвердил продолжение с обрезкой полей."""
    await callback.message.edit_text(
        "Продолжаю с обрезкой длинных текстов...",
        parse_mode="HTML",
    )
    await callback.answer()

    # Переходим к нумерации вместо proceed_after_codes
    await proceed_to_numbering(callback.message, state)


@router.message(GenerateStates.waiting_codes, ~F.document)
async def waiting_codes_wrong_type(message: Message):
    """Неверный тип сообщения при ожидании кодов."""
    await message.answer(
        "Пожалуйста, отправьте PDF файл с кодами Честного Знака.\n\n"
        "💡 Скачайте PDF из личного кабинета ЧЗ (crpt.ru)",
        reply_markup=get_cancel_kb(),
    )


# ===== Organization / INN флоу (первая генерация) =====


@router.message(GenerateStates.waiting_organization, F.text)
async def receive_organization(message: Message, state: FSMContext):
    """Получение названия организации."""
    text = message.text.strip()

    # Если /skip — сохраняем пустое значение
    if text.lower() == "/skip":
        organization_name = ""
    else:
        organization_name = text

    # Сохраняем в FSM state
    await state.update_data(organization_name=organization_name)

    # Переходим к ИНН
    await state.set_state(GenerateStates.waiting_inn)
    await message.answer(
        ASK_INN_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )


@router.message(GenerateStates.waiting_inn, F.text)
async def receive_inn(message: Message, state: FSMContext, bot: Bot):
    """Получение ИНН и запуск генерации."""
    text = message.text.strip()

    # Если /skip — сохраняем пустое значение
    if text.lower() == "/skip":
        inn = ""
    else:
        inn = text

    # Сохраняем в FSM state
    await state.update_data(inn=inn)

    # Получаем telegram_id
    telegram_id = message.from_user.id if message.from_user else None

    if not telegram_id:
        await message.answer(
            "Ошибка идентификации пользователя. Попробуйте снова.",
            reply_markup=get_main_menu_kb(),
        )
        await state.clear()
        return

    # Сохраняем настройки в Redis
    data = await state.get_data()
    organization_name = data.get("organization_name", "")

    user_settings = await get_user_settings_async()
    await user_settings.save(
        telegram_id=telegram_id,
        organization_name=organization_name,
        inn=inn,
    )

    # Переходим к выбору шаблона
    await proceed_to_template_selection(message, state)


async def proceed_to_template_selection(message: Message, state: FSMContext):
    """Переход к выбору шаблона (первая генерация)."""
    from pathlib import Path

    from aiogram.types import FSInputFile

    # Отправляем фото-коллаж
    collage_path = Path(__file__).parent.parent / "assets" / "templates-collage.png"
    photo = FSInputFile(collage_path)

    await state.set_state(GenerateStates.selecting_template)
    await message.answer_photo(
        photo=photo,
        caption=(
            "<b>Выберите шаблон этикетки</b>\n\n"
            "Выбор сохранится в настройках.\n"
            "Изменить можно в /settings"
        ),
        reply_markup=get_template_select_kb("basic"),
        parse_mode="HTML",
    )


@router.callback_query(GenerateStates.selecting_template, F.data.startswith("template:"))
async def cb_first_template_selected(callback: CallbackQuery, state: FSMContext):
    """Сохранить шаблон при первой генерации и продолжить."""
    telegram_id = callback.from_user.id
    template = callback.data.split(":")[1]

    # Сохраняем в Redis
    user_settings = await get_user_settings_async()
    await user_settings.save(telegram_id, layout=template)

    # Сохраняем в FSM для текущей генерации
    await state.update_data(layout=template)

    template_names = {
        "basic": "Базовый",
        "professional": "Профессиональный",
        "extended": "Расширенный",
    }
    template_name = template_names.get(template, template)

    await callback.message.edit_caption(
        caption=f"✓ Шаблон: <b>{template_name}</b>\n\nГенерирую этикетки...",
        parse_mode="HTML",
    )
    await callback.answer()

    # Запускаем генерацию
    bot = callback.message.bot
    await process_generation(callback.message, state, bot, telegram_id)


async def process_generation(
    message: Message, state: FSMContext, bot: Bot, user_id: int | None = None
):
    """Процесс генерации этикеток (только Excel режим)."""
    await state.set_state(GenerateStates.processing)

    # Отправляем сообщение о процессе
    processing_msg = await message.answer(
        PROCESSING_TEXT,
        parse_mode="HTML",
    )

    # Получаем данные из состояния
    data = await state.get_data()
    codes_file_id = data.get("codes_file_id")
    codes_filename = data.get("codes_filename", "codes.pdf")
    excel_file_id = data.get("excel_file_id")
    excel_filename = data.get("excel_filename", "barcodes.xlsx")
    selected_column = data.get("selected_column", "")

    # Получаем telegram_id пользователя
    telegram_id = user_id or (message.from_user.id if message.from_user else None)

    if not excel_file_id or not selected_column:
        await processing_msg.edit_text(
            "Ошибка: данные Excel не найдены. Начните заново.",
            reply_markup=get_main_menu_kb(),
        )
        await state.clear()
        return

    # Получаем настройки организации (из FSM state или Redis)
    organization_name = data.get("organization_name")
    inn = data.get("inn")

    # Получаем параметры нумерации (если установлены через /from)
    numbering_mode = data.get("numbering_mode", "sequential")
    start_number = data.get("start_number")

    # Получаем параметры диапазона
    range_start = data.get("range_start")
    range_end = data.get("range_end")

    # Если настроек нет в FSM state — берём из Redis
    if organization_name is None and telegram_id:
        user_settings = await get_user_settings_async()
        redis_settings = await user_settings.get(telegram_id)
        if redis_settings:
            organization_name = redis_settings.get("organization_name", "")
            inn = redis_settings.get("inn", "")

    # Скачиваем файл с кодами
    try:
        codes_file_obj = await bot.get_file(codes_file_id)
        codes_bytes_io = io.BytesIO()
        await bot.download_file(codes_file_obj.file_path, codes_bytes_io)
        codes_file = codes_bytes_io.getvalue()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        await processing_msg.edit_text(
            f"Ошибка скачивания файла с кодами: {e}\nПопробуйте загрузить файлы заново.",
            reply_markup=get_main_menu_kb(),
        )
        await state.clear()
        return

    # Скачиваем Excel файл
    try:
        excel_file_obj = await bot.get_file(excel_file_id)
        excel_bytes_io = io.BytesIO()
        await bot.download_file(excel_file_obj.file_path, excel_bytes_io)
        excel_file = excel_bytes_io.getvalue()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        await processing_msg.edit_text(
            f"Ошибка скачивания Excel: {e}\nПопробуйте загрузить файлы заново.",
            reply_markup=get_main_menu_kb(),
        )
        await state.clear()
        return

    # Вызываем API для генерации из Excel
    api = get_api_client()
    result = await api.generate_from_excel(
        excel_file=excel_file,
        excel_filename=excel_filename,
        barcode_column=selected_column,
        codes_file=codes_file,
        codes_filename=codes_filename,
        telegram_id=telegram_id,
        organization_name=organization_name or None,
        inn=inn or None,
        numbering_mode=numbering_mode,
        start_number=start_number,
        range_start=range_start,
        range_end=range_end,
    )

    if not result.success:
        # Проверяем тип ошибки
        if result.status_code == 403:
            # Превышен лимит — используем данные из ответа API
            error_data = result.data or {}
            used = error_data.get("used_today", error_data.get("used", 50))
            limit = error_data.get("daily_limit", error_data.get("limit", 50))
            error_text = LIMIT_EXCEEDED_TEXT.format(used=used, limit=limit)
            await processing_msg.edit_text(
                error_text,
                reply_markup=get_upgrade_kb(),
                parse_mode="HTML",
            )
        else:
            # Другая ошибка
            error_text = f"""
<b>Ошибка генерации</b>

{result.error}

Проверьте файлы и попробуйте снова.
"""
            await processing_msg.edit_text(
                error_text,
                reply_markup=get_main_menu_kb(),
                parse_mode="HTML",
            )
        await state.clear()
        return

    # Проверяем успех в теле ответа (HTTP 200, но success=False в теле)
    response_data = result.data or {}

    # HITL: проверяем needs_confirmation (количество не совпадает)
    # ИЗМЕНЕНО: теперь просто показываем предупреждение, генерация уже выполнена
    if response_data.get("needs_confirmation"):
        count_mismatch = response_data.get("count_mismatch", {})
        excel_rows = count_mismatch.get("excel_rows", 0)
        codes_count = count_mismatch.get("codes_count", 0)
        will_generate = count_mismatch.get("will_generate", 0)
        # Добавляем предупреждение к успешному сообщению (не return!)
        mismatch_warning = (
            f"\n\n⚠️ <b>Примечание:</b> строк в Excel ({excel_rows}) ≠ кодов ЧЗ ({codes_count})\n"
            f"Создано {will_generate} этикеток по количеству кодов."
        )
    else:
        mismatch_warning = ""

    # Проверяем success в теле ответа
    if not response_data.get("success", True):
        error_message = response_data.get("message", "Неизвестная ошибка")
        await processing_msg.edit_text(
            f"<b>Ошибка генерации</b>\n\n{error_message}",
            reply_markup=get_main_menu_kb(),
            parse_mode="HTML",
        )
        await state.clear()
        return

    # Успешная генерация
    labels_count = response_data.get("labels_count", 0)
    pages_count = response_data.get("pages_count", labels_count)
    preflight = response_data.get("preflight", {})

    # Получаем информацию о лимитах
    daily_limit = response_data.get("daily_limit", 50)
    used_today = response_data.get("used_today", labels_count)

    # Формируем сообщение об успехе
    preflight_status = preflight.get("overall_status", "ok") if preflight else "ok"
    if preflight_status == "ok":
        success_text = f"<b>Сгенерировано {labels_count} этикеток ({pages_count} страниц)</b>\n\n"
        success_text += "Проверка качества: пройдена"
    else:
        success_text = f"<b>Сгенерировано {labels_count} этикеток ({pages_count} страниц)</b>\n\n"
        success_text += "Проверка качества: есть замечания"
        # Добавляем детали предупреждений
        checks = preflight.get("checks", []) if preflight else []
        for check in checks:
            check_status = check.get("status", "ok")
            if check_status in ("warning", "error"):
                check_message = check.get("message", "Проблема")
                success_text += f"\n• {check_message}"

    # Остаток лимита
    if daily_limit == 0 or is_unlimited(daily_limit):
        success_text += "\n\nОсталось сегодня: ∞ безлимит"
    else:
        remaining = max(0, daily_limit - used_today)
        success_text += f"\n\nОсталось сегодня: {remaining} из {daily_limit}"

    # Добавляем предупреждение о несовпадении количества (если было)
    success_text += mismatch_warning

    file_id = response_data.get("file_id")
    pdf_sent = False  # Флаг: PDF отправлен как документ

    if file_id:
        # Скачиваем PDF
        pdf_bytes = await api.download_pdf(file_id)
        if pdf_bytes:
            # Отправляем файл
            await message.answer_document(
                BufferedInputFile(
                    pdf_bytes,
                    filename=f"kleykod_labels_{labels_count}.pdf",
                ),
                caption=success_text,
                parse_mode="HTML",
            )
            pdf_sent = True

            # Показываем клавиатуру действий (не для безлимита)
            if (
                daily_limit > 0
                and not is_unlimited(daily_limit)
                and (daily_limit - used_today) <= 0
            ):
                await message.answer(
                    LIMIT_EXCEEDED_TEXT.format(used=used_today, limit=daily_limit),
                    reply_markup=get_upgrade_kb(),
                    parse_mode="HTML",
                )
            else:
                await message.answer(
                    "Что дальше?",
                    reply_markup=get_after_generation_kb(),
                )
        else:
            # Файл не найден, отправляем только текст
            await processing_msg.edit_text(
                success_text + "\n\n(Файл будет доступен для скачивания на сайте)",
                reply_markup=get_after_generation_kb(),
                parse_mode="HTML",
            )
    else:
        await processing_msg.edit_text(
            success_text,
            reply_markup=get_after_generation_kb(),
            parse_mode="HTML",
        )

    # Очищаем состояние генерации
    await state.clear()

    # Удаляем сообщение о процессе ТОЛЬКО если PDF был отправлен как документ
    # Иначе сообщение уже отредактировано и содержит результат
    if pdf_sent:
        try:
            await processing_msg.delete()
        except Exception:
            pass

    # Проверяем, нужно ли показать опрос обратной связи
    if telegram_id:
        await maybe_ask_feedback(message, state, telegram_id)


async def maybe_ask_feedback(message: Message, state: FSMContext, telegram_id: int):
    """
    Проверить, нужно ли запросить обратную связь.

    Показываем опрос после 3-й генерации, если ещё не спрашивали.
    """
    api = get_api_client()
    feedback_status = await api.get_feedback_status(telegram_id)

    if not feedback_status:
        return

    should_ask = feedback_status.get("should_ask", False)

    if should_ask:
        await state.set_state(GenerateStates.waiting_feedback)
        await message.answer(
            FEEDBACK_REQUEST_TEXT,
            reply_markup=get_feedback_kb(),
            parse_mode="HTML",
        )


@router.message(GenerateStates.waiting_feedback, F.text)
async def receive_feedback(message: Message, state: FSMContext):
    """Обработка текста обратной связи."""
    feedback_text = message.text

    # Отправляем feedback через API
    api = get_api_client()
    telegram_id = message.from_user.id if message.from_user else None

    if telegram_id:
        await api.submit_feedback(
            telegram_id=telegram_id,
            text=feedback_text,
            source="bot",
        )

    await message.answer(
        FEEDBACK_THANKS_TEXT,
        reply_markup=get_main_menu_kb(),
    )
    await state.clear()


@router.callback_query(GenerateStates.waiting_feedback, F.data == "skip_feedback")
async def cb_skip_feedback(callback: CallbackQuery, state: FSMContext):
    """Обработка пропуска обратной связи."""
    await callback.answer()
    await callback.message.edit_text(
        FEEDBACK_SKIP_TEXT,
        reply_markup=get_main_menu_kb(),
    )
    await state.clear()
