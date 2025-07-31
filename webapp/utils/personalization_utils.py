"""
Утилиты для персонализации контента.

Этот модуль содержит функции для выбора и отображения персонализированного контента
на основе профиля пользователя. 
"""

from django.contrib.auth.models import User
from django.utils import timezone
from webapp.models import UserProfile, PersonalizedContent, UserContentView
import logging

logger = logging.getLogger(__name__)


def get_or_create_user_profile(user):
    """
    Получает или создает профиль пользователя.
    
    Args:
        user (User): Пользователь Django
        
    Returns:
        UserProfile: Профиль пользователя
    """
    try:
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'pregnancy_status': 'not_pregnant',
                'experience_level': 'first_time',
                'interests': [],
                'show_daily_tips': True,
                'preferred_content_frequency': 'daily'
            }
        )
        
        if created:
            logger.info(f"Создан новый профиль для пользователя {user.username}")
        
        return profile
    except Exception as e:
        logger.error(f"Ошибка при получении/создании профиля пользователя {user.username}: {e}")
        raise


def update_user_profile(user, **profile_data):
    """
    Обновляет профиль пользователя.
    
    Args:
        user (User): Пользователь Django
        **profile_data: Данные для обновления профиля
        
    Returns:
        UserProfile: Обновленный профиль пользователя
    """
    try:
        profile = get_or_create_user_profile(user)
        
        # Обновляем только переданные поля
        for field, value in profile_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        profile.save()
        logger.info(f"Обновлен профиль пользователя {user.username}")
        return profile
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении профиля пользователя {user.username}: {e}")
        raise


def get_personalized_content_for_user(user, content_type=None, limit=5):
    """
    Получает персонализированный контент для пользователя.
    
    Args:
        user (User): Пользователь Django
        content_type (str, optional): Тип контента для фильтрации
        limit (int): Максимальное количество элементов контента
        
    Returns:
        list: Список подходящего персонализированного контента
    """
    try:
        profile = get_or_create_user_profile(user)
        
        # Проверяем, должен ли показываться контент сегодня
        if not profile.should_show_content_today():
            return []
        
        # Получаем базовый queryset
        queryset = PersonalizedContent.objects.filter(is_active=True)
        
        # Фильтруем по типу контента, если указан
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        # Исключаем контент, который уже был показан (для show_once=True)
        viewed_content_ids = UserContentView.objects.filter(
            user=user,
            content__show_once=True
        ).values_list('content_id', flat=True)
        
        if viewed_content_ids:
            queryset = queryset.exclude(id__in=viewed_content_ids)
        
        # Фильтруем контент по критериям персонализации
        suitable_content = []
        for content in queryset:
            if content.is_suitable_for_user(profile):
                suitable_content.append(content)
        
        # Сортируем по приоритету и дате создания
        priority_order = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}
        suitable_content.sort(
            key=lambda x: (priority_order.get(x.priority, 0), x.created_at),
            reverse=True
        )
        
        return suitable_content[:limit]
        
    except Exception as e:
        logger.error(f"Ошибка при получении персонализированного контента для пользователя {user.username}: {e}")
        return []


def mark_content_as_viewed(user, content, interaction_type='viewed'):
    """
    Отмечает контент как просмотренный пользователем.
    
    Args:
        user (User): Пользователь Django
        content (PersonalizedContent): Контент
        interaction_type (str): Тип взаимодействия
        
    Returns:
        UserContentView: Запись о просмотре
    """
    try:
        view, created = UserContentView.objects.get_or_create(
            user=user,
            content=content,
            defaults={'interaction_type': interaction_type}
        )
        
        if not created and view.interaction_type != interaction_type:
            # Обновляем тип взаимодействия, если он изменился
            view.interaction_type = interaction_type
            view.save()
        
        logger.info(f"Контент '{content.title}' отмечен как {interaction_type} для пользователя {user.username}")
        return view
        
    except Exception as e:
        logger.error(f"Ошибка при отметке контента как просмотренного для пользователя {user.username}: {e}")
        raise


def get_content_recommendations_by_tags(user, tags, limit=3):
    """
    Получает рекомендации контента на основе тегов.
    
    Args:
        user (User): Пользователь Django
        tags (list): Список тегов для поиска контента
        limit (int): Максимальное количество рекомендаций
        
    Returns:
        list: Список рекомендованного контента
    """
    try:
        profile = get_or_create_user_profile(user)
        
        # Получаем весь активный контент (SQLite не поддерживает overlap)
        queryset = PersonalizedContent.objects.filter(is_active=True)
        
        # Исключаем уже просмотренный контент (для show_once=True)
        viewed_content_ids = UserContentView.objects.filter(
            user=user,
            content__show_once=True
        ).values_list('content_id', flat=True)
        
        if viewed_content_ids:
            queryset = queryset.exclude(id__in=viewed_content_ids)
        
        # Фильтруем по критериям персонализации и тегам
        suitable_content = []
        for content in queryset:
            # Проверяем пересечение тегов
            if content.interest_tags and any(tag in content.interest_tags for tag in tags):
                if content.is_suitable_for_user(profile):
                    suitable_content.append(content)
        
        # Сортируем по релевантности (количество совпадающих тегов) и приоритету
        def calculate_relevance(content):
            matching_tags = set(content.interest_tags).intersection(set(tags))
            priority_score = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}.get(content.priority, 0)
            return len(matching_tags) * 10 + priority_score
        
        suitable_content.sort(key=calculate_relevance, reverse=True)
        
        return suitable_content[:limit]
        
    except Exception as e:
        logger.error(f"Ошибка при получении рекомендаций по тегам для пользователя {user.username}: {e}")
        return []


def get_user_personalization_stats(user):
    """
    Получает статистику персонализации для пользователя.
    
    Args:
        user (User): Пользователь Django
        
    Returns:
        dict: Статистика персонализации
    """
    try:
        profile = get_or_create_user_profile(user)
        
        # Подсчитываем статистику просмотров контента
        total_views = UserContentView.objects.filter(user=user).count()
        content_by_type = {}
        
        for view in UserContentView.objects.filter(user=user).select_related('content'):
            content_type = view.content.get_content_type_display()
            content_by_type[content_type] = content_by_type.get(content_type, 0) + 1
        
        # Подсчитываем доступный контент
        available_content = len(get_personalized_content_for_user(user, limit=100))
        
        return {
            'profile': {
                'pregnancy_status': profile.get_pregnancy_status_display(),
                'pregnancy_week': profile.current_pregnancy_week,
                'experience_level': profile.get_experience_level_display(),
                'interests': profile.interests,
                'show_daily_tips': profile.show_daily_tips,
                'content_frequency': profile.get_preferred_content_frequency_display(),
            },
            'content_stats': {
                'total_views': total_views,
                'content_by_type': content_by_type,
                'available_content': available_content,
            },
            'personalization_tags': profile.get_personalization_tags(),
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики персонализации для пользователя {user.username}: {e}")
        return {}


def create_sample_personalized_content():
    """
    Создает примеры персонализированного контента для тестирования.
    
    Returns:
        list: Список созданного контента
    """
    sample_content = [
        {
            'title': 'Питание в первом триместре',
            'content': 'В первом триместре беременности особенно важно получать достаточно фолиевой кислоты. Включите в рацион зеленые листовые овощи, цитрусовые и обогащенные злаки.',
            'content_type': 'tip',
            'pregnancy_status_filter': ['pregnant'],
            'pregnancy_week_min': 1,
            'pregnancy_week_max': 12,
            'interest_tags': ['nutrition', 'health'],
            'priority': 'high'
        },
        {
            'title': 'Подготовка к родам',
            'content': 'На 36-40 неделе беременности важно подготовить сумку в роддом и обсудить план родов с врачом. Практикуйте дыхательные упражнения.',
            'content_type': 'recommendation',
            'pregnancy_status_filter': ['pregnant'],
            'pregnancy_week_min': 36,
            'pregnancy_week_max': 42,
            'interest_tags': ['health', 'safety'],
            'priority': 'urgent'
        },
        {
            'title': 'Развитие речи у малыша',
            'content': 'Читайте ребенку каждый день, даже если он еще очень мал. Это способствует развитию речи и укрепляет эмоциональную связь.',
            'content_type': 'tip',
            'pregnancy_status_filter': ['postpartum'],
            'interest_tags': ['development', 'education'],
            'experience_level_filter': ['first_time'],
            'priority': 'medium'
        },
        {
            'title': 'Безопасность дома для малыша',
            'content': 'Установите защитные замки на шкафы, заглушки на розетки и ограничители на двери. Безопасность - приоритет номер один.',
            'content_type': 'warning',
            'pregnancy_status_filter': ['postpartum'],
            'interest_tags': ['safety'],
            'priority': 'high'
        },
        {
            'title': 'Важность сна для мамы',
            'content': 'Спите, когда спит ребенок. Недостаток сна может повлиять на ваше здоровье и способность ухаживать за малышом.',
            'content_type': 'tip',
            'pregnancy_status_filter': ['postpartum'],
            'interest_tags': ['sleep', 'health'],
            'priority': 'medium'
        }
    ]
    
    created_content = []
    for content_data in sample_content:
        content, created = PersonalizedContent.objects.get_or_create(
            title=content_data['title'],
            defaults=content_data
        )
        if created:
            created_content.append(content)
            logger.info(f"Создан пример контента: {content.title}")
    
    return created_content


def analyze_user_engagement(user, days=30):
    """
    Анализирует вовлеченность пользователя с персонализированным контентом.
    
    Args:
        user (User): Пользователь Django
        days (int): Количество дней для анализа
        
    Returns:
        dict: Статистика вовлеченности
    """
    try:
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Получаем просмотры за указанный период
        views = UserContentView.objects.filter(
            user=user,
            viewed_at__gte=start_date
        ).select_related('content')
        
        # Анализируем типы взаимодействий
        interaction_stats = {}
        content_type_stats = {}
        
        for view in views:
            # Статистика по типам взаимодействий
            interaction_type = view.get_interaction_type_display()
            interaction_stats[interaction_type] = interaction_stats.get(interaction_type, 0) + 1
            
            # Статистика по типам контента
            content_type = view.content.get_content_type_display()
            content_type_stats[content_type] = content_type_stats.get(content_type, 0) + 1
        
        # Вычисляем показатели вовлеченности
        total_views = views.count()
        clicked_views = views.filter(interaction_type='clicked').count()
        saved_views = views.filter(interaction_type='saved').count()
        
        engagement_rate = (clicked_views + saved_views) / total_views * 100 if total_views > 0 else 0
        
        return {
            'period_days': days,
            'total_views': total_views,
            'interaction_stats': interaction_stats,
            'content_type_stats': content_type_stats,
            'engagement_rate': round(engagement_rate, 2),
            'most_engaged_content_type': max(content_type_stats, key=content_type_stats.get) if content_type_stats else None
        }
        
    except Exception as e:
        logger.error(f"Ошибка при анализе вовлеченности пользователя {user.username}: {e}")
        return {}