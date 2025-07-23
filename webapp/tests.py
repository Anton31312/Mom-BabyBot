"""
Тесты для Django views веб-приложения Mom&BabyBot
"""
import json
import os
from datetime import datetime
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock

from botapp.models import User
from webapp.utils.db_utils import get_db_manager


class WebAppTestCase(TestCase):
    """Базовый класс для тестов веб-приложения"""

    def setUp(self):
        """Настройка тестового окружения"""
        self.client = Client()

        # Настраиваем тестовую базу данных в памяти
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

        # Пересоздаем менеджер БД для тестов
        db_manager._setup_engine()
        db_manager.create_tables()

        # Создаем тестовых пользователей
        self._create_test_users()

    def tearDown(self):
        """Очистка после тестов"""
        db_manager = get_db_manager()

        session = db_manager.get_session()
        try:
            session.query(User).delete()
            session.commit()
        finally:
            db_manager.close_session(session)

    def _create_test_users(self):
        """Создание тестовых пользователей"""
        db_manager = get_db_manager()

        session = db_manager.get_session()
        try:
            # Беременная пользовательница
            self.pregnant_user = User(
                telegram_id=123456789,
                username='pregnant_user',
                first_name='Anna',
                last_name='Ivanova',
                is_pregnant=True,
                pregnancy_week=20
            )

            # Пользовательница с ребенком
            self.mom_user = User(
                telegram_id=987654321,
                username='mom_user',
                first_name='Maria',
                last_name='Petrova',
                is_pregnant=False,
                baby_birth_date=datetime(2023, 6, 1)
            )

            session.add_all([self.pregnant_user, self.mom_user])
            session.commit()
            session.refresh(self.pregnant_user)
            session.refresh(self.mom_user)

        finally:
            db_manager.close_session(session)


class IndexViewTests(WebAppTestCase):
    """Тесты для главной страницы"""

    def test_index_view_get(self):
        """Тест GET запроса к главной странице"""
        response = self.client.get(reverse('webapp:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mom&BabyBot')
        self.assertTemplateUsed(response, 'index.html')

    def test_index_html_alternative_url(self):
        """Тест альтернативного URL главной страницы"""
        response = self.client.get(reverse('webapp:index_html'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mom&BabyBot')
        self.assertTemplateUsed(response, 'index.html')


class CreateUserAPITests(WebAppTestCase):
    """Тесты для API создания пользователей"""

    def test_create_user_success(self):
        """Тест успешного создания пользователя"""
        user_data = {
            'telegram_id': 111222333,
            'username': 'new_user',
            'first_name': 'Elena',
            'is_pregnant': True,
            'pregnancy_week': 15
        }

        response = self.client.post(
            reverse('webapp:create_user'),
            data=json.dumps(user_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], 'User created successfully')

        # Проверяем, что пользователь создан в БД
        db_manager = get_db_manager()

        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=111222333).first()
            self.assertIsNotNone(user)
            self.assertEqual(user.username, 'new_user')
            self.assertEqual(user.first_name, 'Elena')
            self.assertTrue(user.is_pregnant)
            self.assertEqual(user.pregnancy_week, 15)
        finally:
            db_manager.close_session(session)

    def test_create_user_with_baby_birth_date(self):
        """Тест создания пользователя с датой рождения ребенка"""
        user_data = {
            'telegram_id': 444555666,
            'username': 'mom_with_baby',
            'is_pregnant': False,
            'baby_birth_date': '2023-08-15T10:30:00'
        }

        response = self.client.post(
            reverse('webapp:create_user'),
            data=json.dumps(user_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # Проверяем данные в БД
        db_manager = get_db_manager()

        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=444555666).first()
            self.assertIsNotNone(user)
            self.assertFalse(user.is_pregnant)
            self.assertIsNotNone(user.baby_birth_date)
        finally:
            db_manager.close_session(session)

    def test_create_user_missing_telegram_id(self):
        """Тест создания пользователя без обязательного telegram_id"""
        user_data = {
            'username': 'invalid_user',
            'is_pregnant': False
        }

        response = self.client.post(
            reverse('webapp:create_user'),
            data=json.dumps(user_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertIn('error', response_data)

    def test_create_user_invalid_json(self):
        """Тест создания пользователя с невалидным JSON"""
        response = self.client.post(
            reverse('webapp:create_user'),
            data='invalid json string',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertIn('error', response_data)

    def test_create_user_get_method_not_allowed(self):
        """Тест что GET запрос не разрешен для создания пользователя"""
        response = self.client.get(reverse('webapp:create_user'))
        self.assertEqual(response.status_code, 405)

    def test_create_user_duplicate_telegram_id(self):
        """Тест создания пользователя с существующим telegram_id"""
        user_data = {
            'telegram_id': self.pregnant_user.telegram_id,  # Используем существующий ID
            'username': 'duplicate_user'
        }

        response = self.client.post(
            reverse('webapp:create_user'),
            data=json.dumps(user_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertIn('error', response_data)


class WebAppDataAPITests(WebAppTestCase):
    """Тесты для API обновления данных пользователей"""

    def test_update_pregnant_user_data(self):
        """Тест обновления данных беременной пользовательницы"""
        data = {
            'user_id': self.pregnant_user.telegram_id,
            'pregnancy_week': 25
        }

        response = self.client.post(
            reverse('webapp:web_app_data'),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')

        # Проверяем обновление в БД
        db_manager = get_db_manager()

        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(
                telegram_id=self.pregnant_user.telegram_id
            ).first()
            self.assertEqual(user.pregnancy_week, 25)
        finally:
            db_manager.close_session(session)

    def test_update_mom_user_baby_birth_date(self):
        """Тест обновления даты рождения ребенка"""
        data = {
            'user_id': self.mom_user.telegram_id,
            'baby_birth_date': '2023-07-15T14:30:00'
        }

        response = self.client.post(
            reverse('webapp:web_app_data'),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')

        # Проверяем обновление в БД
        db_manager = get_db_manager()

        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(
                telegram_id=self.mom_user.telegram_id
            ).first()
            self.assertIsNotNone(user.baby_birth_date)
        finally:
            db_manager.close_session(session)

    def test_update_nonexistent_user(self):
        """Тест обновления данных несуществующего пользователя"""
        data = {
            'user_id': 999999999,
            'pregnancy_week': 20
        }

        response = self.client.post(
            reverse('webapp:web_app_data'),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'User not found')

    def test_update_user_invalid_json(self):
        """Тест обновления данных с невалидным JSON"""
        response = self.client.post(
            reverse('webapp:web_app_data'),
            data='invalid json',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)

        response_data = json.loads(response.content)
        self.assertIn('error', response_data)

    def test_update_user_get_method_not_allowed(self):
        """Тест что GET запрос не разрешен для обновления данных"""
        response = self.client.get(reverse('webapp:web_app_data'))
        self.assertEqual(response.status_code, 405)

    def test_update_user_missing_user_id(self):
        """Тест обновления данных без указания user_id"""
        data = {
            'pregnancy_week': 20
        }

        response = self.client.post(
            reverse('webapp:web_app_data'),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'User not found')


class WebAppIntegrationTests(WebAppTestCase):
    """Интеграционные тесты веб-приложения"""

    def test_full_user_lifecycle(self):
        """Тест полного жизненного цикла пользователя"""
        # 1. Создаем пользователя
        user_data = {
            'telegram_id': 777888999,
            'username': 'lifecycle_user',
            'is_pregnant': True,
            'pregnancy_week': 10
        }

        create_response = self.client.post(
            reverse('webapp:create_user'),
            data=json.dumps(user_data),
            content_type='application/json'
        )

        self.assertEqual(create_response.status_code, 200)

        # 2. Обновляем данные пользователя
        update_data = {
            'user_id': 777888999,
            'pregnancy_week': 30
        }

        update_response = self.client.post(
            reverse('webapp:web_app_data'),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(update_response.status_code, 200)

        # 3. Проверяем финальное состояние в БД
        db_manager = get_db_manager()

        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=777888999).first()
            self.assertIsNotNone(user)
            self.assertEqual(user.username, 'lifecycle_user')
            self.assertEqual(user.pregnancy_week, 30)
            self.assertTrue(user.is_pregnant)
        finally:
            db_manager.close_session(session)

    def test_database_transaction_rollback(self):
        """Тест отката транзакций при ошибках"""
        # Создаем пользователя с невалидными данными, которые вызовут ошибку
        with patch('botapp.models.db_manager.get_session') as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value = mock_session_instance
            mock_session_instance.add.side_effect = Exception("Database error")

            user_data = {
                'telegram_id': 555666777,
                'username': 'error_user'
            }

            response = self.client.post(
                reverse('webapp:create_user'),
                data=json.dumps(user_data),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 400)

            # Проверяем, что rollback был вызван
            mock_session_instance.rollback.assert_called_once()
