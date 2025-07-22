"""
API эндпоинты для сбора и анализа метрик производительности.

Этот модуль содержит представления API для сбора метрик производительности
и предоставления статистики для оптимизации приложения.
"""

import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.conf import settings

from mom_baby_bot.query_optimizer import get_slow_queries, reset_query_stats
from mom_baby_bot.cache_manager import get_cache_stats, reset_cache_stats

logger = logging.getLogger(__name__)

# Константы для хранения метрик
METRICS_CACHE_KEY = 'performance_metrics'
METRICS_MAX_ENTRIES = 1000  # Максимальное количество записей метрик


@csrf_exempt
@require_http_methods(["POST"])
def collect_metrics(request):
    """
    API эндпоинт для сбора метрик производительности.
    
    URL: /api/performance-metrics
    Метод: POST
    """
    try:
        # Получаем данные из запроса
        data = json.loads(request.body)
        
        # Добавляем временную метку
        data['server_timestamp'] = datetime.now().isoformat()
        
        # Получаем текущие метрики из кэша
        metrics = cache.get(METRICS_CACHE_KEY, [])
        
        # Добавляем новые метрики
        metrics.append(data)
        
        # Ограничиваем количество записей
        if len(metrics) > METRICS_MAX_ENTRIES:
            metrics = metrics[-METRICS_MAX_ENTRIES:]
        
        # Сохраняем обновленные метрики в кэш
        cache.set(METRICS_CACHE_KEY, metrics, 60 * 60 * 24 * 7)  # 7 дней
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        logger.error(f"Ошибка при сборе метрик производительности: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_metrics(request):
    """
    API эндпоинт для получения метрик производительности.
    
    URL: /api/performance-metrics
    Метод: GET
    """
    try:
        # Получаем метрики из кэша
        metrics = cache.get(METRICS_CACHE_KEY, [])
        
        # Фильтруем метрики по параметрам запроса
        url_filter = request.GET.get('url')
        days_filter = request.GET.get('days')
        
        if url_filter:
            metrics = [m for m in metrics if m.get('metrics', {}).get('url') == url_filter]
        
        if days_filter:
            try:
                days = int(days_filter)
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                metrics = [m for m in metrics if m.get('server_timestamp', '') >= cutoff_date]
            except ValueError:
                pass
        
        # Возвращаем метрики
        return JsonResponse({'metrics': metrics})
    
    except Exception as e:
        logger.error(f"Ошибка при получении метрик производительности: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_performance_stats(request):
    """
    API эндпоинт для получения статистики производительности.
    
    URL: /api/performance-stats
    Метод: GET
    """
    try:
        # Получаем статистику запросов
        slow_queries = get_slow_queries()
        
        # Получаем статистику кэширования
        cache_stats = get_cache_stats()
        
        # Получаем метрики из кэша
        metrics = cache.get(METRICS_CACHE_KEY, [])
        
        # Вычисляем средние значения метрик
        page_load_times = {}
        fcp_times = {}
        
        for metric in metrics:
            url = metric.get('metrics', {}).get('url')
            if not url:
                continue
            
            # Собираем времена загрузки страниц
            page_load_time = metric.get('metrics', {}).get('pageLoadTime')
            if page_load_time:
                if url not in page_load_times:
                    page_load_times[url] = []
                page_load_times[url].append(float(page_load_time))
            
            # Собираем времена First Contentful Paint
            fcp_time = metric.get('metrics', {}).get('fcp')
            if fcp_time:
                if url not in fcp_times:
                    fcp_times[url] = []
                fcp_times[url].append(float(fcp_time))
        
        # Вычисляем средние значения
        avg_page_load_times = {
            url: sum(times) / len(times) for url, times in page_load_times.items()
        }
        
        avg_fcp_times = {
            url: sum(times) / len(times) for url, times in fcp_times.items()
        }
        
        # Формируем статистику
        stats = {
            'slow_queries': slow_queries,
            'cache_stats': cache_stats,
            'avg_page_load_times': avg_page_load_times,
            'avg_fcp_times': avg_fcp_times,
            'total_metrics_collected': len(metrics)
        }
        
        return JsonResponse(stats)
    
    except Exception as e:
        logger.error(f"Ошибка при получении статистики производительности: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def reset_stats(request):
    """
    API эндпоинт для сброса статистики производительности.
    
    URL: /api/performance-stats/reset
    Метод: POST
    """
    try:
        # Сбрасываем статистику запросов
        reset_query_stats()
        
        # Сбрасываем статистику кэширования
        reset_cache_stats()
        
        # Очищаем метрики
        cache.delete(METRICS_CACHE_KEY)
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        logger.error(f"Ошибка при сбросе статистики производительности: {e}")
        return JsonResponse({'error': str(e)}, status=500)