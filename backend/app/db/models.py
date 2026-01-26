"""
SQLAlchemy модели базы данных.

Персональные данные (ПДн) шифруются согласно 152-ФЗ.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.utils.encryption import EncryptedString


class UserPlan(str, PyEnum):
    """Тарифные планы."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PaymentStatus(str, PyEnum):
    """Статусы платежей."""

    PENDING = "pending"
    SUCCESS = "success"
    COMPLETED = "completed"  # Deprecated: использовать SUCCESS
    FAILED = "failed"
    REFUNDED = "refunded"


class TaskStatus(str, PyEnum):
    """Статусы фоновых задач."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionType(str, PyEnum):
    """Типы транзакций баланса этикеток."""

    CREDIT = "credit"  # Начисление (подписка, бонус)
    DEBIT = "debit"  # Списание (генерация)


class User(Base):
    """
    Модель пользователя.

    Поля с ПДн шифруются (152-ФЗ):
    - telegram_id
    - telegram_username
    - first_name
    - last_name
    - email
    """

    __tablename__ = "users"

    # Первичный ключ
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Telegram данные (зашифрованы)
    telegram_id: Mapped[str | None] = mapped_column(
        EncryptedString(255),
        unique=False,  # Уникальность через telegram_id_hash
        index=False,  # Индекс на telegram_id_hash
        nullable=True,  # Nullable — пользователь может быть из VK
        comment="Telegram ID (зашифровано)",
    )
    # Детерминистический хеш для поиска (Fernet не детерминистичен)
    telegram_id_hash: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=True,  # Nullable для совместимости с существующими записями
        comment="SHA-256 хеш telegram_id для поиска",
    )

    # VK данные (зашифрованы)
    vk_user_id: Mapped[str | None] = mapped_column(
        EncryptedString(255),
        unique=False,  # Уникальность через vk_user_id_hash
        index=False,
        nullable=True,
        comment="VK user ID (зашифровано)",
    )
    vk_user_id_hash: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=True,
        comment="SHA-256 хеш vk_user_id для поиска",
    )
    telegram_username: Mapped[str | None] = mapped_column(
        EncryptedString(255),
        nullable=True,
        comment="Telegram username (зашифровано)",
    )
    first_name: Mapped[str | None] = mapped_column(
        EncryptedString(255),
        nullable=True,
        comment="Имя (зашифровано)",
    )
    last_name: Mapped[str | None] = mapped_column(
        EncryptedString(255),
        nullable=True,
        comment="Фамилия (зашифровано)",
    )
    email: Mapped[str | None] = mapped_column(
        EncryptedString(255),
        nullable=True,
        comment="Email (зашифровано)",
    )
    photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL аватарки из Telegram",
    )

    # Тарифный план
    plan: Mapped[UserPlan] = mapped_column(
        Enum(UserPlan, values_callable=lambda x: [e.value for e in x]),
        default=UserPlan.FREE,
        comment="Текущий тариф",
    )
    plan_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Срок действия подписки",
    )

    # Trial период (7 дней полного доступа для новых пользователей)
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата окончания trial периода",
    )

    # Согласие на обработку ПДн (152-ФЗ)
    consent_given_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата согласия на обработку ПДн",
    )

    # Статус
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Активен ли пользователь",
    )

    # Обратная связь
    feedback_asked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Показывали ли опрос пользователю",
    )
    last_conversion_prompt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Когда последний раз показывали промо Pro",
    )
    has_seen_cards_hint: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Показывали ли подсказку о карточках товаров",
    )

    # Настройки генерации этикеток
    organization_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Название организации для этикеток",
    )
    inn: Mapped[str | None] = mapped_column(
        String(12),
        nullable=True,
        comment="ИНН организации",
    )
    organization_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Адрес производства",
    )
    production_country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Страна производства",
    )
    certificate_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Номер сертификата",
    )
    preferred_layout: Mapped[str] = mapped_column(
        String(20),
        default="basic",
        server_default="basic",
        comment="Предпочитаемый layout этикетки (basic, professional)",
    )
    preferred_label_size: Mapped[str] = mapped_column(
        String(10),
        default="58x40",
        server_default="58x40",
        comment="Предпочитаемый размер этикетки",
    )
    preferred_format: Mapped[str] = mapped_column(
        String(20),
        default="combined",
        server_default="combined",
        comment="Предпочитаемый формат (combined/separate)",
    )
    show_article: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Показывать артикул на этикетке",
    )
    show_size_color: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Показывать размер/цвет на этикетке",
    )
    show_name: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Показывать название товара на этикетке",
    )
    custom_lines: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="Кастомные строки для Extended шаблона (до 3 строк)",
    )
    field_priority: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="Приоритет полей для обрезки при превышении лимита (PRO/ENT)",
    )

    # Глобальный счётчик нумерации этикеток
    last_label_number: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Последний глобальный номер этикетки",
    )

    # Баланс этикеток (накопительная система)
    label_balance: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Текущий баланс этикеток (накопительный)",
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата регистрации",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата обновления",
    )

    # Связи
    usage_logs: Mapped[list["UsageLog"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    generations: Mapped[list["Generation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    feedback_responses: Mapped[list["FeedbackResponse"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    product_cards: Mapped[list["ProductCard"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    marketplace_keys: Mapped[list["MarketplaceKey"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    label_transactions: Mapped[list["LabelTransaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class ApiKey(Base):
    """
    API ключи для Enterprise пользователей.

    Ключ хранится в виде SHA-256 хеша (безопасность).
    Один пользователь = один активный ключ.
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Храним только хеш ключа (безопасность)
    key_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        comment="SHA-256 хеш ключа",
    )
    key_prefix: Mapped[str] = mapped_column(
        String(16),
        comment="Префикс ключа для отображения (kk_live_...)",
    )

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Последнее использование ключа",
    )

    # Связи
    user: Mapped["User"] = relationship(back_populates="api_keys")


class MarketplaceKey(Base):
    """
    API ключи маркетплейсов для Enterprise пользователей.

    Ключ шифруется AES-256 (Fernet) перед сохранением.
    Пока поддерживается только Wildberries.
    """

    __tablename__ = "marketplace_keys"
    __table_args__ = (UniqueConstraint("user_id", "marketplace", name="uq_user_marketplace"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Маркетплейс: пока только "wb"
    marketplace: Mapped[str] = mapped_column(
        String(10),
        comment="Маркетплейс: wb",
    )

    # Зашифрованный API ключ
    encrypted_api_key: Mapped[str] = mapped_column(
        Text,
        comment="API ключ (зашифрован Fernet)",
    )

    # Статистика
    products_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Количество синхронизированных товаров",
    )

    # Временные метки
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата подключения",
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Последняя синхронизация",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Активно ли подключение",
    )

    # Связи
    user: Mapped["User"] = relationship(back_populates="marketplace_keys")


class UsageLog(Base):
    """
    Лог использования сервиса.

    Хранит статистику генераций для подсчёта лимитов.
    """

    __tablename__ = "usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Данные генерации
    labels_count: Mapped[int] = mapped_column(
        Integer,
        comment="Количество этикеток",
    )
    preflight_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Статус Pre-flight проверки",
    )

    # Время
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    # Связи
    user: Mapped["User"] = relationship(back_populates="usage_logs")


class Generation(Base):
    """
    История генераций (для Pro пользователей).

    Хранит информацию о сгенерированных файлах.
    Файлы удаляются через 24 часа.
    """

    __tablename__ = "generations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Данные файла
    labels_count: Mapped[int] = mapped_column(
        Integer,
        comment="Количество этикеток",
    )
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Путь к файлу (хранится 7 дней)",
    )
    file_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 хеш файла",
    )
    file_size_bytes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Размер файла в байтах",
    )
    preflight_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Прошла ли Pre-flight проверка",
    )

    # Время жизни
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        comment="Время удаления файла",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Связи
    user: Mapped["User"] = relationship(back_populates="generations")


class Payment(Base):
    """
    Платежи пользователей.

    Поддерживает:
    - ЮКасса
    """

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Сумма
    amount: Mapped[int] = mapped_column(
        Integer,
        comment="Сумма в копейках",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="RUB",
        comment="Валюта (RUB)",
    )

    # Статус
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, values_callable=lambda x: [e.value for e in x]),
        default=PaymentStatus.PENDING,
    )

    # Провайдер
    provider: Mapped[str] = mapped_column(
        String(50),
        comment="Платёжный провайдер (yookassa)",
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="ID транзакции в платёжной системе",
    )

    # Тариф
    plan: Mapped[UserPlan | None] = mapped_column(
        Enum(UserPlan, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        comment="Оплаченный тариф",
    )

    # Время
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Связи
    user: Mapped["User"] = relationship(back_populates="payments")


class FeedbackResponse(Base):
    """
    Ответы пользователей на опрос.

    Собираем после 3-й генерации для понимания потребностей.
    """

    __tablename__ = "feedback_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    text: Mapped[str] = mapped_column(
        Text,
        comment="Текст ответа пользователя",
    )

    source: Mapped[str] = mapped_column(
        String(10),
        comment="Источник: web | bot",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Связи
    user: Mapped["User"] = relationship(back_populates="feedback_responses")


class CodeUsage(Base):
    """
    История использования кодов маркировки.

    Хранит хеши кодов для предотвращения повторного использования.
    Коды хранятся 30 дней, затем автоматически удаляются.
    """

    __tablename__ = "code_usages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # SHA-256 хеш кода (не храним сам код)
    code_hash: Mapped[str] = mapped_column(
        String(64),
        index=True,
        comment="SHA-256 хеш кода маркировки",
    )

    # Ссылка на генерацию (опционально)
    generation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Время использования
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        comment="Когда код был использован",
    )


class PdnAccessLog(Base):
    """
    Лог доступа к персональным данным (152-ФЗ).

    Обязательно для аудита обработки ПДн.
    """

    __tablename__ = "pdn_access_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Чьи данные
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Кто обращался
    accessed_by: Mapped[str] = mapped_column(
        String(255),
        comment="Кто обращался (system, admin_id, api_key)",
    )

    # Действие
    action: Mapped[str] = mapped_column(
        String(50),
        comment="Действие (read, write, delete, export)",
    )
    field_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Какое поле",
    )

    # Контекст
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 до 45 символов
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Причина доступа",
    )

    # Время
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )


class ProductCard(Base):
    """
    Карточка товара пользователя для быстрой генерации.

    Хранит данные о товарах пользователя, включая последний
    использованный серийный номер для нумерации этикеток.
    """

    __tablename__ = "product_cards"
    __table_args__ = (UniqueConstraint("user_id", "barcode", name="uq_user_barcode"),)

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="Владелец карточки",
    )

    # Идентификатор товара
    barcode: Mapped[str] = mapped_column(
        String(20),
        index=True,
        comment="EAN-13 или Code128 баркод",
    )

    # Данные товара
    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Название товара",
    )
    article: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Артикул",
    )
    size: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Размер",
    )
    color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Цвет",
    )
    composition: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Состав изделия",
    )
    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Страна производства",
    )
    brand: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Бренд",
    )
    manufacturer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Производитель",
    )
    production_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Дата производства",
    )
    importer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Импортёр",
    )
    certificate_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Номер сертификата",
    )
    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Адрес производства/продавца",
    )

    # Нумерация — последний использованный серийный номер
    last_serial_number: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        comment="Последний использованный серийный номер",
    )

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания карточки",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления",
    )

    # Связь с пользователем
    user: Mapped["User"] = relationship(back_populates="product_cards")


class Task(Base):
    """
    Фоновые задачи генерации этикеток.

    Используется для асинхронной обработки больших PDF через Celery.
    Результаты хранятся 24 часа, затем автоматически удаляются.
    """

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="Владелец задачи",
    )

    # Статус выполнения
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]),
        default=TaskStatus.PENDING,
        index=True,
        comment="Статус: pending, processing, completed, failed",
    )

    # Прогресс (0-100)
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Прогресс выполнения в процентах",
    )

    # Результат
    result_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Путь к готовому PDF файлу",
    )

    # Ошибка (если failed)
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Сообщение об ошибке",
    )

    # Метаданные задачи
    total_pages: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Общее количество страниц для обработки",
    )
    labels_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Количество этикеток в результате",
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Время создания задачи",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время начала обработки",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время завершения",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время удаления результата (TTL 24ч)",
    )

    # Связь с пользователем
    user: Mapped["User"] = relationship(back_populates="tasks")


class LabelTransaction(Base):
    """
    История транзакций баланса этикеток.

    Отслеживает начисления (подписка, бонусы) и списания (генерации).
    Используется для аудита и поддержки пользователей.
    """

    __tablename__ = "label_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Тип операции: credit (начисление) или debit (списание)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, values_callable=lambda x: [e.value for e in x]),
        comment="Тип: credit (начисление) или debit (списание)",
    )

    # Количество этикеток
    amount: Mapped[int] = mapped_column(
        Integer,
        comment="Количество этикеток",
    )

    # Баланс после операции
    balance_after: Mapped[int] = mapped_column(
        Integer,
        comment="Баланс после операции",
    )

    # Причина операции
    reason: Mapped[str] = mapped_column(
        String(50),
        index=True,
        comment="Причина: subscription_renewal, generation, bonus, refund, migration",
    )

    # Ссылка на связанную сущность (payment_id, generation_id)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Ссылка на payment_id или generation_id",
    )

    # Дополнительное описание
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Дополнительное описание операции",
    )

    # Время операции
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    # Связь с пользователем
    user: Mapped["User"] = relationship(back_populates="label_transactions")
