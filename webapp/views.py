import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json

from botapp.models import User
from webapp.utils.date_utils import parse_datetime
from webapp.utils.request_utils import parse_json_request, error_response, success_response, get_int_param
from webapp.utils.common_utils import safe_execute
from webapp.utils.validation_utils import validate_required_fields, validate_numeric_value, validate_date
from webapp.utils.db_utils import get_db_manager

logger = logging.getLogger(__name__)


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
    user_id = get_int_param(request, 'user_id', 1)
    
    return render(request, 'tools/contraction_counter/index.html', {
        'user_id': user_id
    })


def kick_counter(request):
    """Страница счетчика шевелений"""
    # Получаем user_id из запроса или используем значение по умолчанию
    user_id = get_int_param(request, 'user_id', 1)
    
    return render(request, 'tools/kick_counter/index.html', {
        'user_id': user_id
    })


def sleep_timer(request):
    """Страница таймера сна"""
    # Получаем user_id и child_id из запроса или используем значение по умолчанию
    user_id = get_int_param(request, 'user_id', 1)
    child_id = get_int_param(request, 'child_id', 1)
    
    return render(request, 'tools/sleep_timer/index.html', {
        'user_id': user_id,
        'child_id': child_id
    })


def feeding_tracker(request):
    """Страница отслеживания кормления"""
    # Получаем user_id и child_id из запроса или используем значение по умолчанию
    user_id = get_int_param(request, 'user_id', 1)
    child_id = get_int_param(request, 'child_id', 1)
    
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
    user_id = get_int_param(request, 'user_id', 1)
    
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
@safe_execute
def create_user(request):
    """API endpoint для создания пользователя"""
    # Парсим JSON из запроса
    data, error = parse_json_request(request)
    if error:
        return error
    
    # Проверяем наличие обязательных полей
    is_valid, error = validate_required_fields(data, ['telegram_id'])
    if not is_valid:
        return error
    
    # Создание пользователя через SQLAlchemy
    db_manager = get_db_manager()
    session = db_manager.get_session()
    try:
        # Проверяем, существует ли уже пользователь с таким telegram_id
        existing_user = session.query(User).filter_by(telegram_id=data['telegram_id']).first()
        if existing_user:
            return error_response("Пользователь с таким telegram_id уже существует", 409)
        
        # Парсим дату рождения ребенка, если она передана
        baby_birth_date, error = validate_date(data.get('baby_birth_date'), 'даты рождения ребенка')
        if error and data.get('baby_birth_date'):
            return error
        
        # Проверяем pregnancy_week, если передано
        pregnancy_week = None
        if 'pregnancy_week' in data and data['pregnancy_week'] is not None:
            pregnancy_week, error = validate_numeric_value(data['pregnancy_week'], 'pregnancy_week', min_value=1)
            if error:
                return error
        
        user = User(
            telegram_id=data['telegram_id'],
            username=data.get('username'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            is_pregnant=data.get('is_pregnant', False),
            pregnancy_week=pregnancy_week,
            baby_birth_date=baby_birth_date
        )
        session.add(user)
        session.commit()
        logger.info(f"Создан новый пользователь через API: {data.get('username', data['telegram_id'])}")
        return success_response({"user_id": user.id}, message="Пользователь успешно создан")
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при создании пользователя в базе данных: {str(e)}")
        return error_response(f"Ошибка при создании пользователя: {str(e)}", 500)
    finally:
        db_manager.close_session(session)


@csrf_exempt
@require_http_methods(["POST"])
@safe_execute
def web_app_data(request):
    """Обработка данных от веб-приложения"""
    # Парсим JSON из запроса
    data, error = parse_json_request(request)
    if error:
        return error
    
    # Проверяем наличие обязательных полей
    is_valid, error = validate_required_fields(data, ['user_id'])
    if not is_valid:
        return error
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    try:
        user = session.query(User).filter_by(telegram_id=data['user_id']).first()
        
        if not user:
            return error_response('Пользователь не найден', 404)
            
        if user.is_pregnant:
            pregnancy_week = data.get('pregnancy_week')
            if pregnancy_week is not None:
                numeric_value, error = validate_numeric_value(pregnancy_week, 'pregnancy_week', min_value=1)
                if error:
                    return error
                user.pregnancy_week = numeric_value
        else:
            # Обновлено для работы с baby_birth_date вместо baby_age
            if 'baby_birth_date' in data:
                birth_date, error = validate_date(data.get('baby_birth_date'), 'даты рождения ребенка')
                if error and data['baby_birth_date']:
                    return error
                user.baby_birth_date = birth_date
                
        session.commit()
        return success_response(message='Данные успешно обновлены')
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при обновлении данных пользователя: {str(e)}")
        return error_response(f"Ошибка при обновлении данных: {str(e)}", 500)
    finally:
        db_manager.close_session(session)

# Документация
def documentation(request):
    """Главная страница документации"""
    return render(request, 'documentation/index.html')


def user_guide_general(request):
    """Общая информация о приложении"""
    return render(request, 'documentation/user_guide_general.html')


def user_guide_pregnancy(request):
    """Руководство по функциям для беременных"""
    return render(request, 'documentation/user_guide_pregnancy.html')


def user_guide_baby(request):
    """Руководство по уходу за ребенком"""
    return render(request, 'documentation/user_guide_baby.html')


def user_guide_tools(request):
    """Подробное руководство по инструментам"""
    return render(request, 'documentation/user_guide_tools.html')


def user_guide_sync(request):
    """Руководство по синхронизации данных"""
    return render(request, 'documentation/user_guide_sync.html')


def faq(request):
    """Часто задаваемые вопросы"""
    return render(request, 'documentation/faq.html')

def api_documentation(request):
    """Документация по API"""
    return render(request, 'documentation/api_documentation.html')

def architecture(request):
    """Документация по архитектуре приложения"""
    return render(request, 'documentation/architecture.html')

def deployment(request):
    """Документация по развертыванию приложения"""
    return render(request, 'documentation/deployment.html')
    
def tooltips_example(request):
    """Страница с примерами подсказок в интерфейсе"""
    return render(request, 'components/tooltips_example.html')