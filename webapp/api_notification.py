"""
API эндпоинты для управления уведомлениями.

Этот модуль содержит представления API для работы с настройками уведомлений
и интеграции с Telegram ботом.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from botapp.models import User
from webapp.utils.db_utils import get_db_manager
from botapp.models_notification import (
    NotificationPreference, get_notification_preferences,
    create_notification_preferences, update_notification_preferences,
    get_recent_notifications
)
from botapp.models_child import Child
from botapp.utils.telegram_notifier import (
    send_telegram_notification, format_sleep_notification,
    format_feeding_notification, format_contraction_notification,
    format_kick_notification
)

logger = logging.getLogger(__name__)


def notification_preference_to_dict(preference):
    """Преобразует объект NotificationPreference в словарь."""
    if not preference:
        return None
        
    return {
        'id': preference.id,
        'user_id': preference.user_id,
        'enabled': preference.enabled,
        'telegram_enabled': preference.telegram_enabled,
        'web_enabled': preference.web_enabled,
        'sleep_timer_notifications': preference.sleep_timer_notifications,
        'feeding_timer_notifications': preference.feeding_timer_notifications,
        'contraction_counter_notifications': preference.contraction_counter_notifications,
        'kick_counter_notifications': preference.kick_counter_notifications,
        'vaccine_reminder_notifications': preference.vaccine_reminder_notifications,
        'sleep_notification_frequency': preference.sleep_notification_frequency,
        'feeding_notification_frequency': preference.feeding_notification_frequency,
        'contraction_notification_frequency': preference.contraction_notification_frequency,
        'created_at': preference.created_at.isoformat() if preference.created_at else None,
        'updated_at': preference.updated_at.isoformat() if preference.updated_at else None
    }


def notification_log_to_dict(log):
    """Преобразует объект NotificationLog в словарь."""
    return {
        'id': log.id,
        'user_id': log.user_id,
        'notification_type': log.notification_type,
        'entity_id': log.entity_id,
        'channel': log.channel,
        'content': log.content,
        'sent_at': log.sent_at.isoformat() if log.sent_at else None,
        'status': log.status
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def notification_preferences(request, user_id):
    """
    Получение или создание настроек уведомлений для пользователя.
    
    GET: Получить настройки уведомлений пользователя
    POST: Создать или обновить настройки уведомлений
    """
    try:
        # Преобразуем ID в целое число
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
        
        if request.method == 'GET':
            # Получаем настройки уведомлений
            preferences = get_notification_preferences(user_id)
            
            # Если настройки не найдены, создаем их с значениями по умолчанию
            if not preferences:
                preferences = create_notification_preferences(user_id)
            
            # Преобразуем в словарь
            preferences_data = notification_preference_to_dict(preferences)
            
            return JsonResponse(preferences_data)
        
        elif request.method == 'POST':
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Создаем или обновляем настройки уведомлений
            preferences = create_notification_preferences(user_id, **data)
            
            # Преобразуем в словарь
            preferences_data = notification_preference_to_dict(preferences)
            
            return JsonResponse(preferences_data)
    
    except Exception as e:
        logger.error(f"Error in notification_preferences: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def notification_history(request, user_id):
    """
    Получение истории уведомлений для пользователя.
    
    GET: Получить историю уведомлений пользователя
    """
    try:
        # Преобразуем ID в целое число
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
        
        # Получаем параметры запроса
        notification_type = request.GET.get('type')
        limit = int(request.GET.get('limit', 10))
        
        # Получаем историю уведомлений
        logs = get_recent_notifications(user_id, notification_type, limit)
        
        # Преобразуем в словарь
        logs_data = [notification_log_to_dict(log) for log in logs]
        
        return JsonResponse({'notification_logs': logs_data})
    
    except Exception as e:
        logger.error(f"Error in notification_history: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def test_notification(request, user_id):
    """
    Отправка тестового уведомления пользователю.
    
    POST: Отправить тестовое уведомление
    """
    try:
        # Преобразуем ID в целое число
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
        notification_type = data.get('type', 'test')
        
        # Отправляем тестовое уведомление
        text = "🔔 <b>Тестовое уведомление</b>\n\nЭто тестовое уведомление для проверки интеграции с Telegram ботом."
        success = send_telegram_notification(user_id, notification_type, 0, text)
        
        if success:
            return JsonResponse({'success': True, 'message': 'Тестовое уведомление отправлено'})
        else:
            return JsonResponse({'success': False, 'message': 'Не удалось отправить тестовое уведомление'}, status=500)
    
    except Exception as e:
        logger.error(f"Error in test_notification: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_notification(request, user_id):
    """
    Отправка уведомления пользователю.
    
    POST: Отправить уведомление
    """
    try:
        # Преобразуем ID в целое число
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
        notification_type = data.get('notification_type')
        entity_id = data.get('entity_id')
        notification_data = data.get('data', {})
        
        if not notification_type or not entity_id:
            return JsonResponse({'error': 'Не указан тип уведомления или ID сущности'}, status=400)
        
        # Формируем текст уведомления в зависимости от типа
        text = None
        
        if notification_type == 'sleep':
            # Получаем имя ребенка
            child_name = notification_data.get('child_name', 'Ребенок')
            if notification_data.get('child_id'):
                db_manager = get_db_manager()

                session = db_manager.get_session()
                try:
                    child = session.query(Child).filter_by(id=notification_data.get('child_id')).first()
                    if child and child.name:
                        child_name = child.name
                finally:
                    db_manager.close_session(session)
            
            text = format_sleep_notification(
                child_name=child_name,
                duration_minutes=notification_data.get('duration_minutes', 0),
                sleep_type=notification_data.get('sleep_type', 'day')
            )
        
        elif notification_type == 'feeding':
            # Получаем имя ребенка
            child_name = notification_data.get('child_name', 'Ребенок')
            if notification_data.get('child_id'):
                db_manager = get_db_manager()

                session = db_manager.get_session()
                try:
                    child = session.query(Child).filter_by(id=notification_data.get('child_id')).first()
                    if child and child.name:
                        child_name = child.name
                finally:
                    db_manager.close_session(session)
            
            text = format_feeding_notification(
                child_name=child_name,
                feeding_type=notification_data.get('feeding_type', 'bottle'),
                amount=notification_data.get('amount'),
                duration=notification_data.get('duration'),
                breast=notification_data.get('breast')
            )
        
        elif notification_type == 'contraction':
            text = format_contraction_notification(
                count=notification_data.get('count', 0),
                avg_interval=notification_data.get('avg_interval', 0),
                duration=notification_data.get('duration', 0)
            )
        
        elif notification_type == 'kick':
            text = format_kick_notification(
                count=notification_data.get('count', 0),
                duration=notification_data.get('duration', 0)
            )
        
        else:
            # Для неизвестных типов используем общий формат
            text = f"🔔 <b>Уведомление</b>\n\n{notification_data.get('message', 'Новое уведомление')}"
        
        # Отправляем уведомление
        success = send_telegram_notification(user_id, notification_type, entity_id, text)
        
        if success:
            return JsonResponse({'success': True, 'message': 'Уведомление отправлено'})
        else:
            return JsonResponse({'success': False, 'message': 'Не удалось отправить уведомление'}, status=500)
    
    except Exception as e:
        logger.error(f"Error in send_notification: {e}")
        return JsonResponse({'error': str(e)}, status=500)