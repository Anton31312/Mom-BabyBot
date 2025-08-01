#!/bin/bash

# Скрипт для быстрого запуска с SQLite
set -e

echo "🚀 Запуск Mom&Baby Bot с SQLite..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "📝 Создание .env файла из примера..."
    if [ -f env.sqlite.example ]; then
        cp env.sqlite.example .env
        echo "✅ .env файл создан из env.sqlite.example"
        echo "⚠️ Не забудьте настроить переменные окружения в .env файле!"
    else
        echo "❌ Файл env.sqlite.example не найден"
        exit 1
    fi
fi

# Проверяем готовность
echo "🧪 Проверка готовности..."
if python check_amvera_ready.py; then
    echo "✅ Проверка готовности прошла успешно"
else
    echo "❌ Проверка готовности не прошла"
    exit 1
fi

# Инициализируем базу данных
echo "🗄️ Инициализация SQLite базы данных..."
if python init_sqlite_amvera.py; then
    echo "✅ База данных инициализирована"
else
    echo "❌ Ошибка инициализации базы данных"
    exit 1
fi

# Применяем миграции
echo "📊 Применение миграций..."
if python manage.py migrate --noinput; then
    echo "✅ Миграции применены"
else
    echo "❌ Ошибка применения миграций"
    exit 1
fi

# Собираем статические файлы
echo "📁 Сбор статических файлов..."
if python manage.py collectstatic --noinput --clear; then
    echo "✅ Статические файлы собраны"
else
    echo "⚠️ Предупреждение: проблемы со сбором статических файлов"
fi

echo "🎉 Инициализация завершена!"

# Спрашиваем пользователя о режиме запуска
echo ""
echo "Выберите режим запуска:"
echo "1) Development (Django runserver)"
echo "2) Production (Docker Compose)"
echo "3) Development Docker"
echo "4) Только бот"
read -p "Введите номер (1-4): " choice

case $choice in
    1)
        echo "🚀 Запуск в режиме разработки..."
        python manage.py runserver 0.0.0.0:8000
        ;;
    2)
        echo "🚀 Запуск в production режиме..."
        docker-compose up -d
        echo "✅ Сервисы запущены в фоновом режиме"
        echo "📊 Просмотр логов: docker-compose logs -f"
        echo "🛑 Остановка: docker-compose down"
        ;;
    3)
        echo "🚀 Запуск в development Docker режиме..."
        docker-compose -f docker-compose.dev.yml up
        ;;
    4)
        echo "🤖 Запуск только бота..."
        python manage.py run_bot
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac 