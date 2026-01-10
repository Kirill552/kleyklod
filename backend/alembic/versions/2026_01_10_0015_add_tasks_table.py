"""add_tasks_table

Revision ID: 0015
Revises: 4ba2d2f1c10b
Create Date: 2026-01-10 12:00:00.000000

Добавляет таблицу tasks для фоновых задач генерации этикеток.
Используется для асинхронной обработки больших PDF через Celery.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0015"
down_revision = "4ba2d2f1c10b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаём enum для статусов задач
    task_status = postgresql.ENUM(
        "pending", "processing", "completed", "failed", name="taskstatus", create_type=False
    )
    task_status.create(op.get_bind(), checkfirst=True)

    # Создаём таблицу tasks
    op.create_table(
        "tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Владелец задачи",
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", name="taskstatus"),
            nullable=False,
            server_default="pending",
            comment="Статус: pending, processing, completed, failed",
        ),
        sa.Column(
            "progress",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Прогресс выполнения в процентах",
        ),
        sa.Column(
            "result_path",
            sa.String(500),
            nullable=True,
            comment="Путь к готовому PDF файлу",
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="Сообщение об ошибке",
        ),
        sa.Column(
            "total_pages",
            sa.Integer(),
            nullable=True,
            comment="Общее количество страниц для обработки",
        ),
        sa.Column(
            "labels_count",
            sa.Integer(),
            nullable=True,
            comment="Количество этикеток в результате",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Время создания задачи",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Время начала обработки",
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Время завершения",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Время удаления результата (TTL 24ч)",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Создаём индексы
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_user_id", table_name="tasks")

    # Удаляем таблицу
    op.drop_table("tasks")

    # Удаляем enum
    op.execute("DROP TYPE IF EXISTS taskstatus")
