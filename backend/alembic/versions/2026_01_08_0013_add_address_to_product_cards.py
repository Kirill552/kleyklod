"""add address to product cards

Добавляет поле address в таблицу product_cards:
- address (адрес производства/продавца)

Revision ID: 0013
Revises: 0012
Create Date: 2026-01-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "product_cards",
        sa.Column(
            "address",
            sa.String(500),
            nullable=True,
            comment="Адрес производства/продавца",
        ),
    )


def downgrade() -> None:
    op.drop_column("product_cards", "address")
