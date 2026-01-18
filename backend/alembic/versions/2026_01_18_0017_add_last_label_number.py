"""add_last_label_number

Revision ID: 0017
Revises: 0016
Create Date: 2026-01-18 12:00:00.000000

Добавляет глобальный счётчик нумерации этикеток:
- last_label_number: последний использованный глобальный номер
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0017"
down_revision: str | Sequence[str] | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "last_label_number",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Последний глобальный номер этикетки",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "last_label_number")
