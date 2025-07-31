"""
API для системы достижений.

Этот модуль содержит API-представления для управления достижениями пользователей,
включая получение списка достижений, проверку прогресса и отображение статистики.

Соответствует требованию 9.3 о создании системы достижений.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
import json
import logging

from .models import Achievement, UserAchievement, AchievementNotification

logger = logging.getLogger(__name__)


@method_decorator([login_required, csrf_exempt], name='dispatch')
class AchievementListView(View):
    """
    API для получения списка достижений пользователя.
    
    GET: Возвращает список всех доступных достижений с информацией о прогрессе
    """
    
    def get(self, request):
        """
        Возвращает список достижений с информацией о прогрессе для текущего пользователя.
        
        Query параметры:
        - type: фильтр по типу достижения
        - completed: true/false - показывать только завершенные/незавершенные
        - page: номер страницы для пагинации
        - limit: количество элементов на странице (по умолчанию 20)
        """
        try:
            user = request.user
            
            # Получаем параметры запроса
            achievement_type = request.GET.get('type')
            completed_filter = request.GET.get('completed')
            page = int(request.GET.get('page', 1))
            limit = min(int(request.GET.get('limit', 20)), 100)  # Максимум 100 элементов
            
            # Базовый запрос
            achievements = Achievement.objects.filter(is_active=True)
            
            # Фильтрация по типу
            if achievement_type:
                achievements = achievements.filter(achievement_type=achievement_type)
            
            # Получаем ID уже полученных достижений
            earned_achievement_ids = set(
                UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
            )
            
            # Фильтрация по статусу завершения
            if completed_filter == 'true':
                achievements = achievements.filter(id__in=earned_achievement_ids)
            elif completed_filter == 'false':
                achievements = achievements.exclude(id__in=earned_achievement_ids)
            
            # Исключаем скрытые достижения, которые еще не получены
            achievements = achievements.exclude(
                Q(is_hidden=True) & ~Q(id__in=earned_achievement_ids)
            )
            
            # Пагинация
            paginator = Paginator(achievements, limit)
            page_obj = paginator.get_page(page)
            
            # Формируем ответ
            achievements_data = []
            for achievement in page_obj:
                progress_info = achievement.get_progress_for_user(user)
                is_earned = achievement.id in earned_achievement_ids
                
                achievement_data = {
                    'id': achievement.id,
                    'title': achievement.title,
                    'description': achievement.description,
                    'icon': achievement.icon,
                    'type': achievement.achievement_type,
                    'type_display': achievement.get_achievement_type_display(),
                    'difficulty': achievement.difficulty,
                    'difficulty_display': achievement.get_difficulty_display(),
                    'points': achievement.points,
                    'is_earned': is_earned,
                    'progress': progress_info if not is_earned else None,
                    'show_progress': achievement.show_progress and not is_earned,
                }
                
                # Добавляем информацию о дате получения, если достижение получено
                if is_earned:
                    try:
                        user_achievement = UserAchievement.objects.get(
                            user=user, achievement=achievement
                        )
                        achievement_data['earned_at'] = user_achievement.earned_at.isoformat()
                        achievement_data['days_since_earned'] = user_achievement.days_since_earned
                    except UserAchievement.DoesNotExist:
                        pass
                
                achievements_data.append(achievement_data)
            
            return JsonResponse({
                'success': True,
                'achievements': achievements_data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            })
            
        except Exception as e:
            logger.error(f'Ошибка при получении списка достижений для пользователя {request.user.id}: {e}')
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при загрузке достижений'
            }, status=500)


@method_decorator([login_required, csrf_exempt], name='dispatch')
class UserAchievementStatsView(View):
    """
    API для получения статистики достижений пользователя.
    
    GET: Возвращает подробную статистику по достижениям пользователя
    """
    
    def get(self, request):
        """
        Возвращает статистику достижений для текущего пользователя.
        """
        try:
            user = request.user
            
            # Получаем статистику
            stats = UserAchievement.get_user_statistics(user)
            
            # Добавляем дополнительную информацию
            total_available = Achievement.objects.filter(is_active=True).count()
            completion_percentage = (
                (stats['total_achievements'] / total_available * 100) 
                if total_available > 0 else 0
            )
            
            # Получаем недавние достижения
            recent_achievements = UserAchievement.get_recent_achievements(user, days=30)
            recent_achievements_data = []
            for ua in recent_achievements:
                recent_achievements_data.append({
                    'id': ua.achievement.id,
                    'title': ua.achievement.title,
                    'icon': ua.achievement.icon,
                    'points': ua.achievement.points,
                    'earned_at': ua.earned_at.isoformat(),
                    'days_ago': ua.days_since_earned,
                })
            
            # Получаем прогресс по незавершенным достижениям
            available_achievements = Achievement.get_available_achievements_for_user(user)
            progress_data = []
            for achievement in available_achievements[:5]:  # Топ 5 ближайших к завершению
                progress_info = achievement.get_progress_for_user(user)
                if progress_info['progress_percentage'] > 0:
                    progress_data.append({
                        'id': achievement.id,
                        'title': achievement.title,
                        'icon': achievement.icon,
                        'progress_percentage': progress_info['progress_percentage'],
                        'current_progress': progress_info['current_progress'],
                        'target_value': progress_info['target_value'],
                    })
            
            # Сортируем по проценту выполнения
            progress_data.sort(key=lambda x: x['progress_percentage'], reverse=True)
            
            return JsonResponse({
                'success': True,
                'statistics': {
                    **stats,
                    'total_available': total_available,
                    'completion_percentage': round(completion_percentage, 1),
                    'recent_achievements': recent_achievements_data,
                    'progress_towards_next': progress_data,
                }
            })
            
        except Exception as e:
            logger.error(f'Ошибка при получении статистики достижений для пользователя {request.user.id}: {e}')
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при загрузке статистики'
            }, status=500)


@method_decorator([login_required, csrf_exempt], name='dispatch')
class CheckAchievementsView(View):
    """
    API для проверки и присвоения новых достижений.
    
    POST: Проверяет условия всех достижений и присваивает новые
    """
    
    def post(self, request):
        """
        Проверяет все доступные достижения для пользователя и присваивает новые.
        
        Этот метод следует вызывать после важных действий пользователя
        (например, после добавления записи о кормлении, весе и т.д.)
        """
        try:
            user = request.user
            
            # Проверяем и присваиваем новые достижения
            new_achievements = Achievement.check_and_award_achievements(user)
            
            # Создаем уведомления для новых достижений
            notifications_created = []
            for user_achievement in new_achievements:
                notification = AchievementNotification.create_achievement_notification(
                    user, user_achievement.achievement
                )
                notifications_created.append(notification)
            
            # Формируем ответ
            new_achievements_data = []
            for ua in new_achievements:
                new_achievements_data.append({
                    'id': ua.achievement.id,
                    'title': ua.achievement.title,
                    'description': ua.achievement.description,
                    'icon': ua.achievement.icon,
                    'points': ua.achievement.points,
                    'type': ua.achievement.achievement_type,
                    'type_display': ua.achievement.get_achievement_type_display(),
                    'earned_at': ua.earned_at.isoformat(),
                })
            
            return JsonResponse({
                'success': True,
                'new_achievements': new_achievements_data,
                'count': len(new_achievements),
                'message': f'Проверка завершена. Получено новых достижений: {len(new_achievements)}'
            })
            
        except Exception as e:
            logger.error(f'Ошибка при проверке достижений для пользователя {request.user.id}: {e}')
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при проверке достижений'
            }, status=500)


@method_decorator([login_required, csrf_exempt], name='dispatch')
class AchievementNotificationsView(View):
    """
    API для работы с уведомлениями о достижениях.
    
    GET: Получить список уведомлений
    POST: Отметить уведомления как прочитанные
    """
    
    def get(self, request):
        """
        Возвращает список уведомлений о достижениях для пользователя.
        
        Query параметры:
        - unread_only: true/false - показывать только непрочитанные
        - limit: количество уведомлений (по умолчанию 10)
        """
        try:
            user = request.user
            unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
            limit = min(int(request.GET.get('limit', 10)), 50)
            
            # Получаем уведомления
            if unread_only:
                notifications = AchievementNotification.get_unread_notifications(user)
            else:
                notifications = AchievementNotification.objects.filter(user=user).select_related('achievement')
            
            notifications = notifications[:limit]
            
            # Формируем ответ
            notifications_data = []
            for notification in notifications:
                notification_data = {
                    'id': notification.id,
                    'type': notification.notification_type,
                    'type_display': notification.get_notification_type_display(),
                    'title': notification.title,
                    'message': notification.message,
                    'status': notification.status,
                    'status_display': notification.get_status_display(),
                    'created_at': notification.created_at.isoformat(),
                    'is_read': notification.status == 'read',
                }
                
                if notification.achievement:
                    notification_data['achievement'] = {
                        'id': notification.achievement.id,
                        'title': notification.achievement.title,
                        'icon': notification.achievement.icon,
                        'points': notification.achievement.points,
                    }
                
                notifications_data.append(notification_data)
            
            # Подсчитываем непрочитанные уведомления
            unread_count = AchievementNotification.get_unread_notifications(user).count()
            
            return JsonResponse({
                'success': True,
                'notifications': notifications_data,
                'unread_count': unread_count,
            })
            
        except Exception as e:
            logger.error(f'Ошибка при получении уведомлений для пользователя {request.user.id}: {e}')
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при загрузке уведомлений'
            }, status=500)
    
    def post(self, request):
        """
        Отмечает уведомления как прочитанные.
        
        Body параметры:
        - notification_ids: список ID уведомлений для отметки как прочитанные
        - mark_all: true - отметить все уведомления как прочитанные
        """
        try:
            user = request.user
            data = json.loads(request.body)
            
            if data.get('mark_all'):
                # Отмечаем все непрочитанные уведомления как прочитанные
                updated_count = AchievementNotification.objects.filter(
                    user=user,
                    status__in=['pending', 'sent', 'delivered']
                ).update(status='read', read_at=timezone.now())
                
                return JsonResponse({
                    'success': True,
                    'message': f'Отмечено как прочитанные: {updated_count} уведомлений'
                })
            
            elif 'notification_ids' in data:
                # Отмечаем конкретные уведомления как прочитанные
                notification_ids = data['notification_ids']
                if not isinstance(notification_ids, list):
                    return JsonResponse({
                        'success': False,
                        'error': 'notification_ids должен быть списком'
                    }, status=400)
                
                notifications = AchievementNotification.objects.filter(
                    user=user,
                    id__in=notification_ids
                )
                
                updated_count = 0
                for notification in notifications:
                    if notification.status != 'read':
                        notification.mark_as_read()
                        updated_count += 1
                
                return JsonResponse({
                    'success': True,
                    'message': f'Отмечено как прочитанные: {updated_count} уведомлений'
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Необходимо указать notification_ids или mark_all'
                }, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат JSON'
            }, status=400)
        except Exception as e:
            logger.error(f'Ошибка при обновлении уведомлений для пользователя {request.user.id}: {e}')
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при обновлении уведомлений'
            }, status=500)


@method_decorator([login_required, csrf_exempt], name='dispatch')
class AchievementDetailView(View):
    """
    API для получения детальной информации о конкретном достижении.
    
    GET: Возвращает подробную информацию о достижении и прогрессе пользователя
    """
    
    def get(self, request, achievement_id):
        """
        Возвращает детальную информацию о достижении.
        
        Args:
            achievement_id: ID достижения
        """
        try:
            user = request.user
            
            # Получаем достижение
            try:
                achievement = Achievement.objects.get(id=achievement_id, is_active=True)
            except Achievement.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Достижение не найдено'
                }, status=404)
            
            # Проверяем, скрыто ли достижение и не получено ли оно
            is_earned = UserAchievement.objects.filter(user=user, achievement=achievement).exists()
            if achievement.is_hidden and not is_earned:
                return JsonResponse({
                    'success': False,
                    'error': 'Достижение не найдено'
                }, status=404)
            
            # Получаем информацию о прогрессе
            progress_info = achievement.get_progress_for_user(user)
            
            # Формируем ответ
            achievement_data = {
                'id': achievement.id,
                'title': achievement.title,
                'description': achievement.description,
                'icon': achievement.icon,
                'type': achievement.achievement_type,
                'type_display': achievement.get_achievement_type_display(),
                'difficulty': achievement.difficulty,
                'difficulty_display': achievement.get_difficulty_display(),
                'points': achievement.points,
                'condition_type': achievement.condition_type,
                'condition_value': achievement.condition_value,
                'is_earned': is_earned,
                'progress': progress_info if not is_earned else None,
                'show_progress': achievement.show_progress,
            }
            
            # Добавляем информацию о получении, если достижение получено
            if is_earned:
                try:
                    user_achievement = UserAchievement.objects.get(user=user, achievement=achievement)
                    achievement_data.update({
                        'earned_at': user_achievement.earned_at.isoformat(),
                        'days_since_earned': user_achievement.days_since_earned,
                        'progress_data': user_achievement.progress_data,
                    })
                except UserAchievement.DoesNotExist:
                    pass
            
            return JsonResponse({
                'success': True,
                'achievement': achievement_data
            })
            
        except Exception as e:
            logger.error(f'Ошибка при получении информации о достижении {achievement_id} для пользователя {request.user.id}: {e}')
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при загрузке информации о достижении'
            }, status=500)


# Вспомогательные функции для интеграции с другими частями приложения

def trigger_achievement_check(user, context=None):
    """
    Вспомогательная функция для запуска проверки достижений.
    
    Эта функция должна вызываться из других частей приложения
    после важных действий пользователя.
    
    Args:
        user (User): Пользователь для проверки
        context (dict): Дополнительный контекст для логирования
        
    Returns:
        list: Список новых достижений
    """
    try:
        new_achievements = Achievement.check_and_award_achievements(user)
        
        # Создаем уведомления для новых достижений
        for user_achievement in new_achievements:
            AchievementNotification.create_achievement_notification(
                user, user_achievement.achievement
            )
        
        if new_achievements and context:
            logger.info(f'Пользователь {user.id} получил {len(new_achievements)} новых достижений. Контекст: {context}')
        
        return new_achievements
        
    except Exception as e:
        logger.error(f'Ошибка при проверке достижений для пользователя {user.id}: {e}')
        return []


def get_achievement_progress_summary(user):
    """
    Возвращает краткую сводку прогресса достижений для отображения в интерфейсе.
    
    Args:
        user (User): Пользователь
        
    Returns:
        dict: Сводка прогресса
    """
    try:
        stats = UserAchievement.get_user_statistics(user)
        unread_notifications = AchievementNotification.get_unread_notifications(user).count()
        
        return {
            'total_achievements': stats['total_achievements'],
            'total_points': stats['total_points'],
            'unread_notifications': unread_notifications,
            'recent_achievements_count': stats['recent_achievements'],
        }
        
    except Exception as e:
        logger.error(f'Ошибка при получении сводки прогресса для пользователя {user.id}: {e}')
        return {
            'total_achievements': 0,
            'total_points': 0,
            'unread_notifications': 0,
            'recent_achievements_count': 0,
        }