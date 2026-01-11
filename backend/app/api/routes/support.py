"""
API эндпоинты для чата поддержки.

Агрегатор сообщений с сайта и Telegram в VK личку админа.
"""

import contextlib
import json
import logging
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis

from app.api.dependencies import get_current_user
from app.config import get_settings
from app.db.database import get_redis
from app.db.models import User

router = APIRouter(prefix="/api/v1/support", tags=["Support"])
logger = logging.getLogger(__name__)
settings = get_settings()

# Redis ключи
MESSAGES_KEY = "support:chat:{user_id}:messages"
PENDING_KEY = "support:pending:{chat_id}"
UNREAD_KEY = "support:unread:{user_id}"

# TTL для сообщений (30 дней)
MESSAGES_TTL = 60 * 60 * 24 * 30


# === Pydantic Models ===


class SendMessageRequest(BaseModel):
    """Запрос отправки сообщения."""

    text: str


class SendMessageResponse(BaseModel):
    """Ответ на отправку сообщения."""

    message_id: str
    status: str


class SupportMessage(BaseModel):
    """Сообщение в чате поддержки."""

    id: str
    text: str
    from_: str  # "user" или "support"
    created_at: str

    class Config:
        populate_by_name = True


class MessagesResponse(BaseModel):
    """Ответ со списком сообщений."""

    messages: list[SupportMessage]


class UnreadResponse(BaseModel):
    """Количество непрочитанных сообщений."""

    count: int


class ReplyRequest(BaseModel):
    """Запрос ответа от VK бота."""

    chat_id: str
    text: str


# === VK API ===


async def send_to_vk(user: User, text: str, chat_id: str) -> bool:
    """
    Отправить сообщение в VK личку админу.

    Формат: [Сайт] Имя Фамилия (PLAN): текст
    С inline-кнопкой "Ответить".
    """
    if not settings.vk_group_token or not settings.admin_vk_id:
        logger.warning("VK настройки не заданы, сообщение не отправлено")
        return False

    # Формируем сообщение
    plan = user.plan.upper() if user.plan else "FREE"
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Пользователь"
    message = f"[Сайт] {name} ({plan}):\n{text}"

    # Клавиатура с кнопкой "Ответить"
    keyboard = {
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "callback",
                        "label": "Ответить",
                        "payload": json.dumps({"cmd": "reply", "chat_id": chat_id}),
                    }
                }
            ]
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.vk.ru/method/messages.send",
                data={
                    "access_token": settings.vk_group_token,
                    "user_id": settings.admin_vk_id,
                    "message": message,
                    "keyboard": json.dumps(keyboard),
                    "random_id": hash(chat_id) % (2**31),
                    "v": "5.199",
                },
                timeout=10.0,
            )

            result = response.json()
            if "error" in result:
                logger.error(f"VK API error: {result['error']}")
                return False

            logger.info(f"Сообщение отправлено в VK админу, chat_id={chat_id}")
            return True

    except Exception as e:
        logger.error(f"Ошибка отправки в VK: {e}")
        return False


# === Endpoints ===


@router.post("/message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> SendMessageResponse:
    """
    Отправить сообщение в поддержку.

    Сообщение сохраняется в Redis и пересылается в VK личку админа.
    """

    # Генерируем ID сообщения
    message_id = str(uuid.uuid4())
    chat_id = f"{user.id}-{message_id[:8]}"

    # Создаём сообщение
    message = SupportMessage(
        id=message_id,
        text=request.text.strip(),
        from_="user",
        created_at=datetime.now(UTC).isoformat(),
    )

    # Сохраняем в Redis
    messages_key = MESSAGES_KEY.format(user_id=user.id)
    await redis.rpush(messages_key, message.model_dump_json())
    await redis.expire(messages_key, MESSAGES_TTL)

    # Сохраняем pending для ответа
    pending_key = PENDING_KEY.format(chat_id=chat_id)
    pending_data = {
        "user_id": user.id,
        "source": "site",
        "telegram_chat_id": user.telegram_id,
    }
    await redis.set(pending_key, json.dumps(pending_data), ex=MESSAGES_TTL)

    # Отправляем в VK
    await send_to_vk(user, request.text.strip(), chat_id)

    logger.info(f"Сообщение от user {user.id} сохранено, chat_id={chat_id}")

    return SendMessageResponse(message_id=message_id, status="sent")


@router.get("/messages", response_model=MessagesResponse)
async def get_messages(
    since: str | None = None,
    user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> MessagesResponse:
    """
    Получить историю сообщений.

    Если указан since (ISO timestamp), возвращает только новые сообщения.
    """

    messages_key = MESSAGES_KEY.format(user_id=user.id)
    raw_messages = await redis.lrange(messages_key, 0, -1)

    messages: list[SupportMessage] = []
    since_dt = None

    if since:
        with contextlib.suppress(ValueError):
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))

    for raw in raw_messages:
        try:
            data = json.loads(raw)
            msg = SupportMessage(
                id=data["id"],
                text=data["text"],
                from_=data["from_"],
                created_at=data["created_at"],
            )

            # Фильтруем по времени если указан since
            if since_dt:
                msg_dt = datetime.fromisoformat(msg.created_at.replace("Z", "+00:00"))
                if msg_dt <= since_dt:
                    continue

            messages.append(msg)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Ошибка парсинга сообщения: {e}")

    # Сбрасываем счётчик непрочитанных
    unread_key = UNREAD_KEY.format(user_id=user.id)
    await redis.delete(unread_key)

    return MessagesResponse(messages=messages)


@router.get("/unread", response_model=UnreadResponse)
async def get_unread_count(
    user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> UnreadResponse:
    """Получить количество непрочитанных сообщений от поддержки."""

    unread_key = UNREAD_KEY.format(user_id=user.id)
    count = await redis.get(unread_key)

    return UnreadResponse(count=int(count) if count else 0)


class BotSendMessageRequest(BaseModel):
    """Запрос отправки сообщения от TG бота."""

    telegram_id: int
    text: str


@router.post("/bot/message", response_model=SendMessageResponse)
async def send_message_from_bot(
    request: BotSendMessageRequest,
    x_bot_secret: str = Header(..., alias="X-Bot-Secret"),
    redis: Redis = Depends(get_redis),
) -> SendMessageResponse:
    """
    Отправить сообщение в поддержку от TG бота.

    Защищён X-Bot-Secret заголовком.
    """
    # Проверяем секрет
    if x_bot_secret != settings.bot_secret_key:
        raise HTTPException(status_code=403, detail="Invalid bot secret")

    # Получаем пользователя по telegram_id
    from app.db.database import get_db_session
    from app.repositories.user_repository import UserRepository

    async with get_db_session() as db:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_telegram_id(request.telegram_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Генерируем ID сообщения
        message_id = str(uuid.uuid4())
        chat_id = f"{user.id}-{message_id[:8]}"

        # Создаём сообщение
        message = SupportMessage(
            id=message_id,
            text=request.text.strip(),
            from_="user",
            created_at=datetime.now(UTC).isoformat(),
        )

        # Сохраняем в Redis
        messages_key = MESSAGES_KEY.format(user_id=user.id)
        await redis.rpush(messages_key, message.model_dump_json())
        await redis.expire(messages_key, MESSAGES_TTL)

        # Сохраняем pending для ответа (источник = telegram)
        pending_key = PENDING_KEY.format(chat_id=chat_id)
        pending_data = {
            "user_id": user.id,
            "source": "telegram",
            "telegram_chat_id": request.telegram_id,
        }
        await redis.set(pending_key, json.dumps(pending_data), ex=MESSAGES_TTL)

        # Отправляем в VK (с пометкой что из Telegram)
        await send_to_vk_from_telegram(user, request.telegram_id, request.text.strip(), chat_id)

        logger.info(f"Сообщение от TG user {request.telegram_id} сохранено, chat_id={chat_id}")

        return SendMessageResponse(message_id=message_id, status="sent")


async def send_to_vk_from_telegram(user: User, telegram_id: int, text: str, chat_id: str) -> bool:
    """
    Отправить сообщение в VK личку админу из Telegram.

    Формат: [Telegram] @username (PLAN): текст
    """
    if not settings.vk_group_token or not settings.admin_vk_id:
        logger.warning("VK настройки не заданы, сообщение не отправлено")
        return False

    # Формируем сообщение
    plan = user.plan.upper() if user.plan else "FREE"
    username = f"@{user.username}" if user.username else f"ID:{telegram_id}"
    message = f"[Telegram] {username} ({plan}):\n{text}"

    # Клавиатура с кнопкой "Ответить"
    keyboard = {
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "callback",
                        "label": "Ответить",
                        "payload": json.dumps({"cmd": "reply", "chat_id": chat_id}),
                    }
                }
            ]
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.vk.ru/method/messages.send",
                data={
                    "access_token": settings.vk_group_token,
                    "user_id": settings.admin_vk_id,
                    "message": message,
                    "keyboard": json.dumps(keyboard),
                    "random_id": hash(chat_id) % (2**31),
                    "v": "5.199",
                },
                timeout=10.0,
            )

            result = response.json()
            if "error" in result:
                logger.error(f"VK API error: {result['error']}")
                return False

            logger.info(f"Сообщение из Telegram отправлено в VK, chat_id={chat_id}")
            return True

    except Exception as e:
        logger.error(f"Ошибка отправки в VK: {e}")
        return False


@router.post("/reply")
async def reply_from_bot(
    request: ReplyRequest,
    x_bot_secret: str = Header(..., alias="X-Bot-Secret"),
    redis: Redis = Depends(get_redis),
) -> dict:
    """
    Получить ответ от VK бота и сохранить в историю.

    Защищён X-Bot-Secret заголовком.
    """
    # Проверяем секрет
    if x_bot_secret != settings.bot_secret_key:
        raise HTTPException(status_code=403, detail="Invalid bot secret")

    # Находим pending chat
    pending_key = PENDING_KEY.format(chat_id=request.chat_id)
    pending_raw = await redis.get(pending_key)

    if not pending_raw:
        raise HTTPException(status_code=404, detail="Chat not found")

    pending = json.loads(pending_raw)
    user_id = pending["user_id"]
    source = pending.get("source", "site")

    # Создаём сообщение от поддержки
    message = SupportMessage(
        id=str(uuid.uuid4()),
        text=request.text.strip(),
        from_="support",
        created_at=datetime.now(UTC).isoformat(),
    )

    # Сохраняем в Redis
    messages_key = MESSAGES_KEY.format(user_id=user_id)
    await redis.rpush(messages_key, message.model_dump_json())
    await redis.expire(messages_key, MESSAGES_TTL)

    # Увеличиваем счётчик непрочитанных
    unread_key = UNREAD_KEY.format(user_id=user_id)
    await redis.incr(unread_key)
    await redis.expire(unread_key, MESSAGES_TTL)

    # Если источник Telegram — отправить ответ в TG
    if source == "telegram" and pending.get("telegram_chat_id"):
        telegram_chat_id = pending["telegram_chat_id"]
        await send_telegram_reply(telegram_chat_id, request.text.strip())

    logger.info(f"Ответ от поддержки сохранён для user {user_id}")

    return {"status": "ok", "user_id": user_id}


async def send_telegram_reply(chat_id: int, text: str) -> bool:
    """
    Отправить ответ поддержки в Telegram.

    Args:
        chat_id: Telegram chat_id пользователя
        text: Текст ответа

    Returns:
        True при успехе
    """
    telegram_token = settings.telegram_bot_token
    if not telegram_token:
        logger.warning("TELEGRAM_BOT_TOKEN не задан, ответ не отправлен")
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"📩 <b>Ответ от поддержки:</b>\n\n{text}",
                    "parse_mode": "HTML",
                },
                timeout=10.0,
            )

            result = response.json()
            if not result.get("ok"):
                logger.error(f"Telegram API error: {result}")
                return False

            logger.info(f"Ответ отправлен в Telegram chat_id={chat_id}")
            return True

    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")
        return False
