# Настройка Cron для уведомлений о неделях беременности

## Описание

Для автоматической проверки новых недель беременности и отправки уведомлений необходимо настроить регулярное выполнение команды Django.

## Настройка Cron

### 1. Ежедневная проверка в 9:00 утра

Добавьте следующую строку в crontab:

```bash
0 9 * * * /path/to/your/project/venv/bin/python /path/to/your/project/manage.py process_pregnancy_notifications
```

### 2. Проверка каждые 6 часов

Для более частой проверки:

```bash
0 */6 * * * /path/to/your/project/venv/bin/python /path/to/your/project/manage.py process_pregnancy_notifications
```

### 3. Тестовый запуск

Для тестирования без изменений в базе данных:

```bash
/path/to/your/project/venv/bin/python /path/to/your/project/manage.py process_pregnancy_notifications --dry-run --verbose
```

## Команды для управления

### Проверка для конкретного пользователя

```bash
python manage.py process_pregnancy_notifications --user username
```

### Подробный вывод

```bash
python manage.py process_pregnancy_notifications --verbose
```

### Тестовый режим

```bash
python manage.py process_pregnancy_notifications --dry-run
```

## Логирование

Рекомендуется настроить логирование для отслеживания работы системы уведомлений:

```bash
0 9 * * * /path/to/your/project/venv/bin/python /path/to/your/project/manage.py process_pregnancy_notifications >> /var/log/pregnancy_notifications.log 2>&1
```

## Мониторинг

Для мониторинга работы системы можно использовать следующие команды:

### Проверка статистики уведомлений

```python
from webapp.utils.notification_utils import get_notification_statistics
stats = get_notification_statistics()
print(f"Всего уведомлений: {stats['total']}")
print(f"Доставлено: {stats['delivery_rate']:.1f}%")
```

### Проверка активных беременностей

```python
from webapp.models import PregnancyInfo
active_count = PregnancyInfo.objects.filter(is_active=True).count()
print(f"Активных беременностей: {active_count}")
```

## Альтернативные решения

### Использование Celery

Если в проекте используется Celery, можно настроить периодические задачи:

```python
# В settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-pregnancy-weeks': {
        'task': 'webapp.tasks.process_pregnancy_notifications',
        'schedule': crontab(hour=9, minute=0),  # Каждый день в 9:00
    },
}
```

### Использование Django-crontab

Установите django-crontab и добавьте в settings.py:

```python
INSTALLED_APPS = [
    # ...
    'django_crontab',
]

CRONJOBS = [
    ('0 9 * * *', 'webapp.management.commands.process_pregnancy_notifications.Command'),
]
```

Затем выполните:

```bash
python manage.py crontab add
```