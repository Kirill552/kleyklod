# KleyKod Backend Dockerfile
# Multi-stage build для минимального размера образа

# ===== Stage 1: Builder =====
FROM python:3.11-slim as builder

WORKDIR /build

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libdmtx-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только файлы зависимостей
COPY pyproject.toml ./

# Устанавливаем uv для быстрой установки пакетов
RUN pip install --no-cache-dir uv

# Создаём виртуальное окружение и устанавливаем зависимости
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install .


# ===== Stage 2: Runtime =====
FROM python:3.11-slim as runtime

WORKDIR /app

# Установка runtime зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    libdmtx0b \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создаём non-root пользователя
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем код приложения
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup alembic.ini ./

# Создаём директорию для хранения генераций
RUN mkdir -p /app/data/generations && chown -R appuser:appgroup /app/data

# Переключаемся на non-root пользователя
USER appuser

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Порт
EXPOSE 8000

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
