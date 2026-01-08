"""add custom_lines to users

Revision ID: 0011
Revises: 0010
Create Date: 2026-01-05

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "custom_lines",
            sa.JSON(),
            nullable=True,
            comment="Кастомные строки для Extended шаблона (до 3 строк)",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "custom_lines")
