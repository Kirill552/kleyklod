"""add_user_photo_url_and_generation_fields

Revision ID: 0002
Revises: 0001
Create Date: 2025-12-25 17:35:00.000000

Добавлены поля:
- User.photo_url - URL аватарки из Telegram
- Generation.file_path - путь к файлу (хранится 7 дней)
- Generation.preflight_passed - прошла ли Pre-flight проверка
- PaymentStatus.SUCCESS - новое значение enum для успешных платежей
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Добавляем поле photo_url в таблицу users
    op.add_column(
        "users",
        sa.Column(
            "photo_url", sa.String(length=500), nullable=True, comment="URL аватарки из Telegram"
        ),
    )

    # Добавляем поле file_path в таблицу generations
    op.add_column(
        "generations",
        sa.Column(
            "file_path",
            sa.String(length=500),
            nullable=True,
            comment="Путь к файлу (хранится 7 дней)",
        ),
    )

    # Добавляем поле preflight_passed в таблицу generations
    op.add_column(
        "generations",
        sa.Column(
            "preflight_passed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Прошла ли Pre-flight проверка",
        ),
    )

    # Обновляем enum PaymentStatus - добавляем значение 'success'
    # Для PostgreSQL используем ALTER TYPE
    op.execute(
        """
        ALTER TYPE paymentstatus ADD VALUE IF NOT EXISTS 'success' BEFORE 'completed';
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем поле preflight_passed из таблицы generations
    op.drop_column("generations", "preflight_passed")

    # Удаляем поле file_path из таблицы generations
    op.drop_column("generations", "file_path")

    # Удаляем поле photo_url из таблицы users
    op.drop_column("users", "photo_url")

    # Примечание: PostgreSQL не поддерживает удаление значения из enum
    # Для полного отката нужно пересоздать тип или использовать новую миграцию
