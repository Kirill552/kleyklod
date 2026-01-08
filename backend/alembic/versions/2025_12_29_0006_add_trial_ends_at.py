"""add_trial_ends_at

Revision ID: 0006
Revises: 0005
Create Date: 2025-12-29 12:00:00.000000

Добавляет поле trial_ends_at для поддержки 7-дневного trial периода.
Новые пользователи получают 7 дней с PRO лимитами (500 этикеток/день).
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
    # Добавляем колонку trial_ends_at
    op.add_column(
        "users",
        sa.Column(
            "trial_ends_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Дата окончания trial периода",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "trial_ends_at")
