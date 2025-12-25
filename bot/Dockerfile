# KleyKod Telegram Bot Dockerfile

# ===== Stage 1: Builder =====
FROM python:3.11-slim as builder

WORKDIR /build

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

# Создаём non-root пользователя
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем код приложения
COPY --chown=appuser:appgroup bot/ ./bot/

# Переключаемся на non-root пользователя
USER appuser

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Запуск
CMD ["python", "-m", "bot.main"]
