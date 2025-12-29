"""
Обработчики генерации этикеток.

Основной workflow:
1. Пользователь нажимает «Создать этикетки»
2. Отправляет PDF от Wildberries
3. Отправляет CSV/Excel с кодами ЧЗ
4. Получает готовый PDF
"""

import io

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.config import get_bot_settings
from bot.keyboards import (
    get_after_generation_kb,
    get_cancel_kb,
    get_column_confirm_kb,
    get_column_select_kb,
    get_feedback_kb,
    get_format_choice_kb,
    get_main_menu_kb,
    get_mode_choice_kb,
    get_upgrade_kb,
)
from bot.states import GenerateStates
from bot.utils import get_api_client

router = Router(name="generate")


# Тексты
CHOOSE_MODE_TEXT = """
<b>Создание этикеток</b>

Выберите, что у вас есть:

📄 <b>PDF из WB</b> — готовые этикетки из раздела "Поставки"
📊 <b>Excel с баркодами</b> — файл со списком штрихкодов
"""

SEND_PDF_TEXT = """
<b>Шаг 1 из 3: PDF от Wildberries</b>

Отправьте PDF файл с этикетками от Wildberries.

Этот файл вы скачиваете из личного кабинета WB при создании поставки.
"""

SEND_EXCEL_TEXT = """
<b>Шаг 1 из 3: Excel с баркодами</b>

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
<b>Шаг 2 из 3: Коды Честного Знака</b>

Теперь отправьте файл с кодами маркировки:
• CSV файл
• Excel файл (.xlsx)

Файл должен содержать коды DataMatrix из системы Честный Знак.
"""

CHOOSE_FORMAT_TEXT = """
<b>Шаг 3 из 3: Формат этикеток</b>

Выберите как разместить коды:

<b>Объединённые</b> (рекомендуется)
WB + DataMatrix на одной этикетке 58×40мм
Экономит материал и время печати

<b>Раздельные</b>
WB и DataMatrix на отдельных листах
Порядок: WB1, ЧЗ1, WB2, ЧЗ2...
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


@router.callback_query(F.data == "generate")
async def cb_generate_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса генерации — выбор режима."""
    await state.set_state(GenerateStates.choosing_mode)
    await callback.message.edit_text(
        CHOOSE_MODE_TEXT,
        reply_markup=get_mode_choice_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(GenerateStates.choosing_mode, F.data == "mode_pdf")
async def cb_mode_pdf(callback: CallbackQuery, state: FSMContext):
    """Выбран PDF режим — существующий флоу."""
    await state.update_data(mode="pdf")
    await state.set_state(GenerateStates.waiting_pdf)
    await callback.message.edit_text(
        SEND_PDF_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(GenerateStates.choosing_mode, F.data == "mode_excel")
async def cb_mode_excel(callback: CallbackQuery, state: FSMContext):
    """Выбран Excel режим — новый флоу."""
    await state.update_data(mode="excel")
    await state.set_state(GenerateStates.waiting_excel)
    await callback.message.edit_text(
        SEND_EXCEL_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.text == "Создать этикетки")
async def text_generate_start(message: Message, state: FSMContext):
    """Текстовая команда для начала генерации — показываем выбор режима."""
    await state.set_state(GenerateStates.choosing_mode)
    await message.answer(
        CHOOSE_MODE_TEXT,
        reply_markup=get_mode_choice_kb(),
        parse_mode="HTML",
    )


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
    await state.update_data(
        excel_file_id=document.file_id,
        excel_filename=filename,
        excel_columns=result.get("columns", []),
        detected_column=result.get("detected_column"),
        confidence=result.get("confidence", 0),
        barcodes_count=result.get("total_count", 0),
        sample_items=result.get("sample_items", []),
    )

    columns = result.get("columns", [])
    confidence = result.get("confidence", 0)
    detected_column = result.get("detected_column")
    total_count = result.get("total_count", 0)
    sample_items = result.get("sample_items", [])

    # Решаем: подтверждение или выбор
    if confidence >= 0.8 and detected_column:
        # Высокая уверенность — просим подтвердить
        await state.set_state(GenerateStates.confirming_column)
        await status_msg.edit_text(
            CONFIRM_COLUMN_TEXT.format(
                count=total_count,
                column=detected_column,
                sample_1=sample_items[0] if sample_items else "—",
                sample_2=sample_items[1] if len(sample_items) > 1 else "—",
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

    # Переходим к загрузке кодов ЧЗ
    await state.set_state(GenerateStates.waiting_codes)
    await callback.message.edit_text(
        SEND_CODES_TEXT,
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

    # Переходим к загрузке кодов ЧЗ
    await state.set_state(GenerateStates.waiting_codes)
    await callback.message.edit_text(
        SEND_CODES_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


# ===== PDF флоу =====


@router.message(GenerateStates.waiting_pdf, F.document)
async def receive_pdf(message: Message, state: FSMContext, bot: Bot):
    """Получение PDF файла."""
    document = message.document

    # Проверка типа файла
    if document.mime_type != "application/pdf":
        await message.answer(
            "Пожалуйста, отправьте PDF файл.\n\nФайл должен быть в формате .pdf",
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

    # Сохраняем file_id в состояние (не bytes, чтобы Redis мог сериализовать)
    await state.update_data(
        wb_pdf_file_id=document.file_id,
        wb_pdf_name=document.file_name or "wb_labels.pdf",
    )

    # Переходим к следующему шагу
    await state.set_state(GenerateStates.waiting_codes)
    await message.answer(
        SEND_CODES_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )


@router.message(GenerateStates.waiting_pdf, ~F.document)
async def waiting_pdf_wrong_type(message: Message):
    """Неверный тип сообщения при ожидании PDF."""
    await message.answer(
        "Пожалуйста, отправьте PDF файл с этикетками от Wildberries.",
        reply_markup=get_cancel_kb(),
    )


@router.message(GenerateStates.waiting_codes, F.document)
async def receive_codes(message: Message, state: FSMContext, bot: Bot):
    """Получение файла с кодами ЧЗ."""
    document = message.document

    # Проверка типа файла
    allowed_types = [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "application/octet-stream",  # Иногда CSV отправляется так
    ]

    filename = document.file_name or "codes.csv"
    extension = filename.lower().split(".")[-1] if "." in filename else ""

    if document.mime_type not in allowed_types and extension not in ["csv", "xlsx", "xls"]:
        await message.answer(
            "Пожалуйста, отправьте CSV или Excel файл с кодами.\n\n"
            "Поддерживаемые форматы: .csv, .xlsx, .xls",
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

    # Сохраняем file_id в состояние (не bytes, чтобы Redis мог сериализовать)
    await state.update_data(
        codes_file_id=document.file_id,
        codes_filename=filename,
    )

    # Переходим к выбору формата
    await state.set_state(GenerateStates.choosing_format)
    await message.answer(
        CHOOSE_FORMAT_TEXT,
        reply_markup=get_format_choice_kb(),
        parse_mode="HTML",
    )


@router.message(GenerateStates.waiting_codes, ~F.document)
async def waiting_codes_wrong_type(message: Message):
    """Неверный тип сообщения при ожидании кодов."""
    await message.answer(
        "Пожалуйста, отправьте CSV или Excel файл с кодами Честного Знака.",
        reply_markup=get_cancel_kb(),
    )


@router.callback_query(GenerateStates.choosing_format, F.data.startswith("format_"))
async def cb_choose_format(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обработка выбора формата этикеток."""
    # Определяем выбранный формат
    format_type = callback.data.replace("format_", "")  # combined или separate

    # Сохраняем в состояние
    await state.update_data(label_format=format_type)

    # Запускаем генерацию
    await callback.answer()
    await process_generation(callback.message, state, bot, callback.from_user.id)


async def process_generation(
    message: Message, state: FSMContext, bot: Bot, user_id: int | None = None
):
    """Процесс генерации этикеток (PDF или Excel режим)."""
    await state.set_state(GenerateStates.processing)

    # Отправляем сообщение о процессе
    processing_msg = await message.answer(
        PROCESSING_TEXT,
        parse_mode="HTML",
    )

    # Получаем данные из состояния
    data = await state.get_data()
    mode = data.get("mode", "pdf")
    codes_file_id = data.get("codes_file_id")
    codes_filename = data.get("codes_filename", "codes.csv")
    label_format = data.get("label_format", "combined")

    # Получаем telegram_id пользователя
    telegram_id = user_id or (message.from_user.id if message.from_user else None)

    # Скачиваем файл с кодами (общий для обоих режимов)
    try:
        codes_file_obj = await bot.get_file(codes_file_id)
        codes_bytes_io = io.BytesIO()
        await bot.download_file(codes_file_obj.file_path, codes_bytes_io)
        codes_file = codes_bytes_io.getvalue()
    except Exception as e:
        await processing_msg.edit_text(
            f"Ошибка скачивания файла с кодами: {e}\nПопробуйте загрузить файлы заново.",
            reply_markup=get_main_menu_kb(),
        )
        await state.clear()
        return

    api = get_api_client()

    if mode == "excel":
        # Excel режим — генерация из Excel с баркодами
        excel_file_id = data.get("excel_file_id")
        excel_filename = data.get("excel_filename", "barcodes.xlsx")
        selected_column = data.get("selected_column", "")

        if not excel_file_id or not selected_column:
            await processing_msg.edit_text(
                "Ошибка: данные Excel не найдены. Начните заново.",
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
            await processing_msg.edit_text(
                f"Ошибка скачивания Excel: {e}\nПопробуйте загрузить файлы заново.",
                reply_markup=get_main_menu_kb(),
            )
            await state.clear()
            return

        # Вызываем API для генерации из Excel
        result = await api.generate_from_excel(
            excel_file=excel_file,
            excel_filename=excel_filename,
            barcode_column=selected_column,
            codes_file=codes_file,
            codes_filename=codes_filename,
            telegram_id=telegram_id,
            label_format=label_format,
        )
    else:
        # PDF режим — существующая логика
        wb_pdf_file_id = data.get("wb_pdf_file_id")

        if not wb_pdf_file_id:
            await processing_msg.edit_text(
                "Ошибка: PDF файл не найден. Начните заново.",
                reply_markup=get_main_menu_kb(),
            )
            await state.clear()
            return

        # Скачиваем PDF файл
        try:
            wb_file = await bot.get_file(wb_pdf_file_id)
            wb_bytes_io = io.BytesIO()
            await bot.download_file(wb_file.file_path, wb_bytes_io)
            wb_pdf = wb_bytes_io.getvalue()
        except Exception as e:
            await processing_msg.edit_text(
                f"Ошибка скачивания PDF: {e}\nПопробуйте загрузить файлы заново.",
                reply_markup=get_main_menu_kb(),
            )
            await state.clear()
            return

        # Вызываем API для генерации из PDF
        result = await api.merge_labels(
            wb_pdf=wb_pdf,
            codes_file=codes_file,
            codes_filename=codes_filename,
            telegram_id=telegram_id,
            label_format=label_format,
        )

    if not result.success:
        # Проверяем тип ошибки
        if result.status_code == 403:
            # Превышен лимит
            error_text = """
<b>Превышен дневной лимит</b>

Ваш бесплатный лимит на сегодня исчерпан.

<b>Варианты:</b>
• Подождите до завтра (лимит обновится)
• Оформите Pro подписку (500 этикеток/день)

Нажмите «Тарифы» для просмотра планов.
"""
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

    # Успешная генерация
    response_data = result.data or {}
    labels_count = response_data.get("labels_count", 0)
    pages_count = response_data.get("pages_count", labels_count)
    result_format = response_data.get("label_format", label_format)
    preflight = response_data.get("preflight", {})

    # Получаем информацию о лимитах
    daily_limit = response_data.get("daily_limit", 50)
    used_today = response_data.get("used_today", labels_count)

    # Определяем текст формата
    format_text = "объединённый" if result_format == "combined" else "раздельный"

    # Формируем сообщение об успехе
    success_text = f"""
<b>Этикетки готовы!</b>

Сгенерировано: {labels_count} этикеток • {pages_count} страниц
Формат: {format_text}
Шаблон: 58x40мм (203 DPI)
"""

    # Добавляем результаты проверки качества
    if preflight:
        preflight_status = preflight.get("overall_status", "ok")
        if preflight_status == "ok":
            success_text += "\nПроверка качества: Все проверки пройдены"
        elif preflight_status == "warning":
            success_text += "\nПроверка качества: Есть предупреждения (см. выше)"
        else:
            success_text += "\nПроверка качества: Обнаружены проблемы"

    # TODO: Получить PDF из хранилища и отправить
    # Пока отправляем заглушку
    file_id = response_data.get("file_id")

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

            # Показываем остаток лимита
            if daily_limit == 0:
                # Enterprise — безлимит
                await message.answer(
                    "Что дальше?",
                    reply_markup=get_after_generation_kb(),
                )
            else:
                remaining = max(0, daily_limit - used_today)
                if remaining > 0:
                    await message.answer(
                        f"Осталось на сегодня: {remaining} этикеток",
                        reply_markup=get_after_generation_kb(),
                    )
                else:
                    await message.answer(
                        "Дневной лимит исчерпан. Оформите Pro для 500 этикеток/день!",
                        reply_markup=get_upgrade_kb(),
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

    # Удаляем сообщение о процессе
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
