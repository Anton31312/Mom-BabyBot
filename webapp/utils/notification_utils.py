"""
Утилиты для работы с уведомлениями о беременности.

Этот модуль содержит функции для создания и управления уведомлениями
о новых неделях беременности и других важных событиях.
"""

from typing import List, Optional
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


def detect_new_pregnancy_weeks_for_user(user: User) -> List[int]:
    """
    Определяет новые недели беременности для конкретного пользователя.
    
    Args:
        user (User): Пользователь для проверки
        
    Returns:
        list: Список номеров новых недель беременности
    """
    from webapp.models import PregnancyInfo, PregnancyWeekNotification
    from webapp.utils.pregnancy_utils import detect_new_pregnancy_week
    
    new_weeks = []
    
    try:
        # Получаем активные беременности пользователя
        active_pregnancies = PregnancyInfo.objects.filter(user=user, is_active=True)
        
        for pregnancy_info in active_pregnancies:
            current_week = pregnancy_info.current_week
            
            if current_week and current_week > 0:
                # Получаем последнюю неделю, для которой было создано уведомление
                last_notification = PregnancyWeekNotification.objects.filter(
                    user=user,
                    pregnancy_info=pregnancy_info
                ).order_by('-week_number').first()
                
                last_checked_week = last_notification.week_number if last_notification else None
                
                # Проверяем, есть ли новая неделя
                new_week = detect_new_pregnancy_week(pregnancy_info, last_checked_week)
                
                if new_week:
                    new_weeks.append(new_week)
                    logger.info(f"Обнаружена новая неделя {new_week} для пользователя {user.username}")
    
    except Exception as e:
        logger.error(f"Ошибка при определении новых недель для пользователя {user.username}: {e}")
    
    return new_weeks


def check_and_create_pregnancy_week_notifications(user: Optional[User] = None) -> List:
    """
    Проверяет и создает уведомления о новых неделях беременности.
    
    Эта функция должна вызываться регулярно (например, ежедневно)
    для проверки наступления новых недель беременности у пользователей.
    
    Args:
        user (User, optional): Конкретный пользователь или None для всех
        
    Returns:
        list: Список созданных уведомлений
    """
    from webapp.models import PregnancyInfo, PregnancyWeekNotification
    from webapp.utils.pregnancy_utils import should_send_week_notification, create_week_notification_content
    
    created_notifications = []
    
    try:
        # Получаем пользователей для проверки
        if user:
            users_to_check = [user]
        else:
            # Получаем всех пользователей с активными беременностями
            users_to_check = User.objects.filter(
                pregnancy_info__is_active=True
            ).distinct()
        
        for user_obj in users_to_check:
            try:
                # Определяем новые недели для пользователя
                new_weeks = detect_new_pregnancy_weeks_for_user(user_obj)
                
                # Создаем уведомления для каждой новой недели
                for week_number in new_weeks:
                    # Получаем информацию о беременности
                    pregnancy_info = PregnancyInfo.objects.filter(
                        user=user_obj, 
                        is_active=True
                    ).first()
                    
                    if pregnancy_info and should_send_week_notification(pregnancy_info, week_number):
                        # Создаем контент уведомления
                        content = create_week_notification_content(week_number)
                        
                        # Создаем уведомление
                        with transaction.atomic():
                            notification = PregnancyWeekNotification.objects.create(
                                user=user_obj,
                                pregnancy_info=pregnancy_info,
                                week_number=week_number,
                                title=content['title'],
                                message=content['message']
                            )
                            created_notifications.append(notification)
                            
                            logger.info(
                                f"Создано уведомление о {week_number} неделе для пользователя {user_obj.username}"
                            )
                
            except Exception as e:
                logger.error(
                    f"Ошибка при создании уведомления для пользователя {user_obj.username}: {e}"
                )
                continue
    
    except Exception as e:
        logger.error(f"Ошибка при проверке уведомлений о неделях беременности: {e}")
    
    return created_notifications


def send_pregnancy_week_notifications(notifications: Optional[List] = None) -> int:
    """
    Отправляет уведомления о неделях беременности.
    
    В реальном приложении здесь была бы интеграция с системой отправки
    уведомлений (email, push-уведомления, SMS и т.д.).
    
    Args:
        notifications (list, optional): Список уведомлений для отправки
                                      или None для всех неотправленных
    
    Returns:
        int: Количество отправленных уведомлений
    """
    from webapp.models import PregnancyWeekNotification
    
    if notifications is None:
        # Получаем все неотправленные уведомления
        notifications = PregnancyWeekNotification.objects.filter(
            status='pending'
        ).select_related('user', 'pregnancy_info')
    
    sent_count = 0
    
    for notification in notifications:
        try:
            # Здесь была бы логика отправки уведомления
            # Например, отправка email или push-уведомления
            
            # Пока просто помечаем как отправленное
            notification.mark_as_sent()
            sent_count += 1
            
            logger.info(
                f"Отправлено уведомление о {notification.week_number} неделе "
                f"пользователю {notification.user.username}"
            )
            
        except Exception as e:
            logger.error(
                f"Ошибка при отправке уведомления {notification.id}: {e}"
            )
            notification.status = 'failed'
            notification.save(update_fields=['status'])
    
    return sent_count


def get_user_pregnancy_notifications(user: User, limit: int = 10) -> List:
    """
    Получает последние уведомления о беременности для пользователя.
    
    Args:
        user (User): Пользователь
        limit (int): Максимальное количество уведомлений
        
    Returns:
        list: Список уведомлений
    """
    from webapp.models import PregnancyWeekNotification
    
    return list(PregnancyWeekNotification.objects.filter(
        user=user
    ).select_related('pregnancy_info').order_by('-created_at')[:limit])


def mark_notification_as_read(notification_id: int, user: User) -> bool:
    """
    Отмечает уведомление как прочитанное.
    
    Args:
        notification_id (int): ID уведомления
        user (User): Пользователь (для проверки прав доступа)
        
    Returns:
        bool: True если уведомление было отмечено как прочитанное
    """
    from webapp.models import PregnancyWeekNotification
    
    try:
        notification = PregnancyWeekNotification.objects.get(
            id=notification_id,
            user=user
        )
        notification.mark_as_read()
        return True
    except PregnancyWeekNotification.DoesNotExist:
        return False


def get_notification_statistics(user: Optional[User] = None) -> dict:
    """
    Получает статистику по уведомлениям.
    
    Args:
        user (User, optional): Конкретный пользователь или None для всех
        
    Returns:
        dict: Статистика уведомлений
    """
    from webapp.models import PregnancyWeekNotification
    
    queryset = PregnancyWeekNotification.objects.all()
    if user:
        queryset = queryset.filter(user=user)
    
    total = queryset.count()
    pending = queryset.filter(status='pending').count()
    sent = queryset.filter(status='sent').count()
    read = queryset.filter(status='read').count()
    failed = queryset.filter(status='failed').count()
    
    return {
        'total': total,
        'pending': pending,
        'sent': sent,
        'read': read,
        'failed': failed,
        'delivery_rate': (sent + read) / total * 100 if total > 0 else 0,
        'read_rate': read / (sent + read) * 100 if (sent + read) > 0 else 0
    }


def cleanup_old_notifications(days_old: int = 90) -> int:
    """
    Удаляет старые прочитанные уведомления.
    
    Args:
        days_old (int): Возраст уведомлений в днях для удаления
        
    Returns:
        int: Количество удаленных уведомлений
    """
    from webapp.models import PregnancyWeekNotification
    
    cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
    
    old_notifications = PregnancyWeekNotification.objects.filter(
        status='read',
        read_at__lt=cutoff_date
    )
    
    count = old_notifications.count()
    old_notifications.delete()
    
    logger.info(f"Удалено {count} старых уведомлений")
    return count


def schedule_daily_pregnancy_check():
    """
    Планирует ежедневную проверку новых недель беременности.
    
    Эта функция должна вызываться один раз в день (например, в 9:00 утра)
    для проверки всех активных беременностей и создания уведомлений о новых неделях.
    
    Returns:
        dict: Результаты ежедневной проверки
    """
    logger.info("Начинаем ежедневную проверку недель беременности")
    
    try:
        from webapp.models import PregnancyInfo
        
        # Получаем статистику активных беременностей
        active_pregnancies_count = PregnancyInfo.objects.filter(is_active=True).count()
        
        # Проверяем и создаем новые уведомления
        new_notifications = check_and_create_pregnancy_week_notifications()
        
        # Группируем уведомления по неделям для статистики
        weeks_notified = {}
        for notification in new_notifications:
            week = notification.week_number
            if week not in weeks_notified:
                weeks_notified[week] = 0
            weeks_notified[week] += 1
        
        result = {
            'active_pregnancies_checked': active_pregnancies_count,
            'new_notifications_created': len(new_notifications),
            'weeks_notified': weeks_notified,
            'timestamp': timezone.now(),
            'status': 'success'
        }
        
        logger.info(f"Ежедневная проверка завершена успешно: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при ежедневной проверке недель беременности: {e}")
        return {
            'status': 'error',
            'error_message': str(e),
            'timestamp': timezone.now()
        }


def process_pregnancy_notifications():
    """
    Основная функция для обработки уведомлений о беременности.
    
    Эта функция должна вызываться регулярно (например, через cron или Celery)
    для проверки новых недель и отправки уведомлений.
    
    Returns:
        dict: Результаты обработки
    """
    logger.info("Начинаем обработку уведомлений о беременности")
    
    # Проверяем и создаем новые уведомления
    new_notifications = check_and_create_pregnancy_week_notifications()
    
    # Отправляем неотправленные уведомления
    sent_count = send_pregnancy_week_notifications()
    
    # Очищаем старые уведомления
    cleaned_count = cleanup_old_notifications()
    
    result = {
        'new_notifications_created': len(new_notifications),
        'notifications_sent': sent_count,
        'old_notifications_cleaned': cleaned_count,
        'timestamp': timezone.now()
    }
    
    logger.info(f"Обработка уведомлений завершена: {result}")
    return result


def check_pregnancy_week_transitions():
    """
    Проверяет переходы между неделями беременности для всех активных беременностей.
    
    Эта функция анализирует, у каких пользователей произошел переход на новую неделю
    с момента последней проверки, и создает соответствующие уведомления.
    
    Returns:
        dict: Детальная информация о переходах между неделями
    """
    from webapp.models import PregnancyInfo, PregnancyWeekNotification
    
    transitions = {
        'users_checked': 0,
        'transitions_detected': 0,
        'notifications_created': 0,
        'errors': [],
        'details': []
    }
    
    try:
        # Получаем все активные беременности
        active_pregnancies = PregnancyInfo.objects.filter(is_active=True).select_related('user')
        transitions['users_checked'] = active_pregnancies.count()
        
        for pregnancy_info in active_pregnancies:
            try:
                current_week = pregnancy_info.current_week
                
                if current_week and current_week > 0:
                    # Получаем последнее уведомление для этой беременности
                    last_notification = PregnancyWeekNotification.objects.filter(
                        user=pregnancy_info.user,
                        pregnancy_info=pregnancy_info
                    ).order_by('-week_number').first()
                    
                    last_notified_week = last_notification.week_number if last_notification else 0
                    
                    # Проверяем, есть ли переход на новую неделю
                    if current_week > last_notified_week:
                        transitions['transitions_detected'] += 1
                        
                        # Создаем уведомления для всех пропущенных недель
                        for week_to_notify in range(last_notified_week + 1, current_week + 1):
                            if should_send_week_notification(pregnancy_info, week_to_notify):
                                from webapp.utils.pregnancy_utils import create_week_notification_content
                                content = create_week_notification_content(week_to_notify)
                                
                                notification = PregnancyWeekNotification.objects.create(
                                    user=pregnancy_info.user,
                                    pregnancy_info=pregnancy_info,
                                    week_number=week_to_notify,
                                    title=content['title'],
                                    message=content['message']
                                )
                                
                                transitions['notifications_created'] += 1
                                transitions['details'].append({
                                    'user': pregnancy_info.user.username,
                                    'week': week_to_notify,
                                    'notification_id': notification.id
                                })
                                
                                logger.info(
                                    f"Создано уведомление о переходе на {week_to_notify} неделю "
                                    f"для пользователя {pregnancy_info.user.username}"
                                )
            
            except Exception as e:
                error_msg = f"Ошибка при проверке пользователя {pregnancy_info.user.username}: {e}"
                transitions['errors'].append(error_msg)
                logger.error(error_msg)
    
    except Exception as e:
        error_msg = f"Критическая ошибка при проверке переходов между неделями: {e}"
        transitions['errors'].append(error_msg)
        logger.error(error_msg)
    
    return transitions