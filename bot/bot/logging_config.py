"""
Централизованная конфигурация логирования для бота.

JSON формат для production, human-readable для development.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from bot.config import get_bot_settings


class JSONFormatter(logging.Formatter):
    """
    Форматтер для структурированных JSON логов.

    Формат:
    {"timestamp": "...", "level": "INFO", "logger": "bot.handlers", "message": "...", "extra": {...}}
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Добавляем информацию об исключении если есть
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Добавляем extra поля (кроме стандартных)
        standard_attrs = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName",
            "taskName", "message",
        }
        extra = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        if extra:
            log_data["extra"] = extra

        return json.dumps(log_data, ensure_ascii=False, default=str)


class HumanFormatter(logging.Formatter):
    """Человекочитаемый формат для development."""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging() -> None:
    """
    Настройка централизованного логирования для бота.

    В production: JSON формат для парсинга (ELK, Loki, etc.)
    В development: человекочитаемый формат
    """
    settings = get_bot_settings()

    # Определяем уровень логирования
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Выбираем форматтер
    formatter = HumanFormatter() if settings.debug else JSONFormatter()

    # Настраиваем root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Удаляем существующие handlers
    root_logger.handlers.clear()

    # Добавляем handler для stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Уменьшаем verbosity сторонних библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Наши логгеры оставляем verbose
    logging.getLogger("bot").setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер с правильным именем.

    Args:
        name: Имя модуля (обычно __name__)

    Returns:
        Настроенный логгер

    Example:
        logger = get_logger(__name__)
        logger.info("Generation started", extra={"user_id": 123, "labels_count": 50})
    """
    return logging.getLogger(name)
