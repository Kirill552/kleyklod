"""add_professional_template_fields

Revision ID: 0008
Revises: 0007
Create Date: 2025-12-31 12:00:00.000000

Добавляет поля реквизитов для профессионального шаблона этикеток:
- inn: ИНН организации
- organization_address: Адрес производства
- production_country: Страна производства
- certificate_number: Номер сертификата

Также обновляет preferred_layout со значения 'classic' на 'basic'
(переименование шаблонов: classic -> basic, centered -> professional)
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем новые поля для профессионального шаблона
    op.add_column(
        "users", sa.Column("inn", sa.String(12), nullable=True, comment="ИНН организации")
    )

    op.add_column(
        "users",
        sa.Column("organization_address", sa.Text(), nullable=True, comment="Адрес производства"),
    )

    op.add_column(
        "users",
        sa.Column(
            "production_country", sa.String(100), nullable=True, comment="Страна производства"
        ),
    )

    op.add_column(
        "users",
        sa.Column("certificate_number", sa.String(100), nullable=True, comment="Номер сертификата"),
    )

    # Обновляем существующие записи: classic -> basic, centered -> professional
    op.execute("UPDATE users SET preferred_layout = 'basic' WHERE preferred_layout = 'classic'")
    op.execute(
        "UPDATE users SET preferred_layout = 'professional' WHERE preferred_layout = 'centered'"
    )

    # Меняем server_default для новых записей
    op.alter_column("users", "preferred_layout", server_default="basic")


def downgrade() -> None:
    # Обратное переименование
    op.execute("UPDATE users SET preferred_layout = 'classic' WHERE preferred_layout = 'basic'")
    op.execute(
        "UPDATE users SET preferred_layout = 'centered' WHERE preferred_layout = 'professional'"
    )

    op.alter_column("users", "preferred_layout", server_default="classic")

    op.drop_column("users", "certificate_number")
    op.drop_column("users", "production_country")
    op.drop_column("users", "organization_address")
    op.drop_column("users", "inn")
