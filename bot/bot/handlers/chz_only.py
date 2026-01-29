"""Обработчик генерации ЧЗ-only этикеток."""

import io
import logging

import sentry_sdk
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.config import get_bot_settings
from bot.keyboards import get_cancel_kb, get_main_menu_kb
from bot.keyboards.inline import chz_only_upsell_keyboard
from bot.states import ChzOnlyStates
from bot.utils import get_api_client

router = Router(name="chz_only")
logger = logging.getLogger(__name__)


# === Тексты сообщений ===

START_CHZ_ONLY_TEXT = """
<b>Генерация ЧЗ этикеток</b>

Загрузите CSV файл с кодами маркировки.

<i>Как скачать:</i>
ЛК Честного Знака -> Коды маркировки -> Экспорт -> CSV

<b>Важно:</b> Не открывайте CSV в Excel — это испортит коды!
"""

PROCESSING_TEXT = """
<b>Генерация этикеток...</b>

Создаю этикетки с DataMatrix кодами.
Это займёт несколько секунд.
"""

INVALID_FORMAT_TEXT = """
Неверный формат файла.

Загрузите <b>CSV файл</b> из личного кабинета Честного Знака.

<i>Путь:</i> ЛК ЧЗ -> Коды маркировки -> Экспорт -> CSV
"""

UPSELL_TEXT = """
<b>Совет:</b> Добавьте штрихкод WB на этикетку!
Объедините ШК и DataMatrix — клеить в 2 раза быстрее.
"""


@router.callback_query(F.data == "gen_mode:chz_only")
async def start_chz_only(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало ЧЗ-only генерации."""
    await callback.answer()
    await state.set_state(ChzOnlyStates.waiting_csv)

    await callback.message.edit_text(
        START_CHZ_ONLY_TEXT,
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )


@router.message(ChzOnlyStates.waiting_csv, F.document)
async def process_csv(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Обработка загруженного CSV файла."""
    document = message.document
    filename = document.file_name or "codes.csv"

    # Проверяем формат
    if not filename.lower().endswith(".csv"):
        await message.answer(
            INVALID_FORMAT_TEXT,
            reply_markup=get_cancel_kb(),
            parse_mode="HTML",
        )
        return

    # Проверяем размер файла
    settings = get_bot_settings()
    if document.file_size > settings.max_file_size_bytes:
        await message.answer(
            f"Файл слишком большой. Максимум: {settings.max_file_size_mb} МБ",
            reply_markup=get_cancel_kb(),
        )
        return

    # Отправляем статус
    status_msg = await message.answer(
        PROCESSING_TEXT,
        parse_mode="HTML",
    )

    # Скачиваем файл
    try:
        file = await bot.get_file(document.file_id)
        file_bytes_io = io.BytesIO()
        await bot.download_file(file.file_path, file_bytes_io)
        csv_bytes = file_bytes_io.getvalue()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        await status_msg.edit_text(
            f"Ошибка загрузки файла: {e}",
            reply_markup=get_cancel_kb(),
        )
        return

    # Получаем telegram_id
    telegram_id = message.from_user.id if message.from_user else None

    if not telegram_id:
        await status_msg.edit_text(
            "Ошибка идентификации пользователя. Попробуйте снова.",
            reply_markup=get_main_menu_kb(),
        )
        await state.clear()
        return

    try:
        # Вызываем API для генерации ЧЗ-only
        api = get_api_client()
        result = await api.generate_chz_only(
            csv_bytes=csv_bytes,
            filename=filename,
            telegram_id=telegram_id,
        )

        if not result.success:
            # Обработка ошибок
            if result.status_code == 403:
                error_data = result.data or {}
                used = error_data.get("used_today", error_data.get("used", 50))
                limit = error_data.get("daily_limit", error_data.get("limit", 50))
                error_text = (
                    f"<b>Лимит исчерпан</b>\n\n"
                    f"Использовано: {used} / {limit} этикеток\n\n"
                    f"Перейдите на PRO для увеличения лимита."
                )
            else:
                error_text = f"<b>Ошибка генерации</b>\n\n{result.error}"

            await status_msg.edit_text(
                error_text,
                reply_markup=get_main_menu_kb(),
                parse_mode="HTML",
            )
            await state.clear()
            return

        # Успешная генерация
        response_data = result.data or {}
        labels_count = response_data.get("labels_count", 0)
        file_id = response_data.get("file_id")

        # Скачиваем PDF
        if file_id:
            pdf_bytes = await api.download_pdf(file_id)
            if pdf_bytes:
                # Отправляем файл
                await message.answer_document(
                    BufferedInputFile(
                        pdf_bytes,
                        filename=f"chz_labels_{labels_count}.pdf",
                    ),
                    caption=f"<b>Готово!</b> Сгенерировано {labels_count} этикеток",
                    parse_mode="HTML",
                )

                # Удаляем сообщение о процессе
                try:
                    await status_msg.delete()
                except Exception:
                    pass

                # Апсейл
                await message.answer(
                    UPSELL_TEXT,
                    reply_markup=chz_only_upsell_keyboard(),
                    parse_mode="HTML",
                )
            else:
                await status_msg.edit_text(
                    f"<b>Готово!</b> {labels_count} этикеток\n\n"
                    "(Файл доступен для скачивания на сайте)",
                    reply_markup=chz_only_upsell_keyboard(),
                    parse_mode="HTML",
                )
        else:
            await status_msg.edit_text(
                f"<b>Готово!</b> {labels_count} этикеток",
                reply_markup=chz_only_upsell_keyboard(),
                parse_mode="HTML",
            )

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Ошибка генерации ЧЗ-only: {e}")
        await status_msg.edit_text(
            f"Ошибка: {e}",
            reply_markup=get_main_menu_kb(),
        )

    finally:
        await state.clear()


@router.message(ChzOnlyStates.waiting_csv, ~F.document)
async def waiting_csv_wrong_type(message: Message) -> None:
    """Неверный тип сообщения при ожидании CSV."""
    await message.answer(
        "Пожалуйста, отправьте <b>CSV файл</b> с кодами Честного Знака.\n\n"
        "Скачайте CSV из личного кабинета ЧЗ (crpt.ru)",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML",
    )
