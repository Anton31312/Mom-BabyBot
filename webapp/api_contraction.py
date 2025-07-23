"""
API эндпоинты для счетчика схваток.

Этот модуль содержит представления API для работы с сессиями схваток и событиями схваток.
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
    Contraction, ContractionEvent,
    get_contraction_sessions, create_contraction_session,
    end_contraction_session, add_contraction_event
)

logger = logging.getLogger(__name__)


def contraction_to_dict(contraction):
    """Преобразует объект Contraction в словарь."""
    events = []
    for event in contraction.contraction_events:
        events.append({
            'id': event.id,
            'timestamp': event.timestamp.isoformat() if event.timestamp else None,
            'duration': event.duration,
            'intensity': event.intensity
        })
    
    return {
        'id': contraction.id,
        'user_id': contraction.user_id,
        'start_time': contraction.start_time.isoformat() if contraction.start_time else None,
        'end_time': contraction.end_time.isoformat() if contraction.end_time else None,
        'notes': contraction.notes,
        'duration': contraction.duration,
        'count': contraction.count,
        'average_interval': contraction.average_interval,
        'events': events
    }


# API эндпоинты для сессий схваток
@method_decorator(csrf_exempt, name='dispatch')
class ContractionSessionsView(View):
    """
    API представление для получения списка и создания сессий схваток.
    
    URL: /api/users/{user_id}/contractions/
    Методы: GET, POST
    """
    
    def get(self, request, user_id):
        """Получить все сессии схваток для конкретного пользователя."""
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
            
            # Получаем сессии схваток
            contractions = get_contraction_sessions(user_id)
            
            # Преобразуем в словарь
            contractions_data = [contraction_to_dict(contraction) for contraction in contractions]
            
            return JsonResponse({'contractions': contractions_data})
        
        except Exception as e:
            logger.error(f"Error getting contraction sessions for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def post(self, request, user_id):
        """Создать новую сессию схваток."""
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
            
            # Создаем сессию схваток
            contraction = create_contraction_session(
                user_id=user_id,
                notes=data.get('notes')
            )
            
            # Возвращаем созданную сессию
            return JsonResponse(contraction_to_dict(contraction), status=201)
        
        except Exception as e:
            logger.error(f"Error creating contraction session for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContractionSessionDetailView(View):
    """
    API представление для получения, обновления и завершения конкретной сессии схваток.
    
    URL: /api/users/{user_id}/contractions/{session_id}/
    Методы: GET, PUT
    """
    
    def get(self, request, user_id, session_id):
        """Получить конкретную сессию схваток."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            session_id = int(session_id)
            
            # Получаем сессию схваток
            db_session = db_manager.get_session()
            try:
                contraction = db_session.query(Contraction).filter_by(id=session_id).first()
                
                # Проверяем существование сессии и принадлежность пользователю
                if not contraction:
                    return JsonResponse({'error': 'Сессия схваток не найдена'}, status=404)
                
                if contraction.user_id != user_id:
                    return JsonResponse({'error': 'Сессия схваток не принадлежит этому пользователю'}, status=403)
                
                # Возвращаем данные сессии
                return JsonResponse(contraction_to_dict(contraction))
            finally:
                db_manager.close_session(db_session)
        
        except Exception as e:
            logger.error(f"Error getting contraction session {session_id} for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def put(self, request, user_id, session_id):
        """Обновить или завершить сессию схваток."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            session_id = int(session_id)
            
            # Получаем сессию схваток
            db_session = db_manager.get_session()
            try:
                contraction = db_session.query(Contraction).filter_by(id=session_id).first()
                
                # Проверяем существование сессии и принадлежность пользователю
                if not contraction:
                    return JsonResponse({'error': 'Сессия схваток не найдена'}, status=404)
                
                if contraction.user_id != user_id:
                    return JsonResponse({'error': 'Сессия схваток не принадлежит этому пользователю'}, status=403)
            finally:
                db_manager.close_session(db_session)
            
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Проверяем, нужно ли завершить сессию
            if data.get('end_session', False):
                contraction = end_contraction_session(session_id)
            
            # Возвращаем обновленную сессию
            return JsonResponse(contraction_to_dict(contraction))
        
        except Exception as e:
            logger.error(f"Error updating contraction session {session_id} for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContractionEventView(View):
    """
    API представление для добавления событий схваток к сессии.
    
    URL: /api/users/{user_id}/contractions/{session_id}/events/
    Методы: POST
    """
    
    def post(self, request, user_id, session_id):
        """Добавить новое событие схватки к сессии."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            session_id = int(session_id)
            
            # Получаем сессию схваток
            db_session = db_manager.get_session()
            try:
                contraction = db_session.query(Contraction).filter_by(id=session_id).first()
                
                # Проверяем существование сессии и принадлежность пользователю
                if not contraction:
                    return JsonResponse({'error': 'Сессия схваток не найдена'}, status=404)
                
                if contraction.user_id != user_id:
                    return JsonResponse({'error': 'Сессия схваток не принадлежит этому пользователю'}, status=403)
                
                # Проверяем, не завершена ли сессия
                if contraction.end_time:
                    return JsonResponse({'error': 'Невозможно добавить событие к завершенной сессии'}, status=400)
            finally:
                db_manager.close_session(db_session)
            
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Добавляем событие схватки
            event = add_contraction_event(
                session_id=session_id,
                duration=data.get('duration'),
                intensity=data.get('intensity')
            )
            
            # Возвращаем данные события
            return JsonResponse({
                'id': event.id,
                'session_id': event.session_id,
                'timestamp': event.timestamp.isoformat() if event.timestamp else None,
                'duration': event.duration,
                'intensity': event.intensity
            }, status=201)
        
        except Exception as e:
            logger.error(f"Error adding contraction event to session {session_id} for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


# Функции маршрутизации URL
def contraction_sessions(request, user_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = ContractionSessionsView()
    if request.method == 'GET':
        return view.get(request, user_id)
    elif request.method == 'POST':
        return view.post(request, user_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def contraction_session_detail(request, user_id, session_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = ContractionSessionDetailView()
    if request.method == 'GET':
        return view.get(request, user_id, session_id)
    elif request.method == 'PUT':
        return view.put(request, user_id, session_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def contraction_events(request, user_id, session_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = ContractionEventView()
    if request.method == 'POST':
        return view.post(request, user_id, session_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)