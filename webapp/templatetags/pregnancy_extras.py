"""
Дополнительные теги и фильтры для шаблонов, связанных с беременностью.

Этот модуль содержит пользовательские теги и фильтры Django для работы
с данными о беременности в шаблонах.
"""

from django import template
from django.utils.safestring import mark_safe
from datetime import date, timedelta
from webapp.utils.pregnancy_utils import (
    calculate_current_pregnancy_week,
    calculate_progress_percentage,
    determine_trimester,
    get_pregnancy_milestones,
    calculate_days_until_due,
    is_high_risk_week,
    is_pregnancy_full_term
)

register = template.Library()


@register.filter
def multiply(value, arg):
    """
    Умножает значение на аргумент.
    
    Использование: {{ value|multiply:3.14159 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def pregnancy_week(pregnancy_info):
    """
    Возвращает текущую неделю беременности.
    
    Использование: {{ pregnancy_info|pregnancy_week }}
    """
    if not pregnancy_info or not hasattr(pregnancy_info, 'start_date'):
        return None
    
    return calculate_current_pregnancy_week(
        pregnancy_info.start_date,
        pregnancy_info.is_active
    )


@register.filter
def pregnancy_progress(pregnancy_info):
    """
    Возвращает процент прогресса беременности.
    
    Использование: {{ pregnancy_info|pregnancy_progress }}
    """
    if not pregnancy_info:
        return 0
    
    current_week = pregnancy_week(pregnancy_info)
    return calculate_progress_percentage(current_week)


@register.filter
def pregnancy_trimester(pregnancy_info):
    """
    Возвращает текущий триместр беременности.
    
    Использование: {{ pregnancy_info|pregnancy_trimester }}
    """
    if not pregnancy_info:
        return None
    
    current_week = pregnancy_week(pregnancy_info)
    return determine_trimester(current_week)


@register.filter
def pregnancy_milestones(pregnancy_info):
    """
    Возвращает информацию о достигнутых вехах беременности.
    
    Использование: {{ pregnancy_info|pregnancy_milestones }}
    """
    if not pregnancy_info:
        return {}
    
    current_week = pregnancy_week(pregnancy_info)
    return get_pregnancy_milestones(current_week)


@register.filter
def days_until_due(pregnancy_info):
    """
    Возвращает количество дней до ПДР.
    
    Использование: {{ pregnancy_info|days_until_due }}
    """
    if not pregnancy_info or not hasattr(pregnancy_info, 'due_date'):
        return None
    
    return calculate_days_until_due(pregnancy_info.due_date)


@register.filter
def days_pregnant(pregnancy_info):
    """
    Возвращает количество дней беременности.
    
    Использование: {{ pregnancy_info|days_pregnant }}
    """
    if not pregnancy_info or not hasattr(pregnancy_info, 'start_date'):
        return 0
    
    today = date.today()
    if today < pregnancy_info.start_date:
        return 0
    
    return (today - pregnancy_info.start_date).days


@register.filter
def is_high_risk(pregnancy_info):
    """
    Проверяет, является ли текущая неделя беременности высокого риска.
    
    Использование: {{ pregnancy_info|is_high_risk }}
    """
    if not pregnancy_info:
        return False
    
    current_week = pregnancy_week(pregnancy_info)
    return is_high_risk_week(current_week)


@register.filter
def is_full_term(pregnancy_info):
    """
    Проверяет, является ли беременность доношенной.
    
    Использование: {{ pregnancy_info|is_full_term }}
    """
    if not pregnancy_info:
        return False
    
    current_week = pregnancy_week(pregnancy_info)
    return is_pregnancy_full_term(current_week)


@register.filter
def current_day_of_week(pregnancy_info):
    """
    Возвращает текущий день недели беременности.
    
    Использование: {{ pregnancy_info|current_day_of_week }}
    """
    if not pregnancy_info or not hasattr(pregnancy_info, 'start_date'):
        return 0
    
    today = date.today()
    if today < pregnancy_info.start_date:
        return 0
    
    days_pregnant = (today - pregnancy_info.start_date).days
    return (days_pregnant % 7) + 1


@register.simple_tag
def pregnancy_week_description(current_week):
    """
    Возвращает описание текущей недели беременности.
    
    Использование: {% pregnancy_week_description current_week %}
    """
    from webapp.utils.pregnancy_utils import get_week_description
    return get_week_description(current_week)


@register.simple_tag
def pregnancy_checkup_schedule(current_week):
    """
    Возвращает рекомендуемый график осмотров.
    
    Использование: {% pregnancy_checkup_schedule current_week %}
    """
    from webapp.utils.pregnancy_utils import get_recommended_checkup_schedule
    return get_recommended_checkup_schedule(current_week)


@register.inclusion_tag('components/pregnancy_milestone_badge.html')
def pregnancy_milestone_badge(milestone_key, milestone_achieved, milestone_title, milestone_icon):
    """
    Отображает значок достижения вехи беременности.
    
    Использование: {% pregnancy_milestone_badge 'heart_beating' True 'Сердце бьется' '💓' %}
    """
    return {
        'milestone_key': milestone_key,
        'milestone_achieved': milestone_achieved,
        'milestone_title': milestone_title,
        'milestone_icon': milestone_icon,
    }


@register.filter
def format_pregnancy_duration(days):
    """
    Форматирует продолжительность беременности в удобочитаемый вид.
    
    Использование: {{ days|format_pregnancy_duration }}
    """
    if not days or days < 0:
        return "0 дней"
    
    weeks = days // 7
    remaining_days = days % 7
    
    if weeks == 0:
        return f"{days} дн."
    elif remaining_days == 0:
        return f"{weeks} нед."
    else:
        return f"{weeks} нед. {remaining_days} дн."


@register.filter
def pregnancy_status_class(pregnancy_info):
    """
    Возвращает CSS класс для статуса беременности.
    
    Использование: {{ pregnancy_info|pregnancy_status_class }}
    """
    if not pregnancy_info:
        return "inactive"
    
    current_week = pregnancy_week(pregnancy_info)
    
    if not current_week:
        return "inactive"
    elif current_week < 12:
        return "first-trimester"
    elif current_week < 28:
        return "second-trimester"
    elif current_week < 37:
        return "third-trimester"
    elif current_week >= 42:
        return "overdue"
    else:
        return "full-term"


@register.filter
def trimester_color(trimester):
    """
    Возвращает цвет для триместра.
    
    Использование: {{ trimester|trimester_color }}
    """
    colors = {
        1: "#ff9a9e",  # Розовый для первого триместра
        2: "#a8edea",  # Бирюзовый для второго триместра
        3: "#ffd89b",  # Желтый для третьего триместра
    }
    return colors.get(trimester, "#e2e8f0")


@register.simple_tag
def pregnancy_progress_ring_circumference():
    """
    Возвращает длину окружности для кругового индикатора прогресса.
    
    Использование: {% pregnancy_progress_ring_circumference %}
    """
    # Радиус 50, длина окружности = 2 * π * r
    return 2 * 3.14159 * 50


@register.filter
def pregnancy_progress_stroke_dasharray(percentage):
    """
    Рассчитывает stroke-dasharray для кругового индикатора прогресса.
    
    Использование: {{ percentage|pregnancy_progress_stroke_dasharray }}
    """
    circumference = 2 * 3.14159 * 50  # 314.159
    progress_length = (percentage / 100) * circumference
    return f"{progress_length} {circumference}"


@register.filter
def safe_percentage(value, max_value=100):
    """
    Безопасно конвертирует значение в процент, ограничивая максимум.
    
    Использование: {{ value|safe_percentage:100 }}
    """
    try:
        percentage = float(value)
        return min(max(percentage, 0), max_value)
    except (ValueError, TypeError):
        return 0