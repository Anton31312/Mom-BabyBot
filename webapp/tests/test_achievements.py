"""
Тесты для системы достижений.

Этот модуль содержит тесты для моделей и API системы достижений,
соответствующей требованию 9.3.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json

from webapp.models import (
    Achievement, UserAchievement, AchievementNotification,
    UserProfile, FeedingSession, WeightRecord, BloodPressureRecord
)


class AchievementModelTest(TestCase):
    """Тесты для модели Achievement."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем профиль пользователя
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            pregnancy_status='pregnant',
            pregnancy_week=20,
            experience_level='first_time'
        )
        
        # Создаем тестовое достижение
        self.achievement = Achievement.objects.create(
            title='Первое кормление',
            description='Записать первый сеанс кормления',
            achievement_type='feeding_milestone',
            difficulty='easy',
            icon='🍼',
            points=10,
            condition_type='feeding_sessions',
            condition_value=1
        )
    
    def test_achievement_creation(self):
        """Тест создания достижения."""
        self.assertEqual(self.achievement.title, 'Первое кормление')
        self.assertEqual(self.achievement.points, 10)
        self.assertEqual(self.achievement.condition_type, 'feeding_sessions')
        self.assertTrue(self.achievement.is_active)
        self.assertFalse(self.achievement.is_hidden)
    
    def test_achievement_str_representation(self):
        """Тест строкового представления достижения."""
        expected = f'{self.achievement.icon} {self.achievement.title} ({self.achievement.points} очков)'
        self.assertEqual(str(self.achievement), expected)
    
    def test_check_condition_feeding_sessions(self):
        """Тест проверки условия для сессий кормления."""
        # Изначально условие не выполнено
        is_completed, progress = self.achievement.check_condition_for_user(self.user)
        self.assertFalse(is_completed)
        self.assertEqual(progress, 0)
        
        # Создаем сессию кормления
        FeedingSession.objects.create(
            user=self.user,
            feeding_type='breast',
            left_breast_duration=timedelta(minutes=10)
        )
        
        # Теперь условие должно быть выполнено
        is_completed, progress = self.achievement.check_condition_for_user(self.user)
        self.assertTrue(is_completed)
        self.assertEqual(progress, 1)
    
    def test_check_condition_pregnancy_week(self):
        """Тест проверки условия для недели беременности."""
        pregnancy_achievement = Achievement.objects.create(
            title='20 недель беременности',
            description='Достигнуть 20 недели беременности',
            achievement_type='pregnancy_milestone',
            condition_type='pregnancy_week',
            condition_value=20
        )
        
        # Условие должно быть выполнено (у пользователя 20 неделя)
        is_completed, progress = pregnancy_achievement.check_condition_for_user(self.user)
        self.assertTrue(is_completed)
        self.assertEqual(progress, 20)
    
    def test_get_progress_for_user(self):
        """Тест получения прогресса для пользователя."""
        progress_info = self.achievement.get_progress_for_user(self.user)
        
        self.assertFalse(progress_info['is_completed'])
        self.assertEqual(progress_info['current_progress'], 0)
        self.assertEqual(progress_info['target_value'], 1)
        self.assertEqual(progress_info['progress_percentage'], 0)
    
    def test_get_available_achievements_for_user(self):
        """Тест получения доступных достижений для пользователя."""
        # Создаем еще одно достижение
        Achievement.objects.create(
            title='Второе достижение',
            description='Тестовое достижение',
            achievement_type='app_usage',
            condition_type='feeding_sessions',
            condition_value=5
        )
        
        available = Achievement.get_available_achievements_for_user(self.user)
        self.assertEqual(available.count(), 2)
        
        # Присваиваем одно достижение
        UserAchievement.objects.create(user=self.user, achievement=self.achievement)
        
        # Теперь доступно должно быть только одно
        available = Achievement.get_available_achievements_for_user(self.user)
        self.assertEqual(available.count(), 1)
    
    def test_check_and_award_achievements(self):
        """Тест проверки и присвоения достижений."""
        # Изначально нет достижений
        new_achievements = Achievement.check_and_award_achievements(self.user)
        self.assertEqual(len(new_achievements), 0)
        
        # Создаем сессию кормления
        FeedingSession.objects.create(
            user=self.user,
            feeding_type='breast',
            left_breast_duration=timedelta(minutes=10)
        )
        
        # Теперь должно быть присвоено достижение
        new_achievements = Achievement.check_and_award_achievements(self.user)
        self.assertEqual(len(new_achievements), 1)
        self.assertEqual(new_achievements[0].achievement, self.achievement)


class UserAchievementModelTest(TestCase):
    """Тесты для модели UserAchievement."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.achievement = Achievement.objects.create(
            title='Тестовое достижение',
            description='Описание достижения',
            achievement_type='app_usage',
            points=15
        )
        
        self.user_achievement = UserAchievement.objects.create(
            user=self.user,
            achievement=self.achievement
        )
    
    def test_user_achievement_creation(self):
        """Тест создания достижения пользователя."""
        self.assertEqual(self.user_achievement.user, self.user)
        self.assertEqual(self.user_achievement.achievement, self.achievement)
        self.assertFalse(self.user_achievement.is_viewed)
    
    def test_days_since_earned(self):
        """Тест подсчета дней с момента получения достижения."""
        # Только что созданное достижение должно иметь 0 дней
        self.assertEqual(self.user_achievement.days_since_earned, 0)
    
    def test_mark_as_viewed(self):
        """Тест отметки достижения как просмотренного."""
        self.assertFalse(self.user_achievement.is_viewed)
        
        self.user_achievement.mark_as_viewed()
        self.user_achievement.refresh_from_db()
        
        self.assertTrue(self.user_achievement.is_viewed)
    
    def test_get_recent_achievements(self):
        """Тест получения недавних достижений."""
        recent = UserAchievement.get_recent_achievements(self.user, days=7)
        self.assertEqual(recent.count(), 1)
        
        # Создаем старое достижение
        old_achievement = Achievement.objects.create(
            title='Старое достижение',
            description='Старое описание',
            achievement_type='app_usage'
        )
        old_user_achievement = UserAchievement.objects.create(
            user=self.user,
            achievement=old_achievement
        )
        
        # Устанавливаем дату получения на 10 дней назад
        old_date = timezone.now() - timedelta(days=10)
        old_user_achievement.earned_at = old_date
        old_user_achievement.save()
        
        # Недавних должно остаться только одно
        recent = UserAchievement.get_recent_achievements(self.user, days=7)
        self.assertEqual(recent.count(), 1)
    
    def test_get_user_statistics(self):
        """Тест получения статистики пользователя."""
        # Создаем еще одно достижение
        achievement2 = Achievement.objects.create(
            title='Второе достижение',
            description='Описание',
            achievement_type='feeding_milestone',
            difficulty='hard',
            points=25
        )
        UserAchievement.objects.create(user=self.user, achievement=achievement2)
        
        stats = UserAchievement.get_user_statistics(self.user)
        
        self.assertEqual(stats['total_achievements'], 2)
        self.assertEqual(stats['total_points'], 40)  # 15 + 25
        self.assertIn('Использование приложения', stats['achievements_by_type'])
        self.assertIn('Достижение в кормлении', stats['achievements_by_type'])


class AchievementNotificationModelTest(TestCase):
    """Тесты для модели AchievementNotification."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.achievement = Achievement.objects.create(
            title='Тестовое достижение',
            description='Описание достижения',
            achievement_type='app_usage',
            points=10
        )
    
    def test_create_achievement_notification(self):
        """Тест создания уведомления о достижении."""
        notification = AchievementNotification.create_achievement_notification(
            self.user, self.achievement
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.achievement, self.achievement)
        self.assertEqual(notification.notification_type, 'achievement_earned')
        self.assertEqual(notification.status, 'pending')
        self.assertIn(self.achievement.title, notification.title)
    
    def test_mark_as_sent(self):
        """Тест отметки уведомления как отправленного."""
        notification = AchievementNotification.create_achievement_notification(
            self.user, self.achievement
        )
        
        self.assertEqual(notification.status, 'pending')
        self.assertIsNone(notification.sent_at)
        
        notification.mark_as_sent()
        notification.refresh_from_db()
        
        self.assertEqual(notification.status, 'sent')
        self.assertIsNotNone(notification.sent_at)
    
    def test_mark_as_read(self):
        """Тест отметки уведомления как прочитанного."""
        notification = AchievementNotification.create_achievement_notification(
            self.user, self.achievement
        )
        
        notification.mark_as_read()
        notification.refresh_from_db()
        
        self.assertEqual(notification.status, 'read')
        self.assertIsNotNone(notification.read_at)
    
    def test_get_unread_notifications(self):
        """Тест получения непрочитанных уведомлений."""
        # Создаем несколько уведомлений
        notification1 = AchievementNotification.create_achievement_notification(
            self.user, self.achievement
        )
        
        achievement2 = Achievement.objects.create(
            title='Второе достижение',
            description='Описание',
            achievement_type='app_usage'
        )
        notification2 = AchievementNotification.create_achievement_notification(
            self.user, achievement2
        )
        
        # Все уведомления должны быть непрочитанными
        unread = AchievementNotification.get_unread_notifications(self.user)
        self.assertEqual(unread.count(), 2)
        
        # Отмечаем одно как прочитанное
        notification1.mark_as_read()
        
        # Непрочитанным должно остаться только одно
        unread = AchievementNotification.get_unread_notifications(self.user)
        self.assertEqual(unread.count(), 1)


class AchievementAPITest(TestCase):
    """Тесты для API системы достижений."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Авторизуемся
        self.client.login(username='testuser', password='testpass123')
        
        # Создаем тестовые достижения
        self.achievement1 = Achievement.objects.create(
            title='Первое достижение',
            description='Описание первого достижения',
            achievement_type='feeding_milestone',
            difficulty='easy',
            points=10,
            condition_type='feeding_sessions',
            condition_value=1
        )
        
        self.achievement2 = Achievement.objects.create(
            title='Второе достижение',
            description='Описание второго достижения',
            achievement_type='pregnancy_milestone',
            difficulty='medium',
            points=20,
            condition_type='weight_records',
            condition_value=5
        )
    
    def test_achievement_list_api(self):
        """Тест API списка достижений."""
        url = reverse('webapp:achievement_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['achievements']), 2)
        self.assertIn('pagination', data)
    
    def test_achievement_list_api_with_filters(self):
        """Тест API списка достижений с фильтрами."""
        url = reverse('webapp:achievement_list')
        
        # Фильтр по типу
        response = self.client.get(url, {'type': 'feeding_milestone'})
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['achievements']), 1)
        self.assertEqual(data['achievements'][0]['type'], 'feeding_milestone')
    
    def test_achievement_stats_api(self):
        """Тест API статистики достижений."""
        # Присваиваем одно достижение
        UserAchievement.objects.create(user=self.user, achievement=self.achievement1)
        
        url = reverse('webapp:achievement_stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['statistics']['total_achievements'], 1)
        self.assertEqual(data['statistics']['total_points'], 10)
        self.assertIn('completion_percentage', data['statistics'])
    
    def test_check_achievements_api(self):
        """Тест API проверки достижений."""
        # Создаем сессию кормления для выполнения условия
        FeedingSession.objects.create(
            user=self.user,
            feeding_type='breast',
            left_breast_duration=timedelta(minutes=10)
        )
        
        url = reverse('webapp:check_achievements')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['new_achievements']), 1)
        self.assertEqual(data['new_achievements'][0]['title'], 'Первое достижение')
    
    def test_achievement_detail_api(self):
        """Тест API детальной информации о достижении."""
        url = reverse('webapp:achievement_detail', kwargs={'achievement_id': self.achievement1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['achievement']['title'], 'Первое достижение')
        self.assertEqual(data['achievement']['points'], 10)
        self.assertFalse(data['achievement']['is_earned'])
    
    def test_achievement_notifications_api(self):
        """Тест API уведомлений о достижениях."""
        # Создаем уведомление
        notification = AchievementNotification.create_achievement_notification(
            self.user, self.achievement1
        )
        
        url = reverse('webapp:achievement_notifications')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['notifications']), 1)
        self.assertEqual(data['unread_count'], 1)
    
    def test_mark_notifications_as_read(self):
        """Тест отметки уведомлений как прочитанных."""
        # Создаем уведомления
        notification1 = AchievementNotification.create_achievement_notification(
            self.user, self.achievement1
        )
        notification2 = AchievementNotification.create_achievement_notification(
            self.user, self.achievement2
        )
        
        url = reverse('webapp:achievement_notifications')
        
        # Отмечаем конкретные уведомления как прочитанные
        response = self.client.post(
            url,
            json.dumps({'notification_ids': [notification1.id]}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Проверяем, что уведомление отмечено как прочитанное
        notification1.refresh_from_db()
        self.assertEqual(notification1.status, 'read')
        
        # Второе уведомление должно остаться непрочитанным
        notification2.refresh_from_db()
        self.assertEqual(notification2.status, 'pending')
    
    def test_unauthorized_access(self):
        """Тест доступа без авторизации."""
        self.client.logout()
        
        url = reverse('webapp:achievement_list')
        response = self.client.get(url)
        
        # Должен быть редирект на страницу входа
        self.assertEqual(response.status_code, 302)


class AchievementIntegrationTest(TestCase):
    """Интеграционные тесты для системы достижений."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем профиль пользователя
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            pregnancy_status='pregnant',
            pregnancy_week=15
        )
        
        # Создаем достижения для разных типов активности
        self.feeding_achievement = Achievement.objects.create(
            title='Первое кормление',
            description='Записать первый сеанс кормления',
            achievement_type='feeding_milestone',
            condition_type='feeding_sessions',
            condition_value=1,
            points=10
        )
        
        self.weight_achievement = Achievement.objects.create(
            title='Отслеживание веса',
            description='Записать 3 измерения веса',
            achievement_type='health_milestone',
            condition_type='weight_records',
            condition_value=3,
            points=15
        )
        
        self.pregnancy_achievement = Achievement.objects.create(
            title='Второй триместр',
            description='Достичь 14 недели беременности',
            achievement_type='pregnancy_milestone',
            condition_type='pregnancy_week',
            condition_value=14,
            points=20
        )
    
    def test_full_achievement_workflow(self):
        """Тест полного рабочего процесса достижений."""
        # 1. Изначально у пользователя нет достижений
        user_achievements = UserAchievement.objects.filter(user=self.user)
        self.assertEqual(user_achievements.count(), 0)
        
        # 2. Проверяем достижения - должно быть присвоено достижение за беременность
        new_achievements = Achievement.check_and_award_achievements(self.user)
        self.assertEqual(len(new_achievements), 1)
        self.assertEqual(new_achievements[0].achievement, self.pregnancy_achievement)
        
        # 3. Создаем сессию кормления
        FeedingSession.objects.create(
            user=self.user,
            feeding_type='breast',
            left_breast_duration=timedelta(minutes=10)
        )
        
        # 4. Проверяем достижения снова - должно быть присвоено достижение за кормление
        new_achievements = Achievement.check_and_award_achievements(self.user)
        self.assertEqual(len(new_achievements), 1)
        self.assertEqual(new_achievements[0].achievement, self.feeding_achievement)
        
        # 5. Создаем записи веса с разными датами
        base_date = timezone.now()
        for i in range(3):
            WeightRecord.objects.create(
                user=self.user,
                weight=65.0 + i,
                date=base_date - timedelta(days=i)
            )
        
        # 6. Проверяем достижения - должно быть присвоено достижение за отслеживание веса
        new_achievements = Achievement.check_and_award_achievements(self.user)
        self.assertEqual(len(new_achievements), 1)
        self.assertEqual(new_achievements[0].achievement, self.weight_achievement)
        
        # 7. Проверяем итоговую статистику
        stats = UserAchievement.get_user_statistics(self.user)
        self.assertEqual(stats['total_achievements'], 3)
        self.assertEqual(stats['total_points'], 45)  # 10 + 15 + 20
        
        # 8. Проверяем, что уведомления созданы (создаем их вручную для теста)
        user_achievements = UserAchievement.objects.filter(user=self.user)
        for ua in user_achievements:
            AchievementNotification.create_achievement_notification(self.user, ua.achievement)
        
        notifications = AchievementNotification.objects.filter(user=self.user)
        self.assertEqual(notifications.count(), 3)
    
    def test_achievement_progress_tracking(self):
        """Тест отслеживания прогресса достижений."""
        # Проверяем прогресс для достижения по весу (нужно 3 записи)
        progress = self.weight_achievement.get_progress_for_user(self.user)
        self.assertEqual(progress['current_progress'], 0)
        self.assertEqual(progress['progress_percentage'], 0)
        
        # Добавляем одну запись веса
        base_date = timezone.now()
        WeightRecord.objects.create(user=self.user, weight=65.0, date=base_date)
        
        progress = self.weight_achievement.get_progress_for_user(self.user)
        self.assertEqual(progress['current_progress'], 1)
        self.assertEqual(progress['progress_percentage'], 33)  # 1/3 * 100
        
        # Добавляем еще две записи с разными датами
        WeightRecord.objects.create(user=self.user, weight=65.5, date=base_date - timedelta(days=1))
        WeightRecord.objects.create(user=self.user, weight=66.0, date=base_date - timedelta(days=2))
        
        progress = self.weight_achievement.get_progress_for_user(self.user)
        self.assertEqual(progress['current_progress'], 3)
        self.assertEqual(progress['progress_percentage'], 100)
        self.assertTrue(progress['is_completed'])