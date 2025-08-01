# Используем Python 3.11 для лучшей производительности
FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=mom_baby_bot.settings_prod
ENV PORT=8000

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/staticfiles /app/media /app/logs /app/data

# Собираем статические файлы (только если есть статика)
RUN python manage.py collectstatic --noinput --clear || true

# Делаем startup скрипты исполняемыми
RUN chmod +x start.sh start_simple.sh

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Открываем порт (Amvera автоматически определяет порт из переменной PORT)
EXPOSE $PORT

# Healthcheck для мониторинга
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health/ || exit 1

# Запускаем приложение через startup скрипт
CMD ["./start.sh"]