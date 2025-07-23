"""
Общие утилитарные функции.

Этот модуль содержит общие утилитарные функции, которые могут использоваться
в различных частях приложения.
"""

import logging
import traceback
from functools import wraps
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def safe_execute(func):
    """
    Декоратор для безопасного выполнения функций с обработкой исключений.
    
    Args:
        func: Функция для выполнения.
        
    Returns:
        function: Обернутая функция с обработкой исключений.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при выполнении {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)
    return wrapper


def get_client_ip(request):
    """
    Получает IP-адрес клиента из запроса.
    
    Args:
        request: Объект HTTP запроса Django.
        
    Returns:
        str: IP-адрес клиента.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def format_age_display(months):
    """
    Форматирует возраст в месяцах в удобочитаемую строку.
    
    Args:
        months (int): Возраст в месяцах.
        
    Returns:
        str: Отформатированная строка с возрастом.
    """
    if months is None:
        return "Возраст неизвестен"
        
    years = months // 12
    remaining_months = months % 12
    
    if years == 0:
        if remaining_months == 0:
            return "Менее месяца"
        elif remaining_months == 1:
            return "1 месяц"
        elif 2 <= remaining_months <= 4:
            return f"{remaining_months} месяца"
        else:
            return f"{remaining_months} месяцев"
    elif years == 1:
        if remaining_months == 0:
            return "1 год"
        elif remaining_months == 1:
            return "1 год и 1 месяц"
        elif 2 <= remaining_months <= 4:
            return f"1 год и {remaining_months} месяца"
        else:
            return f"1 год и {remaining_months} месяцев"
    elif 2 <= years <= 4:
        if remaining_months == 0:
            return f"{years} года"
        elif remaining_months == 1:
            return f"{years} года и 1 месяц"
        elif 2 <= remaining_months <= 4:
            return f"{years} года и {remaining_months} месяца"
        else:
            return f"{years} года и {remaining_months} месяцев"
    else:
        if remaining_months == 0:
            return f"{years} лет"
        elif remaining_months == 1:
            return f"{years} лет и 1 месяц"
        elif 2 <= remaining_months <= 4:
            return f"{years} лет и {remaining_months} месяца"
        else:
            return f"{years} лет и {remaining_months} месяцев"