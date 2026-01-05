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


class CountMismatchInfo(BaseModel):
    """Информация о несовпадении количества строк Excel и кодов ЧЗ."""

    excel_rows: int = Field(description="Количество строк в Excel")
    codes_count: int = Field(description="Количество кодов ЧЗ")
    will_generate: int = Field(description="Сколько этикеток будет создано (минимум)")


class LabelMergeResponse(BaseModel):
    """Ответ с результатом объединения."""

    success: bool = Field(description="Успешность операции")
    # HITL: требуется подтверждение пользователя
    needs_confirmation: bool = Field(
        default=False, description="Требуется подтверждение пользователя"
    )
    count_mismatch: CountMismatchInfo | None = Field(
        default=None, description="Информация о несовпадении количества (если есть)"
    )
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
    # Предупреждение о дубликатах кодов
    duplicate_warning: str | None = Field(
        default=None, description="Предупреждение если коды уже использовались ранее"
    )
    duplicate_count: int = Field(default=0, description="Количество дубликатов кодов")


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
    name: str | None = Field(default=None, description="Название товара")
    country: str | None = Field(default=None, description="Страна производства")
    composition: str | None = Field(default=None, description="Состав")
    brand: str | None = Field(default=None, description="Бренд")
    manufacturer: str | None = Field(default=None, description="Производитель")
    production_date: str | None = Field(default=None, description="Дата производства")
    importer: str | None = Field(default=None, description="Импортёр")
    certificate_number: str | None = Field(default=None, description="Номер сертификата")
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


# === File Detection (Auto-detect PDF/Excel) ===


class FileType(str, Enum):
    """Тип загруженного файла."""

    PDF = "pdf"
    EXCEL = "excel"
    UNKNOWN = "unknown"


class FileDetectionResponse(BaseModel):
    """Ответ автодетекта типа файла."""

    file_type: FileType = Field(description="Тип файла (pdf, excel, unknown)")
    filename: str = Field(description="Имя файла")
    size_bytes: int = Field(description="Размер файла в байтах")

    # Для PDF
    pages_count: int | None = Field(default=None, description="Количество страниц (PDF)")

    # Для Excel
    rows_count: int | None = Field(default=None, description="Количество строк (Excel)")
    columns: list[str] | None = Field(default=None, description="Колонки в файле (Excel)")
    detected_barcode_column: str | None = Field(
        default=None, description="Автоопределённая колонка с баркодами"
    )
    sample_items: list[ExcelSampleItem] | None = Field(
        default=None, description="Примеры данных (Excel)"
    )

    # Ошибка
    error: str | None = Field(default=None, description="Сообщение об ошибке")


# === Generate from Excel ===


class GenerateFromExcelRequest(BaseModel):
    """Параметры генерации из Excel (для справки, используется Form)."""

    organization: str = Field(..., min_length=1, max_length=255, description="Название организации")
    layout: Literal["basic", "professional"] = Field(default="basic", description="Шаблон этикетки")
    label_size: Literal["58x40", "58x30", "58x60"] = Field(
        default="58x40", description="Размер этикетки"
    )
    label_format: LabelFormat = Field(
        default=LabelFormat.COMBINED, description="Формат (combined/separate)"
    )
    show_article: bool = Field(default=True, description="Показывать артикул")
    show_size_color: bool = Field(default=True, description="Показывать размер/цвет")
    show_name: bool = Field(default=True, description="Показывать название товара")

    # Fallback для отсутствующих данных
    fallback_size: str | None = Field(default=None, description="Размер по умолчанию")
    fallback_color: str | None = Field(default=None, description="Цвет по умолчанию")

    # Выбор колонки вручную
    barcode_column: str | None = Field(
        default=None, description="Колонка с баркодами (если автодетект не сработал)"
    )


# === User Label Preferences ===


class UserLabelPreferences(BaseModel):
    """Настройки генерации этикеток пользователя."""

    organization_name: str | None = Field(
        default=None, max_length=255, description="Название организации для этикеток"
    )
    inn: str | None = Field(default=None, max_length=12, description="ИНН организации")
    organization_address: str | None = Field(
        default=None, max_length=500, description="Адрес организации/производства"
    )
    production_country: str | None = Field(
        default=None, max_length=100, description="Страна производства"
    )
    certificate_number: str | None = Field(
        default=None, max_length=100, description="Номер сертификата"
    )
    preferred_layout: Literal["basic", "professional", "extended"] = Field(
        default="basic", description="Предпочитаемый шаблон этикетки"
    )
    preferred_label_size: Literal["58x40", "58x30", "58x60"] = Field(
        default="58x40", description="Предпочитаемый размер этикетки"
    )
    preferred_format: Literal["combined", "separate"] = Field(
        default="combined", description="Предпочитаемый формат (combined/separate)"
    )
    show_article: bool = Field(default=True, description="Показывать артикул на этикетке")
    show_size_color: bool = Field(default=True, description="Показывать размер/цвет на этикетке")
    show_name: bool = Field(default=True, description="Показывать название товара на этикетке")
    custom_lines: list[str] | None = Field(
        default=None, max_length=3, description="Кастомные строки для Extended шаблона (до 3)"
    )


class UserLabelPreferencesUpdate(BaseModel):
    """Обновление настроек генерации этикеток."""

    organization_name: str | None = Field(
        default=None, max_length=255, description="Название организации для этикеток"
    )
    inn: str | None = Field(default=None, max_length=12, description="ИНН организации")
    organization_address: str | None = Field(
        default=None, max_length=500, description="Адрес организации/производства"
    )
    production_country: str | None = Field(
        default=None, max_length=100, description="Страна производства"
    )
    certificate_number: str | None = Field(
        default=None, max_length=100, description="Номер сертификата"
    )
    preferred_layout: Literal["basic", "professional", "extended"] | None = Field(
        default=None, description="Предпочитаемый шаблон этикетки"
    )
    preferred_label_size: Literal["58x40", "58x30", "58x60"] | None = Field(
        default=None, description="Предпочитаемый размер этикетки"
    )
    preferred_format: Literal["combined", "separate"] | None = Field(
        default=None, description="Предпочитаемый формат (combined/separate)"
    )
    show_article: bool | None = Field(default=None, description="Показывать артикул на этикетке")
    show_size_color: bool | None = Field(
        default=None, description="Показывать размер/цвет на этикетке"
    )
    show_name: bool | None = Field(
        default=None, description="Показывать название товара на этикетке"
    )
    custom_lines: list[str] | None = Field(
        default=None, max_length=3, description="Кастомные строки для Extended шаблона (до 3)"
    )


# === Product Cards ===


class ProductCardCreate(BaseModel):
    """Данные для создания/обновления карточки товара."""

    barcode: str = Field(min_length=1, max_length=20, description="EAN-13 или Code128 баркод")
    name: str | None = Field(default=None, max_length=255, description="Название товара")
    article: str | None = Field(default=None, max_length=100, description="Артикул")
    size: str | None = Field(default=None, max_length=50, description="Размер")
    color: str | None = Field(default=None, max_length=50, description="Цвет")
    composition: str | None = Field(default=None, max_length=255, description="Состав изделия")
    country: str | None = Field(default=None, max_length=100, description="Страна производства")
    brand: str | None = Field(default=None, max_length=100, description="Бренд")


class ProductCardResponse(BaseModel):
    """Информация о карточке товара."""

    id: int = Field(description="ID карточки")
    barcode: str = Field(description="EAN-13 или Code128 баркод")
    name: str | None = Field(default=None, description="Название товара")
    article: str | None = Field(default=None, description="Артикул")
    size: str | None = Field(default=None, description="Размер")
    color: str | None = Field(default=None, description="Цвет")
    composition: str | None = Field(default=None, description="Состав изделия")
    country: str | None = Field(default=None, description="Страна производства")
    brand: str | None = Field(default=None, description="Бренд")
    last_serial_number: int = Field(description="Последний использованный серийный номер")
    created_at: datetime = Field(description="Дата создания")
    updated_at: datetime = Field(description="Дата последнего обновления")


class ProductCardListResponse(BaseModel):
    """Список карточек товаров."""

    items: list[ProductCardResponse] = Field(description="Список карточек")
    total: int = Field(description="Общее количество карточек")


class ProductCardBulkResponse(BaseModel):
    """Результат массового upsert карточек."""

    created: int = Field(description="Создано новых карточек")
    updated: int = Field(description="Обновлено существующих карточек")
    skipped: int = Field(description="Пропущено (пустой barcode или без изменений)")


class ProductCardSerialUpdate(BaseModel):
    """Обновление последнего серийного номера."""

    last_serial_number: int = Field(ge=0, description="Новый серийный номер")
