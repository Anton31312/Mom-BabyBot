"""
Тесты для функциональности визуальной статистики прогресса.

Этот модуль содержит тесты для API и логики сбора, анализа и отображения
статистики прогресса пользователей.

Соответствует требованию 9.4 о визуальной статистике прогресса и достижений.
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock

from webapp.models import (
    FeedingSession, WeightRecord, BloodPressureRecord, UserProfile,
    Achievement, UserAchievement, PersonalizedContent, UserContentView,
    DailyTip
)
from webapp.api_progress import (
    ProgressStatisticsView, ProgressChartsView, ProgressSummaryView,
    get_user_progress_summary, update_user_progress_metrics
)


class ProgressStatisticsViewTest(TestCase):
    """Тесты для API статистики прогресса."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Создаем профиль пользователя
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            pregnancy_status='pregnant',
            pregnancy_week=20,
            experience_level='first_time',
            interests=['nutrition', 'health']
        )
        
        # Создаем тестовые данные
        self._create_test_data()
        
        # Авторизуемся
        self.client.login(username='testuser', password='testpass123')
    
    def _create_test_data(self):
        """Создает тестовые данные для статистики."""
        now = timezone.now()
        
        # Создаем сессии кормления
        for i in range(5):
            FeedingSession.objects.create(
                user=self.user,
                start_time=now - timedelta(days=i),
                end_time=now - timedelta(days=i) + timedelta(hours=1),
                left_breast_duration=timedelta(minutes=15),
                right_breast_duration=timedelta(minutes=10),
                feeding_type='breast'
            )
        
        # Создаем записи веса
        for i in range(3):
            WeightRecord.objects.create(
                user=self.user,
                date=now - timedelta(days=i * 2),
                weight=Decimal('65.5') + Decimal(str(i * 0.5)),
                notes=f'Запись веса {i}'
            )
        
        # Создаем записи давления
        for i in range(4):
            BloodPressureRecord.objects.create(
                user=self.user,
                date=now - timedelta(days=i),
                systolic=120 + i * 5,
                diastolic=80 + i * 2,
                pulse=70 + i
            )
        
        # Создаем достижения
        self.achievement1 = Achievement.objects.create(
            title='Первое кормление',
            description='Записать первую сессию кормления',
            achievement_type='feeding_milestone',
            difficulty='easy',
            points=10,
            condition_type='feeding_sessions',
            condition_value=1
        )
        
        self.achievement2 = Achievement.objects.create(
            title='Активный пользователь',
            description='Использовать приложение 5 дней',
            achievement_type='app_usage',
            difficulty='medium',
            points=25,
            condition_type='app_usage_days',
            condition_value=5
        )
        
        # Присваиваем одно достижение
        UserAchievement.objects.create(
            user=self.user,
            achievement=self.achievement1
        )
        
        # Создаем персонализированный контент
        self.content = PersonalizedContent.objects.create(
            title='Совет дня',
            content='Полезный совет для беременных',
            content_type='tip',
            pregnancy_status_filter=['pregnant'],
            is_active=True
        )
        
        # Создаем просмотр контента
        UserContentView.objects.create(
            user=self.user,
            content=self.content,
            interaction_type='viewed'
        )
    
    def test_get_statistics_success(self):
        """Тест успешного получения статистики."""
        url = reverse('webapp:progress_statistics')
        response = self.client.get(url, {'period': 'month'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['period'], 'month')
        self.assertIn('statistics', data)
        
        stats = data['statistics']
        
        # Проверяем структуру статистики
        self.assertIn('feeding', stats)
        self.assertIn('health', stats)
        self.assertIn('achievements', stats)
        self.assertIn('engagement', stats)
        self.assertIn('activity', stats)
        
        # Проверяем данные кормления
        feeding_stats = stats['feeding']
        self.assertEqual(feeding_stats['total_sessions'], 5)
        self.assertGreater(feeding_stats['total_duration_minutes'], 0)
        
        # Проверяем данные здоровья
        health_stats = stats['health']
        self.assertEqual(health_stats['weight_records_count'], 3)
        self.assertEqual(health_stats['blood_pressure_records_count'], 4)
        
        # Проверяем данные достижений
        achievement_stats = stats['achievements']
        self.assertEqual(achievement_stats['total_earned'], 1)
        self.assertEqual(achievement_stats['total_points'], 10)
    
    def test_get_statistics_with_details(self):
        """Тест получения статистики с детальной разбивкой."""
        url = reverse('webapp:progress_statistics')
        response = self.client.get(url, {
            'period': 'week',
            'include_details': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertIn('details', data['statistics'])
        self.assertIn('trends', data['statistics'])
    
    def test_get_statistics_different_periods(self):
        """Тест получения статистики для разных периодов."""
        url = reverse('webapp:progress_statistics')
        
        periods = ['week', 'month', 'quarter', 'year', 'all']
        
        for period in periods:
            with self.subTest(period=period):
                response = self.client.get(url, {'period': period})
                self.assertEqual(response.status_code, 200)
                
                data = json.loads(response.content)
                self.assertTrue(data['success'])
                self.assertEqual(data['period'], period)
    
    def test_get_statistics_unauthorized(self):
        """Тест получения статистики неавторизованным пользователем."""
        self.client.logout()
        url = reverse('webapp:progress_statistics')
        response = self.client.get(url)
        
        # Должен быть редирект на страницу входа
        self.assertEqual(response.status_code, 302)
    
    def test_get_statistics_empty_data(self):
        """Тест получения статистики при отсутствии данных."""
        # Создаем нового пользователя без данных
        empty_user = User.objects.create_user(
            username='emptyuser',
            password='testpass123'
        )
        
        self.client.logout()
        self.client.login(username='emptyuser', password='testpass123')
        
        url = reverse('webapp:progress_statistics')
        response = self.client.get(url, {'period': 'month'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        stats = data['statistics']
        
        # Проверяем, что статистика пустая
        self.assertEqual(stats['feeding']['total_sessions'], 0)
        self.assertEqual(stats['health']['weight_records_count'], 0)
        self.assertEqual(stats['achievements']['total_earned'], 0)


class ProgressChartsViewTest(TestCase):
    """Тесты для API графиков прогресса."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self._create_chart_test_data()
        self.client.login(username='testuser', password='testpass123')
    
    def _create_chart_test_data(self):
        """Создает тестовые данные для графиков."""
        now = timezone.now()
        
        # Создаем данные для графика веса
        for i in range(7):
            WeightRecord.objects.create(
                user=self.user,
                date=now - timedelta(days=i),
                weight=Decimal('70.0') + Decimal(str(i * 0.1))
            )
        
        # Создаем данные для графика давления
        for i in range(5):
            BloodPressureRecord.objects.create(
                user=self.user,
                date=now - timedelta(days=i),
                systolic=120 + i,
                diastolic=80 + i
            )
        
        # Создаем данные для графика кормления
        for i in range(6):
            FeedingSession.objects.create(
                user=self.user,
                start_time=now - timedelta(days=i),
                left_breast_duration=timedelta(minutes=10 + i),
                right_breast_duration=timedelta(minutes=8 + i)
            )
    
    def test_get_weight_chart(self):
        """Тест получения данных для графика веса."""
        url = reverse('webapp:progress_charts')
        response = self.client.get(url, {
            'chart_type': 'weight',
            'period': 'week',
            'format': 'chart_js'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['chart_type'], 'weight')
        self.assertIn('data', data)
        
        chart_data = data['data']
        self.assertIn('labels', chart_data)
        self.assertIn('datasets', chart_data)
        self.assertEqual(len(chart_data['datasets']), 1)
        self.assertEqual(chart_data['datasets'][0]['label'], 'Вес (кг)')
    
    def test_get_blood_pressure_chart(self):
        """Тест получения данных для графика давления."""
        url = reverse('webapp:progress_charts')
        response = self.client.get(url, {
            'chart_type': 'blood_pressure',
            'period': 'week',
            'format': 'chart_js'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        chart_data = data['data']
        self.assertEqual(len(chart_data['datasets']), 2)
        
        # Проверяем наличие систолического и диастолического давления
        labels = [ds['label'] for ds in chart_data['datasets']]
        self.assertIn('Систолическое', labels)
        self.assertIn('Диастолическое', labels)
    
    def test_get_feeding_chart(self):
        """Тест получения данных для графика кормления."""
        url = reverse('webapp:progress_charts')
        response = self.client.get(url, {
            'chart_type': 'feeding',
            'period': 'week',
            'format': 'chart_js'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        chart_data = data['data']
        self.assertEqual(len(chart_data['datasets']), 2)
        
        # Проверяем наличие данных для обеих грудей
        labels = [ds['label'] for ds in chart_data['datasets']]
        self.assertIn('Левая грудь (мин)', labels)
        self.assertIn('Правая грудь (мин)', labels)
    
    def test_get_activity_chart(self):
        """Тест получения данных для графика активности."""
        url = reverse('webapp:progress_charts')
        response = self.client.get(url, {
            'chart_type': 'activity',
            'period': 'week',
            'format': 'chart_js'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        chart_data = data['data']
        self.assertEqual(len(chart_data['datasets']), 1)
        self.assertEqual(chart_data['datasets'][0]['label'], 'Общая активность')
    
    def test_get_raw_format_data(self):
        """Тест получения данных в сыром формате."""
        url = reverse('webapp:progress_charts')
        response = self.client.get(url, {
            'chart_type': 'weight',
            'period': 'week',
            'format': 'raw'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        chart_data = data['data']
        
        # В сыром формате данные должны быть списком объектов
        self.assertIsInstance(chart_data, list)
        if chart_data:
            self.assertIn('date', chart_data[0])
            self.assertIn('weight', chart_data[0])
    
    def test_invalid_chart_type(self):
        """Тест запроса неподдерживаемого типа графика."""
        url = reverse('webapp:progress_charts')
        response = self.client.get(url, {
            'chart_type': 'invalid_type',
            'period': 'week'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)


class ProgressSummaryViewTest(TestCase):
    """Тесты для API сводки прогресса."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self._create_summary_test_data()
        self.client.login(username='testuser', password='testpass123')
    
    def _create_summary_test_data(self):
        """Создает тестовые данные для сводки."""
        now = timezone.now()
        
        # Создаем достижения
        achievement1 = Achievement.objects.create(
            title='Новичок',
            description='Первые шаги',
            achievement_type='app_usage',
            difficulty='easy',
            points=50,
            condition_type='app_usage_days',
            condition_value=1
        )
        
        achievement2 = Achievement.objects.create(
            title='Продвинутый',
            description='Опытный пользователь',
            achievement_type='app_usage',
            difficulty='medium',
            points=150,
            condition_type='app_usage_days',
            condition_value=10
        )
        
        # Присваиваем достижения
        UserAchievement.objects.create(user=self.user, achievement=achievement1)
        UserAchievement.objects.create(user=self.user, achievement=achievement2)
        
        # Создаем активность для серии
        for i in range(3):
            FeedingSession.objects.create(
                user=self.user,
                start_time=now - timedelta(days=i),
                left_breast_duration=timedelta(minutes=10)
            )
    
    def test_get_summary_success(self):
        """Тест успешного получения сводки прогресса."""
        url = reverse('webapp:progress_summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertIn('summary', data)
        
        summary = data['summary']
        
        # Проверяем структуру сводки
        self.assertIn('user_level', summary)
        self.assertIn('consistency_score', summary)
        self.assertIn('total_points', summary)
        self.assertIn('active_streak', summary)
        self.assertIn('next_achievements', summary)
        self.assertIn('recent_milestones', summary)
        self.assertIn('quick_stats', summary)
        
        # Проверяем уровень пользователя
        user_level = summary['user_level']
        self.assertIn('current_level', user_level)
        self.assertIn('total_points', user_level)
        self.assertIn('progress_to_next_level', user_level)
        
        # Проверяем, что очки рассчитаны правильно
        self.assertEqual(user_level['total_points'], 200)  # 50 + 150
    
    def test_user_level_calculation(self):
        """Тест расчета уровня пользователя."""
        view = ProgressSummaryView()
        
        # Тест уровня 1 (менее 100 очков)
        user1 = User.objects.create_user(username='user1', password='pass')
        achievement = Achievement.objects.create(
            title='Test', description='Test', achievement_type='app_usage',
            difficulty='easy', points=50, condition_type='app_usage_days', condition_value=1
        )
        UserAchievement.objects.create(user=user1, achievement=achievement)
        
        level_info = view._calculate_user_level(user1)
        self.assertEqual(level_info['current_level'], 1)
        self.assertEqual(level_info['total_points'], 50)
        
        # Тест уровня 2 (100-299 очков)
        user2 = User.objects.create_user(username='user2', password='pass')
        achievement2 = Achievement.objects.create(
            title='Test2', description='Test2', achievement_type='app_usage',
            difficulty='medium', points=150, condition_type='app_usage_days', condition_value=1
        )
        UserAchievement.objects.create(user=user2, achievement=achievement2)
        
        level_info = view._calculate_user_level(user2)
        self.assertEqual(level_info['current_level'], 2)
        self.assertEqual(level_info['total_points'], 150)
    
    def test_active_streak_calculation(self):
        """Тест расчета серии активности."""
        view = ProgressSummaryView()
        
        # Создаем активность на последние 3 дня
        now = timezone.now()
        for i in range(3):
            FeedingSession.objects.create(
                user=self.user,
                start_time=now - timedelta(days=i),
                left_breast_duration=timedelta(minutes=5)
            )
        
        streak = view._calculate_active_streak(self.user)
        self.assertGreaterEqual(streak, 3)
    
    def test_next_achievements(self):
        """Тест получения ближайших достижений."""
        view = ProgressSummaryView()
        
        # Создаем достижение с прогрессом
        achievement = Achievement.objects.create(
            title='Много кормлений',
            description='10 сессий кормления',
            achievement_type='feeding_milestone',
            difficulty='medium',
            points=100,
            condition_type='feeding_sessions',
            condition_value=10
        )
        
        # Создаем 5 сессий (50% прогресса)
        for i in range(5):
            FeedingSession.objects.create(
                user=self.user,
                start_time=timezone.now() - timedelta(hours=i),
                left_breast_duration=timedelta(minutes=10)
            )
        
        next_achievements = view._get_next_achievements(self.user, limit=5)
        
        # Должно быть хотя бы одно достижение с прогрессом
        self.assertGreater(len(next_achievements), 0)
        
        # Проверяем структуру данных
        achievement_data = next_achievements[0]
        self.assertIn('id', achievement_data)
        self.assertIn('title', achievement_data)
        self.assertIn('progress_percentage', achievement_data)


class ProgressUtilityFunctionsTest(TestCase):
    """Тесты для вспомогательных функций прогресса."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_get_user_progress_summary(self):
        """Тест функции получения сводки прогресса пользователя."""
        # Создаем базовые данные
        achievement = Achievement.objects.create(
            title='Test Achievement',
            description='Test',
            achievement_type='app_usage',
            difficulty='easy',
            points=25,
            condition_type='app_usage_days',
            condition_value=1
        )
        UserAchievement.objects.create(user=self.user, achievement=achievement)
        
        summary = get_user_progress_summary(self.user)
        
        # Проверяем структуру сводки
        self.assertIn('user_level', summary)
        self.assertIn('consistency_score', summary)
        self.assertIn('active_streak', summary)
        self.assertIn('total_points', summary)
        
        # Проверяем значения
        self.assertEqual(summary['total_points'], 25)
        self.assertIsInstance(summary['consistency_score'], (int, float))
        self.assertIsInstance(summary['active_streak'], int)
    
    def test_get_user_progress_summary_error_handling(self):
        """Тест обработки ошибок в функции получения сводки."""
        # Создаем пользователя без данных
        empty_user = User.objects.create_user(
            username='emptyuser',
            password='testpass123'
        )
        
        summary = get_user_progress_summary(empty_user)
        
        # Должны получить значения по умолчанию
        self.assertEqual(summary['total_points'], 0)
        self.assertEqual(summary['user_level']['current_level'], 1)
        self.assertEqual(summary['active_streak'], 0)
    
    @patch('webapp.api_progress.logger')
    def test_update_user_progress_metrics(self, mock_logger):
        """Тест функции обновления метрик прогресса."""
        # Тестируем вызов функции
        update_user_progress_metrics(
            self.user, 
            'feeding', 
            {'session_id': 123}
        )
        
        # Проверяем, что логирование произошло
        mock_logger.info.assert_called_once()
        
        # Проверяем аргументы логирования
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('feeding', call_args)
        self.assertIn(str(self.user.id), call_args)
    
    @patch('webapp.api_achievement.trigger_achievement_check')
    def test_update_user_progress_metrics_triggers_achievements(self, mock_trigger):
        """Тест того, что обновление метрик запускает проверку достижений."""
        update_user_progress_metrics(self.user, 'health_record')
        
        # Проверяем, что функция проверки достижений была вызвана
        mock_trigger.assert_called_once_with(
            self.user, 
            {'action_type': 'health_record', 'context': None}
        )


class ProgressViewIntegrationTest(TestCase):
    """Интеграционные тесты для представления прогресса."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_progress_dashboard_view(self):
        """Тест отображения страницы дашборда прогресса."""
        url = reverse('webapp:progress_dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Статистика прогресса')
        self.assertContains(response, 'progress-dashboard')
    
    def test_progress_dashboard_unauthorized(self):
        """Тест доступа к дашборду неавторизованного пользователя."""
        self.client.logout()
        url = reverse('webapp:progress_dashboard')
        response = self.client.get(url)
        
        # Должен быть редирект на страницу входа
        self.assertEqual(response.status_code, 302)
    
    def test_api_endpoints_integration(self):
        """Тест интеграции всех API endpoints."""
        # Создаем тестовые данные
        FeedingSession.objects.create(
            user=self.user,
            start_time=timezone.now(),
            left_breast_duration=timedelta(minutes=10)
        )
        
        # Тестируем все endpoints
        endpoints = [
            'webapp:progress_statistics',
            'webapp:progress_charts',
            'webapp:progress_summary'
        ]
        
        for endpoint_name in endpoints:
            with self.subTest(endpoint=endpoint_name):
                url = reverse(endpoint_name)
                response = self.client.get(url)
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)
                self.assertTrue(data['success'])


class ProgressDataConsistencyTest(TestCase):
    """Тесты для проверки консистентности данных прогресса."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_feeding_duration_calculation(self):
        """Тест правильности расчета продолжительности кормления."""
        session = FeedingSession.objects.create(
            user=self.user,
            start_time=timezone.now(),
            left_breast_duration=timedelta(minutes=15),
            right_breast_duration=timedelta(minutes=10)
        )
        
        # Проверяем расчет общей продолжительности
        total_minutes = session.get_total_duration_minutes()
        self.assertEqual(total_minutes, 25)
        
        # Проверяем расчет процентов
        left_percentage = session.get_breast_percentage('left')
        right_percentage = session.get_breast_percentage('right')
        
        self.assertEqual(left_percentage, 60.0)  # 15/25 * 100
        self.assertEqual(right_percentage, 40.0)  # 10/25 * 100
    
    def test_weight_trend_calculation(self):
        """Тест расчета тренда изменения веса."""
        view = ProgressStatisticsView()
        
        # Создаем записи веса с увеличением
        now = timezone.now()
        WeightRecord.objects.create(
            user=self.user,
            date=now - timedelta(days=5),
            weight=Decimal('65.0')
        )
        WeightRecord.objects.create(
            user=self.user,
            date=now,
            weight=Decimal('66.0')
        )
        
        trend = view._calculate_weight_trend(self.user, now - timedelta(days=10))
        self.assertEqual(trend, 'increasing')
        
        # Создаем записи с уменьшением
        user2 = User.objects.create_user(username='user2', password='pass')
        WeightRecord.objects.create(
            user=user2,
            date=now - timedelta(days=5),
            weight=Decimal('70.0')
        )
        WeightRecord.objects.create(
            user=user2,
            date=now,
            weight=Decimal('68.5')
        )
        
        trend = view._calculate_weight_trend(user2, now - timedelta(days=10))
        self.assertEqual(trend, 'decreasing')
    
    def test_blood_pressure_categorization(self):
        """Тест правильности категоризации артериального давления."""
        # Нормальное давление
        bp_normal = BloodPressureRecord.objects.create(
            user=self.user,
            date=timezone.now(),
            systolic=120,
            diastolic=80
        )
        
        self.assertEqual(bp_normal.get_pressure_category(), 'Нормальное')
        self.assertTrue(bp_normal.is_pressure_normal())
        self.assertFalse(bp_normal.needs_medical_attention())
        
        # Высокое давление
        bp_high = BloodPressureRecord.objects.create(
            user=self.user,
            date=timezone.now(),
            systolic=180,
            diastolic=110
        )
        
        self.assertIn('Гипертония', bp_high.get_pressure_category())
        self.assertFalse(bp_high.is_pressure_normal())
        self.assertTrue(bp_high.needs_medical_attention())
    
    def test_consistency_score_bounds(self):
        """Тест того, что оценка постоянства находится в правильных границах."""
        view = ProgressStatisticsView()
        
        # Создаем активность на каждый день последней недели
        now = timezone.now()
        for i in range(7):
            FeedingSession.objects.create(
                user=self.user,
                start_time=now - timedelta(days=i),
                left_breast_duration=timedelta(minutes=5)
            )
        
        start_date = now - timedelta(days=7)
        score = view._calculate_consistency_score(self.user, start_date, now)
        
        # Оценка должна быть в пределах 0-100
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        
        # При ежедневной активности оценка должна быть высокой
        self.assertGreater(score, 80)