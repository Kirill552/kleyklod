"""
Конфигурация Celery для фоновых задач.

Celery используется для асинхронной обработки больших PDF файлов,
чтобы не блокировать веб-сервер во время генерации этикеток.
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

# Используем отдельные базы Redis для broker и backend
# db/0 — backend (rate limiter), db/1 — bot FSM, db/2 — GlitchTip
# db/3 — Celery broker, db/4 — Celery results
broker_url = settings.redis_url.replace("/0", "/3")
backend_url = settings.redis_url.replace("/0", "/4")

celery = Celery(
    "kleykod",
    broker=broker_url,
    backend=backend_url,
    include=["app.tasks.generate_labels"],
)

celery.conf.update(
    # Сериализация
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Результаты хранятся 24 часа
    result_expires=86400,
    # Prefetch = 1 для равномерного распределения задач
    worker_prefetch_multiplier=1,
    # Подтверждение после выполнения (задача вернётся в очередь если worker упадёт)
    task_acks_late=True,
    # Таймзона
    timezone="UTC",
    enable_utc=True,
    # Retry при потере соединения с брокером
    broker_connection_retry_on_startup=True,
)
