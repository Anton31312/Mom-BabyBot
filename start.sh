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

# Проверяем доступность SQLite базы данных
echo "🗄️ Проверка SQLite базы данных..."
python -c "
import os
import sqlite3

db_path = '/app/data/mom_baby_bot.db'
db_dir = os.path.dirname(db_path)

# Создаем директорию если не существует
if not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)
    print(f'✅ Создана директория: {db_dir}')

# Проверяем доступность SQLite
try:
    conn = sqlite3.connect(db_path, timeout=10)
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    conn.close()
    print('✅ SQLite база данных доступна!')
except Exception as e:
    print(f'⚠️ Проблема с SQLite: {e}')
    print('🔧 Создаем новую базу данных...')
    try:
        conn = sqlite3.connect(db_path)
        conn.close()
        print('✅ SQLite база данных создана!')
    except Exception as e2:
        print(f'❌ Не удалось создать SQLite базу: {e2}')
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

# Инициализируем SQLite базу данных
echo "🗄️ Полная инициализация SQLite базы данных..."
if python init_sqlite.py; then
    echo "✅ SQLite база данных полностью инициализирована"
else
    echo "⚠️ Предупреждение: проблемы с инициализацией SQLite"
    echo "🔄 Пытаемся базовую инициализацию..."
    python manage.py init_sqlalchemy || echo "⚠️ Базовая инициализация также не удалась"
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