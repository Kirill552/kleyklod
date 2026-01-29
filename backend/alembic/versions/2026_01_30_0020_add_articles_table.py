"""add_articles_table

Revision ID: 0020
Revises: 0019
Create Date: 2026-01-30

Добавляет таблицу articles для SEO-статей и блога.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020"
down_revision: str | Sequence[str] | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создаёт таблицу articles."""
    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("keywords", sa.String(500), nullable=True),
        sa.Column("og_image", sa.String(300), nullable=True),
        sa.Column("canonical_url", sa.String(300), nullable=True),
        sa.Column("author", sa.String(100), server_default="KleyKod", nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("tags", sa.String(300), nullable=True),
        sa.Column("reading_time", sa.Integer(), server_default="5", nullable=False),
        sa.Column(
            "structured_data",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("is_published", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_articles_slug", "articles", ["slug"], unique=True)


def downgrade() -> None:
    """Удаляет таблицу articles."""
    op.drop_index("ix_articles_slug", table_name="articles")
    op.drop_table("articles")
