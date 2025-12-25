"""add api_keys table

Revision ID: 0003_add_api_keys
Revises: 0002_add_user_photo_url_and_generation_fields
Create Date: 2025-12-25

Добавляет таблицу api_keys для Enterprise пользователей.
API ключи позволяют автоматизировать генерацию этикеток через REST API.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создаём таблицу api_keys."""
    op.create_table(
        "api_keys",
        sa.Column("id", sa.UUID(), nullable=False, comment="Первичный ключ"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="ID пользователя"),
        sa.Column(
            "key_hash",
            sa.String(64),
            nullable=False,
            comment="SHA-256 хеш ключа",
        ),
        sa.Column(
            "key_prefix",
            sa.String(16),
            nullable=False,
            comment="Префикс ключа для отображения (kk_live_...)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Дата создания",
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Последнее использование ключа",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_api_keys_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Индекс для быстрого поиска по хешу ключа
    op.create_index(
        "ix_api_keys_key_hash",
        "api_keys",
        ["key_hash"],
        unique=True,
    )

    # Индекс для поиска ключей пользователя
    op.create_index(
        "ix_api_keys_user_id",
        "api_keys",
        ["user_id"],
    )


def downgrade() -> None:
    """Удаляем таблицу api_keys."""
    op.drop_index("ix_api_keys_user_id", table_name="api_keys")
    op.drop_index("ix_api_keys_key_hash", table_name="api_keys")
    op.drop_table("api_keys")
