"""
API эндпоинты для счетчика шевелений.

Этот модуль содержит представления API для работы с сессиями шевелений и событиями шевелений.
"""

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator

from botapp.models import User
from webapp.utils.db_utils import get_db_manager
from botapp.models_timers import (
    Kick, KickEvent,
    get_kick_sessions, create_kick_session,
    end_kick_session, add_kick_event
)

logger = logging.getLogger(__name__)


def kick_to_dict(kick):
    """Преобразует объект Kick в словарь."""
    events = []
    for event in kick.kick_events:
        events.append({
            'id': event.id,
            'timestamp': event.timestamp.isoformat() if event.timestamp else None,
            'intensity': event.intensity
        })
    
    return {
        'id': kick.id,
        'user_id': kick.user_id,
        'start_time': kick.start_time.isoformat() if kick.start_time else None,
        'end_time': kick.end_time.isoformat() if kick.end_time else None,
        'notes': kick.notes,
        'duration': kick.duration,
        'count': kick.count,
        'average_interval': kick.average_interval,
        'events': events
    }


# API эндпоинты для сессий шевелений
@method_decorator(csrf_exempt, name='dispatch')
class KickSessionsView(View):
    """
    API представление для получения списка и создания сессий шевелений.
    
    URL: /api/users/{user_id}/kicks/
    Методы: GET, POST
    """
    
    def get(self, request, user_id):
        """Получить все сессии шевелений для конкретного пользователя."""
        try:
            # Преобразуем user_id в целое число
            user_id = int(user_id)
            
            # Проверяем существование пользователя
            db_manager = get_db_manager()

            session = db_manager.get_session()
            try:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return JsonResponse({'error': 'Пользователь не найден'}, status=404)
            finally:
                db_manager.close_session(session)
            
            # Получаем сессии шевелений
            kicks = get_kick_sessions(user_id)
            
            # Преобразуем в словарь
            kicks_data = [kick_to_dict(kick) for kick in kicks]
            
            return JsonResponse({'kicks': kicks_data})
        
        except Exception as e:
            logger.error(f"Error getting kick sessions for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def post(self, request, user_id):
        """Создать новую сессию шевелений."""
        try:
            # Преобразуем user_id в целое число
            user_id = int(user_id)
            
            # Проверяем существование пользователя
            db_manager = get_db_manager()

            session = db_manager.get_session()
            try:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return JsonResponse({'error': 'Пользователь не найден'}, status=404)
            finally:
                db_manager.close_session(session)
            
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Создаем сессию шевелений
            kick = create_kick_session(
                user_id=user_id,
                notes=data.get('notes')
            )
            
            # Возвращаем созданную сессию
            return JsonResponse(kick_to_dict(kick), status=201)
        
        except Exception as e:
            logger.error(f"Error creating kick session for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class KickSessionDetailView(View):
    """
    API представление для получения, обновления и завершения конкретной сессии шевелений.
    
    URL: /api/users/{user_id}/kicks/{session_id}/
    Методы: GET, PUT
    """
    
    def get(self, request, user_id, session_id):
        """Получить конкретную сессию шевелений."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            session_id = int(session_id)
            
            # Получаем сессию шевелений
            db_session = db_manager.get_session()
            try:
                kick = db_session.query(Kick).filter_by(id=session_id).first()
                
                # Проверяем существование сессии и принадлежность пользователю
                if not kick:
                    return JsonResponse({'error': 'Сессия шевелений не найдена'}, status=404)
                
                if kick.user_id != user_id:
                    return JsonResponse({'error': 'Сессия шевелений не принадлежит этому пользователю'}, status=403)
                
                # Возвращаем данные сессии
                return JsonResponse(kick_to_dict(kick))
            finally:
                db_manager.close_session(db_session)
        
        except Exception as e:
            logger.error(f"Error getting kick session {session_id} for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def put(self, request, user_id, session_id):
        """Обновить или завершить сессию шевелений."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            session_id = int(session_id)
            
            # Получаем сессию шевелений
            db_session = db_manager.get_session()
            try:
                kick = db_session.query(Kick).filter_by(id=session_id).first()
                
                # Проверяем существование сессии и принадлежность пользователю
                if not kick:
                    return JsonResponse({'error': 'Сессия шевелений не найдена'}, status=404)
                
                if kick.user_id != user_id:
                    return JsonResponse({'error': 'Сессия шевелений не принадлежит этому пользователю'}, status=403)
            finally:
                db_manager.close_session(db_session)
            
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Проверяем, нужно ли завершить сессию
            if data.get('end_session', False):
                kick = end_kick_session(session_id)
            
            # Возвращаем обновленную сессию
            return JsonResponse(kick_to_dict(kick))
        
        except Exception as e:
            logger.error(f"Error updating kick session {session_id} for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class KickEventView(View):
    """
    API представление для добавления событий шевелений к сессии.
    
    URL: /api/users/{user_id}/kicks/{session_id}/events/
    Методы: POST
    """
    
    def post(self, request, user_id, session_id):
        """Добавить новое событие шевеления к сессии."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            session_id = int(session_id)
            
            # Получаем сессию шевелений
            db_session = db_manager.get_session()
            try:
                kick = db_session.query(Kick).filter_by(id=session_id).first()
                
                # Проверяем существование сессии и принадлежность пользователю
                if not kick:
                    return JsonResponse({'error': 'Сессия шевелений не найдена'}, status=404)
                
                if kick.user_id != user_id:
                    return JsonResponse({'error': 'Сессия шевелений не принадлежит этому пользователю'}, status=403)
                
                # Проверяем, не завершена ли сессия
                if kick.end_time:
                    return JsonResponse({'error': 'Невозможно добавить событие к завершенной сессии'}, status=400)
            finally:
                db_manager.close_session(db_session)
            
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Добавляем событие шевеления
            event = add_kick_event(
                session_id=session_id,
                intensity=data.get('intensity')
            )
            
            # Возвращаем данные события
            return JsonResponse({
                'id': event.id,
                'session_id': event.session_id,
                'timestamp': event.timestamp.isoformat() if event.timestamp else None,
                'intensity': event.intensity
            }, status=201)
        
        except Exception as e:
            logger.error(f"Error adding kick event to session {session_id} for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


# Функции маршрутизации URL
def kick_sessions(request, user_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = KickSessionsView()
    if request.method == 'GET':
        return view.get(request, user_id)
    elif request.method == 'POST':
        return view.post(request, user_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def kick_session_detail(request, user_id, session_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = KickSessionDetailView()
    if request.method == 'GET':
        return view.get(request, user_id, session_id)
    elif request.method == 'PUT':
        return view.put(request, user_id, session_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def kick_events(request, user_id, session_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = KickEventView()
    if request.method == 'POST':
        return view.post(request, user_id, session_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)