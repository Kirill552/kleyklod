"""add_product_cards_table

Revision ID: 0010
Revises: 0009
Create Date: 2026-01-05 12:00:00.000000

Добавляет таблицу product_cards для хранения карточек товаров пользователей.
Поддерживает нумерацию этикеток (серийные номера) и быстрый поиск по баркодам.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаём таблицу product_cards
    op.create_table(
        "product_cards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), nullable=False, comment="Владелец карточки"
        ),
        sa.Column("barcode", sa.String(20), nullable=False, comment="EAN-13 или Code128 баркод"),
        sa.Column("name", sa.String(255), nullable=True, comment="Название товара"),
        sa.Column("article", sa.String(100), nullable=True, comment="Артикул"),
        sa.Column("size", sa.String(50), nullable=True, comment="Размер"),
        sa.Column("color", sa.String(50), nullable=True, comment="Цвет"),
        sa.Column("composition", sa.String(255), nullable=True, comment="Состав изделия"),
        sa.Column("country", sa.String(100), nullable=True, comment="Страна производства"),
        sa.Column("brand", sa.String(100), nullable=True, comment="Бренд"),
        sa.Column(
            "last_serial_number",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="Последний использованный серийный номер",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания карточки",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего обновления",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "barcode", name="uq_user_barcode"),
    )

    # Создаём индексы для быстрого поиска
    op.create_index("ix_product_cards_user_id", "product_cards", ["user_id"])
    op.create_index("ix_product_cards_barcode", "product_cards", ["barcode"])


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index("ix_product_cards_barcode", table_name="product_cards")
    op.drop_index("ix_product_cards_user_id", table_name="product_cards")

    # Удаляем таблицу
    op.drop_table("product_cards")
