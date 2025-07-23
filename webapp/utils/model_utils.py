"""
Утилитарные функции для работы с моделями данных.

Этот модуль содержит функции для конвертации моделей в словари и другие операции с моделями.
"""

def child_to_dict(child):
    """
    Преобразует объект Child в словарь.
    
    Args:
        child: Объект модели Child.
        
    Returns:
        dict: Словарь с данными ребенка.
    """
    return {
        'id': child.id,
        'user_id': child.user_id,
        'name': child.name,
        'birth_date': child.birth_date.isoformat() if child.birth_date else None,
        'gender': child.gender,
        'age_in_months': child.age_in_months,
        'age_display': child.age_display,
        'created_at': child.created_at.isoformat() if child.created_at else None,
        'updated_at': child.updated_at.isoformat() if child.updated_at else None,
    }


def measurement_to_dict(measurement):
    """
    Преобразует объект Measurement в словарь.
    
    Args:
        measurement: Объект модели Measurement.
        
    Returns:
        dict: Словарь с данными измерения.
    """
    return {
        'id': measurement.id,
        'child_id': measurement.child_id,
        'date': measurement.date.isoformat() if measurement.date else None,
        'height': measurement.height,
        'weight': measurement.weight,
        'head_circumference': measurement.head_circumference,
        'notes': measurement.notes,
    }