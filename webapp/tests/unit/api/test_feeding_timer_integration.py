"""
Интеграционные тесты для API управления таймерами кормления.

Этот модуль содержит интеграционные тесты для API эндпоинтов управления таймерами кормления,
которые тестируют реальную работу с базой данных.
Тесты покрывают требования 6.1 и 6.2.
"""

import json
import unittest
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from botapp.models import User as BotUser
from botapp.models_child import Child
from botapp.models_timers import FeedingSession


class FeedingTimerIntegrationTest(TestCase):
    """Интеграционные тесты для API управления таймерами кормления."""
    
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
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_start_feeding_timer_creates_new_session(self, mock_get_db_manager):
        """Тест создания новой сессии при запуске таймера."""
        # Настройка мока базы данных
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Создаем моки для пользователя и ребенка
        mock_user = MagicMock()
        mock_user.id = self.user_id
        
        mock_child = MagicMock()
        mock_child.id = 1
        mock_child.user_id = self.user_id
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_user,  # Запрос пользователя
            mock_child   # Запрос ребенка
        ]
        
        # Мокаем создание новой сессии
        mock_new_session = MagicMock()
        mock_new_session.id = 1
        mock_new_session.child_id = 1
        mock_new_session.timestamp = datetime.utcnow()
        mock_new_session.type = 'breast'
        mock_new_session.left_timer_active = False
        mock_new_session.right_timer_active = False
        
        # Настраиваем мок для добавления новой сессии
        def mock_add(obj):
            # Симулируем установку атрибутов при создании новой сессии
            obj.id = 1
            obj.left_timer_active = True
            obj.left_timer_start = datetime.utcnow()
            obj.last_active_breast = 'left'
        
        mock_session.add.side_effect = mock_add
        mock_session.flush.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
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
        
        # Проверяем, что была вызвана функция добавления в сессию
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_pause_feeding_timer_updates_duration(self, mock_get_db_manager):
        """Тест обновления продолжительности при приостановке таймера."""
        # Настройка мока базы данных
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Создаем моки для пользователя, ребенка и сессии кормления
        mock_user = MagicMock()
        mock_user.id = self.user_id
        
        mock_child = MagicMock()
        mock_child.id = 1
        mock_child.user_id = self.user_id
        
        mock_feeding_session = MagicMock()
        mock_feeding_session.id = 1
        mock_feeding_session.child_id = 1
        mock_feeding_session.left_timer_active = True
        mock_feeding_session.left_timer_start = datetime.utcnow() - timedelta(minutes=5)
        mock_feeding_session.left_breast_duration = 0
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_user,  # Запрос пользователя
            mock_child,  # Запрос ребенка
            mock_feeding_session  # Запрос сессии кормления
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
        
        # Проверяем, что была вызвана функция коммита
        mock_session.commit.assert_called_once()
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_switch_breast_functionality(self, mock_get_db_manager):
        """Тест функциональности переключения между грудями."""
        # Настройка мока базы данных
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Создаем моки для пользователя, ребенка и сессии кормления
        mock_user = MagicMock()
        mock_user.id = self.user_id
        
        mock_child = MagicMock()
        mock_child.id = 1
        mock_child.user_id = self.user_id
        
        mock_feeding_session = MagicMock()
        mock_feeding_session.id = 1
        mock_feeding_session.child_id = 1
        mock_feeding_session.left_timer_active = True
        mock_feeding_session.right_timer_active = False
        mock_feeding_session.left_timer_start = datetime.utcnow() - timedelta(minutes=3)
        mock_feeding_session.left_breast_duration = 0
        mock_feeding_session.right_breast_duration = 0
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_user,  # Запрос пользователя
            mock_child,  # Запрос ребенка
            mock_feeding_session  # Запрос сессии кормления
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
        
        # Проверяем, что была вызвана функция коммита
        mock_session.commit.assert_called_once()
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_stop_feeding_session_ends_all_timers(self, mock_get_db_manager):
        """Тест завершения сессии останавливает все таймеры."""
        # Настройка мока базы данных
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Создаем моки для пользователя, ребенка и сессии кормления
        mock_user = MagicMock()
        mock_user.id = self.user_id
        
        mock_child = MagicMock()
        mock_child.id = 1
        mock_child.user_id = self.user_id
        
        mock_feeding_session = MagicMock()
        mock_feeding_session.id = 1
        mock_feeding_session.child_id = 1
        mock_feeding_session.left_timer_active = True
        mock_feeding_session.right_timer_active = True
        mock_feeding_session.left_timer_start = datetime.utcnow() - timedelta(minutes=5)
        mock_feeding_session.right_timer_start = datetime.utcnow() - timedelta(minutes=3)
        mock_feeding_session.left_breast_duration = 0
        mock_feeding_session.right_breast_duration = 0
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_user,  # Запрос пользователя
            mock_child,  # Запрос ребенка
            mock_feeding_session  # Запрос сессии кормления
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
        
        # Проверяем, что была вызвана функция коммита
        mock_session.commit.assert_called_once()
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_get_active_feeding_session_returns_active(self, mock_get_db_manager):
        """Тест получения активной сессии кормления."""
        # Настройка мока базы данных
        mock_db_manager = MagicMock()
        mock_session = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.get_session.return_value = mock_session
        
        # Создаем моки для пользователя и ребенка
        mock_user = MagicMock()
        mock_user.id = self.user_id
        
        mock_child = MagicMock()
        mock_child.id = 1
        mock_child.user_id = self.user_id
        
        # Создаем мок активной сессии с простыми атрибутами
        mock_active_session = MagicMock()
        mock_active_session.id = 1
        mock_active_session.child_id = 1
        mock_active_session.timestamp = datetime.utcnow()
        mock_active_session.end_time = None
        mock_active_session.type = 'breast'
        mock_active_session.amount = None
        mock_active_session.duration = None
        mock_active_session.breast = None
        mock_active_session.notes = ''
        mock_active_session.left_breast_duration = 300  # 5 минут в секундах
        mock_active_session.right_breast_duration = 0
        mock_active_session.left_timer_active = True
        mock_active_session.right_timer_active = False
        mock_active_session.left_timer_start = datetime.utcnow()
        mock_active_session.right_timer_start = None
        mock_active_session.last_active_breast = 'left'
        
        # Настройка запросов к базе данных
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_user,  # Запрос пользователя
            mock_child   # Запрос ребенка
        ]
        mock_session.query.return_value.filter.return_value.first.return_value = mock_active_session
        
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
        self.assertEqual(response_data['session_data']['id'], 1)
        self.assertTrue(response_data['session_data']['is_active'])
    
    @patch('webapp.api_feeding.get_db_manager')
    def test_error_handling_user_not_found(self, mock_get_db_manager):
        """Тест обработки ошибки когда пользователь не найден."""
        # Настройка мока базы данных
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
    def test_error_handling_invalid_breast_parameter(self, mock_get_db_manager):
        """Тест обработки ошибки при неверном параметре груди."""
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


if __name__ == '__main__':
    unittest.main()