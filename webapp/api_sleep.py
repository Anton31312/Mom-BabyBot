"""
API эндпоинты для таймера сна.

Этот модуль содержит представления API для работы с сессиями сна.
"""

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from botapp.models import User, db_manager
from botapp.models_child import Child, get_child
from botapp.models_timers import (
    SleepSession, get_sleep_sessions, create_sleep_session, end_sleep_session
)

logger = logging.getLogger(__name__)


def sleep_session_to_dict(sleep_session):
    """Преобразует объект SleepSession в словарь."""
    return {
        'id': sleep_session.id,
        'child_id': sleep_session.child_id,
        'start_time': sleep_session.start_time.isoformat() if sleep_session.start_time else None,
        'end_time': sleep_session.end_time.isoformat() if sleep_session.end_time else None,
        'type': sleep_session.type,
        'quality': sleep_session.quality,
        'notes': sleep_session.notes,
        'duration': sleep_session.duration,
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def sleep_sessions(request, user_id, child_id):
    """
    Получение списка сессий сна или создание новой сессии.

    GET: Получить все сессии сна для конкретного ребенка
    POST: Создать новую сессию сна
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
        finally:
            db_manager.close_session(session)

        if request.method == 'GET':
            # Получаем сессии сна
            sleep_sessions_list = get_sleep_sessions(child_id)

            # Преобразуем в словарь
            sleep_sessions_data = [sleep_session_to_dict(
                session) for session in sleep_sessions_list]

            return JsonResponse({'sleep_sessions': sleep_sessions_data})

        elif request.method == 'POST':
            # Разбираем данные запроса
            data = json.loads(request.body)

            # Создаем сессию сна
            sleep_session = create_sleep_session(
                child_id=child_id,
                type=data.get('type', 'day'),
                quality=data.get('quality'),
                notes=data.get('notes')
            )

            # Возвращаем созданную сессию
            return JsonResponse(sleep_session_to_dict(sleep_session), status=201)

    except Exception as e:
        logger.error(f"Error in sleep_sessions: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def sleep_session_detail(request, user_id, child_id, session_id):
    """
    Получение, обновление или удаление конкретной сессии сна.

    GET: Получить детали сессии сна
    PUT: Обновить сессию сна (завершить или изменить параметры)
    DELETE: Удалить сессию сна
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

            # Получаем сессию сна
            sleep_session = session.query(
                SleepSession).filter_by(id=session_id).first()
            if not sleep_session:
                return JsonResponse({'error': 'Сессия сна не найдена'}, status=404)

            if sleep_session.child_id != child_id:
                return JsonResponse({'error': 'Сессия сна не принадлежит этому ребенку'}, status=403)
        finally:
            db_manager.close_session(session)

        if request.method == 'GET':
            # Возвращаем данные сессии сна
            return JsonResponse(sleep_session_to_dict(sleep_session))

        elif request.method == 'PUT':
            # Разбираем данные запроса
            data = json.loads(request.body)

            # Если запрос на завершение сессии
            if data.get('end_session', False):
                updated_session = end_sleep_session(
                    session_id=session_id,
                    quality=data.get('quality')
                )
                return JsonResponse(sleep_session_to_dict(updated_session))

            # Если запрос на обновление других параметров
            session = db_manager.get_session()
            try:
                sleep_session = session.query(
                    SleepSession).filter_by(id=session_id).first()

                if 'type' in data:
                    sleep_session.type = data['type']

                if 'quality' in data:
                    sleep_session.quality = data['quality']

                if 'notes' in data:
                    sleep_session.notes = data['notes']

                session.commit()
                session.refresh(sleep_session)

                return JsonResponse(sleep_session_to_dict(sleep_session))
            except Exception as e:
                session.rollback()
                raise e
            finally:
                db_manager.close_session(session)

        elif request.method == 'DELETE':
            # Удаляем сессию сна
            session = db_manager.get_session()
            try:
                sleep_session = session.query(
                    SleepSession).filter_by(id=session_id).first()
                session.delete(sleep_session)
                session.commit()

                return JsonResponse({'message': 'Сессия сна успешно удалена'})
            except Exception as e:
                session.rollback()
                raise e
            finally:
                db_manager.close_session(session)

    except Exception as e:
        logger.error(f"Error in sleep_session_detail: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def sleep_statistics(request, user_id, child_id):
    """
    Получение статистики сна для ребенка.

    GET: Получить статистику сна (общее время, средняя продолжительность и т.д.)
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

            # Получаем все сессии сна
            sleep_sessions_list = get_sleep_sessions(child_id)
        finally:
            db_manager.close_session(session)

        # Рассчитываем статистику
        total_sessions = len(sleep_sessions_list)
        day_sessions = [
            s for s in sleep_sessions_list if s.type == 'day' and s.end_time]
        night_sessions = [
            s for s in sleep_sessions_list if s.type == 'night' and s.end_time]

        # Общее время сна
        total_day_sleep = sum([s.duration or 0 for s in day_sessions])
        total_night_sleep = sum([s.duration or 0 for s in night_sessions])

        # Средняя продолжительность
        avg_day_sleep = total_day_sleep / \
            len(day_sessions) if day_sessions else 0
        avg_night_sleep = total_night_sleep / \
            len(night_sessions) if night_sessions else 0

        # Среднее качество сна
        avg_quality = sum([s.quality or 0 for s in sleep_sessions_list if s.quality]) / len(
            [s for s in sleep_sessions_list if s.quality]) if [s for s in sleep_sessions_list if s.quality] else 0

        # Возвращаем статистику
        return JsonResponse({
            'total_sessions': total_sessions,
            'day_sessions': len(day_sessions),
            'night_sessions': len(night_sessions),
            'total_day_sleep': total_day_sleep,
            'total_night_sleep': total_night_sleep,
            'avg_day_sleep': avg_day_sleep,
            'avg_night_sleep': avg_night_sleep,
            'avg_quality': avg_quality
        })
    except Exception as e:
        logger.error(f"Error in sleep_statistics: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def active_sleep_session(request, user_id, child_id):
    """
    Получение активной сессии сна для ребенка.

    GET: Получить активную сессию сна (если есть)
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

            # Ищем активную сессию сна (без end_time)
            active_session = session.query(SleepSession).filter_by(
                child_id=child_id, end_time=None).first()
            
            if not active_session:
                return JsonResponse({'message': 'Активная сессия сна не найдена'}, status=404)
                
            # Возвращаем данные активной сессии
            return JsonResponse(sleep_session_to_dict(active_session))
        finally:
            db_manager.close_session(session)
    except Exception as e:
        logger.error(f"Error in active_sleep_session: {e}")
        return JsonResponse({'error': str(e)}, status=500)