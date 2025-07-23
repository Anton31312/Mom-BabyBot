# Руководство по развертыванию Mom&BabyBot

Это руководство описывает процесс развертывания приложения Mom&BabyBot в продакшен-среде с использованием Docker и Docker Compose.

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- Доменное имя с настроенными DNS-записями
- SSL-сертификаты (можно использовать Let's Encrypt)

## Подготовка к развертыванию

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/Mom-BabyBot.git
cd Mom-BabyBot
```

### 2. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте файл `.env` и укажите следующие параметры:

```env
# Django settings
DEBUG=False
SECRET_KEY=your-secure-secret-key-here
ALLOWED_HOSTS=example.com,www.example.com,localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=mom_baby_bot.settings_prod

# Database settings
DATABASE_URL=postgresql://mombabybot:secure-password-here@db:5432/mombabybot
DB_NAME=mombabybot
DB_USER=mombabybot
DB_PASSWORD=secure-password-here
DB_HOST=db
DB_PORT=5432

# Redis settings
REDIS_URL=redis://redis:6379/0

# Telegram Bot settings
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
WEBHOOK_URL=https://example.com/webhook
WEBAPP_URL=https://example.com
ADMIN_IDS=123456789,987654321

# Server settings
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO
BOT_LOG_LEVEL=INFO
DJANGO_LOG_LEVEL=INFO
```

### 3. Настройка SSL-сертификатов

Создайте директорию для SSL-сертификатов:

```bash
mkdir -p nginx/ssl
```

Поместите ваши SSL-сертификаты в директорию `nginx/ssl`:
- `cert.pem` - сертификат
- `key.pem` - приватный ключ

Если у вас нет сертификатов, вы можете сгенерировать самоподписанные сертификаты для тестирования:

```bash
python generate_ssl_certs.py
```

### 4. Настройка Nginx

Проверьте и при необходимости отредактируйте конфигурационные файлы Nginx:

- `nginx/conf.d/app.conf` - основная конфигурация
- `nginx/conf.d/cache.conf` - настройки кэширования

Замените `server_name localhost;` на ваше доменное имя в файле `nginx/conf.d/app.conf`.

## Развертывание приложения

### 1. Сборка и запуск контейнеров

```bash
docker-compose build
docker-compose up -d
```

### 2. Проверка статуса контейнеров

```bash
docker-compose ps
```

Убедитесь, что все контейнеры запущены и работают корректно.

### 3. Инициализация базы данных

```bash
docker-compose exec web python init_db.py
```

### 4. Создание суперпользователя Django

```bash
docker-compose exec web python manage.py createsuperuser
```

## Обновление приложения

### 1. Получение последних изменений

```bash
git pull origin main
```

### 2. Пересборка и перезапуск контейнеров

```bash
docker-compose build
docker-compose down
docker-compose up -d
```

### 3. Применение миграций

```bash
docker-compose exec web python manage.py migrate
```

## Мониторинг и обслуживание

### Просмотр логов

```bash
# Логи всех контейнеров
docker-compose logs

# Логи конкретного контейнера
docker-compose logs web
docker-compose logs bot
docker-compose logs nginx
```

### Резервное копирование базы данных

```bash
docker-compose exec db pg_dump -U mombabybot mombabybot > backup_$(date +%Y%m%d).sql
```

### Восстановление базы данных из резервной копии

```bash
cat backup_YYYYMMDD.sql | docker-compose exec -T db psql -U mombabybot mombabybot
```

## Оптимизация производительности

### Оптимизация статических файлов

Перед развертыванием рекомендуется оптимизировать статические файлы:

```bash
python optimize_static.py
```

Этот скрипт выполняет:
- Минификацию CSS и JavaScript файлов
- Оптимизацию изображений
- Создание сжатых версий файлов (gzip и brotli)

### Настройка кэширования

В продакшен-среде используется Redis для кэширования:
- Кэширование сессий
- Кэширование запросов к базе данных
- Кэширование шаблонов

Настройки кэширования можно изменить в файле `mom_baby_bot/settings_prod.py`.

## Устранение неполадок

### Проблемы с подключением к базе данных

1. Проверьте статус контейнера базы данных:
```bash
docker-compose ps db
```

2. Проверьте логи базы данных:
```bash
docker-compose logs db
```

3. Убедитесь, что переменные окружения для подключения к базе данных указаны правильно в файле `.env`.

### Проблемы с Nginx

1. Проверьте статус контейнера Nginx:
```bash
docker-compose ps nginx
```

2. Проверьте логи Nginx:
```bash
docker-compose logs nginx
```

3. Проверьте конфигурацию Nginx:
```bash
docker-compose exec nginx nginx -t
```

### Проблемы с ботом

1. Проверьте статус контейнера бота:
```bash
docker-compose ps bot
```

2. Проверьте логи бота:
```bash
docker-compose logs bot
```

3. Убедитесь, что токен бота указан правильно в файле `.env`.

## Безопасность

- Регулярно обновляйте зависимости проекта
- Используйте сложные пароли для базы данных и административного доступа
- Настройте брандмауэр для ограничения доступа к серверу
- Регулярно создавайте резервные копии данных
- Используйте HTTPS для всех соединений