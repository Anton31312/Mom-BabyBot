# Mom&BabyBot

Telegram бот для помощи мамам и будущим мамам, созданный с использованием aiogram и Flask.

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
- Flask 3.0.0 (веб-приложение)
- SQLAlchemy 2.0.23 (работа с базой данных)
- APScheduler 3.10.4 (планировщик задач)
- Flask-SQLAlchemy 3.1.1 (интеграция Flask и SQLAlchemy)
- Flask-Migrate 4.0.5 (миграции базы данных)
- Flask-CORS 4.0.0 (CORS для веб-приложения)

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
DATABASE_URL=sqlite:///app.db
FLASK_ENV=development
FLASK_APP=app.py
```

5. Инициализируйте базу данных:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Структура проекта

```
Mom&BabyBot/
├── app/
│   ├── __init__.py
│   ├── bot.py              # Основной файл бота
│   │   ├── __init__.py
│   │   └── config.py       # Конфигурация приложения
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py     # Обработчики команд
│   │   ├── conversation.py # Обработчики диалогов
│   │   └── web_app.py      # Обработчики веб-приложения
│   ├── keyboards/
│   │   ├── __init__.py
│   │   └── keyboards.py    # Клавиатуры бота
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py         # Модели данных
│   └── routes.py           # Маршруты Flask
├── migrations/             # Миграции базы данных
├── .env                    # Переменные окружения
├── .gitignore
├── app.py                 # Точка входа приложения
├── config.py              # Конфигурация
├── requirements.txt       # Зависимости проекта
└── README.md
```

## Запуск

1. Запустите приложение:
```bash
python app.py
```

2. Бот будет доступен в Telegram, а веб-интерфейс по адресу `http://localhost:5000`

## Основные команды бота

- `/start` - Начать опрос
- `/help` - Показать справку
- `/stats` - Показать статистику
- `/update` - Обновить данные

## Разработка

### Добавление новых функций

1. Создайте новый обработчик в директории `app/handlers/`
2. Зарегистрируйте обработчик в `app/bot.py`
3. При необходимости добавьте новые клавиатуры в `app/keyboards/keyboards.py`
4. Обновите модели данных в `app/models/` если требуется

### Работа с базой данных

1. Создайте новую миграцию:
```bash
flask db migrate -m "description"
```

2. Примените миграцию:
```bash
flask db upgrade
```

## Лицензия

MIT License. См. файл `LICENSE` для подробностей. 