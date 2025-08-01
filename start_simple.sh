#!/bin/bash

# Простой скрипт запуска для Amvera
echo "🚀 Запуск Mom&Baby Bot на Amvera (простая версия)..."

# Показываем переменные окружения
echo "📋 Переменные окружения:"
echo "PORT: ${PORT:-8000}"
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE}"
if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL: установлена (${#DATABASE_URL} символов)"
else
    echo "DATABASE_URL: НЕ УСТАНОВЛЕНА"
fi

# Применяем миграции Django (обязательно)
echo "📊 Применение миграций Django..."
python manage.py migrate --noinput || {
    echo "❌ Критическая ошибка: не удалось применить миграции"
    exit 1
}

# Собираем статические файлы (не критично)
echo "📁 Сборка статических файлов..."
python manage.py collectstatic --noinput --clear || {
    echo "⚠️ Предупреждение: не удалось собрать статические файлы"
}

# Проверяем работоспособность Django
echo "🔍 Проверка Django..."
python -c "
import django
from django.conf import settings
print('✅ Django настроен корректно')
print(f'DEBUG: {settings.DEBUG}')
print(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
" || {
    echo "❌ Критическая ошибка: Django не настроен"
    exit 1
}

echo "🎉 Инициализация завершена! Запуск Gunicorn..."

# Запускаем Gunicorn с упрощенными настройками
exec gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    mom_baby_bot.wsgi:application