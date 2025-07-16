# Mom&BabyBot

Telegram бот для помощи мамам и будущим мамам, созданный с использованием aiogram и Django.

## Возможности

- 📊 Отслеживание срока беременности
- 👶 Отслеживание возраста ребенка
- 💡 Полезные советы и рекомендации
- 📱 Веб-интерфейс для удобного управления
- 📈 Статистика использования бота
- 🔄 Автоматическое обновление данных

## Технологии

- Python 3.8+
- aiogram 3.3.0 (Telegram Bot API)
- Django 4.2+ (веб-приложение)
- SQLAlchemy 2.0.23 (работа с базой данных)
- APScheduler 3.10.4 (планировщик задач)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/Mom&BabyBot.git
cd Mom&BabyBot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` в корневой директории проекта и добавьте необходимые переменные окружения:
```env
TELEGRAM_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite:///mom_baby_bot.db
DJANGO_SECRET_KEY=your_django_secret_key
DEBUG=True
```

5. Выполните миграции Django и создайте таблицы SQLAlchemy:
```bash
python manage.py migrate
python init_db.py
```

6. Создайте суперпользователя для доступа к админ-панели Django:
```bash
python manage.py createsuperuser
```

## Структура проекта

```
mom_baby_bot/
├── manage.py               # Django управление
├── mom_baby_bot/           # Основной Django проект
│   ├── __init__.py
│   ├── settings.py         # Настройки Django
│   ├── urls.py             # Главные URL маршруты
│   ├── wsgi.py             # WSGI конфигурация
│   ├── asgi.py             # ASGI конфигурация
│   └── middleware.py       # Middleware для SQLAlchemy
├── botapp/                 # Django приложение для бота
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy модели
│   ├── admin.py            # Django админ конфигурация
│   ├── apps.py             # Конфигурация приложения
│   ├── handlers/           # Обработчики команд бота
│   │   ├── __init__.py
│   │   ├── commands.py     # Обработчики команд
│   │   ├── conversation.py # Обработчики диалогов
│   │   └── web_app.py      # Обработчики веб-приложения
│   ├── keyboards/          # Клавиатуры бота
│   │   ├── __init__.py
│   │   └── keyboards.py    # Клавиатуры бота
│   ├── management/         # Django команды
│   │   └── commands/
│   │       └── runbot.py   # Команда запуска бота
│   └── migrations/         # Django миграции
├── webapp/                 # Django приложение для веб-интерфейса
│   ├── __init__.py
│   ├── views.py            # Django представления
│   ├── urls.py             # URL маршруты веб-приложения
│   ├── admin.py            # Django админ
│   ├── apps.py             # Конфигурация приложения
│   ├── models.py           # Django модели (если нужны)
│   ├── templates/          # Django шаблоны
│   │   └── webapp/
│   │       └── index.html  # Главная страница
│   └── migrations/         # Django миграции
├── static/                 # Статические файлы
│   └── css/
├── .env                    # Переменные окружения
├── .gitignore
├── init_db.py             # Инициализация SQLAlchemy таблиц
├── requirements.txt       # Зависимости проекта
└── README.md
```

## Запуск

1. Запустите Django веб-сервер:
```bash
python manage.py runserver
```

2. В отдельном терминале запустите Telegram бота:
```bash
python manage.py runbot
```

3. Веб-интерфейс будет доступен по адресу `http://localhost:8000`
4. Админ-панель Django доступна по адресу `http://localhost:8000/admin/`

## Основные команды бота

- `/start` - Начать опрос
- `/help` - Показать справку
- `/stats` - Показать статистику
- `/update` - Обновить данные

## Разработка

### Добавление новых функций

#### Для веб-интерфейса:
1. Создайте новые Django views в `webapp/views.py`
2. Добавьте URL маршруты в `webapp/urls.py`
3. Создайте или обновите шаблоны в `webapp/templates/`
4. При необходимости обновите SQLAlchemy модели в `botapp/models.py`

#### Для Telegram бота:
1. Создайте новый обработчик в директории `botapp/handlers/`
2. Зарегистрируйте обработчик в Django management команде `botapp/management/commands/runbot.py`
3. При необходимости добавьте новые клавиатуры в `botapp/keyboards/keyboards.py`
4. Обновите SQLAlchemy модели в `botapp/models.py` если требуется

### Работа с базой данных

#### Django миграции:
1. Создайте новую Django миграцию:
```bash
python manage.py makemigrations
```

2. Примените Django миграции:
```bash
python manage.py migrate
```

#### SQLAlchemy модели:
1. После изменения SQLAlchemy моделей в `botapp/models.py`, обновите таблицы:
```bash
python init_db.py
```

### Полезные Django команды

1. Запуск интерактивной оболочки Django:
```bash
python manage.py shell
```

2. Сбор статических файлов:
```bash
python manage.py collectstatic
```

3. Проверка конфигурации проекта:
```bash
python manage.py check
```

4. Запуск тестов:
```bash
python manage.py test
```

## Лицензия

MIT License. См. файл `LICENSE` для подробностей. 