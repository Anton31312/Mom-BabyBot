"""
Тесты для функциональности подтверждения ознакомления с дисклеймером
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from webapp.models import DisclaimerAcknowledgment
from webapp.utils.disclaimer_utils import (
    check_disclaimer_acknowledgment,
    get_user_acknowledgments,
    get_features_requiring_acknowledgment,
    create_acknowledgment_context,
    get_disclaimer_text
)
import json


class DisclaimerAcknowledgmentModelTest(TestCase):
    """Тесты для модели DisclaimerAcknowledgment"""

    def setUp(self):
        """Настройка тестового окружения"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_disclaimer_acknowledgment(self):
        """Тест создания записи подтверждения дисклеймера"""
        acknowledgment = DisclaimerAcknowledgment.objects.create(
            user=self.user,
            feature='pregnancy_info',
            ip_address='127.0.0.1',
            user_agent='Test Browser'
        )
        
        self.assertEqual(acknowledgment.user, self.user)
        self.assertEqual(acknowledgment.feature, 'pregnancy_info')
        self.assertEqual(acknowledgment.ip_address, '127.0.0.1')
        self.assertEqual(acknowledgment.user_agent, 'Test Browser')
        self.assertIsNotNone(acknowledgment.acknowledged_at)

    def test_has_user_acknowledged_true(self):
        """Тест проверки подтверждения - пользователь подтвердил"""
        DisclaimerAcknowledgment.objects.create(
            user=self.user,
            feature='nutrition_advice'
        )
        
        result = DisclaimerAcknowledgment.has_user_acknowledged(self.user, 'nutrition_advice')
        self.assertTrue(result)

    def test_has_user_acknowledged_false(self):
        """Тест проверки подтверждения - пользователь не подтвердил"""
        result = DisclaimerAcknowledgment.has_user_acknowledged(self.user, 'health_tracking')
        self.assertFalse(result)

    def test_acknowledge_feature_new(self):
        """Тест создания нового подтверждения через метод acknowledge_feature"""
        acknowledgment = DisclaimerAcknowledgment.acknowledge_feature(
            user=self.user,
            feature='child_development',
            ip_address='192.168.1.1',
            user_agent='Chrome Browser'
        )
        
        self.assertEqual(acknowledgment.user, self.user)
        self.assertEqual(acknowledgment.feature, 'child_development')
        self.assertEqual(acknowledgment.ip_address, '192.168.1.1')
        self.assertEqual(acknowledgment.user_agent, 'Chrome Browser')

    def test_acknowledge_feature_existing(self):
        """Тест получения существующего подтверждения через метод acknowledge_feature"""
        # Создаем первое подтверждение
        first_acknowledgment = DisclaimerAcknowledgment.acknowledge_feature(
            user=self.user,
            feature='kick_counter',
            ip_address='127.0.0.1'
        )
        
        # Пытаемся создать второе подтверждение для той же функции
        second_acknowledgment = DisclaimerAcknowledgment.acknowledge_feature(
            user=self.user,
            feature='kick_counter',
            ip_address='192.168.1.1'
        )
        
        # Должно вернуться то же самое подтверждение
        self.assertEqual(first_acknowledgment.id, second_acknowledgment.id)
        self.assertEqual(first_acknowledgment.ip_address, '127.0.0.1')  # IP не должен измениться

    def test_get_features_requiring_acknowledgment(self):
        """Тест получения списка функций, требующих подтверждения"""
        features = DisclaimerAcknowledgment.get_features_requiring_acknowledgment()
        
        self.assertIsInstance(features, list)
        self.assertIn('pregnancy_info', features)
        self.assertIn('nutrition_advice', features)
        self.assertIn('health_tracking', features)

    def test_get_acknowledgment_age_days(self):
        """Тест получения возраста подтверждения в днях"""
        acknowledgment = DisclaimerAcknowledgment.objects.create(
            user=self.user,
            feature='feeding_tracker'
        )
        
        age_days = acknowledgment.get_acknowledgment_age_days()
        self.assertEqual(age_days, 0)  # Только что создано

    def test_unique_constraint(self):
        """Тест уникального ограничения на пользователя и функцию"""
        # Создаем первое подтверждение
        DisclaimerAcknowledgment.objects.create(
            user=self.user,
            feature='sleep_tracker'
        )
        
        # Пытаемся создать второе подтверждение для той же комбинации
        with self.assertRaises(Exception):  # Должно вызвать ошибку уникальности
            DisclaimerAcknowledgment.objects.create(
                user=self.user,
                feature='sleep_tracker'
            )

    def test_string_representation(self):
        """Тест строкового представления модели"""
        acknowledgment = DisclaimerAcknowledgment.objects.create(
            user=self.user,
            feature='vaccine_calendar'
        )
        
        str_repr = str(acknowledgment)
        self.assertIn('testuser', str_repr)
        self.assertIn('Календарь прививок', str_repr)


class DisclaimerUtilsTest(TestCase):
    """Тесты для утилит дисклеймера"""

    def setUp(self):
        """Настройка тестового окружения"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_check_disclaimer_acknowledgment_true(self):
        """Тест проверки подтверждения через утилиту - подтверждено"""
        DisclaimerAcknowledgment.objects.create(
            user=self.user,
            feature='general_recommendations'
        )
        
        result = check_disclaimer_acknowledgment(self.user, 'general_recommendations')
        self.assertTrue(result)

    def test_check_disclaimer_acknowledgment_false(self):
        """Тест проверки подтверждения через утилиту - не подтверждено"""
        result = check_disclaimer_acknowledgment(self.user, 'pregnancy_info')
        self.assertFalse(result)

    def test_get_user_acknowledgments(self):
        """Тест получения всех подтверждений пользователя"""
        # Создаем несколько подтверждений
        DisclaimerAcknowledgment.objects.create(user=self.user, feature='nutrition_advice')
        DisclaimerAcknowledgment.objects.create(user=self.user, feature='health_tracking')
        
        acknowledgments = get_user_acknowledgments(self.user)
        self.assertEqual(acknowledgments.count(), 2)

    def test_get_features_requiring_acknowledgment_util(self):
        """Тест получения функций через утилиту"""
        features = get_features_requiring_acknowledgment()
        
        self.assertIsInstance(features, list)
        self.assertTrue(len(features) > 0)
        # Проверяем, что это список кортежей (код, название)
        for feature in features:
            self.assertIsInstance(feature, tuple)
            self.assertEqual(len(feature), 2)

    def test_create_acknowledgment_context(self):
        """Тест создания контекста для шаблона подтверждения"""
        context = create_acknowledgment_context('pregnancy_info', '/test-url/')
        
        self.assertEqual(context['feature'], 'pregnancy_info')
        self.assertEqual(context['feature_display'], 'Информация о беременности')
        self.assertEqual(context['return_url'], '/test-url/')
        self.assertIn('disclaimer_text', context)

    def test_create_acknowledgment_context_default_url(self):
        """Тест создания контекста с URL по умолчанию"""
        context = create_acknowledgment_context('nutrition_advice')
        
        self.assertEqual(context['return_url'], '/')

    def test_get_disclaimer_text(self):
        """Тест получения текста дисклеймера"""
        text = get_disclaimer_text()
        
        self.assertIsInstance(text, str)
        self.assertIn('рекомендации', text.lower())
        self.assertIn('специалист', text.lower())


class DisclaimerAcknowledgmentViewTest(TestCase):
    """Тесты для представления подтверждения дисклеймера"""

    def setUp(self):
        """Настройка тестового окружения"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_acknowledge_disclaimer_success(self):
        """Тест успешного подтверждения дисклеймера"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('webapp:acknowledge_disclaimer'),
            data=json.dumps({'feature': 'pregnancy_info'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('acknowledged_at', data)
        
        # Проверяем, что запись создана в базе данных
        self.assertTrue(
            DisclaimerAcknowledgment.objects.filter(
                user=self.user,
                feature='pregnancy_info'
            ).exists()
        )

    def test_acknowledge_disclaimer_unauthenticated(self):
        """Тест подтверждения дисклеймера неаутентифицированным пользователем"""
        response = self.client.post(
            reverse('webapp:acknowledge_disclaimer'),
            data=json.dumps({'feature': 'nutrition_advice'}),
            content_type='application/json'
        )
        
        # Должно перенаправить на страницу входа
        self.assertEqual(response.status_code, 302)

    def test_acknowledge_disclaimer_missing_feature(self):
        """Тест подтверждения дисклеймера без указания функции"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('webapp:acknowledge_disclaimer'),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Не указана функция', data['error'])

    def test_acknowledge_disclaimer_invalid_feature(self):
        """Тест подтверждения дисклеймера с неверной функцией"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('webapp:acknowledge_disclaimer'),
            data=json.dumps({'feature': 'invalid_feature'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Неизвестная функция', data['error'])

    def test_acknowledge_disclaimer_invalid_json(self):
        """Тест подтверждения дисклеймера с неверным JSON"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('webapp:acknowledge_disclaimer'),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Неверный формат данных', data['error'])

    def test_acknowledge_disclaimer_get_method(self):
        """Тест GET-запроса к endpoint подтверждения (должен быть запрещен)"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('webapp:acknowledge_disclaimer'))
        
        # Должен вернуть ошибку метода
        self.assertEqual(response.status_code, 405)

    def test_acknowledge_disclaimer_duplicate(self):
        """Тест повторного подтверждения той же функции"""
        self.client.login(username='testuser', password='testpass123')
        
        # Первое подтверждение
        response1 = self.client.post(
            reverse('webapp:acknowledge_disclaimer'),
            data=json.dumps({'feature': 'health_tracking'}),
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, 200)
        
        # Второе подтверждение той же функции
        response2 = self.client.post(
            reverse('webapp:acknowledge_disclaimer'),
            data=json.dumps({'feature': 'health_tracking'}),
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 200)
        
        # Должна быть только одна запись в базе данных
        count = DisclaimerAcknowledgment.objects.filter(
            user=self.user,
            feature='health_tracking'
        ).count()
        self.assertEqual(count, 1)