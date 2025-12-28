"""
Конфигурация Telegram бота KleyKod.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Настройки Telegram бота."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === Telegram ===
    bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")

    # Webhook (для production)
    webhook_url: str = Field(default="", alias="TELEGRAM_WEBHOOK_URL")
    webhook_secret: str = Field(default="", alias="TELEGRAM_WEBHOOK_SECRET")

    # === Backend API ===
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    api_timeout: int = Field(default=60, alias="API_TIMEOUT")

    # Секрет для защищённых bot endpoints (IDOR protection)
    bot_secret_key: str = Field(default="", alias="BOT_SECRET_KEY")

    # === Redis ===
    redis_url: str = Field(default="redis://localhost:6379/1", alias="REDIS_URL")

    # === Лимиты ===
    free_daily_limit: int = Field(default=50, alias="FREE_TIER_DAILY_LIMIT")
    max_file_size_mb: int = Field(default=20, alias="MAX_FILE_SIZE_MB")

    # === Админы ===
    admin_ids: list[int] = Field(default=[], alias="ADMIN_IDS")

    # === Режим ===
    debug: bool = Field(default=False, alias="DEBUG")

    # === Мониторинг ошибок (GlitchTip/Sentry) ===
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")

    # === Приложение ===
    app_name: str = "KleyKod Bot"
    app_version: str = "1.0.0"

    @property
    def max_file_size_bytes(self) -> int:
        """Максимальный размер файла в байтах."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_bot_settings() -> BotSettings:
    """Получить настройки бота (singleton)."""
    return BotSettings()
