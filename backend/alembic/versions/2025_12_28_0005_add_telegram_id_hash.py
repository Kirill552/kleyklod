"""add_telegram_id_hash

Revision ID: 0005
Revises: 0004
Create Date: 2025-12-28 16:00:00.000000

Добавляет колонку telegram_id_hash для детерминистического поиска.
Fernet шифрование не детерминистическое (каждый encrypt() создаёт разный результат),
поэтому для поиска пользователей по telegram_id используем SHA-256 хеш.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Добавляем колонку telegram_id_hash (nullable сначала для существующих записей)
    op.add_column(
        "users",
        sa.Column(
            "telegram_id_hash",
            sa.String(length=64),
            nullable=True,  # Nullable пока не заполним хеши существующих пользователей
            comment="SHA-256 хеш telegram_id для поиска",
        ),
    )

    # Создаём уникальный индекс (разрешаем NULL для существующих записей)
    op.create_index(
        "ix_users_telegram_id_hash",
        "users",
        ["telegram_id_hash"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_users_telegram_id_hash", table_name="users")
    op.drop_column("users", "telegram_id_hash")
