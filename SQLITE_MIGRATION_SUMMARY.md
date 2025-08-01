# Миграция на SQLite - Резюме изменений

## Что было изменено

### 1. Docker Compose файлы

#### `docker-compose.yml` (Production)
- ❌ Удален сервис `db` (PostgreSQL)
- ✅ Добавлен volume `sqlite_data` для SQLite
- ✅ Обновлены команды запуска с инициализацией SQLite
- ✅ Уменьшено количество workers с 3 до 2 (оптимизация для SQLite)

#### `docker-compose.dev.yml` (Development)
- ✅ Новый файл для упрощенной разработки
- ✅ Без Redis и Nginx
- ✅ Hot reload для разработки
- ✅ Монтирование кода в контейнер

### 2. Переменные окружения

#### `env.sqlite.example`
- ✅ Пример файла с переменными для SQLite
- ✅ Убраны переменные PostgreSQL
- ✅ Добавлены переменные для SQLite

### 3. Скрипты запуска

#### `start_sqlite.sh` (Linux/Mac)
- ✅ Автоматическая инициализация
- ✅ Проверка готовности
- ✅ Выбор режима запуска

#### `start_sqlite.bat` (Windows)
- ✅ Аналог для Windows
- ✅ Те же функции что и в .sh версии

### 4. Документация

#### `DOCKER_SQLITE_README.md`
- ✅ Подробные инструкции по использованию
- ✅ Команды для мониторинга
- ✅ Устранение проблем
- ✅ Примеры использования

## Преимущества SQLite

### 🚀 Простота развертывания
- Не требует отдельного сервера БД
- Меньше зависимостей
- Проще настройка

### 💾 Эффективность
- Меньше потребление ресурсов
- Быстрее запуск
- Проще backup

### 🔧 Разработка
- Легче тестирование
- Проще отладка
- Меньше конфигурации

## Как использовать

### Быстрый запуск
```bash
# Linux/Mac
./start_sqlite.sh

# Windows
start_sqlite.bat
```

### Docker Compose
```bash
# Production
docker-compose up -d

# Development
docker-compose -f docker-compose.dev.yml up
```

### Ручная настройка
```bash
# 1. Скопируйте переменные окружения
cp env.sqlite.example .env

# 2. Настройте .env файл
# 3. Инициализируйте базу данных
python init_sqlite_amvera.py

# 4. Примените миграции
python manage.py migrate

# 5. Запустите
python manage.py runserver
```

## Переменные окружения

### Обязательные
- `SECRET_KEY` - секретный ключ Django
- `TELEGRAM_BOT_TOKEN` - токен бота

### Опциональные
- `WEBHOOK_URL` - URL webhook
- `WEBAPP_URL` - URL приложения
- `ADMIN_IDS` - ID администраторов

## База данных

### Расположение
- Файл: `/app/data/mom_baby_bot.db`
- Volume: `sqlite_data`

### Инициализация
- Автоматическая при запуске
- Скрипт: `init_sqlite_amvera.py`
- Проверка: `check_amvera_ready.py`

## Мониторинг

### Логи
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f web
```

### Состояние
```bash
docker-compose ps
docker stats
```

## Backup

### Резервное копирование
```bash
# В контейнере
docker-compose exec web sqlite3 /app/data/mom_baby_bot.db ".backup /app/backup/backup.db"

# Локально
sqlite3 /app/data/mom_baby_bot.db ".backup backup.db"
```

## Устранение проблем

### База данных не создается
```bash
# Проверьте права доступа
docker-compose exec web ls -la /app/data

# Пересоздайте volume
docker-compose down -v
docker-compose up -d
```

### Миграции не применяются
```bash
# Принудительное применение
docker-compose exec web python manage.py migrate --run-syncdb
```

## Результат

✅ **Упрощенное развертывание** - меньше зависимостей
✅ **Быстрый запуск** - не нужен отдельный сервер БД
✅ **Простота разработки** - легче тестирование и отладка
✅ **Эффективность** - меньше потребление ресурсов
✅ **Надежность** - SQLite очень стабильная БД

## Следующие шаги

1. Настройте переменные окружения в `.env`
2. Запустите `start_sqlite.sh` или `start_sqlite.bat`
3. Проверьте работу приложения
4. Настройте backup если нужно
5. Разверните на продакшене 