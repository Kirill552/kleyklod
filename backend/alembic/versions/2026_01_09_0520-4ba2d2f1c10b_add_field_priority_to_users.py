"""add_field_priority_to_users

Revision ID: 4ba2d2f1c10b
Revises: 0014
Create Date: 2026-01-09 05:20:57.600166

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4ba2d2f1c10b"
down_revision: Union[str, Sequence[str], None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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
