"""
Тесты для системы персонализированного контента.

Этот модуль содержит тесты для моделей и утилит персонализации контента,
соответствующих требованию 9.1 о создании системы персонализированного контента.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

from webapp.models import UserProfile, PersonalizedContent, UserContentView
from webapp.utils.personalization_utils import (
    get_or_create_user_profile,
    update_user_profile,
    get_personalized_content_for_user,
    mark_content_as_viewed,
    get_content_recommendations_by_tags,
    get_user_personalization_stats,
    analyze_user_engagement
)


class UserProfileModelTest(TestCase):
    """Тесты для модели UserProfile."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_user_profile(self):
        """Тест создания профиля пользователя."""
        profile = UserProfile.objects.create(
            user=self.user,
            pregnancy_status='pregnant',
            pregnancy_week=20,
            experience_level='first_time',
            interests=['nutrition', 'health']
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.pregnancy_status, 'pregnant')
        self.assertEqual(profile.pregnancy_week, 20)
        self.assertEqual(profile.experience_level, 'first_time')
        self.assertEqual(profile.interests, ['nutrition', 'health'])
    
    def test_current_pregnancy_week_calculation(self):
        """Тест расчета текущей недели беременности."""
        # Тест с установленной датой родов
        due_date = date.today() + timedelta(weeks=10)  # 10 недель до родов
        profile = UserProfile.objects.create(
            user=self.user,
            pregnancy_status='pregnant',
            due_date=due_date
        )
        
        expected_week = 30  # 40 - 10 = 30
        self.assertEqual(profile.current_pregnancy_week, expected_week)
        
        # Тест с установленной неделей беременности (без даты родов)
        profile.due_date = None
        profile.pregnancy_week = 25
        profile.save()
        
        self.assertEqual(profile.current_pregnancy_week, 25)
    
    def test_is_high_risk_pregnancy(self):
        """Тест определения беременности высокого риска."""
        profile = UserProfile.objects.create(
            user=self.user,
            pregnancy_status='pregnant',
            pregnancy_week=8  # Первый триместр - высокий риск
        )
        
        self.assertTrue(profile.is_high_risk_pregnancy)
        
        # Тест нормальной беременности
        profile.pregnancy_week = 20
        profile.save()
        
        self.assertFalse(profile.is_high_risk_pregnancy)
        
        # Тест поздней беременности - высокий риск
        profile.pregnancy_week = 39
        profile.save()
        
        self.assertTrue(profile.is_high_risk_pregnancy)
    
    def test_get_personalization_tags(self):
        """Тест получения тегов персонализации."""
        profile = UserProfile.objects.create(
            user=self.user,
            pregnancy_status='pregnant',
            pregnancy_week=15,  # Второй триместр
            experience_level='first_time',
            interests=['nutrition', 'health']
        )
        
        tags = profile.get_personalization_tags()
        
        self.assertIn('pregnant', tags)
        self.assertIn('second_trimester', tags)
        self.assertIn('first_time', tags)
        self.assertIn('nutrition', tags)
        self.assertIn('health', tags)
    
    def test_should_show_content_today(self):
        """Тест определения необходимости показа контента."""
        profile = UserProfile.objects.create(
            user=self.user,
            show_daily_tips=True,
            preferred_content_frequency='daily'
        )
        
        self.assertTrue(profile.should_show_content_today())
        
        # Тест отключенных советов
        profile.show_daily_tips = False
        profile.save()
        
        self.assertFalse(profile.should_show_content_today())


class PersonalizedContentModelTest(TestCase):
    """Тесты для модели PersonalizedContent."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            pregnancy_status='pregnant',
            pregnancy_week=20,
            experience_level='first_time',
            interests=['nutrition', 'health']
        )
    
    def test_create_personalized_content(self):
        """Тест создания персонализированного контента."""
        content = PersonalizedContent.objects.create(
            title='Тестовый совет',
            content='Это тестовый совет для беременных',
            content_type='tip',
            pregnancy_status_filter=['pregnant'],
            pregnancy_week_min=15,
            pregnancy_week_max=25,
            interest_tags=['nutrition'],
            priority='high'
        )
        
        self.assertEqual(content.title, 'Тестовый совет')
        self.assertEqual(content.content_type, 'tip')
        self.assertEqual(content.priority, 'high')
        self.assertTrue(content.is_active)
    
    def test_is_suitable_for_user(self):
        """Тест проверки подходящести контента для пользователя."""
        # Подходящий контент
        suitable_content = PersonalizedContent.objects.create(
            title='Подходящий совет',
            content='Совет для беременных в 20 недель',
            pregnancy_status_filter=['pregnant'],
            pregnancy_week_min=15,
            pregnancy_week_max=25,
            experience_level_filter=['first_time'],
            interest_tags=['nutrition']
        )
        
        self.assertTrue(suitable_content.is_suitable_for_user(self.profile))
        
        # Неподходящий контент (неправильный статус беременности)
        unsuitable_content = PersonalizedContent.objects.create(
            title='Неподходящий совет',
            content='Совет для не беременных',
            pregnancy_status_filter=['not_pregnant']
        )
        
        self.assertFalse(unsuitable_content.is_suitable_for_user(self.profile))
        
        # Неподходящий контент (неправильная неделя беременности)
        unsuitable_week_content = PersonalizedContent.objects.create(
            title='Совет для поздней беременности',
            content='Совет для 35+ недель',
            pregnancy_status_filter=['pregnant'],
            pregnancy_week_min=35,
            pregnancy_week_max=42
        )
        
        self.assertFalse(unsuitable_week_content.is_suitable_for_user(self.profile))
    
    def test_get_personalized_content_for_user(self):
        """Тест получения персонализированного контента для пользователя."""
        # Создаем подходящий контент
        PersonalizedContent.objects.create(
            title='Совет 1',
            content='Подходящий совет',
            pregnancy_status_filter=['pregnant'],
            pregnancy_week_min=15,
            pregnancy_week_max=25,
            priority='high'
        )
        
        # Создаем неподходящий контент
        PersonalizedContent.objects.create(
            title='Совет 2',
            content='Неподходящий совет',
            pregnancy_status_filter=['not_pregnant'],
            priority='medium'
        )
        
        content = PersonalizedContent.get_personalized_content_for_user(self.user, limit=5)
        
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0].title, 'Совет 1')


class UserContentViewModelTest(TestCase):
    """Тесты для модели UserContentView."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.content = PersonalizedContent.objects.create(
            title='Тестовый контент',
            content='Тестовое содержание',
            show_once=True
        )
    
    def test_create_content_view(self):
        """Тест создания записи о просмотре контента."""
        view = UserContentView.objects.create(
            user=self.user,
            content=self.content,
            interaction_type='viewed'
        )
        
        self.assertEqual(view.user, self.user)
        self.assertEqual(view.content, self.content)
        self.assertEqual(view.interaction_type, 'viewed')
    
    def test_unique_user_content_constraint(self):
        """Тест ограничения уникальности пользователь-контент."""
        # Создаем первую запись
        UserContentView.objects.create(
            user=self.user,
            content=self.content,
            interaction_type='viewed'
        )
        
        # Попытка создать дублирующую запись должна вызвать ошибку
        with self.assertRaises(Exception):
            UserContentView.objects.create(
                user=self.user,
                content=self.content,
                interaction_type='clicked'
            )


class PersonalizationUtilsTest(TestCase):
    """Тесты для утилит персонализации."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_or_create_user_profile(self):
        """Тест получения или создания профиля пользователя."""
        # Первый вызов должен создать профиль
        profile = get_or_create_user_profile(self.user)
        
        self.assertIsInstance(profile, UserProfile)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.pregnancy_status, 'not_pregnant')
        
        # Второй вызов должен вернуть существующий профиль
        profile2 = get_or_create_user_profile(self.user)
        
        self.assertEqual(profile.id, profile2.id)
    
    def test_update_user_profile(self):
        """Тест обновления профиля пользователя."""
        # Создаем профиль
        profile = get_or_create_user_profile(self.user)
        
        # Обновляем профиль
        updated_profile = update_user_profile(
            self.user,
            pregnancy_status='pregnant',
            pregnancy_week=15,
            interests=['nutrition', 'health']
        )
        
        self.assertEqual(updated_profile.pregnancy_status, 'pregnant')
        self.assertEqual(updated_profile.pregnancy_week, 15)
        self.assertEqual(updated_profile.interests, ['nutrition', 'health'])
    
    def test_get_personalized_content_for_user(self):
        """Тест получения персонализированного контента."""
        # Создаем профиль
        profile = get_or_create_user_profile(self.user)
        profile.pregnancy_status = 'pregnant'
        profile.pregnancy_week = 20
        profile.save()
        
        # Создаем подходящий контент
        PersonalizedContent.objects.create(
            title='Подходящий совет',
            content='Совет для беременных',
            pregnancy_status_filter=['pregnant'],
            pregnancy_week_min=15,
            pregnancy_week_max=25,
            priority='high'
        )
        
        # Создаем неподходящий контент
        PersonalizedContent.objects.create(
            title='Неподходящий совет',
            content='Совет для не беременных',
            pregnancy_status_filter=['not_pregnant'],
            priority='medium'
        )
        
        content = get_personalized_content_for_user(self.user, limit=5)
        
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0].title, 'Подходящий совет')
    
    def test_mark_content_as_viewed(self):
        """Тест отметки контента как просмотренного."""
        content = PersonalizedContent.objects.create(
            title='Тестовый контент',
            content='Тестовое содержание'
        )
        
        view = mark_content_as_viewed(self.user, content, 'clicked')
        
        self.assertEqual(view.user, self.user)
        self.assertEqual(view.content, content)
        self.assertEqual(view.interaction_type, 'clicked')
        
        # Проверяем, что повторный вызов обновляет тип взаимодействия
        updated_view = mark_content_as_viewed(self.user, content, 'saved')
        
        self.assertEqual(view.id, updated_view.id)
        self.assertEqual(updated_view.interaction_type, 'saved')
    
    def test_get_content_recommendations_by_tags(self):
        """Тест получения рекомендаций по тегам."""
        # Создаем профиль с интересами
        profile = get_or_create_user_profile(self.user)
        profile.interests = ['nutrition', 'health', 'development']
        profile.save()
        
        # Создаем контент с разными тегами (без фильтров персонализации)
        PersonalizedContent.objects.create(
            title='Совет по питанию',
            content='Совет о питании',
            interest_tags=['nutrition', 'health'],
            priority='high',
            # Не устанавливаем фильтры персонализации, чтобы контент подходил всем
            pregnancy_status_filter=[],
            experience_level_filter=[]
        )
        
        PersonalizedContent.objects.create(
            title='Совет по развитию',
            content='Совет о развитии',
            interest_tags=['development'],
            priority='medium',
            pregnancy_status_filter=[],
            experience_level_filter=[]
        )
        
        # Получаем рекомендации по тегам
        recommendations = get_content_recommendations_by_tags(
            self.user, 
            ['nutrition', 'health'], 
            limit=5
        )
        
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].title, 'Совет по питанию')
    
    def test_get_user_personalization_stats(self):
        """Тест получения статистики персонализации."""
        # Создаем профиль
        profile = get_or_create_user_profile(self.user)
        profile.pregnancy_status = 'pregnant'
        profile.pregnancy_week = 20
        profile.interests = ['nutrition', 'health']
        profile.save()
        
        # Создаем контент и просмотры
        content = PersonalizedContent.objects.create(
            title='Тестовый контент',
            content='Тестовое содержание',
            content_type='tip'
        )
        
        UserContentView.objects.create(
            user=self.user,
            content=content,
            interaction_type='viewed'
        )
        
        stats = get_user_personalization_stats(self.user)
        
        self.assertIn('profile', stats)
        self.assertIn('content_stats', stats)
        self.assertIn('personalization_tags', stats)
        
        self.assertEqual(stats['profile']['pregnancy_status'], 'Беременна')
        self.assertEqual(stats['content_stats']['total_views'], 1)
        self.assertIn('pregnant', stats['personalization_tags'])
    
    def test_analyze_user_engagement(self):
        """Тест анализа вовлеченности пользователя."""
        # Создаем контент и различные типы взаимодействий
        content1 = PersonalizedContent.objects.create(
            title='Контент 1',
            content='Содержание 1',
            content_type='tip'
        )
        
        content2 = PersonalizedContent.objects.create(
            title='Контент 2',
            content='Содержание 2',
            content_type='fact'
        )
        
        # Создаем просмотры
        UserContentView.objects.create(
            user=self.user,
            content=content1,
            interaction_type='viewed'
        )
        
        UserContentView.objects.create(
            user=self.user,
            content=content2,
            interaction_type='clicked'
        )
        
        engagement = analyze_user_engagement(self.user, days=30)
        
        self.assertEqual(engagement['total_views'], 2)
        self.assertIn('interaction_stats', engagement)
        self.assertIn('content_type_stats', engagement)
        self.assertGreater(engagement['engagement_rate'], 0)