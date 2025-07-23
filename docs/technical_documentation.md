# Техническая документация Mom&BabyBot

Этот документ содержит техническую информацию о приложении Mom&BabyBot, включая описание архитектуры, API и моделей данных.

## Архитектура приложения

### Общая архитектура

Mom&BabyBot представляет собой приложение, состоящее из нескольких компонентов:

1. **Django веб-приложение** - предоставляет веб-интерфейс и API
2. **Telegram бот** - интерфейс взаимодействия через Telegram
3. **База данных** - хранение данных пользователей и приложения
4. **Redis** - кэширование и очереди задач
5. **Nginx** - веб-сервер и прокси

```
+-------------+     +-------------+     +-------------+
|    Клиент   |---->|    Nginx    |---->|   Django    |
| (Браузер)   |<----|  (Прокси)   |<----|   (Веб)     |
+-------------+     +-------------+     +-------------+
                                              |
+-------------+     +-------------+           |
|   Клиент    |---->|  Telegram   |<----------+
| (Telegram)  |<----|    Бот      |           |
+-------------+     +-------------+           |
                                              v
                    +-------------+     +-------------+
                    |    Redis    |<--->|    База     |
                    | (Кэш/Очереди)|     |   данных    |
                    +-------------+     +-------------+
```

### Компоненты системы

#### Django веб-приложение

- **Фреймворк**: Django 4.2+
- **Основные приложения**:
  - `mom_baby_bot` - основной проект
  - `botapp` - приложение для работы с Telegram ботом
  - `webapp` - приложение для веб-интерфейса

#### Telegram бот

- **Фреймворк**: aiogram 3.3.0
- **Режим работы**: webhook (для продакшена) или polling (для разработки)
- **Интеграция с Django**: через общую базу данных и API

#### База данных

- **Разработка**: SQLite
- **Продакшен**: PostgreSQL
- **ORM**: SQLAlchemy для моделей бота, Django ORM для веб-приложения

#### Кэширование

- **Система кэширования**: Redis
- **Типы кэшей**:
  - Кэш сессий
  - Кэш запросов
  - Кэш шаблонов

#### Веб-сервер

- **Сервер**: Nginx
- **WSGI-сервер**: Gunicorn
- **Статические файлы**: обслуживаются через Nginx с кэшированием

## Модели данных

### Основные модели

#### User (Пользователь)

```python
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(64))
    first_name = Column(String(64))
    last_name = Column(String(64))
    is_pregnant = Column(Boolean, default=False)
    pregnancy_week = Column(Integer)
    baby_birth_date = Column(DateTime)
    is_premium = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Child (Ребенок)

```python
class Child(Base):
    __tablename__ = 'children'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(64))
    birth_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Measurement (Измерение)

```python
class Measurement(Base):
    __tablename__ = 'measurements'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    height = Column(Float)  # в сантиметрах
    weight = Column(Float)  # в килограммах
    head_circumference = Column(Float)  # в сантиметрах
```

### Модели для отслеживания

#### Contraction (Схватка)

```python
class Contraction(Base):
    __tablename__ = 'contractions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
```

#### ContractionEvent (Событие схватки)

```python
class ContractionEvent(Base):
    __tablename__ = 'contraction_events'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('contractions.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
```

#### Kick (Шевеление)

```python
class Kick(Base):
    __tablename__ = 'kicks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
```

#### KickEvent (Событие шевеления)

```python
class KickEvent(Base):
    __tablename__ = 'kick_events'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('kicks.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
```

#### SleepSession (Сессия сна)

```python
class SleepSession(Base):
    __tablename__ = 'sleep_sessions'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    type = Column(String(10))  # 'day' или 'night'
```

#### FeedingSession (Сессия кормления)

```python
class FeedingSession(Base):
    __tablename__ = 'feeding_sessions'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    type = Column(String(10))  # 'breast' или 'bottle'
    amount = Column(Float)  # в мл, только для бутылочки
    duration = Column(Integer)  # в минутах, только для груди
    breast = Column(String(5))  # 'left', 'right' или 'both', только для груди
    notes = Column(String(255))
```

#### Vaccine (Вакцина)

```python
class Vaccine(Base):
    __tablename__ = 'vaccines'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    recommended_age = Column(String(64))  # например, "2 месяца", "1 год"
    is_mandatory = Column(Boolean, default=False)
```

#### ChildVaccine (Вакцина ребенка)

```python
class ChildVaccine(Base):
    __tablename__ = 'child_vaccines'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    vaccine_id = Column(Integer, ForeignKey('vaccines.id'), nullable=False)
    date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    notes = Column(String(255))
```

## API документация

### Аутентификация

Все API-запросы требуют аутентификации. Используется токен-аутентификация:

```
Authorization: Token <token>
```

### Формат ответа

Все ответы возвращаются в формате JSON. Успешные ответы имеют статус 200 OK и содержат данные в поле `data`. Ошибки имеют соответствующий HTTP-статус и содержат информацию об ошибке в поле `error`.

### Пользовательские данные

#### Получение данных пользователя

```
GET /api/user/{user_id}/
```

**Ответ:**

```json
{
  "data": {
    "id": 1,
    "telegram_id": 123456789,
    "username": "username",
    "first_name": "First",
    "last_name": "Last",
    "is_pregnant": true,
    "pregnancy_week": 20,
    "baby_birth_date": null,
    "is_premium": false,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
}
```

#### Обновление данных пользователя

```
PUT /api/user/{user_id}/
```

**Тело запроса:**

```json
{
  "is_pregnant": true,
  "pregnancy_week": 21
}
```

**Ответ:**

```json
{
  "data": {
    "id": 1,
    "telegram_id": 123456789,
    "username": "username",
    "first_name": "First",
    "last_name": "Last",
    "is_pregnant": true,
    "pregnancy_week": 21,
    "baby_birth_date": null,
    "is_premium": false,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T01:00:00Z"
  }
}
```

### Профили детей

#### Получение списка детей пользователя

```
GET /api/user/{user_id}/children/
```

**Ответ:**

```json
{
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "name": "Child 1",
      "birth_date": "2022-01-01T00:00:00Z",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "user_id": 1,
      "name": "Child 2",
      "birth_date": "2023-01-01T00:00:00Z",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

#### Создание нового профиля ребенка

```
POST /api/user/{user_id}/children/
```

**Тело запроса:**

```json
{
  "name": "Child 3",
  "birth_date": "2023-06-01T00:00:00Z"
}
```

**Ответ:**

```json
{
  "data": {
    "id": 3,
    "user_id": 1,
    "name": "Child 3",
    "birth_date": "2023-06-01T00:00:00Z",
    "created_at": "2023-06-10T00:00:00Z",
    "updated_at": "2023-06-10T00:00:00Z"
  }
}
```

#### Получение данных конкретного ребенка

```
GET /api/user/{user_id}/children/{child_id}/
```

**Ответ:**

```json
{
  "data": {
    "id": 1,
    "user_id": 1,
    "name": "Child 1",
    "birth_date": "2022-01-01T00:00:00Z",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z",
    "measurements": [
      {
        "id": 1,
        "child_id": 1,
        "date": "2023-01-01T00:00:00Z",
        "height": 50.0,
        "weight": 3.5,
        "head_circumference": 35.0
      }
    ]
  }
}
```

#### Обновление данных ребенка

```
PUT /api/user/{user_id}/children/{child_id}/
```

**Тело запроса:**

```json
{
  "name": "Updated Name"
}
```

**Ответ:**

```json
{
  "data": {
    "id": 1,
    "user_id": 1,
    "name": "Updated Name",
    "birth_date": "2022-01-01T00:00:00Z",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-06-10T00:00:00Z"
  }
}
```

#### Удаление профиля ребенка

```
DELETE /api/user/{user_id}/children/{child_id}/
```

**Ответ:**

```json
{
  "data": {
    "message": "Child profile deleted successfully"
  }
}
```

### Измерения

#### Получение измерений ребенка

```
GET /api/user/{user_id}/children/{child_id}/measurements/
```

**Ответ:**

```json
{
  "data": [
    {
      "id": 1,
      "child_id": 1,
      "date": "2023-01-01T00:00:00Z",
      "height": 50.0,
      "weight": 3.5,
      "head_circumference": 35.0
    },
    {
      "id": 2,
      "child_id": 1,
      "date": "2023-02-01T00:00:00Z",
      "height": 52.0,
      "weight": 4.0,
      "head_circumference": 36.0
    }
  ]
}
```

#### Добавление нового измерения

```
POST /api/user/{user_id}/children/{child_id}/measurements/
```

**Тело запроса:**

```json
{
  "date": "2023-03-01T00:00:00Z",
  "height": 54.0,
  "weight": 4.5,
  "head_circumference": 37.0
}
```

**Ответ:**

```json
{
  "data": {
    "id": 3,
    "child_id": 1,
    "date": "2023-03-01T00:00:00Z",
    "height": 54.0,
    "weight": 4.5,
    "head_circumference": 37.0
  }
}
```

### Счетчики и таймеры

#### Получение истории схваток

```
GET /api/user/{user_id}/contractions/
```

**Ответ:**

```json
{
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "start_time": "2023-06-01T10:00:00Z",
      "end_time": "2023-06-01T12:00:00Z",
      "contraction_events": [
        {
          "id": 1,
          "session_id": 1,
          "timestamp": "2023-06-01T10:05:00Z"
        },
        {
          "id": 2,
          "session_id": 1,
          "timestamp": "2023-06-01T10:15:00Z"
        }
      ]
    }
  ]
}
```

#### Запись новой сессии схваток

```
POST /api/user/{user_id}/contractions/
```

**Тело запроса:**

```json
{
  "start_time": "2023-06-10T10:00:00Z",
  "contraction_events": [
    {
      "timestamp": "2023-06-10T10:05:00Z"
    },
    {
      "timestamp": "2023-06-10T10:15:00Z"
    }
  ]
}
```

**Ответ:**

```json
{
  "data": {
    "id": 2,
    "user_id": 1,
    "start_time": "2023-06-10T10:00:00Z",
    "end_time": null,
    "contraction_events": [
      {
        "id": 3,
        "session_id": 2,
        "timestamp": "2023-06-10T10:05:00Z"
      },
      {
        "id": 4,
        "session_id": 2,
        "timestamp": "2023-06-10T10:15:00Z"
      }
    ]
  }
}
```

#### Получение истории шевелений

```
GET /api/user/{user_id}/kicks/
```

**Ответ:**

```json
{
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "start_time": "2023-06-01T10:00:00Z",
      "end_time": "2023-06-01T11:00:00Z",
      "kick_events": [
        {
          "id": 1,
          "session_id": 1,
          "timestamp": "2023-06-01T10:05:00Z"
        },
        {
          "id": 2,
          "session_id": 1,
          "timestamp": "2023-06-01T10:10:00Z"
        }
      ]
    }
  ]
}
```

#### Запись новой сессии шевелений

```
POST /api/user/{user_id}/kicks/
```

**Тело запроса:**

```json
{
  "start_time": "2023-06-10T10:00:00Z",
  "kick_events": [
    {
      "timestamp": "2023-06-10T10:05:00Z"
    },
    {
      "timestamp": "2023-06-10T10:10:00Z"
    }
  ]
}
```

**Ответ:**

```json
{
  "data": {
    "id": 2,
    "user_id": 1,
    "start_time": "2023-06-10T10:00:00Z",
    "end_time": null,
    "kick_events": [
      {
        "id": 3,
        "session_id": 2,
        "timestamp": "2023-06-10T10:05:00Z"
      },
      {
        "id": 4,
        "session_id": 2,
        "timestamp": "2023-06-10T10:10:00Z"
      }
    ]
  }
}
```

#### Получение истории сна

```
GET /api/user/{user_id}/children/{child_id}/sleep/
```

**Ответ:**

```json
{
  "data": [
    {
      "id": 1,
      "child_id": 1,
      "start_time": "2023-06-01T20:00:00Z",
      "end_time": "2023-06-02T06:00:00Z",
      "type": "night"
    },
    {
      "id": 2,
      "child_id": 1,
      "start_time": "2023-06-02T13:00:00Z",
      "end_time": "2023-06-02T15:00:00Z",
      "type": "day"
    }
  ]
}
```

#### Запись новой сессии сна

```
POST /api/user/{user_id}/children/{child_id}/sleep/
```

**Тело запроса:**

```json
{
  "start_time": "2023-06-10T20:00:00Z",
  "end_time": "2023-06-11T06:00:00Z",
  "type": "night"
}
```

**Ответ:**

```json
{
  "data": {
    "id": 3,
    "child_id": 1,
    "start_time": "2023-06-10T20:00:00Z",
    "end_time": "2023-06-11T06:00:00Z",
    "type": "night"
  }
}
```

#### Получение истории кормления

```
GET /api/user/{user_id}/children/{child_id}/feeding/
```

**Ответ:**

```json
{
  "data": [
    {
      "id": 1,
      "child_id": 1,
      "timestamp": "2023-06-01T08:00:00Z",
      "type": "breast",
      "duration": 15,
      "breast": "left",
      "amount": null,
      "notes": ""
    },
    {
      "id": 2,
      "child_id": 1,
      "timestamp": "2023-06-01T12:00:00Z",
      "type": "bottle",
      "duration": null,
      "breast": null,
      "amount": 120.0,
      "notes": "Formula"
    }
  ]
}
```

#### Запись новой сессии кормления

```
POST /api/user/{user_id}/children/{child_id}/feeding/
```

**Тело запроса:**

```json
{
  "timestamp": "2023-06-10T08:00:00Z",
  "type": "breast",
  "duration": 20,
  "breast": "right",
  "notes": "Good feeding"
}
```

**Ответ:**

```json
{
  "data": {
    "id": 3,
    "child_id": 1,
    "timestamp": "2023-06-10T08:00:00Z",
    "type": "breast",
    "duration": 20,
    "breast": "right",
    "amount": null,
    "notes": "Good feeding"
  }
}
```

### Прививки

#### Получение списка всех рекомендуемых прививок

```
GET /api/vaccines/
```

**Ответ:**

```json
{
  "data": [
    {
      "id": 1,
      "name": "БЦЖ",
      "description": "Вакцина против туберкулеза",
      "recommended_age": "3-7 дней",
      "is_mandatory": true
    },
    {
      "id": 2,
      "name": "Гепатит B",
      "description": "Вакцина против гепатита B",
      "recommended_age": "0-12 часов",
      "is_mandatory": true
    }
  ]
}
```

#### Получение прививок ребенка

```
GET /api/user/{user_id}/children/{child_id}/vaccines/
```

**Ответ:**

```json
{
  "data": [
    {
      "id": 1,
      "child_id": 1,
      "vaccine_id": 1,
      "vaccine_name": "БЦЖ",
      "date": "2023-01-05T00:00:00Z",
      "is_completed": true,
      "notes": ""
    },
    {
      "id": 2,
      "child_id": 1,
      "vaccine_id": 2,
      "vaccine_name": "Гепатит B",
      "date": "2023-01-01T00:00:00Z",
      "is_completed": true,
      "notes": ""
    }
  ]
}
```

#### Запись сделанной прививки

```
POST /api/user/{user_id}/children/{child_id}/vaccines/
```

**Тело запроса:**

```json
{
  "vaccine_id": 3,
  "date": "2023-03-01T00:00:00Z",
  "is_completed": true,
  "notes": "Реакция отсутствует"
}
```

**Ответ:**

```json
{
  "data": {
    "id": 3,
    "child_id": 1,
    "vaccine_id": 3,
    "vaccine_name": "АКДС",
    "date": "2023-03-01T00:00:00Z",
    "is_completed": true,
    "notes": "Реакция отсутствует"
  }
}
```

## Интеграция с Telegram ботом

### Webhook

Telegram бот использует webhook для получения обновлений от Telegram API. Webhook настраивается при запуске бота:

```python
await bot.set_webhook(url=WEBHOOK_URL)
```

### Обработка обновлений

Обновления от Telegram API обрабатываются через Django view:

```python
@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        update = Update.model_validate_json(request.body.decode('utf-8'))
        asyncio.run(dp.feed_update(bot=bot, update=update))
        return HttpResponse('OK')
    return HttpResponse('Method not allowed')
```

### Интеграция с веб-приложением

Telegram бот и веб-приложение интегрированы через общую базу данных и API. Бот может отправлять уведомления пользователям о событиях, происходящих в веб-приложении, и наоборот.

## Оптимизация производительности

### Оптимизация статических файлов

Для оптимизации статических файлов используется скрипт `optimize_static.py`, который выполняет:

1. Минификацию CSS и JavaScript файлов
2. Оптимизацию изображений
3. Создание сжатых версий файлов (gzip и brotli)

### Кэширование

Для улучшения производительности используется многоуровневое кэширование:

1. **Кэширование на уровне базы данных**:
   - Кэширование запросов
   - Оптимизация запросов через индексы

2. **Кэширование на уровне приложения**:
   - Кэширование шаблонов
   - Кэширование результатов API-запросов

3. **Кэширование на уровне веб-сервера**:
   - Кэширование статических файлов
   - Кэширование ответов API

### Оптимизация запросов к базе данных

Для оптимизации запросов к базе данных используется:

1. **Индексы** для часто используемых полей
2. **Ленивая загрузка** для связанных объектов
3. **Пакетная загрузка** для связанных объектов
4. **Кэширование запросов** для часто используемых данных

## Безопасность

### Аутентификация и авторизация

1. **Аутентификация пользователей**:
   - Через Telegram для бота
   - Через токены для API

2. **Авторизация**:
   - Проверка прав доступа к ресурсам
   - Ограничение доступа к данным других пользователей

### Защита от атак

1. **CSRF-защита** для веб-форм
2. **XSS-защита** через экранирование вывода
3. **SQL-инъекции** предотвращаются через ORM
4. **Rate limiting** для API-запросов

### Безопасность данных

1. **Шифрование данных** при передаче через HTTPS
2. **Безопасное хранение паролей** с использованием хэширования
3. **Регулярное резервное копирование** данных

## Тестирование

### Модульные тесты

Модульные тесты проверяют отдельные компоненты системы:

```bash
python run_model_tests.py
```

### Интеграционные тесты

Интеграционные тесты проверяют взаимодействие между компонентами:

```bash
python run_integration_tests.py
```

### UI-тесты

UI-тесты проверяют пользовательский интерфейс:

```bash
python run_ui_tests.py
```

### Комплексные тесты

Комплексные тесты проверяют всю систему в целом:

```bash
python run_comprehensive_ui_tests.py
```