"""
Утилитарные функции для работы с датами.

Этот модуль содержит функции для парсинга, форматирования и манипуляции с датами.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_datetime(date_string):
    """
    Парсинг строки даты в объект datetime.
    
    Args:
        date_string (str): Строка с датой в различных форматах.
        
    Returns:
        datetime: Объект datetime или None, если парсинг не удался.
    """
    if not date_string:
        return None
    
    # Пробуем разные форматы дат
    formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',  # Добавлен формат с миллисекундами
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%d.%m.%Y',  # Добавлен русский формат даты
        '%d.%m.%Y %H:%M',
        '%d.%m.%Y %H:%M:%S',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    # Если ни один формат не подошел
    logger.error(f"Невозможно разобрать дату: {date_string}")
    return None