"""
Утилиты для работы с ежедневными советами и фактами.

Этот модуль содержит функции для получения и отображения ежедневных советов
на основе профиля пользователя. Соответствует требованию 9.2 о реализации
ежедневных советов и фактов.
"""

from django.contrib.auth.models import User
from django.utils import timezone
from webapp.models import DailyTip, UserDailyTipView, UserProfile
from webapp.utils.personalization_utils import get_or_create_user_profile
import logging
import random

logger = logging.getLogger(__name__)


def get_daily_tip_for_user(user, exclude_seen_today=True):
    """
    Получает ежедневный совет для пользователя.
    
    Args:
        user (User): Пользователь Django
        exclude_seen_today (bool): Исключать советы, уже просмотренные сегодня
        
    Returns:
        DailyTip or None: Подходящий совет или None
    """
    try:
        user_profile = get_or_create_user_profile(user)
        
        # Получаем все активные советы
        tips = DailyTip.objects.filter(is_active=True)
        
        # Исключаем советы, уже просмотренные сегодня
        if exclude_seen_today:
            today = timezone.now().date()
            seen_tip_ids = UserDailyTipView.objects.filter(
                user=user,
                viewed_at__date=today
            ).values_list('tip_id', flat=True)
            
            if seen_tip_ids:
                tips = tips.exclude(id__in=seen_tip_ids)
        
        # Фильтруем подходящие советы
        suitable_tips = []
        for tip in tips:
            if tip.is_suitable_for_user_profile(user_profile):
                suitable_tips.append(tip)
        
        if not suitable_tips:
            logger.info(f"Нет подходящих советов для пользователя {user.username}")
            return None
        
        # Сортируем по приоритету и добавляем элемент случайности
        suitable_tips.sort(key=lambda x: (x.priority, random.random()), reverse=True)
        
        selected_tip = suitable_tips[0]
        logger.info(f"Выбран совет '{selected_tip.title}' для пользователя {user.username}")
        
        return selected_tip
        
    except Exception as e:
        logger.error(f"Ошибка при получении ежедневного совета для пользователя {user.username}: {e}")
        return None


def mark_tip_as_viewed(user, tip, interaction_type='viewed'):
    """
    Отмечает совет как просмотренный пользователем.
    
    Args:
        user (User): Пользователь Django
        tip (DailyTip): Совет
        interaction_type (str): Тип взаимодействия
        
    Returns:
        UserDailyTipView: Запись о просмотре
    """
    try:
        view = UserDailyTipView.mark_tip_as_viewed(user, tip, interaction_type)
        logger.info(f"Совет '{tip.title}' отмечен как {interaction_type} для пользователя {user.username}")
        return view
        
    except Exception as e:
        logger.error(f"Ошибка при отметке совета как просмотренного для пользователя {user.username}: {e}")
        raise


def get_tips_for_pregnancy_week(pregnancy_week, limit=5):
    """
    Получает советы для определенной недели беременности.
    
    Args:
        pregnancy_week (int): Неделя беременности
        limit (int): Максимальное количество советов
        
    Returns:
        QuerySet: Подходящие советы
    """
    try:
        tips = DailyTip.get_tips_for_week(pregnancy_week)[:limit]
        logger.info(f"Найдено {len(tips)} советов для {pregnancy_week} недели беременности")
        return tips
        
    except Exception as e:
        logger.error(f"Ошибка при получении советов для {pregnancy_week} недели беременности: {e}")
        return DailyTip.objects.none()


def get_user_tip_statistics(user, days=30):
    """
    Получает статистику просмотров советов пользователем.
    
    Args:
        user (User): Пользователь Django
        days (int): Количество дней для анализа
        
    Returns:
        dict: Статистика просмотров
    """
    try:
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Получаем просмотры за указанный период
        views = UserDailyTipView.objects.filter(
            user=user,
            viewed_at__gte=start_date
        ).select_related('tip')
        
        # Анализируем типы взаимодействий
        interaction_stats = {}
        tip_type_stats = {}
        
        for view in views:
            # Статистика по типам взаимодействий
            interaction_type = view.get_interaction_type_display()
            interaction_stats[interaction_type] = interaction_stats.get(interaction_type, 0) + 1
            
            # Статистика по типам советов
            tip_type = view.tip.get_tip_type_display()
            tip_type_stats[tip_type] = tip_type_stats.get(tip_type, 0) + 1
        
        total_views = views.count()
        liked_views = views.filter(interaction_type='liked').count()
        dismissed_views = views.filter(interaction_type='dismissed').count()
        
        # Вычисляем показатели вовлеченности
        engagement_rate = (liked_views / total_views * 100) if total_views > 0 else 0
        dismissal_rate = (dismissed_views / total_views * 100) if total_views > 0 else 0
        
        return {
            'period_days': days,
            'total_views': total_views,
            'interaction_stats': interaction_stats,
            'tip_type_stats': tip_type_stats,
            'engagement_rate': round(engagement_rate, 2),
            'dismissal_rate': round(dismissal_rate, 2),
            'most_popular_tip_type': max(tip_type_stats, key=tip_type_stats.get) if tip_type_stats else None
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики советов для пользователя {user.username}: {e}")
        return {}


def create_sample_daily_tips():
    """
    Создает примеры ежедневных советов для тестирования.
    
    Returns:
        list: Список созданных советов
    """
    sample_tips = [
        {
            'title': 'Питание в первом триместре',
            'content': 'В первом триместре беременности особенно важно получать достаточно фолиевой кислоты. Включите в рацион зеленые листовые овощи, цитрусовые и обогащенные злаки.',
            'tip_type': 'tip',
            'pregnancy_week_min': 1,
            'pregnancy_week_max': 12,
            'audience': 'pregnant',
            'priority': 8
        },
        {
            'title': 'Развитие плода на 20 неделе',
            'content': 'На 20 неделе беременности ваш малыш размером с банан! Его органы чувств активно развиваются, и он может слышать звуки извне.',
            'tip_type': 'fact',
            'pregnancy_week_min': 20,
            'pregnancy_week_max': 20,
            'audience': 'pregnant',
            'priority': 7
        },
        {
            'title': 'Подготовка к родам',
            'content': 'На 36-40 неделе беременности важно подготовить сумку в роддом и обсудить план родов с врачом. Практикуйте дыхательные упражнения.',
            'tip_type': 'reminder',
            'pregnancy_week_min': 36,
            'pregnancy_week_max': 40,
            'audience': 'pregnant',
            'priority': 9
        },
        {
            'title': 'Важность сна для новорожденного',
            'content': 'Новорожденные спят 14-17 часов в сутки. Это нормально! Сон критически важен для развития мозга и роста вашего малыша.',
            'tip_type': 'fact',
            'baby_age_min_days': 0,
            'baby_age_max_days': 30,
            'audience': 'new_mom',
            'priority': 6
        },
        {
            'title': 'Грудное вскармливание: первые дни',
            'content': 'В первые дни после родов молозиво обеспечивает малыша всеми необходимыми питательными веществами и антителами. Не переживайте, если молока кажется мало.',
            'tip_type': 'tip',
            'baby_age_min_days': 0,
            'baby_age_max_days': 7,
            'audience': 'new_mom',
            'priority': 8
        },
        {
            'title': 'Признаки готовности к прикорму',
            'content': 'Ребенок готов к прикорму, когда может сидеть с поддержкой, проявляет интерес к еде взрослых и исчез рефлекс выталкивания языка. Обычно это происходит в 4-6 месяцев.',
            'tip_type': 'milestone',
            'baby_age_min_days': 120,  # 4 месяца
            'baby_age_max_days': 180,  # 6 месяцев
            'audience': 'all',
            'priority': 7
        },
        {
            'title': 'Безопасность дома',
            'content': 'Когда малыш начинает ползать, пора обезопасить дом: установите заглушки на розетки, блокираторы на шкафы и уберите мелкие предметы.',
            'tip_type': 'warning',
            'baby_age_min_days': 180,  # 6 месяцев
            'baby_age_max_days': 365,  # 1 год
            'audience': 'all',
            'priority': 9
        },
        {
            'title': 'Развитие речи',
            'content': 'Читайте малышу каждый день, даже если он еще очень мал. Это способствует развитию речи, расширяет словарный запас и укрепляет эмоциональную связь.',
            'tip_type': 'tip',
            'baby_age_min_days': 0,
            'baby_age_max_days': 730,  # 2 года
            'audience': 'all',
            'priority': 6
        }
    ]
    
    created_tips = []
    for tip_data in sample_tips:
        tip, created = DailyTip.objects.get_or_create(
            title=tip_data['title'],
            defaults=tip_data
        )
        if created:
            created_tips.append(tip)
            logger.info(f"Создан пример совета: {tip.title}")
    
    return created_tips


def get_tips_by_type(tip_type, limit=10):
    """
    Получает советы определенного типа.
    
    Args:
        tip_type (str): Тип совета ('tip', 'fact', 'milestone', 'reminder', 'warning')
        limit (int): Максимальное количество советов
        
    Returns:
        QuerySet: Советы указанного типа
    """
    try:
        tips = DailyTip.objects.filter(
            is_active=True,
            tip_type=tip_type
        ).order_by('-priority', '-created_at')[:limit]
        
        logger.info(f"Найдено {len(tips)} советов типа '{tip_type}'")
        return tips
        
    except Exception as e:
        logger.error(f"Ошибка при получении советов типа '{tip_type}': {e}")
        return DailyTip.objects.none()


def get_trending_tips(days=7, limit=5):
    """
    Получает популярные советы за указанный период.
    
    Args:
        days (int): Количество дней для анализа
        limit (int): Максимальное количество советов
        
    Returns:
        list: Популярные советы с количеством просмотров
    """
    try:
        from datetime import timedelta
        from django.db.models import Count
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Получаем советы с количеством просмотров
        trending_tips = DailyTip.objects.filter(
            is_active=True,
            user_views__viewed_at__gte=start_date
        ).annotate(
            view_count=Count('user_views')
        ).order_by('-view_count', '-priority')[:limit]
        
        result = []
        for tip in trending_tips:
            result.append({
                'tip': tip,
                'view_count': tip.view_count
            })
        
        logger.info(f"Найдено {len(result)} популярных советов за {days} дней")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при получении популярных советов: {e}")
        return []