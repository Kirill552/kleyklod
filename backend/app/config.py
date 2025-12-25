"""
Конфигурация приложения KleyKod.

Все настройки в одном месте (SSOT — Single Source of Truth).
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LabelSettings:
    """
    Настройки генерации этикеток.

    Константы из требований Wildberries и Честного Знака.
    Источник: docs/TZ.md, конкурентный аудит.
    """

    # Разрешение печати (строго для термопринтеров)
    DPI: int = 203

    # Размер DataMatrix (минимум по требованиям ЧЗ)
    DATAMATRIX_MIN_MM: float = 22.0
    DATAMATRIX_MAX_MM: float = 26.0  # Оптимальный размер

    # Размер DataMatrix в пикселях при 203 DPI
    # Формула: мм * DPI / 25.4
    DATAMATRIX_MIN_PIXELS: int = 176  # 22мм при 203 DPI
    DATAMATRIX_PIXELS: int = 207  # 26мм при 203 DPI (оптимально)

    # Размер итоговой этикетки (стандарт термопринтеров)
    LABEL_WIDTH_MM: float = 58.0
    LABEL_HEIGHT_MM: float = 40.0

    # Размер этикетки в пикселях при 203 DPI
    LABEL_WIDTH_PIXELS: int = 463  # 58мм при 203 DPI
    LABEL_HEIGHT_PIXELS: int = 320  # 40мм при 203 DPI

    # Зона покоя вокруг кодов (quiet zone)
    QUIET_ZONE_MM: float = 3.0
    QUIET_ZONE_PIXELS: int = 24  # 3мм при 203 DPI

    # Контрастность (минимум для сканера)
    MIN_CONTRAST_PERCENT: int = 80

    # Цвета (строго черный на белом — требование ЧЗ)
    COLOR_BLACK: str = "#000000"
    COLOR_WHITE: str = "#FFFFFF"

    # Поддерживаемые шаблоны этикеток
    SUPPORTED_TEMPLATES: list[tuple[float, float]] = [
        (58.0, 40.0),  # Стандарт
        (58.0, 30.0),  # Компактный
        (58.0, 60.0),  # Расширенный
    ]

    @classmethod
    def mm_to_pixels(cls, mm: float) -> int:
        """Конвертация миллиметров в пиксели при 203 DPI."""
        return int(mm * cls.DPI / 25.4)

    @classmethod
    def pixels_to_mm(cls, pixels: int) -> float:
        """Конвертация пикселей в миллиметры при 203 DPI."""
        return pixels * 25.4 / cls.DPI


class Settings(BaseSettings):
    """
    Настройки приложения из переменных окружения.

    Загружаются из .env файла или переменных окружения.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === Приложение ===
    app_name: str = "KleyKod API"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str = Field(default="change-me-in-production")

    # === База данных ===
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/kleykod"
    )

    # === Redis ===
    redis_url: str = Field(default="redis://localhost:6379/0")

    # === Шифрование (152-ФЗ) ===
    # Ключ шифрования AES-256 (32 байта в base64)
    encryption_key: str = Field(default="")

    # === CORS ===
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # === Лимиты ===
    free_tier_daily_limit: int = 50  # Этикеток в день для Free
    max_upload_size_mb: int = 50  # Максимальный размер файла
    max_batch_size: int = 10000  # Максимум этикеток за раз

    # === Telegram ===
    telegram_bot_token: str = Field(default="")
    telegram_webhook_url: str = Field(default="")

    # === Файлы ===
    # Время хранения сгенерированных файлов (в часах)
    file_retention_hours: int = 24

    # === Логирование ===
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @computed_field
    @property
    def max_upload_size_bytes(self) -> int:
        """Максимальный размер файла в байтах."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """
    Получить настройки приложения (singleton).

    Использует кэширование для избежания повторного чтения .env
    """
    return Settings()


# Экспорт констант этикеток для удобства
LABEL = LabelSettings()
