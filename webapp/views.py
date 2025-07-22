import logging
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json

from botapp.models import User, db_manager

logger = logging.getLogger(__name__)


def parse_datetime(date_string):
    """Парсинг строки даты в объект datetime"""
    if not date_string:
        return None
    
    try:
        # Пробуем разные форматы дат
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # Если ни один формат не подошел
        raise ValueError(f"Unable to parse date: {date_string}")
        
    except Exception as e:
        logger.error(f"Error parsing date '{date_string}': {e}")
        return None


def index(request):
    """Отображение главной страницы веб-приложения"""
    return render(request, 'index.html')


# Информационные разделы
def pregnancy(request):
    """Страница с информацией о беременности"""
    return render(request, 'pregnancy/index.html')


def child_development(request):
    """Страница с информацией о развитии ребенка"""
    return render(request, 'child_development/index.html')


def nutrition(request):
    """Страница с информацией о питании"""
    return render(request, 'nutrition/index.html')


# Инструменты
def contraction_counter(request):
    """Страница счетчика схваток"""
    # Получаем user_id из запроса или используем значение по умолчанию
    user_id = request.GET.get('user_id', 1)
    
    # Проверяем, что user_id является числом
    try:
        user_id = int(user_id)
    except ValueError:
        user_id = 1
    
    return render(request, 'tools/contraction_counter/index.html', {
        'user_id': user_id
    })


def kick_counter(request):
    """Страница счетчика шевелений"""
    # Получаем user_id из запроса или используем значение по умолчанию
    user_id = request.GET.get('user_id', 1)
    
    # Проверяем, что user_id является числом
    try:
        user_id = int(user_id)
    except ValueError:
        user_id = 1
    
    return render(request, 'tools/kick_counter/index.html', {
        'user_id': user_id
    })


def sleep_timer(request):
    """Страница таймера сна"""
    # Получаем user_id из запроса или используем значение по умолчанию
    user_id = request.GET.get('user_id', 1)
    
    # Проверяем, что user_id является числом
    try:
        user_id = int(user_id)
    except ValueError:
        user_id = 1
    
    # Получаем child_id из запроса или используем значение по умолчанию
    child_id = request.GET.get('child_id', 1)
    
    # Проверяем, что child_id является числом
    try:
        child_id = int(child_id)
    except ValueError:
        child_id = 1
    
    return render(request, 'tools/sleep_timer/index.html', {
        'user_id': user_id,
        'child_id': child_id
    })


def feeding_tracker(request):
    """Страница отслеживания кормления"""
    # Получаем user_id из запроса или используем значение по умолчанию
    user_id = request.GET.get('user_id', 1)
    
    # Проверяем, что user_id является числом
    try:
        user_id = int(user_id)
    except ValueError:
        user_id = 1
    
    # Получаем child_id из запроса или используем значение по умолчанию
    child_id = request.GET.get('child_id', 1)
    
    # Проверяем, что child_id является числом
    try:
        child_id = int(child_id)
    except ValueError:
        child_id = 1
    
    return render(request, 'tools/feeding_tracker/index.html', {
        'user_id': user_id,
        'child_id': child_id
    })


def child_profiles(request):
    """Страница управления профилями детей"""
    return render(request, 'tools/child_profiles/index.html')


def vaccine_calendar(request):
    """Страница календаря прививок"""
    # Получаем user_id из запроса или используем значение по умолчанию
    user_id = request.GET.get('user_id', 1)
    
    # Проверяем, что user_id является числом
    try:
        user_id = int(user_id)
    except ValueError:
        user_id = 1
    
    return render(request, 'tools/vaccine_calendar/index.html', {
        'user_id': user_id
    })


def components_showcase(request):
    """Страница демонстрации UI компонентов"""
    return render(request, 'components/showcase.html')


def performance_dashboard(request):
    """Страница мониторинга производительности для администраторов"""
    # Проверяем, что пользователь является администратором
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.shortcuts import redirect
        return redirect('admin:login')
    
    return render(request, 'admin/performance_dashboard.html')


@csrf_exempt
@require_http_methods(["POST"])
def create_user(request):
    """API endpoint для создания пользователя"""
    try:
        data = json.loads(request.body)
        
        # Создание пользователя через SQLAlchemy
        session = db_manager.get_session()
        try:
            # Парсим дату рождения ребенка, если она передана
            baby_birth_date = None
            if 'baby_birth_date' in data:
                baby_birth_date = parse_datetime(data['baby_birth_date'])
            
            user = User(
                telegram_id=data['telegram_id'],
                username=data.get('username'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                is_pregnant=data.get('is_pregnant', False),
                pregnancy_week=data.get('pregnancy_week'),
                baby_birth_date=baby_birth_date
            )
            session.add(user)
            session.commit()
            logger.info(f"Создан новый пользователь через API: {data.get('username', data['telegram_id'])}")
            return JsonResponse({"message": "User created successfully"})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя через API: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def web_app_data(request):
    """Обработка данных от веб-приложения"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=user_id).first()
            
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)
                
            if user.is_pregnant:
                user.pregnancy_week = data.get('pregnancy_week')
            else:
                # Обновлено для работы с baby_birth_date вместо baby_age
                if 'baby_birth_date' in data:
                    user.baby_birth_date = parse_datetime(data.get('baby_birth_date'))
                    
            session.commit()
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Error processing web app data: {e}")
        return JsonResponse({'error': str(e)}, status=500)
