"""
Базовые тесты для API управления таймерами кормления.

Этот модуль содержит простые тесты для проверки основной функциональности
API эндпоинтов управления таймерами кормления без сложного мокирования.
Тесты покрывают требования 6.1 и 6.2.
"""

import json
import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class FeedingTimerBasicTest(TestCase):
    """Базовые тесты для API управления таймерами кормления."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        
        # Создаем тестового пользователя Django
        self.django_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_id = self.django_user.id
    
    def test_start_feeding_timer_endpoint_exists(self):
        """Тест существования эндпоинта запуска таймера."""
        data = {
            'breast': 'left'
        }
        
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Эндпоинт должен существовать (не 404)
        self.assertNotEqual(response.status_code, 404)
    
    def test_start_feeding_timer_invalid_breast_parameter(self):
        """Тест валидации параметра breast."""
        data = {
            'breast': 'invalid'
        }
        
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Должна быть ошибка валидации
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('должен быть "left" или "right"', response_data['error'])
    
    def test_start_feeding_timer_missing_breast_parameter(self):
        """Тест отсутствия обязательного параметра breast."""
        data = {}
        
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Должна быть ошибка валидации
        self.assertEqual(response.status_code, 400)
    
    def test_pause_feeding_timer_endpoint_exists(self):
        """Тест существования эндпоинта приостановки таймера."""
        data = {
            'breast': 'left'
        }
        
        response = self.client.post(
            reverse('webapp:pause_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1,
                'session_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Эндпоинт должен существовать (не 404)
        self.assertNotEqual(response.status_code, 404)
    
    def test_pause_feeding_timer_invalid_breast_parameter(self):
        """Тест валидации параметра breast для приостановки."""
        data = {
            'breast': 'invalid'
        }
        
        response = self.client.post(
            reverse('webapp:pause_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1,
                'session_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Должна быть ошибка валидации
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('должен быть "left" или "right"', response_data['error'])
    
    def test_stop_feeding_session_endpoint_exists(self):
        """Тест существования эндпоинта остановки сессии."""
        response = self.client.post(
            reverse('webapp:stop_feeding_session', kwargs={
                'user_id': self.user_id,
                'child_id': 1,
                'session_id': 1
            }),
            content_type='application/json'
        )
        
        # Эндпоинт должен существовать (не 404)
        self.assertNotEqual(response.status_code, 404)
    
    def test_switch_breast_endpoint_exists(self):
        """Тест существования эндпоинта переключения груди."""
        data = {
            'to_breast': 'right'
        }
        
        response = self.client.post(
            reverse('webapp:switch_breast', kwargs={
                'user_id': self.user_id,
                'child_id': 1,
                'session_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Эндпоинт должен существовать (не 404)
        self.assertNotEqual(response.status_code, 404)
    
    def test_switch_breast_invalid_parameter(self):
        """Тест валидации параметра to_breast."""
        data = {
            'to_breast': 'invalid'
        }
        
        response = self.client.post(
            reverse('webapp:switch_breast', kwargs={
                'user_id': self.user_id,
                'child_id': 1,
                'session_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Должна быть ошибка валидации
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('должен быть "left" или "right"', response_data['error'])
    
    def test_get_active_feeding_session_endpoint_exists(self):
        """Тест существования эндпоинта получения активной сессии."""
        response = self.client.get(
            reverse('webapp:get_active_feeding_session', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            })
        )
        
        # Эндпоинт должен существовать (не 404)
        self.assertNotEqual(response.status_code, 404)
    
    def test_user_not_found_error_handling(self):
        """Тест обработки ошибки когда пользователь не найден."""
        data = {
            'breast': 'left'
        }
        
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': 999,  # Несуществующий пользователь
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Должна быть ошибка 404
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('Пользователь не найден', response_data['error'])
    
    def test_url_patterns_are_correct(self):
        """Тест корректности URL паттернов."""
        # Проверяем, что все URL паттерны корректно разрешаются
        urls_to_test = [
            ('webapp:start_feeding_timer', {'user_id': 1, 'child_id': 1}),
            ('webapp:pause_feeding_timer', {'user_id': 1, 'child_id': 1, 'session_id': 1}),
            ('webapp:stop_feeding_session', {'user_id': 1, 'child_id': 1, 'session_id': 1}),
            ('webapp:switch_breast', {'user_id': 1, 'child_id': 1, 'session_id': 1}),
            ('webapp:get_active_feeding_session', {'user_id': 1, 'child_id': 1}),
        ]
        
        for url_name, kwargs in urls_to_test:
            with self.subTest(url_name=url_name):
                url = reverse(url_name, kwargs=kwargs)
                self.assertIsNotNone(url)
                self.assertTrue(url.startswith('/api/'))
    
    def test_http_methods_validation(self):
        """Тест валидации HTTP методов."""
        # Тест GET запроса к POST эндпоинту
        response = self.client.get(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            })
        )
        
        # Должна быть ошибка метода (405 Method Not Allowed)
        self.assertEqual(response.status_code, 405)
        
        # Тест POST запроса к GET эндпоинту
        response = self.client.post(
            reverse('webapp:get_active_feeding_session', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # Должна быть ошибка метода (405 Method Not Allowed)
        self.assertEqual(response.status_code, 405)
    
    def test_json_content_type_handling(self):
        """Тест обработки JSON content type."""
        # Тест с правильным content type
        data = {
            'breast': 'left'
        }
        
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Не должно быть ошибки content type
        self.assertNotEqual(response.status_code, 415)  # Unsupported Media Type
        
        # Тест с неправильным content type
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data='breast=left',
            content_type='application/x-www-form-urlencoded'
        )
        
        # Может быть ошибка парсинга JSON, но не content type
        self.assertIn(response.status_code, [400, 500])  # Bad Request или Internal Server Error


if __name__ == '__main__':
    unittest.main()