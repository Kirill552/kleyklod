"""add_vk_user_id

Revision ID: 0006
Revises: 0005
Create Date: 2026-01-11 12:00:00.000000

Добавляет поддержку авторизации через VK:
- vk_user_id: зашифрованный VK user ID
- vk_user_id_hash: SHA-256 хеш для поиска
- telegram_id становится nullable (пользователь может быть только из VK)
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Делаем telegram_id nullable (пользователь может быть из VK)
    op.alter_column(
        "users",
        "telegram_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )

    # Добавляем vk_user_id (зашифрованный)
    op.add_column(
        "users",
        sa.Column(
            "vk_user_id",
            sa.String(length=255),
            nullable=True,
            comment="VK user ID (зашифровано)",
        ),
    )

    # Добавляем vk_user_id_hash для поиска
    op.add_column(
        "users",
        sa.Column(
            "vk_user_id_hash",
            sa.String(length=64),
            nullable=True,
            comment="SHA-256 хеш vk_user_id для поиска",
        ),
    )

    # Создаём уникальный индекс
    op.create_index(
        "ix_users_vk_user_id_hash",
        "users",
        ["vk_user_id_hash"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_users_vk_user_id_hash", table_name="users")
    op.drop_column("users", "vk_user_id_hash")
    op.drop_column("users", "vk_user_id")

    # Возвращаем telegram_id как NOT NULL
    op.alter_column(
        "users",
        "telegram_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )
