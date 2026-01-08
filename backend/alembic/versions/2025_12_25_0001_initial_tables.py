"""
Начальная миграция - создание всех таблиц.

Revision ID: 0001
Create Date: 2025-12-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создание таблиц."""

    # Enum типы
    op.execute("CREATE TYPE userplan AS ENUM ('free', 'pro', 'enterprise')")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('pending', 'completed', 'failed', 'refunded')")

    # Таблица пользователей
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "telegram_id",
            sa.String(255),
            nullable=False,
            unique=True,
            index=True,
            comment="Telegram ID (зашифровано)",
        ),
        sa.Column(
            "telegram_username",
            sa.String(255),
            nullable=True,
            comment="Telegram username (зашифровано)",
        ),
        sa.Column("first_name", sa.String(255), nullable=True, comment="Имя (зашифровано)"),
        sa.Column("last_name", sa.String(255), nullable=True, comment="Фамилия (зашифровано)"),
        sa.Column("email", sa.String(255), nullable=True, comment="Email (зашифровано)"),
        sa.Column(
            "plan",
            postgresql.ENUM("free", "pro", "enterprise", name="userplan", create_type=False),
            nullable=False,
            server_default="free",
            comment="Текущий тариф",
        ),
        sa.Column(
            "plan_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Срок действия подписки",
        ),
        sa.Column(
            "consent_given_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Дата согласия на обработку ПДн",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Активен ли пользователь",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Дата регистрации",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Дата обновления",
        ),
    )

    # Таблица логов использования
    op.create_table(
        "usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("labels_count", sa.Integer(), nullable=False, comment="Количество этикеток"),
        sa.Column(
            "preflight_status", sa.String(20), nullable=True, comment="Статус Pre-flight проверки"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )

    # Таблица генераций (история для Pro)
    op.create_table(
        "generations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("labels_count", sa.Integer(), nullable=False, comment="Количество этикеток"),
        sa.Column("file_hash", sa.String(64), nullable=True, comment="SHA-256 хеш файла"),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True, comment="Размер файла в байтах"),
        sa.Column(
            "expires_at", sa.DateTime(timezone=True), nullable=False, comment="Время удаления файла"
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # Таблица платежей
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("amount", sa.Integer(), nullable=False, comment="Сумма в минимальных единицах"),
        sa.Column(
            "currency",
            sa.String(10),
            nullable=False,
            server_default="RUB",
            comment="Валюта (RUB, XTR)",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "completed",
                "failed",
                "refunded",
                name="paymentstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("provider", sa.String(50), nullable=False, comment="Платёжный провайдер"),
        sa.Column(
            "external_id", sa.String(255), nullable=True, unique=True, comment="ID транзакции"
        ),
        sa.Column(
            "plan",
            postgresql.ENUM("free", "pro", "enterprise", name="userplan", create_type=False),
            nullable=True,
            comment="Оплаченный тариф",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Таблица логов доступа к ПДн (152-ФЗ)
    op.create_table(
        "pdn_access_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("accessed_by", sa.String(255), nullable=False, comment="Кто обращался"),
        sa.Column("action", sa.String(50), nullable=False, comment="Действие"),
        sa.Column("field_name", sa.String(100), nullable=True, comment="Какое поле"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True, comment="Причина доступа"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )


def downgrade() -> None:
    """Удаление таблиц."""
    op.drop_table("pdn_access_logs")
    op.drop_table("payments")
    op.drop_table("generations")
    op.drop_table("usage_logs")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS userplan")
