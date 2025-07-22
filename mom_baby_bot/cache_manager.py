"""
Модуль управления кэшированием данных.

Этот модуль содержит функции и классы для эффективного кэширования данных,
включая многоуровневое кэширование, инвалидацию кэша и стратегии кэширования.
"""

import logging
import hashlib
import json
import time
from functools import wraps
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Константы для кэширования
CACHE_TIMEOUT = getattr(settings, 'CACHE_TIMEOUT', 60 * 60)  # 1 час по умолчанию
CACHE_PREFIX = 'mom_baby_bot:'
CACHE_VERSION = '1'  # Увеличивайте при изменении структуры данных


class CacheManager:
    """
    Менеджер кэширования для приложения.
    
    Предоставляет методы для кэширования данных, инвалидации кэша
    и управления стратегиями кэширования.
    """
    
    def __init__(self):
        """Инициализация менеджера кэширования."""
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0
        }
        self.entity_dependencies = {
            'user': ['child', 'contraction', 'kick'],
            'child': ['measurement', 'sleep', 'feeding', 'vaccine'],
            'contraction': ['contraction_event'],
            'kick': ['kick_event']
        }
    
    def get_cache_key(self, prefix, *args, **kwargs):
        """
        Генерация ключа кэша.
        
        Args:
            prefix: Префикс ключа кэша.
            *args: Позиционные аргументы для включения в ключ.
            **kwargs: Именованные аргументы для включения в ключ.
            
        Returns:
            str: Ключ кэша.
        """
        # Создаем строковое представление аргументов
        args_str = '_'.join(str(arg) for arg in args)
        kwargs_str = '_'.join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        
        # Объединяем все части ключа
        key_parts = [CACHE_PREFIX, prefix]
        if args_str:
            key_parts.append(args_str)
        if kwargs_str:
            key_parts.append(kwargs_str)
        key_parts.append(CACHE_VERSION)
        
        # Объединяем части ключа
        key = ':'.join(key_parts)
        
        # Если ключ слишком длинный, используем хеш
        if len(key) > 250:
            # Создаем хеш ключа
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{CACHE_PREFIX}{prefix}:hash:{key_hash}:{CACHE_VERSION}"
        
        return key
    
    def get(self, key, default=None):
        """
        Получение данных из кэша.
        
        Args:
            key: Ключ кэша.
            default: Значение по умолчанию, если ключ не найден.
            
        Returns:
            Данные из кэша или значение по умолчанию.
        """
        value = cache.get(key, default)
        
        # Обновляем статистику
        if value is not default:
            self.cache_stats['hits'] += 1
            logger.debug(f"Cache hit: {key}")
        else:
            self.cache_stats['misses'] += 1
            logger.debug(f"Cache miss: {key}")
        
        return value
    
    def set(self, key, value, timeout=None):
        """
        Сохранение данных в кэш.
        
        Args:
            key: Ключ кэша.
            value: Данные для сохранения.
            timeout: Время жизни кэша в секундах.
        """
        if timeout is None:
            timeout = CACHE_TIMEOUT
        
        cache.set(key, value, timeout)
        
        # Обновляем статистику
        self.cache_stats['sets'] += 1
        logger.debug(f"Cache set: {key}")
    
    def delete(self, key):
        """
        Удаление данных из кэша.
        
        Args:
            key: Ключ кэша.
        """
        cache.delete(key)
        
        # Обновляем статистику
        self.cache_stats['invalidations'] += 1
        logger.debug(f"Cache invalidated: {key}")
    
    def invalidate_entity(self, entity_type, entity_id=None):
        """
        Инвалидация кэша для сущности и зависимых сущностей.
        
        Args:
            entity_type: Тип сущности.
            entity_id: ID сущности (опционально).
        """
        # Инвалидируем кэш для сущности
        if entity_id:
            key = self.get_cache_key(entity_type, entity_id)
            self.delete(key)
            
            # Инвалидируем кэш для коллекции
            collection_key = self.get_cache_key(f"{entity_type}_collection")
            self.delete(collection_key)
        else:
            # Инвалидируем все кэши для этого типа сущности
            keys = cache.keys(f"{CACHE_PREFIX}{entity_type}*")
            for key in keys:
                self.delete(key)
        
        # Инвалидируем кэш для зависимых сущностей
        if entity_type in self.entity_dependencies:
            for dependent_entity in self.entity_dependencies[entity_type]:
                # Инвалидируем коллекции зависимых сущностей
                dependent_collection_key = self.get_cache_key(f"{dependent_entity}_collection")
                self.delete(dependent_collection_key)
    
    def get_stats(self):
        """
        Получение статистики кэширования.
        
        Returns:
            dict: Статистика кэширования.
        """
        return self.cache_stats
    
    def reset_stats(self):
        """Сброс статистики кэширования."""
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0
        }
    
    def clear_all(self):
        """Очистка всего кэша."""
        cache.clear()
        logger.info("Cache cleared")


# Создаем глобальный экземпляр менеджера кэширования
cache_manager = CacheManager()


def cached_data(prefix, timeout=None):
    """
    Декоратор для кэширования результатов функций.
    
    Args:
        prefix: Префикс ключа кэша.
        timeout: Время жизни кэша в секундах.
        
    Returns:
        Декорированная функция.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            cache_key = cache_manager.get_cache_key(prefix, *args, **kwargs)
            
            # Пытаемся получить результат из кэша
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию
            result = func(*args, **kwargs)
            
            # Сохраняем результат в кэш
            cache_manager.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def cached_property(prefix, timeout=None):
    """
    Декоратор для кэширования свойств классов.
    
    Args:
        prefix: Префикс ключа кэша.
        timeout: Время жизни кэша в секундах.
        
    Returns:
        Декорированное свойство.
    """
    def decorator(func):
        @property
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Генерируем ключ кэша
            instance_id = getattr(self, 'id', id(self))
            cache_key = cache_manager.get_cache_key(prefix, instance_id)
            
            # Пытаемся получить результат из кэша
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию
            result = func(self, *args, **kwargs)
            
            # Сохраняем результат в кэш
            cache_manager.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache(entity_type, entity_id=None):
    """
    Инвалидация кэша для сущности.
    
    Args:
        entity_type: Тип сущности.
        entity_id: ID сущности (опционально).
    """
    cache_manager.invalidate_entity(entity_type, entity_id)


def get_cache_stats():
    """
    Получение статистики кэширования.
    
    Returns:
        dict: Статистика кэширования.
    """
    return cache_manager.get_stats()


def reset_cache_stats():
    """Сброс статистики кэширования."""
    cache_manager.reset_stats()


def clear_all_cache():
    """Очистка всего кэша."""
    cache_manager.clear_all()


class CacheMiddleware:
    """
    Middleware для управления кэшированием.
    
    Этот middleware добавляет заголовки кэширования к ответам
    и измеряет производительность кэширования.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Сохраняем начальную статистику кэширования
        initial_stats = get_cache_stats().copy()
        
        # Обрабатываем запрос
        response = self.get_response(request)
        
        # Получаем конечную статистику кэширования
        final_stats = get_cache_stats()
        
        # Вычисляем статистику для этого запроса
        request_stats = {
            'hits': final_stats['hits'] - initial_stats['hits'],
            'misses': final_stats['misses'] - initial_stats['misses'],
            'sets': final_stats['sets'] - initial_stats['sets'],
            'invalidations': final_stats['invalidations'] - initial_stats['invalidations']
        }
        
        # Добавляем заголовки кэширования
        if 'text/html' in response.get('Content-Type', ''):
            # Для HTML-страниц добавляем заголовки для предотвращения кэширования браузером
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        elif any(ct in response.get('Content-Type', '') for ct in ['application/json', 'image/', 'text/css', 'application/javascript']):
            # Для статических ресурсов и API добавляем заголовки для кэширования
            response['Cache-Control'] = f'public, max-age={CACHE_TIMEOUT}'
        
        # Логируем статистику кэширования
        if sum(request_stats.values()) > 0:
            logger.info(
                f"Cache stats for {request.path}: "
                f"hits={request_stats['hits']}, "
                f"misses={request_stats['misses']}, "
                f"sets={request_stats['sets']}, "
                f"invalidations={request_stats['invalidations']}"
            )
        
        return response