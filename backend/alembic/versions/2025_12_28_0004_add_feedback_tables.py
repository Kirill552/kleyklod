"""add feedback tables

Revision ID: 0004_add_feedback
Revises: 0003_add_api_keys
Create Date: 2025-12-28

Добавляет таблицу feedback_responses и поля для отслеживания
показа опроса пользователям (feedback_asked, last_conversion_prompt).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Добавляем таблицу feedback_responses и поля в users."""
    # Добавляем поля в таблицу users
    op.add_column(
        "users",
        sa.Column(
            "feedback_asked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Показывали ли опрос пользователю",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "last_conversion_prompt",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Когда последний раз показывали промо Pro",
        ),
    )

    # Создаём таблицу feedback_responses
    op.create_table(
        "feedback_responses",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            comment="Первичный ключ",
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
            comment="ID пользователя",
        ),
        sa.Column(
            "text",
            sa.Text(),
            nullable=False,
            comment="Текст ответа пользователя",
        ),
        sa.Column(
            "source",
            sa.String(10),
            nullable=False,
            comment="Источник: web | bot",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Дата создания",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_feedback_responses_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Индекс для поиска ответов пользователя
    op.create_index(
        "ix_feedback_responses_user_id",
        "feedback_responses",
        ["user_id"],
    )


def downgrade() -> None:
    """Удаляем таблицу feedback_responses и поля из users."""
    op.drop_index("ix_feedback_responses_user_id", table_name="feedback_responses")
    op.drop_table("feedback_responses")
    op.drop_column("users", "last_conversion_prompt")
    op.drop_column("users", "feedback_asked")
