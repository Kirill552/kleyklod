FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей
RUN pip install --no-cache-dir vk_api requests

# Копирование кода
COPY main.py .

# Запуск бота
CMD ["python", "main.py"]
