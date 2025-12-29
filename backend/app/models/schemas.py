"""
Pydantic схемы для API.

Модели запросов и ответов.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

# === Enums ===


class PreflightStatus(str, Enum):
    """Статус проверки качества."""

    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


class UserPlan(str, Enum):
    """Тарифный план пользователя."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LabelFormat(str, Enum):
    """Формат размещения этикеток."""

    COMBINED = "combined"  # WB + DataMatrix на одной этикетке
    SEPARATE = "separate"  # WB и DataMatrix на отдельных этикетках


# === Проверка качества ===


class PreflightCheck(BaseModel):
    """Результат одной проверки качества."""

    name: str = Field(description="Название проверки")
    status: PreflightStatus = Field(description="Статус проверки")
    message: str = Field(description="Описание результата")
    details: dict[str, Any] | None = Field(
        default=None, description="Дополнительные данные (любые JSON-совместимые значения)"
    )


class PreflightResult(BaseModel):
    """Полный результат проверки качества."""

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
    run_preflight: bool = Field(default=True, description="Выполнять проверку качества")
    label_format: LabelFormat = Field(
        default=LabelFormat.COMBINED,
        description="Формат: combined (одна этикетка) или separate (раздельные)",
    )


class LabelMergeResponse(BaseModel):
    """Ответ с результатом объединения."""

    success: bool = Field(description="Успешность операции")
    labels_count: int = Field(description="Количество сгенерированных этикеток")
    pages_count: int = Field(description="Количество страниц в PDF")
    label_format: LabelFormat = Field(
        default=LabelFormat.COMBINED, description="Использованный формат этикеток"
    )
    preflight: PreflightResult | None = Field(
        default=None, description="Результат проверки качества (если запрошен)"
    )
    download_url: str | None = Field(default=None, description="URL для скачивания PDF")
    file_id: str | None = Field(default=None, description="ID файла для скачивания")
    message: str = Field(description="Сообщение о результате")
    # Информация о лимитах для отображения остатка
    daily_limit: int = Field(default=50, description="Дневной лимит этикеток")
    used_today: int = Field(default=0, description="Использовано сегодня")


class PreflightRequest(BaseModel):
    """Запрос только на проверку качества."""

    pass  # Файлы передаются через multipart/form-data


class PreflightResponse(BaseModel):
    """Ответ проверки качества."""

    result: PreflightResult = Field(description="Результат проверки")


# === Users ===


class UserRegisterRequest(BaseModel):
    """Запрос на регистрацию пользователя."""

    telegram_id: int = Field(description="Telegram ID")
    username: str | None = Field(default=None, description="Username")
    first_name: str | None = Field(default=None, description="Имя")
    last_name: str | None = Field(default=None, description="Фамилия")
    photo_url: str | None = Field(default=None, description="URL аватарки из Telegram")


class UserResponse(BaseModel):
    """Информация о пользователе."""

    id: UUID = Field(description="ID пользователя")
    telegram_id: int | None = Field(default=None, description="Telegram ID")
    username: str | None = Field(default=None, description="Username")
    first_name: str | None = Field(default=None, description="Имя")
    photo_url: str | None = Field(default=None, description="URL аватарки из Telegram")
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
    preflight_errors: int = Field(description="Ошибок проверки качества")
    registered_at: str = Field(description="Дата регистрации")
    subscription_expires_at: str | None = Field(default=None, description="Срок подписки")


class UsageStats(BaseModel):
    """Статистика использования."""

    today_labels: int = Field(description="Этикеток сегодня")
    today_limit: int = Field(description="Лимит на сегодня")
    total_labels: int = Field(description="Всего этикеток за всё время")
    plan: UserPlan = Field(description="Текущий план")


class UserStatsResponse(BaseModel):
    """Статистика использования для фронтенда."""

    today_used: int = Field(description="Использовано сегодня")
    today_limit: int = Field(description="Дневной лимит")
    total_generated: int = Field(description="Всего сгенерировано за всё время")
    this_month: int = Field(description="Сгенерировано за этот месяц")


# === Generations ===


class GenerationResponse(BaseModel):
    """Информация о сгенерированной этикетке."""

    id: UUID = Field(description="ID генерации")
    user_id: UUID = Field(description="ID пользователя")
    labels_count: int = Field(description="Количество этикеток")
    file_path: str | None = Field(default=None, description="Путь к файлу (хранится 7 дней)")
    preflight_passed: bool = Field(default=False, description="Прошла ли проверка качества")
    expires_at: datetime = Field(description="Время удаления файла")
    created_at: datetime = Field(description="Дата создания")


class GenerationListResponse(BaseModel):
    """Список генераций пользователя."""

    items: list[GenerationResponse] = Field(description="История генераций")
    total: int = Field(description="Общее количество")


# === Payments ===


class PaymentPlan(BaseModel):
    """Тарифный план для оплаты."""

    id: str = Field(description="ID плана")
    name: str = Field(description="Название")
    price_rub: int = Field(description="Цена в рублях")
    period: Literal["month", "year"] = Field(description="Период")
    features: list[str] = Field(description="Список возможностей")


class PaymentCreateRequest(BaseModel):
    """Запрос на создание платежа."""

    plan: Literal["pro", "enterprise"] = Field(description="Тариф (pro/enterprise)")
    source: Literal["web", "bot"] = Field(default="web", description="Источник платежа")


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


# === Auth ===


class TelegramAuthData(BaseModel):
    """Данные авторизации через Telegram Login Widget."""

    id: int = Field(description="Telegram ID пользователя")
    first_name: str = Field(description="Имя пользователя")
    last_name: str | None = Field(default=None, description="Фамилия пользователя")
    username: str | None = Field(default=None, description="Username пользователя")
    photo_url: str | None = Field(default=None, description="URL фото профиля")
    auth_date: int = Field(description="Timestamp авторизации")
    hash: str = Field(description="HMAC-SHA256 подпись данных")


class AuthTokenResponse(BaseModel):
    """Ответ с токеном доступа."""

    access_token: str = Field(description="JWT токен доступа")
    token_type: str = Field(default="bearer", description="Тип токена")
    user: UserResponse = Field(description="Данные пользователя")


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


# === Feedback ===


class FeedbackSubmitRequest(BaseModel):
    """Запрос на отправку обратной связи."""

    text: str = Field(min_length=1, max_length=1000, description="Текст отзыва")
    source: Literal["web", "bot"] = Field(default="web", description="Источник")


class FeedbackSubmitResponse(BaseModel):
    """Ответ на отправку обратной связи."""

    success: bool = Field(description="Успешность сохранения")
    message: str = Field(description="Сообщение")


# === Excel Parsing (Human-in-the-loop) ===


class ExcelColumnInfo(BaseModel):
    """Информация о колонке Excel."""

    name: str = Field(description="Название колонки")
    sample_values: list[str] = Field(description="Примеры значений из колонки")
    looks_like_barcode: bool = Field(description="Похожа ли колонка на баркоды")


class ExcelSampleItem(BaseModel):
    """Пример строки из Excel."""

    barcode: str = Field(description="Значение баркода")
    article: str | None = Field(default=None, description="Артикул")
    size: str | None = Field(default=None, description="Размер")
    color: str | None = Field(default=None, description="Цвет")
    row_number: int = Field(description="Номер строки в Excel")


class ExcelParseResponse(BaseModel):
    """Результат анализа Excel файла."""

    success: bool = Field(description="Успешность парсинга")
    detected_column: str | None = Field(
        default=None, description="Автоопределённая колонка с баркодами"
    )
    all_columns: list[str] = Field(default_factory=list, description="Все колонки в файле")
    barcode_candidates: list[str] = Field(
        default_factory=list, description="Колонки, похожие на баркоды"
    )
    total_rows: int = Field(default=0, description="Общее количество строк с данными")
    sample_items: list[ExcelSampleItem] = Field(
        default_factory=list, description="Примеры данных (первые 5 строк)"
    )
    message: str = Field(description="Сообщение о результате")
