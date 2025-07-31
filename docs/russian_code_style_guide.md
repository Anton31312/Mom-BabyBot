# Руководство по стилю кода на русском языке

## Общие принципы

Все комментарии в коде должны быть написаны на русском языке для обеспечения единообразия и лучшего понимания кода русскоязычными разработчиками.

## Правила для комментариев

### 1. Комментарии к функциям и классам

```python
def calculate_pregnancy_week(due_date):
    """
    Вычисляет текущую неделю беременности на основе предполагаемой даты родов.
    
    Args:
        due_date (date): Предполагаемая дата родов
        
    Returns:
        int: Номер текущей недели беременности (1-42)
        
    Raises:
        ValueError: Если дата родов некорректна
    """
    pass
```

### 2. Однострочные комментарии

```python
# Проверяем валидность данных пользователя
if not user.is_valid():
    return False

# TODO: Добавить проверку прав доступа
# FIXME: Исправить проблему с кодировкой
# NOTE: Этот код требует рефакторинга
```

### 3. Комментарии к блокам кода

```python
# Инициализация переменных для расчета
start_date = datetime.now()
end_date = start_date + timedelta(days=280)

# Основной цикл обработки данных
for item in data_list:
    # Обработка каждого элемента
    process_item(item)
```

### 4. Комментарии в URL-маршрутах

```python
urlpatterns = [
    # Основные страницы
    path('', views.index, name='index'),
    path('pregnancy/', views.pregnancy, name='pregnancy'),
    
    # API эндпоинты для здоровья
    path('api/health/weight/', api_health.weight_records, name='weight_records'),
    path('api/health/pressure/', api_health.pressure_records, name='pressure_records'),
    
    # Административные страницы
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
```

### 5. Комментарии в тестах

```python
class TestWeightTracking(TestCase):
    """Тесты для отслеживания веса."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
    
    def test_weight_validation(self):
        """Тест валидации веса."""
        # Тест корректного веса
        weight = WeightRecord(user=self.user, weight=70.5)
        weight.full_clean()  # Не должно вызвать исключение
        
        # Тест отрицательного веса
        with self.assertRaises(ValidationError):
            weight = WeightRecord(user=self.user, weight=-10)
            weight.full_clean()
```

### 6. Комментарии к константам и настройкам

```python
# Максимальное количество попыток входа
MAX_LOGIN_ATTEMPTS = 3

# Время жизни сессии в секундах (24 часа)
SESSION_TIMEOUT = 24 * 60 * 60

# Поддерживаемые форматы файлов
ALLOWED_FILE_FORMATS = ['jpg', 'png', 'pdf']
```

### 7. Комментарии к сложной логике

```python
def calculate_feeding_statistics(sessions):
    """Вычисляет статистику кормления."""
    
    # Группируем сессии по дням для анализа
    daily_sessions = {}
    for session in sessions:
        day = session.start_time.date()
        if day not in daily_sessions:
            daily_sessions[day] = []
        daily_sessions[day].append(session)
    
    # Вычисляем среднее время кормления за день
    daily_averages = {}
    for day, day_sessions in daily_sessions.items():
        total_duration = sum(
            session.total_duration.total_seconds() 
            for session in day_sessions
        )
        daily_averages[day] = total_duration / len(day_sessions)
    
    return daily_averages
```

## Исключения

### Когда можно использовать английский язык:

1. **Технические термины без прямого перевода:**
   ```python
   # API endpoint для получения данных
   # JSON response с данными пользователя
   # HTTP status code 200
   ```

2. **Названия библиотек и фреймворков:**
   ```python
   # Используем Django ORM для запроса
   # Настройка Redis для кэширования
   ```

3. **Стандартные аббревиатуры:**
   ```python
   # CRUD операции для пользователей
   # REST API для мобильного приложения
   ```

## Рекомендации

1. **Будьте конкретными:** Комментарий должен объяснять "почему", а не "что"
2. **Избегайте очевидных комментариев:** `x = x + 1  # Увеличиваем x на 1` - плохо
3. **Обновляйте комментарии:** При изменении кода обновляйте соответствующие комментарии
4. **Используйте правильную грамматику:** Комментарии должны быть грамотными
5. **Соблюдайте единообразие:** Используйте одинаковый стиль во всем проекте

## Примеры переводов часто используемых фраз

| Английский | Русский |
|------------|---------|
| TODO: Fix this | TODO: Исправить это |
| FIXME: Bug in logic | FIXME: Ошибка в логике |
| NOTE: Important | ПРИМЕЧАНИЕ: Важно |
| WARNING: Deprecated | ВНИМАНИЕ: Устарело |
| API endpoint | API эндпоинт |
| Database query | Запрос к базе данных |
| User authentication | Аутентификация пользователя |
| Error handling | Обработка ошибок |
| Data validation | Валидация данных |
| Unit test | Модульный тест |
| Integration test | Интеграционный тест |
| Performance optimization | Оптимизация производительности |

## Заключение

Следование этому руководству поможет поддерживать код в читаемом и понятном состоянии для всех участников проекта. Помните, что хорошие комментарии - это инвестиция в будущее проекта.