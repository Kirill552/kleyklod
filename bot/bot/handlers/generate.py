"""
Обработчики генерации этикеток.

Workflow:
1. Пользователь нажимает «Создать этикетки»
2. Отправляет Excel с баркодами WB
3. Отправляет CSV/Excel с кодами ЧЗ
4. (Первая генерация) Вводит название организации и ИНН
5. Получает готовый PDF
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
    get_excel_step_kb,
    get_feedback_kb,
    get_main_menu_kb,
    get_upgrade_kb,
)
from bot.states import GenerateStates
from bot.utils import get_api_client, get_user_settings_async

router = Router(name="generate")


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

Теперь отправьте файл с кодами маркировки:
• CSV файл
• Excel файл (.xlsx)

⚠️ <b>Важно:</b> количество кодов ЧЗ должно совпадать с количеством баркодов ({barcodes_count} шт.)
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

ASK_ORGANIZATION_TEXT = """
🏢 <b>Укажите название организации для этикеток</b>

Например: ООО «Рога и Копыта»

Или отправьте /skip чтобы пропустить
"""

ASK_INN_TEXT = """
📋 <b>Укажите ИНН</b> (опционально)

Отправьте /skip чтобы пропустить
"""


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
    """Получение файла с кодами ЧЗ — проверяем настройки или запрашиваем."""
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

    # Сохраняем file_id в состояние
    await state.update_data(
        codes_file_id=document.file_id,
        codes_filename=filename,
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

    # Проверяем, есть ли сохранённые настройки в Redis
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


@router.message(GenerateStates.waiting_codes, ~F.document)
async def waiting_codes_wrong_type(message: Message):
    """Неверный тип сообщения при ожидании кодов."""
    await message.answer(
        "Пожалуйста, отправьте CSV или Excel файл с кодами Честного Знака.",
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

    # Запускаем генерацию
    await process_generation(message, state, bot, telegram_id)


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
    codes_filename = data.get("codes_filename", "codes.csv")
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

    # Проверяем успех в теле ответа (HTTP 200, но success=False в теле)
    response_data = result.data or {}

    # HITL: проверяем needs_confirmation (количество не совпадает)
    if response_data.get("needs_confirmation"):
        count_mismatch = response_data.get("count_mismatch", {})
        excel_rows = count_mismatch.get("excel_rows", 0)
        codes_count = count_mismatch.get("codes_count", 0)
        will_generate = count_mismatch.get("will_generate", 0)
        await processing_msg.edit_text(
            f"<b>Количество не совпадает</b>\n\n"
            f"Строк в Excel: {excel_rows}\n"
            f"Кодов ЧЗ: {codes_count}\n\n"
            f"Будет создано {will_generate} этикеток.\n\n"
            f"Для продолжения используйте веб-версию:\n"
            f"🌐 kleykod.ru/app/generate",
            reply_markup=get_main_menu_kb(),
            parse_mode="HTML",
        )
        await state.clear()
        return

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
    success_text = f"""
<b>Этикетки готовы!</b>

Сгенерировано: {labels_count} этикеток • {pages_count} страниц
Шаблон: 58x40мм (203 DPI)
"""

    # Добавляем результаты проверки качества
    if preflight:
        preflight_status = preflight.get("overall_status", "ok")
        if preflight_status == "ok":
            success_text += "\nПроверка качества: Все проверки пройдены"
        elif preflight_status == "warning":
            success_text += "\nПроверка качества: Есть предупреждения"
        else:
            success_text += "\nПроверка качества: Обнаружены проблемы"

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
