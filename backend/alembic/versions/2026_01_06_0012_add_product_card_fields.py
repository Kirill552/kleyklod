"""add product card fields

Добавляет 4 новых поля в таблицу product_cards:
- manufacturer (производитель)
- production_date (дата производства)
- importer (импортёр)
- certificate_number (номер сертификата)

Revision ID: 0012
Revises: 0011
Create Date: 2026-01-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "product_cards",
        sa.Column(
            "manufacturer",
            sa.String(255),
            nullable=True,
            comment="Производитель",
        ),
    )
    op.add_column(
        "product_cards",
        sa.Column(
            "production_date",
            sa.String(50),
            nullable=True,
            comment="Дата производства",
        ),
    )
    op.add_column(
        "product_cards",
        sa.Column(
            "importer",
            sa.String(255),
            nullable=True,
            comment="Импортёр",
        ),
    )
    op.add_column(
        "product_cards",
        sa.Column(
            "certificate_number",
            sa.String(100),
            nullable=True,
            comment="Номер сертификата",
        ),
    )


def downgrade() -> None:
    op.drop_column("product_cards", "certificate_number")
    op.drop_column("product_cards", "importer")
    op.drop_column("product_cards", "production_date")
    op.drop_column("product_cards", "manufacturer")
