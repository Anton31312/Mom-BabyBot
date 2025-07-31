"""
Тесты для системы ежедневных советов и фактов.

Этот модуль содержит тесты для моделей и утилит ежедневных советов,
соответствующих требованию 9.2 о реализации ежедневных советов и фактов.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

from webapp.models import DailyTip, UserDailyTipView, UserProfile
from webapp.utils.daily_tips_utils import (
    get_daily_tip_for_user,
    mark_tip_as_viewed,
    get_tips_for_pregnancy_week,
    get_user_tip_statistics,
    create_sample_daily_tips,
    get_tips_by_type,
    get_trending_tips
)
from webapp.utils.personalization_utils import get_or_create_user_profile


class DailyTipModelTest(TestCase):
    """Тесты для модели DailyTip."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = get_or_create_user_profile(self.user)
    
    def test_create_daily_tip(self):
        """Тест создания ежедневного совета."""
        tip = DailyTip.objects.create(
            title='Тестовый совет',
            content='Это тестовый совет для беременных',
            tip_type='tip',
            pregnancy_week_min=10,
            pregnancy_week_max=20,
            audience='pregnant',
            priority=5
        )
        
        self.assertEqual(tip.title, 'Тестовый совет')
        self.assertEqual(tip.tip_type, 'tip')
        self.assertEqual(tip.audience, 'pregnant')
        self.assertEqual(tip.priority, 5)
        self.assertTrue(tip.is_active)
    
    def test_is_suitable_for_user_profile_pregnancy(self):
        """Тест проверки подходящести совета для беременной пользовательницы."""
        # Настраиваем профиль беременной пользовательницы
        self.profile.pregnancy_status = 'pregnant'
        self.profile.pregnancy_week = 15
        self.profile.save()
        
        # Подходящий совет
        suitable_tip = DailyTip.objects.create(
            title='Совет для беременных',
            content='Совет для 10-20 недель',
            pregnancy_week_min=10,
            pregnancy_week_max=20,
            audience='pregnant'
        )
        
        self.assertTrue(suitable_tip.is_suitable_for_user_profile(self.profile))
        
        # Неподходящий совет (неправильная аудитория)
        unsuitable_tip = DailyTip.objects.create(
            title='Совет для мам',
            content='Совет для молодых мам',
            audience='new_mom'
        )
        
        self.assertFalse(unsuitable_tip.is_suitable_for_user_profile(self.profile))
        
        # Неподходящий совет (неправильная неделя)
        unsuitable_week_tip = DailyTip.objects.create(
            title='Совет для поздней беременности',
            content='Совет для 35+ недель',
            pregnancy_week_min=35,
            pregnancy_week_max=40,
            audience='pregnant'
        )
        
        self.assertFalse(unsuitable_week_tip.is_suitable_for_user_profile(self.profile))
    
    def test_is_suitable_for_user_profile_experience_level(self):
        """Тест проверки подходящести совета по уровню опыта."""
        # Настраиваем профиль новой мамы
        self.profile.experience_level = 'first_time'
        self.profile.save()
        
        # Подходящий совет для новых мам
        suitable_tip = DailyTip.objects.create(
            title='Совет для новых мам',
            content='Совет для первого ребенка',
            audience='new_mom'
        )
        
        self.assertTrue(suitable_tip.is_suitable_for_user_profile(self.profile))
        
        # Неподходящий совет для опытных мам
        unsuitable_tip = DailyTip.objects.create(
            title='Совет для опытных мам',
            content='Совет для опытных мам',
            audience='experienced_mom'
        )
        
        self.assertFalse(unsuitable_tip.is_suitable_for_user_profile(self.profile))
    
    def test_is_suitable_for_user_profile_dates(self):
        """Тест проверки подходящести совета по датам показа."""
        # Совет, который должен показываться только завтра
        future_tip = DailyTip.objects.create(
            title='Будущий совет',
            content='Совет на завтра',
            show_date_start=date.today() + timedelta(days=1),
            audience='all'
        )
        
        self.assertFalse(future_tip.is_suitable_for_user_profile(self.profile))
        
        # Совет, который уже не должен показываться
        past_tip = DailyTip.objects.create(
            title='Прошлый совет',
            content='Совет из прошлого',
            show_date_end=date.today() - timedelta(days=1),
            audience='all'
        )
        
        self.assertFalse(past_tip.is_suitable_for_user_profile(self.profile))
        
        # Актуальный совет
        current_tip = DailyTip.objects.create(
            title='Актуальный совет',
            content='Актуальный совет',
            show_date_start=date.today() - timedelta(days=1),
            show_date_end=date.today() + timedelta(days=1),
            audience='all'
        )
        
        self.assertTrue(current_tip.is_suitable_for_user_profile(self.profile))
    
    def test_get_daily_tip_for_user_class_method(self):
        """Тест получения ежедневного совета через метод класса."""
        # Настраиваем профиль
        self.profile.pregnancy_status = 'pregnant'
        self.profile.pregnancy_week = 15
        self.profile.save()
        
        # Создаем подходящий совет
        DailyTip.objects.create(
            title='Подходящий совет',
            content='Совет для 15 недели',
            pregnancy_week_min=10,
            pregnancy_week_max=20,
            audience='pregnant',
            priority=5
        )
        
        # Создаем неподходящий совет
        DailyTip.objects.create(
            title='Неподходящий совет',
            content='Совет для мам',
            audience='new_mom',
            priority=8
        )
        
        tip = DailyTip.get_daily_tip_for_user(self.user)
        
        self.assertIsNotNone(tip)
        self.assertEqual(tip.title, 'Подходящий совет')
    
    def test_get_tips_for_week_class_method(self):
        """Тест получения советов для определенной недели беременности."""
        # Создаем советы для разных недель
        DailyTip.objects.create(
            title='Совет для 15 недели',
            content='Совет',
            pregnancy_week_min=15,
            pregnancy_week_max=15,
            priority=5
        )
        
        DailyTip.objects.create(
            title='Совет для 10-20 недель',
            content='Совет',
            pregnancy_week_min=10,
            pregnancy_week_max=20,
            priority=3
        )
        
        DailyTip.objects.create(
            title='Совет для 30 недели',
            content='Совет',
            pregnancy_week_min=30,
            pregnancy_week_max=30,
            priority=7
        )
        
        tips = DailyTip.get_tips_for_week(15)
        
        self.assertEqual(len(tips), 2)
        # Проверяем сортировку по приоритету
        self.assertEqual(tips[0].title, 'Совет для 15 недели')
        self.assertEqual(tips[1].title, 'Совет для 10-20 недель')


class UserDailyTipViewModelTest(TestCase):
    """Тесты для модели UserDailyTipView."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tip = DailyTip.objects.create(
            title='Тестовый совет',
            content='Тестовое содержание'
        )
    
    def test_create_tip_view(self):
        """Тест создания записи о просмотре совета."""
        view = UserDailyTipView.objects.create(
            user=self.user,
            tip=self.tip,
            interaction_type='viewed'
        )
        
        self.assertEqual(view.user, self.user)
        self.assertEqual(view.tip, self.tip)
        self.assertEqual(view.interaction_type, 'viewed')
    
    def test_mark_tip_as_viewed_class_method(self):
        """Тест отметки совета как просмотренного через метод класса."""
        view = UserDailyTipView.mark_tip_as_viewed(self.user, self.tip, 'liked')
        
        self.assertEqual(view.user, self.user)
        self.assertEqual(view.tip, self.tip)
        self.assertEqual(view.interaction_type, 'liked')
        
        # Проверяем обновление типа взаимодействия
        updated_view = UserDailyTipView.mark_tip_as_viewed(self.user, self.tip, 'dismissed')
        
        self.assertEqual(view.id, updated_view.id)
        self.assertEqual(updated_view.interaction_type, 'dismissed')
    
    def test_has_user_seen_tip_today(self):
        """Тест проверки, видел ли пользователь совет сегодня."""
        # Сначала пользователь не видел совет
        self.assertFalse(UserDailyTipView.has_user_seen_tip_today(self.user, self.tip))
        
        # Отмечаем совет как просмотренный
        UserDailyTipView.mark_tip_as_viewed(self.user, self.tip)
        
        # Теперь пользователь видел совет сегодня
        self.assertTrue(UserDailyTipView.has_user_seen_tip_today(self.user, self.tip))


class DailyTipsUtilsTest(TestCase):
    """Тесты для утилит ежедневных советов."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = get_or_create_user_profile(self.user)
    
    def test_get_daily_tip_for_user(self):
        """Тест получения ежедневного совета для пользователя."""
        # Настраиваем профиль
        self.profile.pregnancy_status = 'pregnant'
        self.profile.pregnancy_week = 20
        self.profile.save()
        
        # Создаем подходящий совет
        DailyTip.objects.create(
            title='Подходящий совет',
            content='Совет для 20 недели',
            pregnancy_week_min=15,
            pregnancy_week_max=25,
            audience='pregnant',
            priority=5
        )
        
        tip = get_daily_tip_for_user(self.user)
        
        self.assertIsNotNone(tip)
        self.assertEqual(tip.title, 'Подходящий совет')
    
    def test_get_daily_tip_for_user_exclude_seen(self):
        """Тест исключения уже просмотренных советов."""
        # Создаем совет
        tip = DailyTip.objects.create(
            title='Тестовый совет',
            content='Содержание',
            audience='all'
        )
        
        # Сначала совет должен возвращаться
        daily_tip = get_daily_tip_for_user(self.user)
        self.assertEqual(daily_tip, tip)
        
        # Отмечаем как просмотренный
        mark_tip_as_viewed(self.user, tip)
        
        # Теперь совет не должен возвращаться
        daily_tip = get_daily_tip_for_user(self.user, exclude_seen_today=True)
        self.assertIsNone(daily_tip)
        
        # Но должен возвращаться, если не исключать просмотренные
        daily_tip = get_daily_tip_for_user(self.user, exclude_seen_today=False)
        self.assertEqual(daily_tip, tip)
    
    def test_mark_tip_as_viewed(self):
        """Тест отметки совета как просмотренного."""
        tip = DailyTip.objects.create(
            title='Тестовый совет',
            content='Содержание'
        )
        
        view = mark_tip_as_viewed(self.user, tip, 'liked')
        
        self.assertEqual(view.user, self.user)
        self.assertEqual(view.tip, tip)
        self.assertEqual(view.interaction_type, 'liked')
    
    def test_get_tips_for_pregnancy_week(self):
        """Тест получения советов для недели беременности."""
        # Создаем советы для разных недель
        DailyTip.objects.create(
            title='Совет для 20 недели',
            content='Совет',
            pregnancy_week_min=20,
            pregnancy_week_max=20,
            priority=8
        )
        
        DailyTip.objects.create(
            title='Совет для 15-25 недель',
            content='Совет',
            pregnancy_week_min=15,
            pregnancy_week_max=25,
            priority=5
        )
        
        DailyTip.objects.create(
            title='Совет для 30 недели',
            content='Совет',
            pregnancy_week_min=30,
            pregnancy_week_max=30,
            priority=3
        )
        
        tips = get_tips_for_pregnancy_week(20)
        
        self.assertEqual(len(tips), 2)
        # Проверяем сортировку по приоритету
        self.assertEqual(tips[0].title, 'Совет для 20 недели')
        self.assertEqual(tips[1].title, 'Совет для 15-25 недель')
    
    def test_get_user_tip_statistics(self):
        """Тест получения статистики просмотров советов."""
        # Создаем советы разных типов
        tip1 = DailyTip.objects.create(
            title='Совет 1',
            content='Содержание',
            tip_type='tip'
        )
        
        tip2 = DailyTip.objects.create(
            title='Факт 1',
            content='Содержание',
            tip_type='fact'
        )
        
        # Создаем просмотры с разными типами взаимодействий
        UserDailyTipView.objects.create(
            user=self.user,
            tip=tip1,
            interaction_type='viewed'
        )
        
        UserDailyTipView.objects.create(
            user=self.user,
            tip=tip2,
            interaction_type='liked'
        )
        
        stats = get_user_tip_statistics(self.user, days=30)
        
        self.assertEqual(stats['total_views'], 2)
        self.assertIn('interaction_stats', stats)
        self.assertIn('tip_type_stats', stats)
        self.assertGreater(stats['engagement_rate'], 0)
    
    def test_create_sample_daily_tips(self):
        """Тест создания примеров ежедневных советов."""
        # Проверяем, что советов нет
        self.assertEqual(DailyTip.objects.count(), 0)
        
        # Создаем примеры
        created_tips = create_sample_daily_tips()
        
        # Проверяем, что советы созданы
        self.assertGreater(len(created_tips), 0)
        self.assertGreater(DailyTip.objects.count(), 0)
        
        # Проверяем, что повторный вызов не создает дубликаты
        initial_count = DailyTip.objects.count()
        create_sample_daily_tips()
        self.assertEqual(DailyTip.objects.count(), initial_count)
    
    def test_get_tips_by_type(self):
        """Тест получения советов по типу."""
        # Создаем советы разных типов
        DailyTip.objects.create(
            title='Совет',
            content='Содержание',
            tip_type='tip',
            priority=5
        )
        
        DailyTip.objects.create(
            title='Факт',
            content='Содержание',
            tip_type='fact',
            priority=8
        )
        
        DailyTip.objects.create(
            title='Еще один совет',
            content='Содержание',
            tip_type='tip',
            priority=3
        )
        
        # Получаем советы типа 'tip'
        tips = get_tips_by_type('tip')
        
        self.assertEqual(len(tips), 2)
        # Проверяем сортировку по приоритету
        self.assertEqual(tips[0].title, 'Совет')
        self.assertEqual(tips[1].title, 'Еще один совет')
        
        # Получаем советы типа 'fact'
        facts = get_tips_by_type('fact')
        
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].title, 'Факт')
    
    def test_get_trending_tips(self):
        """Тест получения популярных советов."""
        # Создаем советы
        tip1 = DailyTip.objects.create(
            title='Популярный совет',
            content='Содержание',
            priority=5
        )
        
        tip2 = DailyTip.objects.create(
            title='Менее популярный совет',
            content='Содержание',
            priority=3
        )
        
        # Создаем больше просмотров для первого совета
        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            UserDailyTipView.objects.create(user=user, tip=tip1)
        
        # Один просмотр для второго совета
        UserDailyTipView.objects.create(user=self.user, tip=tip2)
        
        trending = get_trending_tips(days=7)
        
        self.assertEqual(len(trending), 2)
        # Проверяем сортировку по популярности
        self.assertEqual(trending[0]['tip'], tip1)
        self.assertEqual(trending[0]['view_count'], 3)
        self.assertEqual(trending[1]['tip'], tip2)
        self.assertEqual(trending[1]['view_count'], 1)