"""
API эндпоинты для отслеживания кормления.

Этот модуль содержит представления API для работы с сессиями кормления.
"""

import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from sqlalchemy import func, and_, or_

from botapp.models import User, db_manager
from botapp.models_child import Child
from botapp.models_timers import FeedingSession

logger = logging.getLogger(__name__)


def feeding_session_to_dict(feeding_session):
    """Преобразует объект FeedingSession в словарь."""
    return {
        'id': feeding_session.id,
        'child_id': feeding_session.child_id,
        'timestamp': feeding_session.timestamp.isoformat() if feeding_session.timestamp else None,
        'type': feeding_session.type,
        'amount': feeding_session.amount,
        'duration': feeding_session.duration,
        'breast': feeding_session.breast,
        'milk_type': feeding_session.milk_type,
        'notes': feeding_session.notes
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def feeding_sessions(request, user_id, child_id):
    """
    Получение списка сессий кормления или создание новой сессии.
    
    GET: Получить все сессии кормления для конкретного ребенка
    POST: Создать новую сессию кормления
    """
    try:
        # Преобразуем ID в целые числа
        user_id = int(user_id)
        child_id = int(child_id)
        
        # Проверяем существование пользователя
        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'Пользователь не найден'}, status=404)
                
            # Проверяем существование ребенка и принадлежность пользователю
            child = session.query(Child).filter_by(id=child_id).first()
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
                
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            if request.method == 'GET':
                # Получаем сессии кормления
                feeding_sessions_list = session.query(FeedingSession).filter_by(child_id=child_id).all()
                
                # Преобразуем в словарь
                feeding_sessions_data = [feeding_session_to_dict(fs) for fs in feeding_sessions_list]
                
                return JsonResponse({'feeding_sessions': feeding_sessions_data})
                
            elif request.method == 'POST':
                # Разбираем данные запроса
                data = json.loads(request.body)
                
                # Создаем сессию кормления
                feeding_session = FeedingSession(
                    child_id=child_id,
                    timestamp=datetime.fromisoformat(data.get('timestamp')) if data.get('timestamp') else datetime.utcnow(),
                    type=data.get('type'),
                    amount=data.get('amount'),
                    duration=data.get('duration'),
                    breast=data.get('breast'),
                    milk_type=data.get('milk_type'),
                    notes=data.get('notes')
                )
                
                session.add(feeding_session)
                session.commit()
                session.refresh(feeding_session)
                
                # Возвращаем созданную сессию
                return JsonResponse(feeding_session_to_dict(feeding_session), status=201)
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Error in feeding_sessions: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def feeding_session_detail(request, user_id, child_id, session_id):
    """
    Получение, обновление или удаление конкретной сессии кормления.
    
    GET: Получить детали сессии кормления
    PUT: Обновить сессию кормления
    DELETE: Удалить сессию кормления
    """
    try:
        # Преобразуем ID в целые числа
        user_id = int(user_id)
        child_id = int(child_id)
        session_id = int(session_id)
        
        # Проверяем существование пользователя и ребенка
        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'Пользователь не найден'}, status=404)
                
            child = session.query(Child).filter_by(id=child_id).first()
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
                
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
                
            # Получаем сессию кормления
            feeding_session = session.query(FeedingSession).filter_by(id=session_id).first()
            if not feeding_session:
                return JsonResponse({'error': 'Сессия кормления не найдена'}, status=404)
                
            if feeding_session.child_id != child_id:
                return JsonResponse({'error': 'Сессия кормления не принадлежит этому ребенку'}, status=403)
                
            if request.method == 'GET':
                # Возвращаем данные сессии кормления
                return JsonResponse(feeding_session_to_dict(feeding_session))
                
            elif request.method == 'PUT':
                # Разбираем данные запроса
                data = json.loads(request.body)
                
                # Обновляем поля
                if 'timestamp' in data:
                    feeding_session.timestamp = datetime.fromisoformat(data['timestamp'])
                if 'type' in data:
                    feeding_session.type = data['type']
                if 'amount' in data:
                    feeding_session.amount = data['amount']
                if 'duration' in data:
                    feeding_session.duration = data['duration']
                if 'breast' in data:
                    feeding_session.breast = data['breast']
                if 'milk_type' in data:
                    feeding_session.milk_type = data['milk_type']
                if 'notes' in data:
                    feeding_session.notes = data['notes']
                
                session.commit()
                session.refresh(feeding_session)
                
                return JsonResponse(feeding_session_to_dict(feeding_session))
                
            elif request.method == 'DELETE':
                # Удаляем сессию кормления
                session.delete(feeding_session)
                session.commit()
                
                return JsonResponse({'message': 'Сессия кормления успешно удалена'})
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Error in feeding_session_detail: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def feeding_statistics(request, user_id, child_id):
    """
    Получение статистики кормления для ребенка.
    
    GET: Получить статистику кормления (общее время, средний объем и т.д.)
    """
    try:
        # Преобразуем ID в целые числа
        user_id = int(user_id)
        child_id = int(child_id)
        
        # Проверяем существование пользователя и ребенка
        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'Пользователь не найден'}, status=404)
                
            child = session.query(Child).filter_by(id=child_id).first()
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
                
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            # Текущая дата
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            # Неделя назад
            week_ago = today - timedelta(days=7)
            week_ago_start = datetime.combine(week_ago, datetime.min.time())
            
            # Получаем статистику за сегодня
            today_sessions = session.query(FeedingSession).filter(
                FeedingSession.child_id == child_id,
                FeedingSession.timestamp >= today_start,
                FeedingSession.timestamp <= today_end
            ).all()
            
            today_count = len(today_sessions)
            today_breast_sessions = [s for s in today_sessions if s.type == 'breast']
            today_bottle_sessions = [s for s in today_sessions if s.type == 'bottle']
            today_duration = sum([s.duration or 0 for s in today_breast_sessions])
            today_amount = sum([s.amount or 0 for s in today_bottle_sessions])
            
            # Получаем статистику за неделю
            weekly_sessions = session.query(FeedingSession).filter(
                FeedingSession.child_id == child_id,
                FeedingSession.timestamp >= week_ago_start,
                FeedingSession.timestamp <= today_end
            ).all()
            
            # Группируем по дням
            daily_stats = {}
            for fs in weekly_sessions:
                day = fs.timestamp.date()
                if day not in daily_stats:
                    daily_stats[day] = {
                        'date': day.strftime('%d.%m'),
                        'count': 0,
                        'breast_duration': 0,
                        'bottle_amount': 0
                    }
                
                daily_stats[day]['count'] += 1
                if fs.type == 'breast':
                    daily_stats[day]['breast_duration'] += fs.duration or 0
                elif fs.type == 'bottle':
                    daily_stats[day]['bottle_amount'] += fs.amount or 0
            
            # Заполняем пропущенные дни
            for i in range(7):
                day = (today - timedelta(days=i)).date()
                if day not in daily_stats:
                    daily_stats[day] = {
                        'date': day.strftime('%d.%m'),
                        'count': 0,
                        'breast_duration': 0,
                        'bottle_amount': 0
                    }
            
            # Сортируем по дате
            daily_stats_list = list(daily_stats.values())
            daily_stats_list.sort(key=lambda x: datetime.strptime(x['date'], '%d.%m'))
            
            # Рассчитываем средние значения за неделю
            days_count = 7  # Всегда берем 7 дней
            weekly_count = len(weekly_sessions)
            weekly_breast_sessions = [s for s in weekly_sessions if s.type == 'breast']
            weekly_bottle_sessions = [s for s in weekly_sessions if s.type == 'bottle']
            weekly_duration = sum([s.duration or 0 for s in weekly_breast_sessions])
            weekly_amount = sum([s.amount or 0 for s in weekly_bottle_sessions])
            
            weekly_avg_count = round(weekly_count / days_count, 1)
            weekly_avg_duration = round(weekly_duration / days_count, 1)
            weekly_avg_amount = round(weekly_amount / days_count, 1)
            
            # Возвращаем статистику
            return JsonResponse({
                'today_count': today_count,
                'today_duration': today_duration,
                'today_amount': today_amount,
                'weekly_avg_count': weekly_avg_count,
                'weekly_avg_duration': weekly_avg_duration,
                'weekly_avg_amount': weekly_avg_amount,
                'daily_stats': daily_stats_list
            })
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Error in feeding_statistics: {e}")
        return JsonResponse({'error': str(e)}, status=500)