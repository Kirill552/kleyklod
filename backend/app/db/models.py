"""
SQLAlchemy модели базы данных.

Персональные данные (ПДн) шифруются согласно 152-ФЗ.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
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
    telegram_id: Mapped[str] = mapped_column(
        EncryptedString(255),
        unique=True,
        index=True,
        comment="Telegram ID (зашифровано)",
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
        Enum(UserPlan),
        default=UserPlan.FREE,
        comment="Текущий тариф",
    )
    plan_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Срок действия подписки",
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
    - Telegram Stars
    - ЮKassa (в будущем)
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
        comment="Сумма в минимальных единицах (копейки/stars)",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="RUB",
        comment="Валюта (RUB, XTR для Stars)",
    )

    # Статус
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
    )

    # Провайдер
    provider: Mapped[str] = mapped_column(
        String(50),
        comment="Платёжный провайдер (stars, yookassa)",
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="ID транзакции в платёжной системе",
    )

    # Тариф
    plan: Mapped[UserPlan | None] = mapped_column(
        Enum(UserPlan),
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
