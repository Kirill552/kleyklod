"""add marketplace_keys table

Revision ID: 0018
Revises: 0017
Create Date: 2026-01-21 08:22:00.000000

Добавляет таблицу marketplace_keys для интеграции с маркетплейсами.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018"
down_revision: str | Sequence[str] | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создание таблицы marketplace_keys
    op.create_table(
        "marketplace_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marketplace", sa.String(length=10), nullable=False, comment="Маркетплейс: wb"),
        sa.Column("encrypted_api_key", sa.Text(), nullable=False, comment="API ключ (зашифрован Fernet)"),
        sa.Column("products_count", sa.Integer(), nullable=False, server_default="0", comment="Количество синхронизированных товаров"),
        sa.Column("connected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Дата подключения"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True, comment="Последняя синхронизация"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true", comment="Активно ли подключение"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "marketplace", name="uq_user_marketplace")
    )
    op.create_index(op.f("ix_marketplace_keys_user_id"), "marketplace_keys", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_marketplace_keys_user_id"), table_name="marketplace_keys")
    op.drop_table("marketplace_keys")