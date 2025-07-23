"""
Утилитарные функции для обработки HTTP запросов.

Этот модуль содержит функции для обработки запросов, валидации параметров и другие
связанные с запросами операции.
"""

import json
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def parse_json_request(request):
    """
    Парсит JSON из тела запроса.
    
    Args:
        request: Объект HTTP запроса Django.
        
    Returns:
        tuple: (данные, ошибка), где данные - это словарь с данными из JSON,
               а ошибка - это объект JsonResponse с ошибкой или None, если парсинг успешен.
    """
    try:
        data = json.loads(request.body)
        return data, None
    except json.JSONDecodeError:
        error_response = JsonResponse({"error": "Невалидный JSON в запросе"}, status=400)
        return None, error_response


def validate_id_param(param_value, param_name="ID"):
    """
    Валидирует параметр ID, преобразуя его в целое число.
    
    Args:
        param_value: Значение параметра для валидации.
        param_name (str): Имя параметра для сообщения об ошибке.
        
    Returns:
        tuple: (id, ошибка), где id - это целочисленное значение параметра,
               а ошибка - это объект JsonResponse с ошибкой или None, если валидация успешна.
    """
    try:
        id_value = int(param_value)
        return id_value, None
    except ValueError:
        error_response = JsonResponse({'error': f'Неверный формат {param_name}'}, status=400)
        return None, error_response


def error_response(message, status_code=400):
    """
    Создает стандартный ответ с ошибкой.
    
    Args:
        message (str): Сообщение об ошибке.
        status_code (int): HTTP код статуса.
        
    Returns:
        JsonResponse: Объект ответа с ошибкой.
    """
    return JsonResponse({'error': message}, status=status_code)


def success_response(data=None, message=None, status_code=200):
    """
    Создает стандартный успешный ответ.
    
    Args:
        data (dict, optional): Данные для включения в ответ.
        message (str, optional): Сообщение об успехе.
        status_code (int): HTTP код статуса.
        
    Returns:
        JsonResponse: Объект успешного ответа.
    """
    response = {}
    
    if data is not None:
        response.update(data)
    
    if message is not None:
        response['message'] = message
        
    if not response:
        response = {'status': 'success'}
        
    return JsonResponse(response, status=status_code)


def get_int_param(request, param_name, default=None):
    """
    Получает целочисленный параметр из запроса.
    
    Args:
        request: Объект HTTP запроса Django.
        param_name (str): Имя параметра.
        default: Значение по умолчанию, если параметр отсутствует или невалиден.
        
    Returns:
        int: Целочисленное значение параметра или значение по умолчанию.
    """
    param_value = request.GET.get(param_name, default)
    
    try:
        return int(param_value)
    except (ValueError, TypeError):
        return default