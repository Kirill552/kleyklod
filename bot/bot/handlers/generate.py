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
from bot.keyboards import get_cancel_kb, get_feedback_kb, get_format_choice_kb, get_main_menu_kb
from bot.states import GenerateStates
from bot.utils import get_api_client

router = Router(name="generate")


# Тексты
SEND_PDF_TEXT = """
<b>Шаг 1 из 2: PDF от Wildberries</b>

Отправьте PDF файл с этикетками от Wildberries.

Этот файл вы скачиваете из личного кабинета WB при создании поставки.
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
    """Начало процесса генерации."""
    # TODO: Проверить лимит пользователя

    await state.set_state(GenerateStates.waiting_pdf)
    await callback.message.edit_text(
        SEND_PDF_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.text == "Создать этикетки")
async def text_generate_start(message: Message, state: FSMContext):
    """Текстовая команда для начала генерации."""
    await state.set_state(GenerateStates.waiting_pdf)
    await message.answer(
        SEND_PDF_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )


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
    """Процесс генерации этикеток."""
    await state.set_state(GenerateStates.processing)

    # Отправляем сообщение о процессе
    processing_msg = await message.answer(
        PROCESSING_TEXT,
        parse_mode="HTML",
    )

    # Получаем данные из состояния
    data = await state.get_data()
    wb_pdf_file_id = data.get("wb_pdf_file_id")
    codes_file_id = data.get("codes_file_id")
    codes_filename = data.get("codes_filename", "codes.csv")
    label_format = data.get("label_format", "combined")

    if not wb_pdf_file_id or not codes_file_id:
        await processing_msg.edit_text(
            "Ошибка: файлы не найдены. Начните заново.",
            reply_markup=get_main_menu_kb(),
        )
        await state.clear()
        return

    # Скачиваем файлы по file_id (только в момент обработки)
    try:
        wb_file = await bot.get_file(wb_pdf_file_id)
        wb_bytes_io = io.BytesIO()
        await bot.download_file(wb_file.file_path, wb_bytes_io)
        wb_pdf = wb_bytes_io.getvalue()

        codes_file_obj = await bot.get_file(codes_file_id)
        codes_bytes_io = io.BytesIO()
        await bot.download_file(codes_file_obj.file_path, codes_bytes_io)
        codes_file = codes_bytes_io.getvalue()
    except Exception as e:
        await processing_msg.edit_text(
            f"Ошибка скачивания файлов: {e}\nПопробуйте загрузить файлы заново.",
            reply_markup=get_main_menu_kb(),
        )
        await state.clear()
        return

    # Получаем telegram_id пользователя (из параметра или message)
    telegram_id = user_id or (message.from_user.id if message.from_user else None)

    # Вызываем API с telegram_id для учёта лимитов и label_format
    api = get_api_client()
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
        else:
            # Файл не найден, отправляем только текст
            await processing_msg.edit_text(
                success_text + "\n\n(Файл будет доступен для скачивания на сайте)",
                reply_markup=get_main_menu_kb(),
                parse_mode="HTML",
            )
    else:
        await processing_msg.edit_text(
            success_text,
            reply_markup=get_main_menu_kb(),
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
