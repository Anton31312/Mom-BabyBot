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
