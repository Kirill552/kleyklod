"""
Обработчик генерации WB-only этикеток.

Workflow:
1. Пользователь выбирает режим "📦 Только WB"
2. Загружает Excel файл с баркодами
3. Выбирает размер этикетки (58×40 или 58×30)
4. Получает PDF с готовыми этикетками
5. Видит апсейл на объединение WB + ЧЗ
"""

import io
import logging

import sentry_sdk
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.config import get_bot_settings
from bot.keyboards.inline import (
    get_cancel_kb,
    get_main_menu_kb,
    label_size_keyboard,
    wb_only_upsell_keyboard,
)
from bot.states import WbOnlyStates
from bot.utils import get_api_client

logger = logging.getLogger(__name__)

router = Router(name="wb_only")


# Тексты
START_WB_ONLY_TEXT = """
<b>📦 Генерация WB этикеток</b>

Загрузите Excel файл с баркодами Wildberries.

<i>Как скачать файл:</i>
WB Партнёры → Товары → Карточки товаров →
Скачать (иконка ↓) → Баркоды шк/размеров

Или создайте файл вручную с колонкой «Баркод».
"""

PROCESSING_TEXT = """
<b>⏳ Генерирую этикетки...</b>

Обрабатываю данные из Excel.
Это займёт несколько секунд.
"""

SUCCESS_TEXT = """
<b>✅ Готово!</b>

Сгенерировано <b>{count}</b> этикеток WB.
Размер: {size}
"""

UPSELL_TEXT = """
💡 <b>Совет:</b> Объедините WB + ЧЗ в одну наклейку!

Экономия времени и расходников — клеить в 2 раза быстрее.
"""


@router.callback_query(F.data == "gen_mode:wb_only")
async def start_wb_only(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало WB-only генерации."""
    await callback.answer()
    await state.set_state(WbOnlyStates.waiting_excel)

    await callback.message.edit_text(
        START_WB_ONLY_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )


@router.message(WbOnlyStates.waiting_excel, F.document)
async def process_excel(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Обработка загруженного Excel."""
    document = message.document
    filename = document.file_name or "barcodes.xlsx"

    # Проверяем формат
    if not filename.lower().endswith((".xlsx", ".xls")):
        await message.answer(
            "❌ Неверный формат файла.\n" "Загрузите Excel (.xlsx или .xls)",
            reply_markup=get_cancel_kb(),
        )
        return

    # Проверка размера
    settings = get_bot_settings()
    if document.file_size and document.file_size > settings.max_file_size_bytes:
        await message.answer(
            f"❌ Файл слишком большой.\n" f"Максимум: {settings.max_file_size_mb} МБ",
            reply_markup=get_cancel_kb(),
        )
        return

    # Показываем статус загрузки
    status_msg = await message.answer("📥 Анализирую Excel файл...")

    # Скачиваем файл
    try:
        file = await bot.get_file(document.file_id)
        file_bytes_io = io.BytesIO()
        await bot.download_file(file.file_path, file_bytes_io)
        excel_bytes = file_bytes_io.getvalue()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        await status_msg.edit_text(
            f"❌ Ошибка загрузки файла: {e}",
            reply_markup=get_cancel_kb(),
        )
        return

    # Парсим Excel через API для получения items
    api = get_api_client()
    result = await api.parse_excel_barcodes(excel_bytes, filename)

    if not result:
        await status_msg.edit_text(
            "❌ Ошибка чтения Excel файла.\n" "Проверьте формат и попробуйте снова.",
            reply_markup=get_cancel_kb(),
        )
        return

    # Проверяем что есть данные
    total_rows = result.get("total_rows", 0)
    sample_items = result.get("sample_items", [])

    if total_rows == 0:
        await status_msg.edit_text(
            "❌ В Excel файле не найдено баркодов.\n"
            "Убедитесь, что файл содержит колонку с баркодами.",
            reply_markup=get_cancel_kb(),
        )
        return

    # Сохраняем данные в состояние
    # sample_items содержит полные данные товаров с barcode, name, article, size, color
    await state.update_data(
        excel_bytes=excel_bytes,
        excel_filename=filename,
        items=sample_items,  # Используем sample_items как items для генерации
        total_rows=total_rows,
    )

    await state.set_state(WbOnlyStates.select_size)

    await status_msg.edit_text(
        f"<b>Найдено {total_rows} баркодов</b>\n\n" "Выберите размер этикетки:",
        reply_markup=label_size_keyboard(),
        parse_mode="HTML",
    )


@router.message(WbOnlyStates.waiting_excel, ~F.document)
async def waiting_excel_wrong_type(message: Message) -> None:
    """Неверный тип сообщения при ожидании Excel."""
    await message.answer(
        "Пожалуйста, отправьте Excel файл (.xlsx) с баркодами.",
        reply_markup=get_cancel_kb(),
    )


@router.callback_query(WbOnlyStates.select_size, F.data.startswith("size:"))
async def process_size(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Обработка выбора размера и генерация."""
    await callback.answer()
    size = callback.data.split(":")[1]  # 58x40 или 58x30

    # Форматируем размер для отображения
    size_display = size.replace("x", "×") + " мм"

    # Получаем telegram_id пользователя
    telegram_id = callback.from_user.id

    data = await state.get_data()
    items = data.get("items", [])
    total_rows = data.get("total_rows", 0)

    if not items:
        await callback.message.edit_text(
            "❌ Данные не найдены. Начните заново.",
            reply_markup=get_main_menu_kb(),
        )
        await state.clear()
        return

    # Отправляем статус
    status_msg = await callback.message.edit_text(PROCESSING_TEXT, parse_mode="HTML")

    try:
        # Вызываем API для генерации WB-only этикеток
        api = get_api_client()

        # Формируем данные для API
        # items из parse_excel_barcodes содержат: barcode, name, article, size, color
        # Добавляем quantity = 1 для каждого item
        items_with_qty = [
            {
                "barcode": item.get("barcode", ""),
                "name": item.get("name", ""),
                "article": item.get("article", ""),
                "size": item.get("size", ""),
                "color": item.get("color", ""),
                "quantity": 1,
            }
            for item in items
        ]

        result = await api.generate_wb_labels(
            items=items_with_qty,
            telegram_id=telegram_id,
            label_size=size,
        )

        if not result.success:
            await status_msg.edit_text(
                f"❌ Ошибка генерации: {result.error}",
                reply_markup=get_main_menu_kb(),
            )
            await state.clear()
            return

        # Получаем PDF
        response_data = result.data or {}
        file_id = response_data.get("file_id")
        labels_count = response_data.get("labels_count", total_rows)

        if file_id:
            # Скачиваем PDF
            pdf_bytes = await api.download_pdf(file_id)

            if pdf_bytes:
                # Отправляем PDF
                await callback.message.answer_document(
                    document=BufferedInputFile(
                        pdf_bytes,
                        filename=f"wb_labels_{size}.pdf",
                    ),
                    caption=SUCCESS_TEXT.format(
                        count=labels_count,
                        size=size_display,
                    ),
                    parse_mode="HTML",
                )

                # Удаляем статусное сообщение
                try:
                    await status_msg.delete()
                except Exception:
                    pass

                # Апсейл на объединение WB + ЧЗ
                await callback.message.answer(
                    UPSELL_TEXT,
                    reply_markup=wb_only_upsell_keyboard(),
                    parse_mode="HTML",
                )
            else:
                await status_msg.edit_text(
                    "❌ Файл не найден. Попробуйте снова.",
                    reply_markup=get_main_menu_kb(),
                )
        else:
            await status_msg.edit_text(
                "❌ Ошибка: файл не создан.",
                reply_markup=get_main_menu_kb(),
            )

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"[WB-only] Ошибка генерации: {e}")
        await status_msg.edit_text(
            f"❌ Ошибка: {e}",
            reply_markup=get_main_menu_kb(),
        )

    finally:
        await state.clear()


@router.callback_query(F.data == "back_to_mode_select")
async def back_to_mode_select(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат к выбору режима генерации."""
    from bot.keyboards.inline import generation_mode_keyboard

    await state.clear()
    await callback.message.edit_text(
        "<b>Выберите режим генерации:</b>",
        reply_markup=generation_mode_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()
