"""
Pydantic схемы для API.

Модели запросов и ответов.
"""

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# === Enums ===


class PreflightStatus(str, Enum):
    """Статус Pre-flight проверки."""

    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


class UserPlan(str, Enum):
    """Тарифный план пользователя."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# === Pre-flight ===


class PreflightCheck(BaseModel):
    """Результат одной проверки Pre-flight."""

    name: str = Field(description="Название проверки")
    status: PreflightStatus = Field(description="Статус проверки")
    message: str = Field(description="Описание результата")
    details: dict[str, str | int | float] | None = Field(
        default=None, description="Дополнительные данные"
    )


class PreflightResult(BaseModel):
    """Полный результат Pre-flight проверки."""

    overall_status: PreflightStatus = Field(description="Общий статус")
    checks: list[PreflightCheck] = Field(description="Список проверок")
    can_proceed: bool = Field(description="Можно ли продолжить генерацию")


# === Labels ===


class LabelTemplate(BaseModel):
    """Шаблон этикетки."""

    width_mm: float = Field(description="Ширина в мм")
    height_mm: float = Field(description="Высота в мм")
    name: str = Field(description="Название шаблона")


class LabelMergeRequest(BaseModel):
    """Запрос на объединение этикеток (для JSON API)."""

    template: Literal["58x40", "58x30", "58x60"] = Field(
        default="58x40", description="Шаблон этикетки"
    )
    run_preflight: bool = Field(default=True, description="Выполнять Pre-flight проверку")


class LabelMergeResponse(BaseModel):
    """Ответ с результатом объединения."""

    success: bool = Field(description="Успешность операции")
    labels_count: int = Field(description="Количество сгенерированных этикеток")
    preflight: PreflightResult | None = Field(
        default=None, description="Результат Pre-flight (если запрошен)"
    )
    download_url: str | None = Field(default=None, description="URL для скачивания PDF")
    file_id: str | None = Field(default=None, description="ID файла для скачивания")
    message: str = Field(description="Сообщение о результате")


class PreflightRequest(BaseModel):
    """Запрос только на Pre-flight проверку."""

    pass  # Файлы передаются через multipart/form-data


class PreflightResponse(BaseModel):
    """Ответ Pre-flight проверки."""

    result: PreflightResult = Field(description="Результат проверки")


# === Users ===


class UserRegisterRequest(BaseModel):
    """Запрос на регистрацию пользователя."""

    telegram_id: int = Field(description="Telegram ID")
    username: str | None = Field(default=None, description="Username")
    first_name: str | None = Field(default=None, description="Имя")
    last_name: str | None = Field(default=None, description="Фамилия")


class UserResponse(BaseModel):
    """Информация о пользователе."""

    id: UUID = Field(description="ID пользователя")
    telegram_id: int | None = Field(default=None, description="Telegram ID")
    username: str | None = Field(default=None, description="Username")
    first_name: str | None = Field(default=None, description="Имя")
    plan: UserPlan = Field(description="Текущий тарифный план")
    plan_expires_at: datetime | None = Field(default=None, description="Срок действия подписки")
    created_at: datetime = Field(description="Дата регистрации")


class UserProfileResponse(BaseModel):
    """Профиль пользователя с расширенной статистикой."""

    plan: str = Field(description="Текущий тариф")
    used_today: int = Field(description="Использовано сегодня")
    daily_limit: int = Field(description="Дневной лимит")
    total_generated: int = Field(description="Всего сгенерировано")
    success_count: int = Field(description="Успешных генераций")
    preflight_errors: int = Field(description="Pre-flight ошибок")
    registered_at: str = Field(description="Дата регистрации")
    subscription_expires_at: str | None = Field(default=None, description="Срок подписки")


class UsageStats(BaseModel):
    """Статистика использования."""

    today_labels: int = Field(description="Этикеток сегодня")
    today_limit: int = Field(description="Лимит на сегодня")
    total_labels: int = Field(description="Всего этикеток за всё время")
    plan: UserPlan = Field(description="Текущий план")


# === Payments ===


class PaymentPlan(BaseModel):
    """Тарифный план для оплаты."""

    id: str = Field(description="ID плана")
    name: str = Field(description="Название")
    price_rub: int = Field(description="Цена в рублях")
    price_stars: int | None = Field(default=None, description="Цена в Stars")
    period: Literal["month", "year"] = Field(description="Период")
    features: list[str] = Field(description="Список возможностей")


class PaymentActivateRequest(BaseModel):
    """Запрос на активацию подписки после оплаты."""

    telegram_id: int = Field(description="Telegram ID пользователя")
    plan: str = Field(description="Тариф (pro/enterprise)")
    duration_days: int = Field(description="Длительность подписки в днях")
    telegram_payment_charge_id: str = Field(description="ID платежа Telegram")
    provider_payment_charge_id: str = Field(description="ID платежа провайдера")
    total_amount: int = Field(description="Сумма в Stars")


class PaymentActivateResponse(BaseModel):
    """Ответ на активацию подписки."""

    success: bool = Field(description="Успешность активации")
    message: str = Field(description="Сообщение")
    expires_at: str | None = Field(default=None, description="Срок действия подписки")


class PaymentHistoryItem(BaseModel):
    """Элемент истории платежей."""

    id: str = Field(description="ID платежа")
    plan: str = Field(description="Тариф")
    amount: int = Field(description="Сумма")
    currency: str = Field(description="Валюта")
    status: str = Field(description="Статус")
    created_at: str = Field(description="Дата создания")


# === Errors ===


class ErrorResponse(BaseModel):
    """Стандартный формат ошибки."""

    error: str = Field(description="Код ошибки")
    message: str = Field(description="Описание ошибки")
    details: dict[str, str | int | float] | None = Field(
        default=None, description="Дополнительные данные"
    )


# === Templates ===


class TemplatesResponse(BaseModel):
    """Список доступных шаблонов."""

    templates: list[LabelTemplate] = Field(description="Доступные шаблоны")
