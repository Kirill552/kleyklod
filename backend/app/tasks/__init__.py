"""
Фоновые задачи приложения.

Модуль содержит:
- cleanup: очистка истекших генераций
- generate_labels: Celery задачи для фоновой генерации этикеток
"""

from app.tasks.cleanup import cleanup_expired_generations, start_cleanup_loop

__all__ = ["cleanup_expired_generations", "start_cleanup_loop"]
