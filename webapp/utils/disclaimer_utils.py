"""
Утилиты для работы с дисклеймером и подтверждениями ознакомления.

Этот модуль содержит функции и декораторы для управления подтверждениями
ознакомления пользователей с дисклеймером согласно требованию 8.3.
"""

from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from webapp.models import DisclaimerAcknowledgment
import json


def get_client_ip(request):
    """
    Получает IP-адрес клиента из запроса.
    
    Args:
        request: Django request объект
        
    Returns:
        str: IP-адрес клиента
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    Получает User Agent из запроса.
    
    Args:
        request: Django request объект
        
    Returns:
        str: User Agent строка
    """
    return request.META.get('HTTP_USER_AGENT', '')


def requires_disclaimer_acknowledgment(feature):
    """
    Декоратор для представлений, требующих подтверждения ознакомления с дисклеймером.
    
    Проверяет, подтвердил ли пользователь ознакомление с дисклеймером для указанной функции.
    Если нет, возвращает JSON-ответ с требованием подтверждения.
    
    Args:
        feature (str): Код функции из DisclaimerAcknowledgment.FEATURE_CHOICES
        
    Returns:
        function: Декорированная функция
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Проверяем, аутентифицирован ли пользователь
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Требуется аутентификация',
                    'redirect': '/login/'
                }, status=401)
            
            # Проверяем, подтвердил ли пользователь ознакомление с дисклеймером
            if not DisclaimerAcknowledgment.has_user_acknowledged(request.user, feature):
                return JsonResponse({
                    'requires_disclaimer_acknowledgment': True,
                    'feature': feature,
                    'message': 'Для использования этой функции необходимо подтвердить ознакомление с дисклеймером.'
                }, status=200)
            
            # Если подтверждение есть, выполняем оригинальное представление
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def requires_disclaimer_acknowledgment_template(feature, template_name=None):
    """
    Декоратор для представлений, возвращающих HTML-шаблоны, требующих подтверждения дисклеймера.
    
    Если пользователь не подтвердил ознакомление с дисклеймером, показывает страницу с запросом подтверждения.
    
    Args:
        feature (str): Код функции из DisclaimerAcknowledgment.FEATURE_CHOICES
        template_name (str): Имя шаблона для страницы подтверждения (опционально)
        
    Returns:
        function: Декорированная функция
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Проверяем, аутентифицирован ли пользователь
            if not request.user.is_authenticated:
                from django.contrib.auth.decorators import login_required
                return login_required(view_func)(request, *args, **kwargs)
            
            # Проверяем, подтвердил ли пользователь ознакомление с дисклеймером
            if not DisclaimerAcknowledgment.has_user_acknowledged(request.user, feature):
                context = {
                    'feature': feature,
                    'feature_display': dict(DisclaimerAcknowledgment.FEATURE_CHOICES).get(feature, feature),
                    'return_url': request.get_full_path(),
                }
                template = template_name or 'components/disclaimer_acknowledgment.html'
                return render(request, template, context)
            
            # Если подтверждение есть, выполняем оригинальное представление
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def acknowledge_disclaimer(request):
    """
    Представление для обработки подтверждения ознакомления с дисклеймером.
    
    Принимает POST-запрос с кодом функции и создает запись о подтверждении.
    
    Returns:
        JsonResponse: Результат операции
    """
    try:
        data = json.loads(request.body)
        feature = data.get('feature')
        
        if not feature:
            return JsonResponse({
                'error': 'Не указана функция'
            }, status=400)
        
        # Проверяем, что функция существует в списке доступных
        valid_features = [choice[0] for choice in DisclaimerAcknowledgment.FEATURE_CHOICES]
        if feature not in valid_features:
            return JsonResponse({
                'error': 'Неизвестная функция'
            }, status=400)
        
        # Создаем запись о подтверждении
        acknowledgment = DisclaimerAcknowledgment.acknowledge_feature(
            user=request.user,
            feature=feature,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Подтверждение ознакомления с дисклеймером сохранено',
            'acknowledged_at': acknowledgment.acknowledged_at.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Неверный формат данных'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Произошла ошибка: {str(e)}'
        }, status=500)


def check_disclaimer_acknowledgment(user, feature):
    """
    Проверяет, подтвердил ли пользователь ознакомление с дисклеймером для указанной функции.
    
    Args:
        user (User): Пользователь
        feature (str): Код функции
        
    Returns:
        bool: True если пользователь подтвердил ознакомление
    """
    return DisclaimerAcknowledgment.has_user_acknowledged(user, feature)


def get_user_acknowledgments(user):
    """
    Возвращает все подтверждения дисклеймера для указанного пользователя.
    
    Args:
        user (User): Пользователь
        
    Returns:
        QuerySet: Подтверждения пользователя
    """
    return DisclaimerAcknowledgment.objects.filter(user=user)


def get_features_requiring_acknowledgment():
    """
    Возвращает список всех функций, требующих подтверждения дисклеймера.
    
    Returns:
        list: Список кортежей (код, название) функций
    """
    return DisclaimerAcknowledgment.FEATURE_CHOICES


def create_acknowledgment_context(feature, return_url=None):
    """
    Создает контекст для шаблона страницы подтверждения дисклеймера.
    
    Args:
        feature (str): Код функции
        return_url (str): URL для возврата после подтверждения
        
    Returns:
        dict: Контекст для шаблона
    """
    return {
        'feature': feature,
        'feature_display': dict(DisclaimerAcknowledgment.FEATURE_CHOICES).get(feature, feature),
        'return_url': return_url or '/',
        'disclaimer_text': get_disclaimer_text(),
    }


def get_disclaimer_text():
    """
    Возвращает текст дисклеймера.
    
    Returns:
        str: Текст дисклеймера
    """
    return (
        "Все рекомендации в приложении являются общими и могут не учитывать "
        "индивидуальные особенности. Для получения персонализированных "
        "рекомендаций обратитесь к специалисту."
    )