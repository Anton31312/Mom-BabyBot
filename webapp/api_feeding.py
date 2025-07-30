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

from botapp.models import User
from webapp.utils.db_utils import get_db_manager
from botapp.models_child import Child
from botapp.models_timers import FeedingSession

logger = logging.getLogger(__name__)


def feeding_session_to_dict(feeding_session):
    """Преобразует объект FeedingSession в словарь."""
    return {
        'id': feeding_session.id,
        'child_id': feeding_session.child_id,
        'timestamp': feeding_session.timestamp.isoformat() if feeding_session.timestamp else None,
        'end_time': feeding_session.end_time.isoformat() if hasattr(feeding_session, 'end_time') and feeding_session.end_time else None,
        'type': feeding_session.type,
        'amount': feeding_session.amount,
        'duration': feeding_session.duration,
        'breast': feeding_session.breast,
        'milk_type': getattr(feeding_session, 'milk_type', None),
        'food_type': getattr(feeding_session, 'food_type', None),
        'notes': feeding_session.notes,
        # Поля для таймеров (продолжительность в секундах)
        'left_breast_duration': getattr(feeding_session, 'left_breast_duration', 0) or 0,
        'right_breast_duration': getattr(feeding_session, 'right_breast_duration', 0) or 0,
        'left_timer_active': getattr(feeding_session, 'left_timer_active', False) or False,
        'right_timer_active': getattr(feeding_session, 'right_timer_active', False) or False,
        'left_timer_start': feeding_session.left_timer_start.isoformat() if hasattr(feeding_session, 'left_timer_start') and feeding_session.left_timer_start else None,
        'right_timer_start': feeding_session.right_timer_start.isoformat() if hasattr(feeding_session, 'right_timer_start') and feeding_session.right_timer_start else None,
        'last_active_breast': getattr(feeding_session, 'last_active_breast', None),
        'is_active': (getattr(feeding_session, 'left_timer_active', False) or getattr(feeding_session, 'right_timer_active', False)),
        # Дополнительные вычисляемые поля
        'total_duration_seconds': getattr(feeding_session, 'total_duration_seconds', 0) if hasattr(feeding_session, 'total_duration_seconds') else ((getattr(feeding_session, 'left_breast_duration', 0) or 0) + (getattr(feeding_session, 'right_breast_duration', 0) or 0)),
        'total_duration_minutes': round(((getattr(feeding_session, 'left_breast_duration', 0) or 0) + (getattr(feeding_session, 'right_breast_duration', 0) or 0)) / 60, 2),
        'left_breast_duration_minutes': round((getattr(feeding_session, 'left_breast_duration', 0) or 0) / 60, 2),
        'right_breast_duration_minutes': round((getattr(feeding_session, 'right_breast_duration', 0) or 0) / 60, 2)
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
        db_manager = get_db_manager()

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
        db_manager = get_db_manager()

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
@require_http_methods(["POST"])
def start_feeding_timer(request, user_id, child_id):
    """
    Запуск таймера кормления для указанной груди.
    
    POST: Запустить таймер для левой или правой груди
    Параметры JSON:
    - breast: 'left' или 'right'
    - session_id: ID существующей сессии (опционально, если не указан - создается новая)
    """
    try:
        user_id = int(user_id)
        child_id = int(child_id)
        
        data = json.loads(request.body)
        breast = data.get('breast')
        session_id = data.get('session_id')
        
        if breast not in ['left', 'right']:
            return JsonResponse({'error': 'Параметр breast должен быть "left" или "right"'}, status=400)
        
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
        try:
            # Проверяем пользователя и ребенка
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'Пользователь не найден'}, status=404)
                
            child = session.query(Child).filter_by(id=child_id).first()
            if not child or child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не найден или не принадлежит пользователю'}, status=404)
            
            # Получаем или создаем сессию кормления
            if session_id:
                feeding_session = session.query(FeedingSession).filter_by(id=session_id).first()
                if not feeding_session or feeding_session.child_id != child_id:
                    return JsonResponse({'error': 'Сессия кормления не найдена'}, status=404)
            else:
                # Создаем новую сессию
                feeding_session = FeedingSession(
                    child_id=child_id,
                    timestamp=datetime.utcnow(),
                    type='breast'
                )
                session.add(feeding_session)
                session.flush()  # Получаем ID без коммита
            
            # Проверяем, что таймер для этой груди не активен
            if breast == 'left' and feeding_session.left_timer_active:
                return JsonResponse({'error': 'Таймер для левой груди уже активен'}, status=400)
            elif breast == 'right' and feeding_session.right_timer_active:
                return JsonResponse({'error': 'Таймер для правой груди уже активен'}, status=400)
            
            # Запускаем таймер
            current_time = datetime.utcnow()
            if breast == 'left':
                feeding_session.left_timer_start = current_time
                feeding_session.left_timer_active = True
            else:
                feeding_session.right_timer_start = current_time
                feeding_session.right_timer_active = True
            
            feeding_session.last_active_breast = breast
            
            session.commit()
            session.refresh(feeding_session)
            
            breast_name = 'левой' if breast == 'left' else 'правой'
            return JsonResponse({
                'message': f'Таймер для {breast_name} груди запущен',
                'session_id': feeding_session.id,
                'breast': breast,
                'timer_start': current_time.isoformat(),
                'session_data': feeding_session_to_dict(feeding_session)
            })
            
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Error in start_feeding_timer: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def pause_feeding_timer(request, user_id, child_id, session_id):
    """
    Приостановка таймера кормления для указанной груди.
    
    POST: Приостановить таймер для левой или правой груди
    Параметры JSON:
    - breast: 'left' или 'right'
    """
    try:
        user_id = int(user_id)
        child_id = int(child_id)
        session_id = int(session_id)
        
        data = json.loads(request.body)
        breast = data.get('breast')
        
        if breast not in ['left', 'right']:
            return JsonResponse({'error': 'Параметр breast должен быть "left" или "right"'}, status=400)
        
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
        try:
            # Проверяем пользователя, ребенка и сессию
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'Пользователь не найден'}, status=404)
                
            child = session.query(Child).filter_by(id=child_id).first()
            if not child or child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не найден или не принадлежит пользователю'}, status=404)
            
            feeding_session = session.query(FeedingSession).filter_by(id=session_id).first()
            if not feeding_session or feeding_session.child_id != child_id:
                return JsonResponse({'error': 'Сессия кормления не найдена'}, status=404)
            
            # Проверяем, что таймер активен
            if breast == 'left' and not feeding_session.left_timer_active:
                return JsonResponse({'error': 'Таймер для левой груди не активен'}, status=400)
            elif breast == 'right' and not feeding_session.right_timer_active:
                return JsonResponse({'error': 'Таймер для правой груди не активен'}, status=400)
            
            # Приостанавливаем таймер и обновляем продолжительность
            current_time = datetime.utcnow()
            if breast == 'left':
                if feeding_session.left_timer_start:
                    elapsed_time = current_time - feeding_session.left_timer_start
                    elapsed_seconds = int(elapsed_time.total_seconds())
                    feeding_session.left_breast_duration = (feeding_session.left_breast_duration or 0) + elapsed_seconds
                feeding_session.left_timer_active = False
                feeding_session.left_timer_start = None
            else:
                if feeding_session.right_timer_start:
                    elapsed_time = current_time - feeding_session.right_timer_start
                    elapsed_seconds = int(elapsed_time.total_seconds())
                    feeding_session.right_breast_duration = (feeding_session.right_breast_duration or 0) + elapsed_seconds
                feeding_session.right_timer_active = False
                feeding_session.right_timer_start = None
            
            session.commit()
            session.refresh(feeding_session)
            
            return JsonResponse({
                'message': f'Таймер для {breast} груди приостановлен',
                'session_id': feeding_session.id,
                'breast': breast,
                'session_data': feeding_session_to_dict(feeding_session)
            })
            
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Error in pause_feeding_timer: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stop_feeding_session(request, user_id, child_id, session_id):
    """
    Завершение сессии кормления.
    
    POST: Остановить все таймеры и завершить сессию кормления
    """
    try:
        user_id = int(user_id)
        child_id = int(child_id)
        session_id = int(session_id)
        
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
        try:
            # Проверяем пользователя, ребенка и сессию
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'Пользователь не найден'}, status=404)
                
            child = session.query(Child).filter_by(id=child_id).first()
            if not child or child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не найден или не принадлежит пользователю'}, status=404)
            
            feeding_session = session.query(FeedingSession).filter_by(id=session_id).first()
            if not feeding_session or feeding_session.child_id != child_id:
                return JsonResponse({'error': 'Сессия кормления не найдена'}, status=404)
            
            # Останавливаем все активные таймеры
            current_time = datetime.utcnow()
            
            if feeding_session.left_timer_active and feeding_session.left_timer_start:
                elapsed_time = current_time - feeding_session.left_timer_start
                elapsed_seconds = int(elapsed_time.total_seconds())
                feeding_session.left_breast_duration = (feeding_session.left_breast_duration or 0) + elapsed_seconds
                feeding_session.left_timer_active = False
                feeding_session.left_timer_start = None
            
            if feeding_session.right_timer_active and feeding_session.right_timer_start:
                elapsed_time = current_time - feeding_session.right_timer_start
                elapsed_seconds = int(elapsed_time.total_seconds())
                feeding_session.right_breast_duration = (feeding_session.right_breast_duration or 0) + elapsed_seconds
                feeding_session.right_timer_active = False
                feeding_session.right_timer_start = None
            
            # Устанавливаем время окончания сессии
            feeding_session.end_time = current_time
            
            session.commit()
            session.refresh(feeding_session)
            
            return JsonResponse({
                'message': 'Сессия кормления завершена',
                'session_id': feeding_session.id,
                'session_data': feeding_session_to_dict(feeding_session)
            })
            
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Error in stop_feeding_session: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def switch_breast(request, user_id, child_id, session_id):
    """
    Переключение между грудями во время кормления.
    
    POST: Приостановить текущий активный таймер и запустить таймер для другой груди
    Параметры JSON:
    - to_breast: 'left' или 'right' - грудь, на которую переключаемся
    """
    try:
        user_id = int(user_id)
        child_id = int(child_id)
        session_id = int(session_id)
        
        data = json.loads(request.body)
        to_breast = data.get('to_breast')
        
        if to_breast not in ['left', 'right']:
            return JsonResponse({'error': 'Параметр to_breast должен быть "left" или "right"'}, status=400)
        
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
        try:
            # Проверяем пользователя, ребенка и сессию
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'Пользователь не найден'}, status=404)
                
            child = session.query(Child).filter_by(id=child_id).first()
            if not child or child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не найден или не принадлежит пользователю'}, status=404)
            
            feeding_session = session.query(FeedingSession).filter_by(id=session_id).first()
            if not feeding_session or feeding_session.child_id != child_id:
                return JsonResponse({'error': 'Сессия кормления не найдена'}, status=404)
            
            # Проверяем, что таймер для целевой груди не активен
            if to_breast == 'left' and feeding_session.left_timer_active:
                return JsonResponse({'error': 'Таймер для левой груди уже активен'}, status=400)
            elif to_breast == 'right' and feeding_session.right_timer_active:
                return JsonResponse({'error': 'Таймер для правой груди уже активен'}, status=400)
            
            current_time = datetime.utcnow()
            from_breast = None
            
            # Приостанавливаем активный таймер
            if feeding_session.left_timer_active:
                from_breast = 'left'
                if feeding_session.left_timer_start:
                    elapsed_time = current_time - feeding_session.left_timer_start
                    elapsed_seconds = int(elapsed_time.total_seconds())
                    feeding_session.left_breast_duration = (feeding_session.left_breast_duration or 0) + elapsed_seconds
                feeding_session.left_timer_active = False
                feeding_session.left_timer_start = None
            
            if feeding_session.right_timer_active:
                from_breast = 'right'
                if feeding_session.right_timer_start:
                    elapsed_time = current_time - feeding_session.right_timer_start
                    elapsed_seconds = int(elapsed_time.total_seconds())
                    feeding_session.right_breast_duration = (feeding_session.right_breast_duration or 0) + elapsed_seconds
                feeding_session.right_timer_active = False
                feeding_session.right_timer_start = None
            
            # Запускаем таймер для новой груди
            if to_breast == 'left':
                feeding_session.left_timer_start = current_time
                feeding_session.left_timer_active = True
            else:
                feeding_session.right_timer_start = current_time
                feeding_session.right_timer_active = True
            
            feeding_session.last_active_breast = to_breast
            
            session.commit()
            session.refresh(feeding_session)
            
            return JsonResponse({
                'message': f'Переключение с {from_breast or "неактивной"} груди на {to_breast}',
                'session_id': feeding_session.id,
                'from_breast': from_breast,
                'to_breast': to_breast,
                'session_data': feeding_session_to_dict(feeding_session)
            })
            
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Error in switch_breast: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_active_feeding_session(request, user_id, child_id):
    """
    Получение активной сессии кормления для ребенка.
    
    GET: Получить текущую активную сессию кормления (если есть)
    """
    try:
        user_id = int(user_id)
        child_id = int(child_id)
        
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
        try:
            # Проверяем пользователя и ребенка
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'Пользователь не найден'}, status=404)
                
            child = session.query(Child).filter_by(id=child_id).first()
            if not child or child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не найден или не принадлежит пользователю'}, status=404)
            
            # Ищем активную сессию кормления
            active_session = session.query(FeedingSession).filter(
                FeedingSession.child_id == child_id,
                or_(
                    FeedingSession.left_timer_active == True,
                    FeedingSession.right_timer_active == True
                )
            ).first()
            
            if active_session:
                return JsonResponse({
                    'has_active_session': True,
                    'session_data': feeding_session_to_dict(active_session)
                })
            else:
                return JsonResponse({
                    'has_active_session': False,
                    'session_data': None
                })
            
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Error in get_active_feeding_session: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def feeding_statistics(request, user_id, child_id):
    """
    Получение статистики кормления для ребенка.
    
    GET: Получить статистику кормления (общее время, средний объем и т.д.)
    Включает детальную статистику для каждой груди согласно требованию 6.4.
    """
    try:
        # Преобразуем ID в целые числа
        user_id = int(user_id)
        child_id = int(child_id)
        
        # Проверяем существование пользователя и ребенка
        db_manager = get_db_manager()

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
            
            # Получаем все сессии за сегодня
            today_sessions = session.query(FeedingSession).filter(
                FeedingSession.child_id == child_id,
                FeedingSession.timestamp >= today_start,
                FeedingSession.timestamp <= today_end
            ).all()
            
            # Получаем все сессии за неделю
            weekly_sessions = session.query(FeedingSession).filter(
                FeedingSession.child_id == child_id,
                FeedingSession.timestamp >= week_ago_start,
                FeedingSession.timestamp <= today_end
            ).all()
            
            # Функция для расчета статистики по сессиям
            def calculate_session_stats(sessions):
                stats = {
                    'total_count': len(sessions),
                    'breast_count': 0,
                    'bottle_count': 0,
                    'total_duration': 0,
                    'left_breast_duration': 0,
                    'right_breast_duration': 0,
                    'total_amount': 0,
                    'left_breast_percentage': 0,
                    'right_breast_percentage': 0,
                    'avg_session_duration': 0,
                    'longest_session': 0,
                    'shortest_session': 0
                }
                
                breast_sessions = []
                bottle_sessions = []
                session_durations = []
                
                for fs in sessions:
                    if fs.type == 'breast':
                        stats['breast_count'] += 1
                        breast_sessions.append(fs)
                        
                        # Используем новые поля для продолжительности каждой груди
                        left_duration = getattr(fs, 'left_breast_duration', 0) or 0
                        right_duration = getattr(fs, 'right_breast_duration', 0) or 0
                        
                        # Конвертируем секунды в минуты
                        left_minutes = left_duration / 60 if left_duration else 0
                        right_minutes = right_duration / 60 if right_duration else 0
                        
                        stats['left_breast_duration'] += left_minutes
                        stats['right_breast_duration'] += right_minutes
                        
                        total_session_duration = left_minutes + right_minutes
                        stats['total_duration'] += total_session_duration
                        
                        if total_session_duration > 0:
                            session_durations.append(total_session_duration)
                        
                    elif fs.type == 'bottle':
                        stats['bottle_count'] += 1
                        bottle_sessions.append(fs)
                        stats['total_amount'] += fs.amount or 0
                
                # Рассчитываем проценты для каждой груди
                if stats['total_duration'] > 0:
                    stats['left_breast_percentage'] = round(
                        (stats['left_breast_duration'] / stats['total_duration']) * 100, 1
                    )
                    stats['right_breast_percentage'] = round(
                        (stats['right_breast_duration'] / stats['total_duration']) * 100, 1
                    )
                
                # Рассчитываем статистику по продолжительности сессий
                if session_durations:
                    stats['avg_session_duration'] = round(sum(session_durations) / len(session_durations), 1)
                    stats['longest_session'] = round(max(session_durations), 1)
                    stats['shortest_session'] = round(min(session_durations), 1)
                
                # Округляем значения
                stats['total_duration'] = round(stats['total_duration'], 1)
                stats['left_breast_duration'] = round(stats['left_breast_duration'], 1)
                stats['right_breast_duration'] = round(stats['right_breast_duration'], 1)
                stats['total_amount'] = round(stats['total_amount'], 1)
                
                return stats
            
            # Рассчитываем статистику за сегодня
            today_stats = calculate_session_stats(today_sessions)
            
            # Рассчитываем статистику за неделю
            weekly_stats = calculate_session_stats(weekly_sessions)
            
            # Группируем по дням для графика
            daily_stats = {}
            for fs in weekly_sessions:
                day = fs.timestamp.date()
                if day not in daily_stats:
                    daily_stats[day] = {
                        'date': day.strftime('%d.%m'),
                        'count': 0,
                        'breast_duration': 0,
                        'left_breast_duration': 0,
                        'right_breast_duration': 0,
                        'bottle_amount': 0
                    }
                
                daily_stats[day]['count'] += 1
                if fs.type == 'breast':
                    left_duration = (getattr(fs, 'left_breast_duration', 0) or 0) / 60
                    right_duration = (getattr(fs, 'right_breast_duration', 0) or 0) / 60
                    total_duration = left_duration + right_duration
                    
                    daily_stats[day]['breast_duration'] += total_duration
                    daily_stats[day]['left_breast_duration'] += left_duration
                    daily_stats[day]['right_breast_duration'] += right_duration
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
                        'left_breast_duration': 0,
                        'right_breast_duration': 0,
                        'bottle_amount': 0
                    }
            
            # Сортируем по дате
            daily_stats_list = list(daily_stats.values())
            daily_stats_list.sort(key=lambda x: datetime.strptime(x['date'], '%d.%m'))
            
            # Рассчитываем средние значения за неделю
            days_count = 7
            weekly_avg_stats = {
                'count': round(weekly_stats['total_count'] / days_count, 1),
                'duration': round(weekly_stats['total_duration'] / days_count, 1),
                'left_breast_duration': round(weekly_stats['left_breast_duration'] / days_count, 1),
                'right_breast_duration': round(weekly_stats['right_breast_duration'] / days_count, 1),
                'amount': round(weekly_stats['total_amount'] / days_count, 1)
            }
            
            # Возвращаем расширенную статистику
            return JsonResponse({
                # Статистика за сегодня
                'today_count': today_stats['total_count'],
                'today_breast_count': today_stats['breast_count'],
                'today_bottle_count': today_stats['bottle_count'],
                'today_duration': today_stats['total_duration'],
                'today_left_breast_duration': today_stats['left_breast_duration'],
                'today_right_breast_duration': today_stats['right_breast_duration'],
                'today_amount': today_stats['total_amount'],
                'today_left_breast_percentage': today_stats['left_breast_percentage'],
                'today_right_breast_percentage': today_stats['right_breast_percentage'],
                
                # Статистика за неделю
                'weekly_total_count': weekly_stats['total_count'],
                'weekly_breast_count': weekly_stats['breast_count'],
                'weekly_bottle_count': weekly_stats['bottle_count'],
                'weekly_total_duration': weekly_stats['total_duration'],
                'weekly_left_breast_duration': weekly_stats['left_breast_duration'],
                'weekly_right_breast_duration': weekly_stats['right_breast_duration'],
                'weekly_total_amount': weekly_stats['total_amount'],
                'weekly_left_breast_percentage': weekly_stats['left_breast_percentage'],
                'weekly_right_breast_percentage': weekly_stats['right_breast_percentage'],
                'weekly_avg_session_duration': weekly_stats['avg_session_duration'],
                'weekly_longest_session': weekly_stats['longest_session'],
                'weekly_shortest_session': weekly_stats['shortest_session'],
                
                # Средние значения за неделю
                'weekly_avg_count': weekly_avg_stats['count'],
                'weekly_avg_duration': weekly_avg_stats['duration'],
                'weekly_avg_left_breast_duration': weekly_avg_stats['left_breast_duration'],
                'weekly_avg_right_breast_duration': weekly_avg_stats['right_breast_duration'],
                'weekly_avg_amount': weekly_avg_stats['amount'],
                
                # Данные для графика
                'daily_stats': daily_stats_list,
                
                # Дополнительная информация
                'has_data': len(weekly_sessions) > 0,
                'period_start': week_ago_start.isoformat(),
                'period_end': today_end.isoformat()
            })
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"Error in feeding_statistics: {e}")
        return JsonResponse({'error': str(e)}, status=500)