@echo off
setlocal enabledelayedexpansion

echo 🚀 Запуск Mom^&Baby Bot с SQLite...

REM Проверяем наличие .env файла
if not exist .env (
    echo 📝 Создание .env файла из примера...
    if exist env.sqlite.example (
        copy env.sqlite.example .env
        echo ✅ .env файл создан из env.sqlite.example
        echo ⚠️ Не забудьте настроить переменные окружения в .env файле!
    ) else (
        echo ❌ Файл env.sqlite.example не найден
        exit /b 1
    )
)

REM Проверяем готовность
echo 🧪 Проверка готовности...
python check_amvera_ready.py
if errorlevel 1 (
    echo ❌ Проверка готовности не прошла
    exit /b 1
)
echo ✅ Проверка готовности прошла успешно

REM Инициализируем базу данных
echo 🗄️ Инициализация SQLite базы данных...
python init_sqlite_amvera.py
if errorlevel 1 (
    echo ❌ Ошибка инициализации базы данных
    exit /b 1
)
echo ✅ База данных инициализирована

REM Применяем миграции
echo 📊 Применение миграций...
python manage.py migrate --noinput
if errorlevel 1 (
    echo ❌ Ошибка применения миграций
    exit /b 1
)
echo ✅ Миграции применены

REM Собираем статические файлы
echo 📁 Сбор статических файлов...
python manage.py collectstatic --noinput --clear
if errorlevel 1 (
    echo ⚠️ Предупреждение: проблемы со сбором статических файлов
) else (
    echo ✅ Статические файлы собраны
)

echo 🎉 Инициализация завершена!

REM Спрашиваем пользователя о режиме запуска
echo.
echo Выберите режим запуска:
echo 1) Development (Django runserver)
echo 2) Production (Docker Compose)
echo 3) Development Docker
echo 4) Только бот
set /p choice="Введите номер (1-4): "

if "%choice%"=="1" (
    echo 🚀 Запуск в режиме разработки...
    python manage.py runserver 0.0.0.0:8000
) else if "%choice%"=="2" (
    echo 🚀 Запуск в production режиме...
    docker-compose up -d
    echo ✅ Сервисы запущены в фоновом режиме
    echo 📊 Просмотр логов: docker-compose logs -f
    echo 🛑 Остановка: docker-compose down
) else if "%choice%"=="3" (
    echo 🚀 Запуск в development Docker режиме...
    docker-compose -f docker-compose.dev.yml up
) else if "%choice%"=="4" (
    echo 🤖 Запуск только бота...
    python manage.py run_bot
) else (
    echo ❌ Неверный выбор
    exit /b 1
) 