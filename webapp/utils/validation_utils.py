"""
Утилитарные функции для валидации данных.

Этот модуль содержит функции для проверки и валидации различных типов данных.
"""

import logging
from django.http import JsonResponse
from webapp.utils.date_utils import parse_datetime

logger = logging.getLogger(__name__)

def validate_required_fields(data, required_fields):
    """
    Проверяет наличие обязательных полей в данных.
    
    Args:
        data (dict): Словарь с данными для проверки.
        required_fields (list): Список обязательных полей.
        
    Returns:
        tuple: (успех, ошибка), где успех - это булево значение,
               а ошибка - это объект JsonResponse с ошибкой или None, если валидация успешна.
    """
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            return False, JsonResponse(
                {'error': f'Отсутствует обязательное поле {field}'}, 
                status=400
            )
    return True, None


def validate_numeric_value(value, field_name, min_value=None, max_value=None):
    """
    Валидирует числовое значение.
    
    Args:
        value: Значение для валидации.
        field_name (str): Имя поля для сообщения об ошибке.
        min_value (float, optional): Минимальное допустимое значение.
        max_value (float, optional): Максимальное допустимое значение.
        
    Returns:
        tuple: (значение, ошибка), где значение - это числовое значение,
               а ошибка - это объект JsonResponse с ошибкой или None, если валидация успешна.
    """
    if value is None:
        return None, None
        
    try:
        numeric_value = float(value)
        
        if min_value is not None and numeric_value < min_value:
            return None, JsonResponse(
                {'error': f'Значение {field_name} должно быть не меньше {min_value}'}, 
                status=400
            )
            
        if max_value is not None and numeric_value > max_value:
            return None, JsonResponse(
                {'error': f'Значение {field_name} должно быть не больше {max_value}'}, 
                status=400
            )
            
        return numeric_value, None
    except (ValueError, TypeError):
        return None, JsonResponse(
            {'error': f'Неверный формат значения {field_name}'}, 
            status=400
        )


def validate_date(date_string, field_name="даты"):
    """
    Валидирует строку даты.
    
    Args:
        date_string (str): Строка с датой для валидации.
        field_name (str): Имя поля для сообщения об ошибке.
        
    Returns:
        tuple: (дата, ошибка), где дата - это объект datetime,
               а ошибка - это объект JsonResponse с ошибкой или None, если валидация успешна.
    """
    if not date_string:
        return None, None
        
    date = parse_datetime(date_string)
    if not date:
        return None, JsonResponse(
            {'error': f'Неверный формат {field_name}'}, 
            status=400
        )
        
    return date, None


def validate_enum_value(value, valid_values, field_name):
    """
    Валидирует значение из перечисления.
    
    Args:
        value: Значение для валидации.
        valid_values (list): Список допустимых значений.
        field_name (str): Имя поля для сообщения об ошибке.
        
    Returns:
        tuple: (значение, ошибка), где значение - это проверенное значение,
               а ошибка - это объект JsonResponse с ошибкой или None, если валидация успешна.
    """
    if value is None or value == '':
        return None, None
        
    if value not in valid_values:
        valid_values_str = ', '.join([str(v) for v in valid_values])
        return None, JsonResponse(
            {'error': f'Неверное значение {field_name}. Допустимые значения: {valid_values_str}'}, 
            status=400
        )
        
    return value, None