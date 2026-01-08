"""add_code_usages_table

Revision ID: 0009
Revises: 0008
Create Date: 2026-01-03 12:00:00.000000

Добавляет таблицу code_usages для отслеживания использованных кодов маркировки.
Предотвращает повторное использование кодов ЧЗ (защита от штрафов).
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаём таблицу code_usages
    op.create_table(
        "code_usages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "code_hash", sa.String(64), nullable=False, comment="SHA-256 хеш кода маркировки"
        ),
        sa.Column("generation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Когда код был использован",
        ),
        sa.ForeignKeyConstraint(["generation_id"], ["generations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Создаём индексы
    op.create_index("ix_code_usages_user_id", "code_usages", ["user_id"])
    op.create_index("ix_code_usages_code_hash", "code_usages", ["code_hash"])
    op.create_index("ix_code_usages_used_at", "code_usages", ["used_at"])


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index("ix_code_usages_used_at", table_name="code_usages")
    op.drop_index("ix_code_usages_code_hash", table_name="code_usages")
    op.drop_index("ix_code_usages_user_id", table_name="code_usages")

    # Удаляем таблицу
    op.drop_table("code_usages")
