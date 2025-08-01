#!/bin/bash

# Скрипт запуска для Amvera
set -e

echo "🚀 Запуск Mom&Baby Bot на Amvera..."

# Проверяем готовность к запуску
echo "🧪 Проверка готовности..."
if python check_before_start.py; then
    echo "✅ Проверка готовности прошла успешно"
else
    echo "❌ Проверка готовности не прошла, но продолжаем..."
fi

# Ждем доступности базы данных
echo "⏳ Ожидание доступности базы данных..."
python -c "
import os
import time
import psycopg2
from urllib.parse import urlparse

max_attempts = 30
attempt = 0

database_url = os.getenv('DATABASE_URL', '')
if database_url:
    parsed = urlparse(database_url)
    while attempt < max_attempts:
        try:
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:] if parsed.path else 'postgres'
            )
            conn.close()
            print('✅ База данных доступна!')
            break
        except psycopg2.OperationalError:
            attempt += 1
            print(f'⏳ Попытка {attempt}/{max_attempts}: база данных недоступна, ждем...')
            time.sleep(2)
    else:
        print('❌ Не удалось подключиться к базе данных')
        exit(1)
else:
    print('⚠️ DATABASE_URL не установлен')
"

# Применяем миграции Django
echo "📊 Применение миграций Django..."
if python manage.py migrate --noinput; then
    echo "✅ Миграции Django применены успешно"
else
    echo "❌ Ошибка применения миграций Django"
    exit 1
fi

# Собираем статические файлы
echo "📁 Сборка статических файлов..."
if python manage.py collectstatic --noinput --clear; then
    echo "✅ Статические файлы собраны успешно"
else
    echo "⚠️ Предупреждение: не удалось собрать статические файлы"
fi

# Инициализируем SQLAlchemy базу данных
echo "🗄️ Инициализация SQLAlchemy базы данных..."
if python manage.py init_sqlalchemy; then
    echo "✅ SQLAlchemy инициализирована успешно"
else
    echo "⚠️ Предупреждение: не удалось инициализировать SQLAlchemy"
    echo "🔄 Пытаемся альтернативный способ..."
    python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
django.setup()

try:
    from botapp.models import Base
    from django.conf import settings
    Base.metadata.create_all(settings.SQLALCHEMY_ENGINE)
    print('✅ SQLAlchemy таблицы созданы альтернативным способом')
except Exception as e:
    print(f'⚠️ Альтернативный способ также не удался: {e}')
    print('🚀 Продолжаем запуск без SQLAlchemy...')
"
fi

echo "🎉 Инициализация завершена! Запуск приложения..."

# Запускаем Gunicorn
exec gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 120 \
    --keep-alive 5 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    mom_baby_bot.wsgi:application