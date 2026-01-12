"""
Конфигурация приложения KleyKod.

Все настройки в одном месте (SSOT — Single Source of Truth).
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LabelSettings:
    """
    Настройки генерации этикеток.

    Константы из требований Wildberries и Честного Знака.
    Источник: docs/TZ.md, конкурентный аудит.
    """

    # Разрешение печати (строго для термопринтеров)
    DPI: int = 203

    # Размер DataMatrix
    # ГОСТ минимум: 10 мм, но для термопринтеров 203 DPI рекомендуем больше
    DATAMATRIX_MIN_MM: float = 22.0  # Рекомендация KleyKod для надёжного сканирования
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
    secret_key: str = Field(default="")

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
    allowed_origins: list[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"])

    # === Лимиты ===
    free_tier_daily_limit: int = 50  # Этикеток в день для Free
    max_upload_size_mb: int = 50  # Максимальный размер файла
    max_batch_size: int = 10000  # Максимум этикеток за раз

    # === Trial период ===
    trial_days: int = 7  # Дней триала с PRO лимитами (500/день)
    trial_daily_limit: int = 500  # Лимит во время триала (как PRO)

    # === Telegram ===
    telegram_bot_token: str = Field(default="")
    telegram_webhook_url: str = Field(default="")

    # === Секрет для бота (защита bot endpoints от IDOR) ===
    bot_secret_key: str = Field(default="")

    # === ЮКасса ===
    yookassa_shop_id: int = Field(default=0)
    yookassa_secret_key: str = Field(default="")
    yookassa_return_url: str = Field(default="https://kleykod.ru/app/subscription/success")

    # === JWT Авторизация ===
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    # === Файлы ===
    # Время хранения сгенерированных файлов (в часах)
    file_retention_hours: int = 24

    # === Логирование ===
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # === Мониторинг ошибок (GlitchTip/Sentry) ===
    sentry_dsn: str = Field(default="")

    # === VK интеграция ===
    vk_group_token: str = Field(default="")  # Токен сообщества VK
    vk_group_id: int = Field(default=0)  # ID сообщества VK
    vk_app_id: int = Field(default=0)  # ID Mini App
    vk_app_secret: str = Field(default="")  # Секретный ключ Mini App (для проверки подписи)
    vk_launch_params_ttl: int = Field(default=86400)  # TTL launch_params в секундах (24 часа)
    admin_vk_id: int = Field(default=0)  # VK ID админа для получения сообщений поддержки

    # === VK ID OAuth (для One Tap на сайте) ===
    vk_id_app_id: int = Field(default=54418365)  # ID VK ID приложения (для One Tap)
    vk_client_secret: str = Field(default="")  # Защищённый ключ VK ID
    vk_redirect_uri: str = Field(default="https://kleykod.ru/api/auth/vk/callback")

    @computed_field
    @property
    def max_upload_size_bytes(self) -> int:
        """Максимальный размер файла в байтах."""
        return self.max_upload_size_mb * 1024 * 1024

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        """
        Валидация критичных настроек безопасности.

        В production режиме SECRET_KEY и ENCRYPTION_KEY обязательны.
        """
        if not self.debug:
            # Production mode — строгие проверки
            if not self.secret_key or self.secret_key == "change-me-in-production":
                raise ValueError(
                    "SECRET_KEY не установлен! "
                    "Для production установите уникальный SECRET_KEY в .env"
                )
            if len(self.secret_key) < 32:
                raise ValueError(
                    "SECRET_KEY слишком короткий! Минимум 32 символа для безопасности."
                )
            if not self.encryption_key:
                raise ValueError(
                    "ENCRYPTION_KEY не установлен! Обязателен для шифрования ПДн по 152-ФЗ."
                )
        else:
            # Debug mode — предупреждения
            if not self.secret_key:
                import secrets

                self.secret_key = secrets.token_urlsafe(32)
                print("⚠️  DEBUG: Сгенерирован временный SECRET_KEY")
            if not self.encryption_key:
                print("⚠️  DEBUG: ENCRYPTION_KEY не установлен, шифрование ПДн отключено")
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Получить настройки приложения (singleton).

    Использует кэширование для избежания повторного чтения .env
    """
    return Settings()


# Экспорт констант этикеток для удобства
LABEL = LabelSettings()
