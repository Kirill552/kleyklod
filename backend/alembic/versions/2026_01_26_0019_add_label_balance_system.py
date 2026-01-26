"""add label balance system

Revision ID: 0019
Revises: 0018
Create Date: 2026-01-26 12:00:00.000000

Добавляет систему накопительных лимитов этикеток:
- Поле label_balance в users для текущего баланса
- Таблица label_transactions для истории операций
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019"
down_revision: str | Sequence[str] | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Добавляем поле label_balance в users
    op.add_column(
        "users",
        sa.Column(
            "label_balance",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Текущий баланс этикеток (накопительный)",
        ),
    )

    # 2. Создаём enum для типа транзакции
    transaction_type = postgresql.ENUM("credit", "debit", name="transaction_type")
    transaction_type.create(op.get_bind(), checkfirst=True)

    # 3. Создаём таблицу label_transactions
    op.create_table(
        "label_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Тип: credit (начисление) или debit (списание)
        sa.Column(
            "type",
            postgresql.ENUM("credit", "debit", name="transaction_type", create_type=False),
            nullable=False,
            comment="Тип: credit (начисление) или debit (списание)",
        ),
        # Количество этикеток
        sa.Column(
            "amount",
            sa.Integer(),
            nullable=False,
            comment="Количество этикеток",
        ),
        # Баланс после операции
        sa.Column(
            "balance_after",
            sa.Integer(),
            nullable=False,
            comment="Баланс после операции",
        ),
        # Причина операции
        sa.Column(
            "reason",
            sa.String(length=50),
            nullable=False,
            comment="Причина: subscription_renewal, generation, bonus, refund, migration",
        ),
        # Ссылка на связанную сущность (payment_id, generation_id)
        sa.Column(
            "reference_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="Ссылка на payment_id или generation_id",
        ),
        # Дополнительное описание
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=True,
            comment="Дополнительное описание операции",
        ),
        # Время операции
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Ключи
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. Индексы для быстрого поиска
    op.create_index(
        op.f("ix_label_transactions_user_id"),
        "label_transactions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_label_transactions_created_at"),
        "label_transactions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_label_transactions_reason"),
        "label_transactions",
        ["reason"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем индексы
    op.drop_index(op.f("ix_label_transactions_reason"), table_name="label_transactions")
    op.drop_index(op.f("ix_label_transactions_created_at"), table_name="label_transactions")
    op.drop_index(op.f("ix_label_transactions_user_id"), table_name="label_transactions")

    # Удаляем таблицу
    op.drop_table("label_transactions")

    # Удаляем enum
    transaction_type = postgresql.ENUM("credit", "debit", name="transaction_type")
    transaction_type.drop(op.get_bind(), checkfirst=True)

    # Удаляем поле из users
    op.drop_column("users", "label_balance")
