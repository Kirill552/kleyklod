"""add has_seen_cards_hint to users

Добавляет поле has_seen_cards_hint в таблицу users для отслеживания,
видел ли пользователь подсказку о карточках товаров.

Revision ID: 0014
Revises: 0013
Create Date: 2026-01-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "has_seen_cards_hint",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="Показывали ли подсказку о карточках товаров",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "has_seen_cards_hint")
