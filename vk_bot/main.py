"""
Мини-бот VK для сообщества KleyKod.

Функции:
- Приветствие новых пользователей
- Кнопка открытия Mini App
- Команда /support
- Обработка callback кнопок "Ответить" для агрегатора поддержки
"""

import json
import logging
import os
import time

import requests
import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.utils import get_random_id

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Конфигурация
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))
VK_APP_ID = int(os.getenv("VK_APP_ID", "0"))
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
BOT_SECRET = os.getenv("BOT_SECRET", "")
ADMIN_VK_ID = int(os.getenv("ADMIN_VK_ID", "0"))  # VK ID админа для команды /stats

if not VK_GROUP_TOKEN:
    raise ValueError("VK_GROUP_TOKEN не задан")
if not VK_GROUP_ID:
    raise ValueError("VK_GROUP_ID не задан")
if not VK_APP_ID:
    raise ValueError("VK_APP_ID не задан")

# Инициализация VK API
vk_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
vk = vk_session.get_api()

# Состояния пользователей для reply flow
# {vk_user_id: {"state": "awaiting_reply", "chat_id": "uuid"}}
user_states: dict[int, dict] = {}


def get_main_keyboard() -> str:
    """Клавиатура с кнопкой открытия Mini App."""
    keyboard = {
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "open_app",
                        "app_id": VK_APP_ID,
                        "owner_id": -VK_GROUP_ID,
                        "label": "Создать этикетки",
                    }
                }
            ],
            [
                {
                    "action": {
                        "type": "callback",
                        "payload": json.dumps({"cmd": "open_site"}),
                        "label": "Открыть сайт",
                    }
                }
            ],
        ],
    }
    return json.dumps(keyboard)


WELCOME_TEXT = """Привет! Я бот KleyKod.

Объединяю этикетки Wildberries и коды маркировки "Честный знак" в одну наклейку.

Нажми кнопку ниже чтобы открыть генератор этикеток."""

SUPPORT_TEXT = """Напишите ваш вопрос — мы ответим в ближайшее время.

Или напишите на support@kleykod.ru"""


def send_reply_to_backend(chat_id: str, text: str) -> bool:
    """Отправить ответ в backend для сохранения и пересылки пользователю."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/support/reply",
            json={"chat_id": chat_id, "text": text},
            headers={"X-Bot-Secret": BOT_SECRET},
            timeout=10,
        )
        if response.ok:
            logger.info(f"Ответ отправлен в backend, chat_id={chat_id}")
            return True
        else:
            logger.error(f"Ошибка отправки в backend: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Ошибка запроса к backend: {e}")
        return False


def get_transfer_token(vk_user_id: int) -> str | None:
    """Получить одноразовый токен для передачи авторизации на сайт."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/transfer-token/vk",
            json={"vk_user_id": vk_user_id},
            headers={"X-Bot-Secret": BOT_SECRET},
            timeout=10,
        )
        if response.ok:
            data = response.json()
            return data.get("transfer_token")
        else:
            logger.warning(f"Не удалось получить transfer_token: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Ошибка запроса transfer_token: {e}")
        return None


def get_admin_stats() -> dict | None:
    """Получить статистику проекта для админа."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/admin/stats",
            headers={"X-Bot-Secret": BOT_SECRET},
            timeout=10,
        )
        if response.ok:
            return response.json()
        else:
            logger.error(f"Ошибка получения статистики: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Ошибка запроса статистики: {e}")
        return None


def format_stats_message(stats: dict) -> str:
    """Форматировать статистику в читаемый текст."""
    users = stats["users"]
    sources = stats["sources"]
    gens = stats["generations"]
    payments = stats["payments"]

    # Форматируем сумму платежей (в рублях)
    month_rub = payments["month_amount"] // 100

    return f"""📊 Статистика KleyKod

👥 Пользователи:
   Всего: {users['total']}
   С Trial: {users['trial_active']} (активных)
   PRO: {users['pro']}
   Enterprise: {users['enterprise']}

📍 Источники регистрации:
   VK: {sources['vk']} ({sources['vk_percent']}%)
   Telegram: {sources['telegram']} ({sources['telegram_percent']}%)
   Сайт: {sources['site']} ({sources['site_percent']}%)

📋 Генерации:
   Сегодня: {gens['today']:,} этикеток
   Вчера: {gens['yesterday']:,} этикеток
   За месяц: {gens['month']:,} этикеток
   Всего: {gens['total']:,} этикеток

💳 Платежи:
   За месяц: {month_rub:,}₽ ({payments['month_count']} платежей)""".replace(",", " ")


def handle_callback(user_id: int, payload: dict, event_id: str) -> None:
    """Обработка callback от inline-кнопки."""
    cmd = payload.get("cmd")

    if cmd == "reply":
        chat_id = payload.get("chat_id")
        if chat_id:
            # Сохраняем состояние — ждём ответ
            user_states[user_id] = {"state": "awaiting_reply", "chat_id": chat_id}

            vk.messages.send(
                user_id=user_id,
                message="Введите ответ:",
                random_id=get_random_id(),
            )
            logger.info(f"Ожидаем ответ от {user_id} для chat_id={chat_id}")

    elif cmd == "open_site":
        # Получаем токен для передачи авторизации
        token = get_transfer_token(user_id)

        if token:
            url = f"https://kleykod.ru/app/generate?transfer_token={token}"
            message = f"Перейдите по ссылке (действует 60 секунд):\n{url}"
        else:
            url = "https://kleykod.ru/app/generate"
            message = f"Перейдите на сайт:\n{url}\n\n💡 Для автоматической авторизации сначала откройте Mini App."

        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=get_random_id(),
        )
        logger.info(f"Отправлена ссылка на сайт пользователю {user_id}")

    # Отправляем event answer чтобы кнопка не крутилась
    try:
        vk.messages.sendMessageEventAnswer(
            event_id=event_id,
            user_id=user_id,
            peer_id=user_id,
        )
    except Exception as e:
        logger.warning(f"Ошибка sendMessageEventAnswer: {e}")


def handle_message(user_id: int, text: str, payload: str | None) -> None:
    """Обработка входящего сообщения."""
    # Проверяем — ждём ли ответ от этого пользователя
    state = user_states.get(user_id)

    if state and state.get("state") == "awaiting_reply":
        chat_id = state["chat_id"]

        # Отправляем ответ в backend
        success = send_reply_to_backend(chat_id, text)

        if success:
            vk.messages.send(
                user_id=user_id,
                message="✓ Ответ отправлен пользователю",
                random_id=get_random_id(),
            )
        else:
            vk.messages.send(
                user_id=user_id,
                message="❌ Ошибка отправки ответа. Попробуйте ещё раз.",
                random_id=get_random_id(),
            )

        # Очищаем состояние
        del user_states[user_id]
        logger.info(f"Ответ от {user_id} обработан для chat_id={chat_id}")
        return

    text_lower = text.lower().strip()

    # Команда /stats — только для админа
    if text_lower in ("/stats", "!stats", "статистика"):
        if user_id != ADMIN_VK_ID:
            vk.messages.send(
                user_id=user_id,
                message="⛔ Команда доступна только администратору.",
                random_id=get_random_id(),
            )
            logger.warning(f"Попытка доступа к /stats от {user_id} (не админ)")
            return

        stats = get_admin_stats()
        if stats:
            message = format_stats_message(stats)
        else:
            message = "❌ Ошибка получения статистики. Попробуйте позже."

        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=get_random_id(),
        )
        logger.info(f"Статистика отправлена админу {user_id}")
        return

    # Команда /support
    if text_lower in ("/support", "поддержка", "помощь"):
        vk.messages.send(
            user_id=user_id,
            message=SUPPORT_TEXT,
            random_id=get_random_id(),
        )
        logger.info(f"Отправлен текст поддержки пользователю {user_id}")
        return

    # Команда /cancel — отменить ожидание ответа
    if text_lower in ("/cancel", "отмена"):
        if user_id in user_states:
            del user_states[user_id]
            vk.messages.send(
                user_id=user_id,
                message="Отменено.",
                random_id=get_random_id(),
            )
            return

    # Обработка payload от кнопки "Начать"
    if payload:
        try:
            data = json.loads(payload)
            if data.get("command") == "start":
                pass  # Продолжаем к приветствию
        except json.JSONDecodeError:
            pass

    # Приветствие по умолчанию
    vk.messages.send(
        user_id=user_id,
        message=WELCOME_TEXT,
        keyboard=get_main_keyboard(),
        random_id=get_random_id(),
    )
    logger.info(f"Отправлено приветствие пользователю {user_id}")


def main() -> None:
    """Основной цикл бота."""
    logger.info(f"VK бот запущен для группы {VK_GROUP_ID}")
    logger.info(f"Mini App ID: {VK_APP_ID}")
    logger.info(f"Backend URL: {BACKEND_URL}")

    while True:
        try:
            longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)

            for event in longpoll.listen():
                # Обработка новых сообщений
                if event.type == VkBotEventType.MESSAGE_NEW:
                    msg = event.object.message
                    user_id = msg["from_id"]
                    text = msg.get("text", "")
                    payload = msg.get("payload")

                    logger.info(f"Сообщение от {user_id}: {text[:50]}")

                    try:
                        handle_message(user_id, text, payload)
                    except Exception as e:
                        logger.error(f"Ошибка обработки сообщения: {e}")

                # Обработка callback от inline-кнопок
                elif event.type == VkBotEventType.MESSAGE_EVENT:
                    user_id = event.object.user_id
                    payload = event.object.payload
                    event_id = event.object.event_id

                    logger.info(f"Callback от {user_id}: {payload}")

                    try:
                        handle_callback(user_id, payload, event_id)
                    except Exception as e:
                        logger.error(f"Ошибка обработки callback: {e}")

        except Exception as e:
            logger.error(f"Ошибка Long Poll: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
