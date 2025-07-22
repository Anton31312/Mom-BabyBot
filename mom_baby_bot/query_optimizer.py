"""
Модуль оптимизации запросов к базе данных.

Этот модуль содержит функции и классы для оптимизации запросов к базе данных,
включая кэширование, пакетную загрузку и оптимизацию SQL-запросов.
"""

import logging
import time
import functools
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from sqlalchemy import event, inspect
from sqlalchemy.orm import joinedload, contains_eager, Load
from sqlalchemy.ext.baked import BakedQuery

logger = logging.getLogger(__name__)

# Константы для кэширования
CACHE_TIMEOUT = 60 * 60  # 1 час
CACHE_PREFIX = 'db_cache:'


class QueryOptimizer:
    """
    Класс для оптимизации запросов к базе данных.
    
    Предоставляет методы для кэширования результатов запросов,
    оптимизации загрузки связанных объектов и мониторинга производительности.
    """
    
    def __init__(self):
        """Инициализация оптимизатора запросов."""
        self.query_stats = {}
        self.slow_query_threshold = 0.5  # секунды
        
        # Инициализация мониторинга запросов
        self._setup_query_monitoring()
    
    def _setup_query_monitoring(self):
        """Настройка мониторинга запросов."""
        # Добавляем обработчик события before_cursor_execute
        event.listen(
            settings.SQLALCHEMY_ENGINE,
            'before_cursor_execute',
            self._before_cursor_execute
        )
        
        # Добавляем обработчик события after_cursor_execute
        event.listen(
            settings.SQLALCHEMY_ENGINE,
            'after_cursor_execute',
            self._after_cursor_execute
        )
    
    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """
        Обработчик события перед выполнением запроса.
        
        Сохраняет время начала выполнения запроса.
        """
        context._query_start_time = time.time()
    
    def _after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """
        Обработчик события после выполнения запроса.
        
        Вычисляет время выполнения запроса и логирует медленные запросы.
        """
        total_time = time.time() - context._query_start_time
        
        # Логируем медленные запросы
        if total_time > self.slow_query_threshold:
            logger.warning(
                f"Slow query detected ({total_time:.4f}s): {statement}"
            )
            
            # Сохраняем статистику по медленным запросам
            query_hash = hash(statement)
            if query_hash in self.query_stats:
                self.query_stats[query_hash]['count'] += 1
                self.query_stats[query_hash]['total_time'] += total_time
                self.query_stats[query_hash]['max_time'] = max(
                    self.query_stats[query_hash]['max_time'], total_time
                )
            else:
                self.query_stats[query_hash] = {
                    'query': statement,
                    'count': 1,
                    'total_time': total_time,
                    'max_time': total_time,
                    'first_seen': datetime.now()
                }
    
    def get_query_stats(self):
        """
        Получение статистики по запросам.
        
        Returns:
            dict: Статистика по запросам.
        """
        return self.query_stats
    
    def reset_query_stats(self):
        """Сброс статистики по запросам."""
        self.query_stats = {}
    
    def optimize_query(self, query, model_class, related_models=None):
        """
        Оптимизация запроса с загрузкой связанных объектов.
        
        Args:
            query: SQLAlchemy запрос.
            model_class: Класс модели.
            related_models: Список связанных моделей для загрузки.
            
        Returns:
            Оптимизированный запрос.
        """
        if related_models is None:
            related_models = []
        
        # Получаем информацию о модели
        mapper = inspect(model_class)
        relationships = mapper.relationships
        
        # Определяем отношения для загрузки
        for rel_name in related_models:
            if rel_name in relationships:
                # Используем joinedload для оптимизации загрузки связанных объектов
                query = query.options(joinedload(getattr(model_class, rel_name)))
        
        return query
    
    def get_or_create_cached_query(self, session, model_class, filters=None, related_models=None, cache_key=None, timeout=None):
        """
        Получение результата запроса из кэша или создание нового запроса.
        
        Args:
            session: SQLAlchemy сессия.
            model_class: Класс модели.
            filters: Словарь с фильтрами запроса.
            related_models: Список связанных моделей для загрузки.
            cache_key: Ключ кэша.
            timeout: Время жизни кэша в секундах.
            
        Returns:
            Результат запроса.
        """
        if filters is None:
            filters = {}
        
        if related_models is None:
            related_models = []
        
        if timeout is None:
            timeout = CACHE_TIMEOUT
        
        # Генерируем ключ кэша, если он не указан
        if cache_key is None:
            cache_key = self._generate_cache_key(model_class, filters, related_models)
        else:
            cache_key = f"{CACHE_PREFIX}{cache_key}"
        
        # Пытаемся получить результат из кэша
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Создаем запрос
        query = session.query(model_class)
        
        # Применяем фильтры
        for key, value in filters.items():
            query = query.filter(getattr(model_class, key) == value)
        
        # Оптимизируем запрос
        query = self.optimize_query(query, model_class, related_models)
        
        # Выполняем запрос
        result = query.all()
        
        # Сохраняем результат в кэш
        cache.set(cache_key, result, timeout)
        
        return result
    
    def invalidate_cache(self, model_class=None, filters=None, related_models=None, cache_key=None):
        """
        Инвалидация кэша для запроса.
        
        Args:
            model_class: Класс модели.
            filters: Словарь с фильтрами запроса.
            related_models: Список связанных моделей для загрузки.
            cache_key: Ключ кэша.
        """
        if cache_key is None and model_class is not None:
            cache_key = self._generate_cache_key(model_class, filters, related_models)
        
        if cache_key:
            cache_key = f"{CACHE_PREFIX}{cache_key}"
            cache.delete(cache_key)
    
    def _generate_cache_key(self, model_class, filters=None, related_models=None):
        """
        Генерация ключа кэша для запроса.
        
        Args:
            model_class: Класс модели.
            filters: Словарь с фильтрами запроса.
            related_models: Список связанных моделей для загрузки.
            
        Returns:
            str: Ключ кэша.
        """
        if filters is None:
            filters = {}
        
        if related_models is None:
            related_models = []
        
        # Создаем строковое представление фильтров
        filters_str = '_'.join(f"{k}:{v}" for k, v in sorted(filters.items()))
        
        # Создаем строковое представление связанных моделей
        related_str = '_'.join(sorted(related_models))
        
        # Генерируем ключ кэша
        return f"{CACHE_PREFIX}{model_class.__name__}_{filters_str}_{related_str}"


# Создаем глобальный экземпляр оптимизатора запросов
query_optimizer = QueryOptimizer()


def cached_query(timeout=CACHE_TIMEOUT, key_prefix=None):
    """
    Декоратор для кэширования результатов запросов.
    
    Args:
        timeout: Время жизни кэша в секундах.
        key_prefix: Префикс ключа кэша.
        
    Returns:
        Декорированная функция.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            if key_prefix:
                cache_key = f"{key_prefix}_{func.__name__}"
            else:
                cache_key = f"{CACHE_PREFIX}{func.__name__}"
            
            # Добавляем аргументы к ключу кэша
            arg_key = '_'.join(str(arg) for arg in args)
            kwarg_key = '_'.join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{cache_key}_{arg_key}_{kwarg_key}"
            
            # Пытаемся получить результат из кэша
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию
            result = func(*args, **kwargs)
            
            # Сохраняем результат в кэш
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def optimize_query_loading(query, model_class, related_models=None):
    """
    Оптимизация загрузки связанных объектов для запроса.
    
    Args:
        query: SQLAlchemy запрос.
        model_class: Класс модели.
        related_models: Список связанных моделей для загрузки.
        
    Returns:
        Оптимизированный запрос.
    """
    return query_optimizer.optimize_query(query, model_class, related_models)


def get_slow_queries():
    """
    Получение списка медленных запросов.
    
    Returns:
        dict: Статистика по медленным запросам.
    """
    return query_optimizer.get_query_stats()


def reset_query_stats():
    """Сброс статистики по запросам."""
    query_optimizer.reset_query_stats()


def analyze_query_performance(session, query, description=None):
    """
    Анализ производительности запроса.
    
    Args:
        session: SQLAlchemy сессия.
        query: SQLAlchemy запрос.
        description: Описание запроса.
        
    Returns:
        dict: Информация о производительности запроса.
    """
    start_time = time.time()
    result = query.all()
    end_time = time.time()
    
    execution_time = end_time - start_time
    
    # Логируем информацию о запросе
    if description:
        logger.info(f"Query '{description}' executed in {execution_time:.4f}s")
    else:
        logger.info(f"Query executed in {execution_time:.4f}s")
    
    # Возвращаем информацию о производительности
    return {
        'result': result,
        'execution_time': execution_time,
        'row_count': len(result)
    }


def batch_load_related(session, objects, relationship_name):
    """
    Пакетная загрузка связанных объектов.
    
    Args:
        session: SQLAlchemy сессия.
        objects: Список объектов.
        relationship_name: Имя связи.
        
    Returns:
        dict: Словарь связанных объектов.
    """
    if not objects:
        return {}
    
    # Получаем класс модели
    model_class = objects[0].__class__
    
    # Получаем информацию о связи
    mapper = inspect(model_class)
    relationship = mapper.relationships[relationship_name]
    
    # Получаем первичные ключи объектов
    primary_keys = [getattr(obj, mapper.primary_key[0].name) for obj in objects]
    
    # Получаем связанные объекты
    related_model = relationship.mapper.class_
    related_objects = session.query(related_model).filter(
        getattr(related_model, relationship.primaryjoin.right.name).in_(primary_keys)
    ).all()
    
    # Группируем связанные объекты по внешнему ключу
    result = {}
    for related_obj in related_objects:
        foreign_key = getattr(related_obj, relationship.primaryjoin.right.name)
        if foreign_key not in result:
            result[foreign_key] = []
        result[foreign_key].append(related_obj)
    
    return result