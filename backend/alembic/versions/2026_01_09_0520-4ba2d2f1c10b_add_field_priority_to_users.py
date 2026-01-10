"""add_field_priority_to_users

Revision ID: 4ba2d2f1c10b
Revises: 0014
Create Date: 2026-01-09 05:20:57.600166

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4ba2d2f1c10b"
down_revision: str | Sequence[str] | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "field_priority",
            sa.JSON(),
            nullable=True,
            comment="Приоритет полей для обрезки при превышении лимита (PRO/ENT)",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "field_priority")
