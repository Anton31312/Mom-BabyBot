"""
Тесты для проверки обработки ошибок в API.

Этот модуль содержит тесты для проверки корректной обработки ошибок
в API эндпоинтах веб-приложения.
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from botapp.models import User, db_manager
from botapp.models_child import Child, Measurement

class APIErrorHandlingTests(TestCase):
    """Тесты для проверки обработки ошибок в API."""
    
    def setUp(self):
        """Настройка перед тестами."""
        self.client = Client()
        
        # Создаем тестового пользователя
        self.user_id = 100
        self.child_id = 200
        self.measurement_id = 300
        
        # Мокаем сессию базы данных
        self.session_patcher = patch('botapp.models.db_manager.get_session')
        self.mock_get_session = self.session_patcher.start()
        self.mock_session = MagicMock()
        self.mock_get_session.return_value = self.mock_session
        
        # Мокаем запросы к базе данных
        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = self.user_id
        self.mock_user.telegram_id = 123456789
        
        self.mock_child = MagicMock(spec=Child)
        self.mock_child.id = self.child_id
        self.mock_child.user_id = self.user_id
        
        self.mock_measurement = MagicMock(spec=Measurement)
        self.mock_measurement.id = self.measurement_id
        self.mock_measurement.child_id = self.child_id
    
    def tearDown(self):
        """Очистка после тестов."""
        self.session_patcher.stop()
    
    @patch('webapp.api.get_child')
    def test_child_not_found(self, mock_get_child):
        """Тест обработки ошибки, когда ребенок не найден."""
        # Настраиваем мок для возврата None (ребенок не найден)
        mock_get_child.return_value = None
        
        # Отправляем запрос к API
        url = reverse('webapp:child_detail', args=[self.user_id, self.child_id])
        response = self.client.get(url)
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Ребенок не найден')
    
    @patch('webapp.api.get_child')
    def test_child_wrong_user(self, mock_get_child):
        """Тест обработки ошибки, когда ребенок принадлежит другому пользователю."""
        # Настраиваем мок для возврата ребенка с другим user_id
        mock_child = MagicMock(spec=Child)
        mock_child.id = self.child_id
        mock_child.user_id = self.user_id + 1  # Другой пользователь
        mock_get_child.return_value = mock_child
        
        # Отправляем запрос к API
        url = reverse('webapp:child_detail', args=[self.user_id, self.child_id])
        response = self.client.get(url)
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Ребенок не принадлежит этому пользователю')
    
    @patch('webapp.api.get_child')
    @patch('webapp.api.update_child')
    def test_update_child_exception(self, mock_update_child, mock_get_child):
        """Тест обработки исключения при обновлении ребенка."""
        # Настраиваем моки
        mock_get_child.return_value = self.mock_child
        mock_update_child.side_effect = Exception("Ошибка базы данных")
        
        # Отправляем запрос к API
        url = reverse('webapp:child_detail', args=[self.user_id, self.child_id])
        data = {'name': 'Новое имя'}
        response = self.client.put(
            url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Ошибка базы данных')
    
    @patch('webapp.api.get_child')
    @patch('webapp.api.delete_child')
    def test_delete_child_failure(self, mock_delete_child, mock_get_child):
        """Тест обработки ошибки при удалении ребенка."""
        # Настраиваем моки
        mock_get_child.return_value = self.mock_child
        mock_delete_child.return_value = False  # Удаление не удалось
        
        # Отправляем запрос к API
        url = reverse('webapp:child_detail', args=[self.user_id, self.child_id])
        response = self.client.delete(url)
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Не удалось удалить профиль ребенка')
    
    @patch('webapp.api.get_child')
    def test_measurements_list_child_not_found(self, mock_get_child):
        """Тест обработки ошибки, когда ребенок не найден при запросе измерений."""
        # Настраиваем мок для возврата None (ребенок не найден)
        mock_get_child.return_value = None
        
        # Отправляем запрос к API
        url = reverse('webapp:measurements_list', args=[self.user_id, self.child_id])
        response = self.client.get(url)
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Ребенок не найден')
    
    @patch('webapp.api.get_child')
    @patch('webapp.api.create_measurement')
    def test_create_measurement_exception(self, mock_create_measurement, mock_get_child):
        """Тест обработки исключения при создании измерения."""
        # Настраиваем моки
        mock_get_child.return_value = self.mock_child
        mock_create_measurement.side_effect = Exception("Ошибка при создании измерения")
        
        # Отправляем запрос к API
        url = reverse('webapp:measurements_list', args=[self.user_id, self.child_id])
        data = {'height': 75.5, 'weight': 9.2}
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Ошибка при создании измерения')
    
    def test_invalid_json_body(self):
        """Тест обработки невалидного JSON в теле запроса."""
        # Отправляем запрос с невалидным JSON
        url = reverse('webapp:children_list', args=[self.user_id])
        response = self.client.post(
            url, 
            data="invalid json",
            content_type='application/json'
        )
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)