"""
Тесты для API управления таймерами кормления.

Этот модуль содержит тесты для API эндпоинтов управления таймерами кормления,
включая запуск, паузу, остановку таймеров и переключение между грудями.
Тесты покрывают требования 6.1 и 6.2.
"""

import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from botapp.models_child import Child
from botapp.models_timers import FeedingSession


class FeedingTimerAPITest(TestCase):
    """Тесты для API управления таймерами кормления."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_id = self.user.id
        
        # Мокаем базу данных и создаем тестовые объекты
        self.mock_user = MagicMock()
        self.mock_user.id = self.user_id
        
        self.mock_child = MagicMock()
        self.mock_child.id = 1
        self.mock_child.user_id = self.user_id
        
        # Создаем более реалистичный мок для FeedingSession
        self.mock_feeding_session = MagicMock()
        self.mock_feeding_session.id = 1
        self.mock_feeding_session.child_id = 1
        self.mock_feeding_session.timestamp = datetime.utcnow()
        self.mock_feeding_session.end_time = None
        self.mock_feeding_session.type = 'breast'
        self.mock_feeding_session.left_breast_duration = 0
        self.mock_feeding_session.right_breast_duration = 0
        self.mock_feeding_session.left_timer_active = False
        self.mock_feeding_session.right_timer_active = False
        self.mock_feeding_session.left_timer_start = None
        self.mock_feeding_session.right_timer_start = None
        self.mock_feeding_session.last_active_breast = None
        self.mock_feeding_session.amount = None
        self.mock_feeding_session.duration = None
        self.mock_feeding_session.breast = None
        self.mock_feeding_session.milk_type = None
        self.mock_feeding_session.food_type = None
        self.mock_feeding_session.notes = ''
        
        # Настраиваем getattr для корректной работы с feeding_session_to_dict
        def mock_getattr(obj, name, default=None):
            if hasattr(obj, name):
                return getattr(obj, name)
            return default
        
        # Переопределяем поведение getattr для мока
        original_getattr = getattr
        def patched_getattr(obj, name, default=None):
            if obj is self.mock_feeding_session:
                return mock_getattr(obj, name, default)
            return original_getattr(obj, name, default) if default is None else original_getattr(obj, name, default)
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_start_feeding_timer_left_breast(self, mock_get_db_manager):
        """Тест запуска таймера для левой груди."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child   # Запрос ребенка
        ]
        
        # Данные запроса
        data = {
            'breast': 'left'
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('message', response_data)
        self.assertIn('левой груди запущен', response_data['message'])
        self.assertEqual(response_data['breast'], 'left')
        self.assertIn('session_id', response_data)
        self.assertIn('timer_start', response_data)
        self.assertIn('session_data', response_data)
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_start_feeding_timer_right_breast(self, mock_get_db_manager):
        """Тест запуска таймера для правой груди."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child   # Запрос ребенка
        ]
        
        # Данные запроса
        data = {
            'breast': 'right'
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('message', response_data)
        self.assertIn('правой груди запущен', response_data['message'])
        self.assertEqual(response_data['breast'], 'right')
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_start_feeding_timer_invalid_breast(self, mock_get_db_manager):
        """Тест запуска таймера с неверным параметром груди."""
        # Данные запроса с неверным параметром
        data = {
            'breast': 'invalid'
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('должен быть "left" или "right"', response_data['error'])
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_start_feeding_timer_with_existing_session(self, mock_get_db_manager):
        """Тест запуска таймера с существующей сессией."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child,  # Запрос ребенка
            self.mock_feeding_session  # Запрос существующей сессии
        ]
        
        # Данные запроса с ID существующей сессии
        data = {
            'breast': 'left',
            'session_id': 1
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['session_id'], 1)
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_start_feeding_timer_already_active(self, mock_get_db_manager):
        """Тест запуска таймера, когда таймер уже активен."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка активного таймера
        self.mock_feeding_session.left_timer_active = True
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child,  # Запрос ребенка
            self.mock_feeding_session  # Запрос существующей сессии
        ]
        
        # Данные запроса
        data = {
            'breast': 'left',
            'session_id': 1
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('уже активен', response_data['error'])
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_pause_feeding_timer(self, mock_get_db_manager):
        """Тест приостановки таймера кормления."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка активного таймера
        self.mock_feeding_session.left_timer_active = True
        self.mock_feeding_session.left_timer_start = datetime.utcnow() - timedelta(minutes=5)
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child,  # Запрос ребенка
            self.mock_feeding_session  # Запрос сессии
        ]
        
        # Данные запроса
        data = {
            'breast': 'left'
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:pause_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1,
                'session_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('message', response_data)
        self.assertIn('приостановлен', response_data['message'])
        self.assertEqual(response_data['breast'], 'left')
        self.assertEqual(response_data['session_id'], 1)
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_pause_feeding_timer_not_active(self, mock_get_db_manager):
        """Тест приостановки неактивного таймера."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Таймер неактивен
        self.mock_feeding_session.left_timer_active = False
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child,  # Запрос ребенка
            self.mock_feeding_session  # Запрос сессии
        ]
        
        # Данные запроса
        data = {
            'breast': 'left'
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:pause_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1,
                'session_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('не активен', response_data['error'])
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_stop_feeding_session(self, mock_get_db_manager):
        """Тест завершения сессии кормления."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка активных таймеров
        self.mock_feeding_session.left_timer_active = True
        self.mock_feeding_session.right_timer_active = True
        self.mock_feeding_session.left_timer_start = datetime.utcnow() - timedelta(minutes=5)
        self.mock_feeding_session.right_timer_start = datetime.utcnow() - timedelta(minutes=3)
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child,  # Запрос ребенка
            self.mock_feeding_session  # Запрос сессии
        ]
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:stop_feeding_session', kwargs={
                'user_id': self.user_id,
                'child_id': 1,
                'session_id': 1
            }),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('message', response_data)
        self.assertIn('завершена', response_data['message'])
        self.assertEqual(response_data['session_id'], 1)
        self.assertIn('session_data', response_data)
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_switch_breast(self, mock_get_db_manager):
        """Тест переключения между грудями."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка активного таймера для левой груди
        self.mock_feeding_session.left_timer_active = True
        self.mock_feeding_session.right_timer_active = False
        self.mock_feeding_session.left_timer_start = datetime.utcnow() - timedelta(minutes=5)
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child,  # Запрос ребенка
            self.mock_feeding_session  # Запрос сессии
        ]
        
        # Данные запроса - переключаемся на правую грудь
        data = {
            'to_breast': 'right'
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:switch_breast', kwargs={
                'user_id': self.user_id,
                'child_id': 1,
                'session_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('message', response_data)
        self.assertIn('Переключение', response_data['message'])
        self.assertEqual(response_data['from_breast'], 'left')
        self.assertEqual(response_data['to_breast'], 'right')
        self.assertEqual(response_data['session_id'], 1)
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_switch_breast_target_already_active(self, mock_get_db_manager):
        """Тест переключения на уже активную грудь."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка активного таймера для правой груди
        self.mock_feeding_session.right_timer_active = True
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child,  # Запрос ребенка
            self.mock_feeding_session  # Запрос сессии
        ]
        
        # Данные запроса - пытаемся переключиться на уже активную правую грудь
        data = {
            'to_breast': 'right'
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:switch_breast', kwargs={
                'user_id': self.user_id,
                'child_id': 1,
                'session_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('уже активен', response_data['error'])
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_get_active_feeding_session_with_active(self, mock_get_db_manager):
        """Тест получения активной сессии кормления."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка активной сессии
        self.mock_feeding_session.left_timer_active = True
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child   # Запрос ребенка
        ]
        mock_session.query.return_value.filter.return_value.first.return_value = self.mock_feeding_session
        
        # Выполнение запроса
        response = self.client.get(
            reverse('webapp:get_active_feeding_session', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            })
        )
        
        # Проверки
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['has_active_session'])
        self.assertIsNotNone(response_data['session_data'])
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_get_active_feeding_session_no_active(self, mock_get_db_manager):
        """Тест получения активной сессии когда активных сессий нет."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Запрос пользователя
            self.mock_child   # Запрос ребенка
        ]
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Выполнение запроса
        response = self.client.get(
            reverse('webapp:get_active_feeding_session', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            })
        )
        
        # Проверки
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['has_active_session'])
        self.assertIsNone(response_data['session_data'])
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_user_not_found(self, mock_get_db_manager):
        """Тест обработки случая, когда пользователь не найден."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Пользователь не найден
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Данные запроса
        data = {
            'breast': 'left'
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': 999,  # Несуществующий пользователь
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('Пользователь не найден', response_data['error'])
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_child_not_found(self, mock_get_db_manager):
        """Тест обработки случая, когда ребенок не найден."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Пользователь найден
            None  # Ребенок не найден
        ]
        
        # Данные запроса
        data = {
            'breast': 'left'
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 999  # Несуществующий ребенок
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('Ребенок не найден', response_data['error'])
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_child_not_belongs_to_user(self, mock_get_db_manager):
        """Тест обработки случая, когда ребенок не принадлежит пользователю."""
        # Настройка мока
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Ребенок принадлежит другому пользователю
        self.mock_child.user_id = 999
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            self.mock_user,  # Пользователь найден
            self.mock_child  # Ребенок найден, но принадлежит другому пользователю
        ]
        
        # Данные запроса
        data = {
            'breast': 'left'
        }
        
        # Выполнение запроса
        response = self.client.post(
            reverse('webapp:start_feeding_timer', kwargs={
                'user_id': self.user_id,
                'child_id': 1
            }),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверки
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('не принадлежит пользователю', response_data['error'])


if __name__ == '__main__':
    unittest.main()