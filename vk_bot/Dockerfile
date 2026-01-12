FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей
RUN pip install --no-cache-dir vk_api requests

# Создание non-root пользователя (безопасность)
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Копирование кода
COPY main.py .

# Смена владельца файлов
RUN chown -R appuser:appgroup /app

# Запуск от non-root пользователя
USER appuser

# Запуск бота
CMD ["python", "main.py"]
