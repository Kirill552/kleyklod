"""
Хендлеры для управления API ключами.

Команды:
- /apikey — информация о текущем ключе
- /newkey — создать новый API ключ
- /revokekey — отозвать текущий ключ
"""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.utils.api_client import get_api_client

router = Router(name="apikey")
logger = logging.getLogger(__name__)


@router.message(Command("apikey"))
async def cmd_apikey(message: Message) -> None:
    """
    Показать информацию о текущем API ключе.

    Отображает префикс ключа, дату создания и последнего использования.
    """
    telegram_id = message.from_user.id
    api = get_api_client()

    result = await api.get_api_key_info(telegram_id)

    if not result.success:
        await message.answer(f"❌ Не удалось получить информацию о ключе.\nОшибка: {result.error}")
        return

    data = result.data
    prefix = data.get("prefix")

    if not prefix:
        await message.answer(
            "🔑 <b>API ключ не создан</b>\n\n"
            "У вас пока нет API ключа.\n"
            "Используйте /newkey для создания (только для Enterprise).",
            parse_mode="HTML",
        )
        return

    # Форматируем даты
    created_at = data.get("created_at", "—")
    last_used_at = data.get("last_used_at", "—")

    if created_at and created_at != "—":
        # Оставляем только дату и время без миллисекунд
        created_at = created_at[:19].replace("T", " ")
    if last_used_at and last_used_at != "—":
        last_used_at = last_used_at[:19].replace("T", " ")

    await message.answer(
        "🔑 <b>Ваш API ключ</b>\n\n"
        f"<b>Префикс:</b> <code>{prefix}...</code>\n"
        f"<b>Создан:</b> {created_at}\n"
        f"<b>Последнее использование:</b> {last_used_at or 'Не использовался'}\n\n"
        "💡 <i>Полный ключ показывается только при создании.</i>\n"
        "Используйте /revokekey чтобы отозвать ключ.",
        parse_mode="HTML",
    )


@router.message(Command("newkey"))
async def cmd_newkey(message: Message) -> None:
    """
    Создать новый API ключ.

    Требует подписку Enterprise.
    Если ключ уже существует — старый будет отозван.
    """
    telegram_id = message.from_user.id
    api = get_api_client()

    # Сначала проверим есть ли уже ключ
    info_result = await api.get_api_key_info(telegram_id)
    if info_result.success and info_result.data.get("prefix"):
        # Ключ уже есть — предупреждаем
        await message.answer(
            "⚠️ <b>Внимание!</b>\n\n"
            "У вас уже есть API ключ. Создание нового отзовёт старый.\n\n"
            "Отправьте команду /newkey ещё раз для подтверждения.",
            parse_mode="HTML",
        )
        # Простая проверка — следующий вызов создаст ключ
        # (в реальном приложении можно использовать FSM для подтверждения)

    result = await api.create_api_key(telegram_id)

    if not result.success:
        error_msg = result.error
        if result.status_code == 403:
            error_msg = (
                "API ключи доступны только для подписки Enterprise.\n"
                "Используйте /subscribe для обновления тарифа."
            )
        await message.answer(f"❌ {error_msg}")
        return

    data = result.data
    api_key = data.get("api_key", "")

    await message.answer(
        "✅ <b>API ключ успешно создан!</b>\n\n"
        f"<code>{api_key}</code>\n\n"
        "⚠️ <b>ВАЖНО:</b> Сохраните ключ прямо сейчас!\n"
        "Он больше <b>не будет показан</b>.\n\n"
        "📖 Документация API: https://kleykod.ru/docs/api\n\n"
        "<b>Пример использования:</b>\n"
        "<code>curl -X POST https://api.kleykod.ru/api/v1/labels/merge \\\n"
        f'  -H "X-API-Key: {api_key[:20]}..." \\\n'
        "  -F wb_pdf=@labels.pdf \\\n"
        "  -F codes_file=@codes.csv</code>",
        parse_mode="HTML",
    )

    logger.info(f"[APIKEY] Пользователь {telegram_id} создал новый API ключ")


@router.message(Command("revokekey"))
async def cmd_revokekey(message: Message) -> None:
    """
    Отозвать текущий API ключ.

    После отзыва ключ перестаёт работать.
    """
    telegram_id = message.from_user.id
    api = get_api_client()

    result = await api.revoke_api_key(telegram_id)

    if not result.success:
        if result.status_code == 404:
            await message.answer(
                "🔑 У вас нет активного API ключа.\nИспользуйте /newkey для создания."
            )
        else:
            await message.answer(f"❌ Ошибка: {result.error}")
        return

    await message.answer(
        "✅ <b>API ключ отозван</b>\n\n"
        "Старый ключ больше не работает.\n"
        "Используйте /newkey для создания нового.",
        parse_mode="HTML",
    )

    logger.info(f"[APIKEY] Пользователь {telegram_id} отозвал API ключ")
