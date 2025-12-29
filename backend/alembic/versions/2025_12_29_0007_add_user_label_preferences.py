"""add_user_label_preferences

Revision ID: 2025_12_29_0007
Revises: 2025_12_29_0006
Create Date: 2025-12-29 12:00:00.000000

Добавляет поля настроек генерации этикеток в таблицу users:
- organization_name: Название организации
- preferred_layout: Выбранный layout (classic, compact, minimal)
- preferred_label_size: Размер этикетки (58x40, 58x30, 58x60)
- preferred_format: Формат (combined, separate)
- show_article, show_size_color, show_name: Какие поля показывать
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_12_29_0007'
down_revision = '2025_12_29_0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем поля настроек генерации этикеток
    op.add_column(
        'users',
        sa.Column(
            'organization_name',
            sa.String(255),
            nullable=True,
            comment='Название организации для этикеток'
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'preferred_layout',
            sa.String(20),
            nullable=False,
            server_default='classic',
            comment='Предпочитаемый layout этикетки'
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'preferred_label_size',
            sa.String(10),
            nullable=False,
            server_default='58x40',
            comment='Предпочитаемый размер этикетки'
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'preferred_format',
            sa.String(20),
            nullable=False,
            server_default='combined',
            comment='Предпочитаемый формат (combined/separate)'
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'show_article',
            sa.Boolean(),
            nullable=False,
            server_default='true',
            comment='Показывать артикул на этикетке'
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'show_size_color',
            sa.Boolean(),
            nullable=False,
            server_default='true',
            comment='Показывать размер/цвет на этикетке'
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'show_name',
            sa.Boolean(),
            nullable=False,
            server_default='true',
            comment='Показывать название товара на этикетке'
        )
    )


def downgrade() -> None:
    op.drop_column('users', 'show_name')
    op.drop_column('users', 'show_size_color')
    op.drop_column('users', 'show_article')
    op.drop_column('users', 'preferred_format')
    op.drop_column('users', 'preferred_label_size')
    op.drop_column('users', 'preferred_layout')
    op.drop_column('users', 'organization_name')
