"""
Тесты для API эндпоинтов таймера сна.

Этот модуль содержит тесты для API эндпоинтов сессий сна.
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse

from botapp.models import User, db_manager
from botapp.models_child import Child
from botapp.models_timers import SleepSession


class SleepAPITestCase(TestCase):
    """Тестовый случай для API эндпоинтов таймера сна."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        # Создаем тестового пользователя и ребенка
        session = db_manager.get_session()
        try:
            self.user = User(
                telegram_id=123456789,
                username='testuser',
                first_name='Test',
                last_name='User'
            )
            session.add(self.user)
            session.commit()
            session.refresh(self.user)
            
            self.child = Child(
                user_id=self.user.id,
                name='Test Child',
                birth_date=datetime.now() - timedelta(days=180),  # 6 месяцев
                gender='male'
            )
            session.add(self.child)
            session.commit()
            session.refresh(self.child)
            
            # Создаем тестовую сессию сна
            self.sleep_session = SleepSession(
                child_id=self.child.id,
                start_time=datetime.now() - timedelta(hours=2),
                type='day',
                quality=4,
                notes='Тестовая сессия сна'
            )
            session.add(self.sleep_session)
            
            # Создаем завершенную сессию сна
            self.completed_sleep_session = SleepSession(
                child_id=self.child.id,
                start_time=datetime.now() - timedelta(days=1, hours=8),
                end_time=datetime.now() - timedelta(days=1, hours=6),
                type='night',
                quality=5,
                notes='Завершенная сессия сна'
            )
            session.add(self.completed_sleep_session)
            
            session.commit()
            session.refresh(self.sleep_session)
            session.refresh(self.completed_sleep_session)
        finally:
            db_manager.close_session(session)
        
        # Создаем тестовый клиент
        self.client = Client()
    
    def tearDown(self):
        """Очистка тестовых данных."""
        session = db_manager.get_session()
        try:
            # Удаляем тестовые сессии сна
            sleep_session = session.query(SleepSession).filter_by(id=self.sleep_session.id).first()
            if sleep_session:
                session.delete(sleep_session)
            
            completed_sleep_session = session.query(SleepSession).filter_by(id=self.completed_sleep_session.id).first()
            if completed_sleep_session:
                session.delete(completed_sleep_session)
            
            # Удаляем тестового ребенка
            child = session.query(Child).filter_by(id=self.child.id).first()
            if child:
                session.delete(child)
            
            # Удаляем тестового пользователя
            user = session.query(User).filter_by(id=self.user.id).first()
            if user:
                session.delete(user)
            
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_sleep_sessions(self):
        """Тест получения списка всех сессий сна."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('sleep_sessions', data)
        self.assertEqual(len(data['sleep_sessions']), 2)
    
    def test_create_sleep_session(self):
        """Тест создания новой сессии сна."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/'
        data = {
            'type': 'night',
            'quality': 5,
            'notes': 'Новая сессия сна'
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['child_id'], self.child.id)
        self.assertEqual(response_data['type'], 'night')
        self.assertEqual(response_data['quality'], 5)
        self.assertEqual(response_data['notes'], 'Новая сессия сна')
        self.assertIsNone(response_data['end_time'])
        
        # Удаляем созданную сессию
        session = db_manager.get_session()
        try:
            sleep_session = session.query(SleepSession).filter_by(id=response_data['id']).first()
            if sleep_session:
                session.delete(sleep_session)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_sleep_session_detail(self):
        """Тест получения конкретной сессии сна."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/{self.sleep_session.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], self.sleep_session.id)
        self.assertEqual(data['type'], 'day')
        self.assertEqual(data['quality'], 4)
        self.assertEqual(data['notes'], 'Тестовая сессия сна')
    
    def test_end_sleep_session(self):
        """Тест завершения сессии сна."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/{self.sleep_session.id}/'
        data = {
            'end_session': True,
            'quality': 5
        }
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsNotNone(response_data['end_time'])
        self.assertEqual(response_data['quality'], 5)
        self.assertIsNotNone(response_data['duration'])
    
    def test_update_sleep_session(self):
        """Тест обновления параметров сессии сна."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/{self.sleep_session.id}/'
        data = {
            'type': 'night',
            'notes': 'Обновленная сессия сна'
        }
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['type'], 'night')
        self.assertEqual(response_data['notes'], 'Обновленная сессия сна')
        self.assertEqual(response_data['quality'], 4)  # Не изменилось
    
    def test_delete_sleep_session(self):
        """Тест удаления сессии сна."""
        # Создаем сессию для удаления
        session = db_manager.get_session()
        try:
            sleep_session_to_delete = SleepSession(
                child_id=self.child.id,
                start_time=datetime.now() - timedelta(hours=4),
                type='day',
                notes='Сессия для удаления'
            )
            session.add(sleep_session_to_delete)
            session.commit()
            session.refresh(sleep_session_to_delete)
            session_id = sleep_session_to_delete.id
        finally:
            db_manager.close_session(session)
        
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/{session_id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Сессия сна успешно удалена')
        
        # Проверяем, что сессия удалена из базы данных
        session = db_manager.get_session()
        try:
            sleep_session = session.query(SleepSession).filter_by(id=session_id).first()
            self.assertIsNone(sleep_session)
        finally:
            db_manager.close_session(session)
    
    def test_sleep_statistics(self):
        """Тест получения статистики сна."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/statistics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('total_sessions', data)
        self.assertIn('day_sessions', data)
        self.assertIn('night_sessions', data)
        self.assertIn('total_day_sleep', data)
        self.assertIn('total_night_sleep', data)
        self.assertIn('avg_day_sleep', data)
        self.assertIn('avg_night_sleep', data)
        self.assertIn('avg_quality', data)
    
    def test_active_sleep_session(self):
        """Тест получения активной сессии сна."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/active/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], self.sleep_session.id)
        self.assertEqual(data['type'], 'day')
        self.assertIsNone(data['end_time'])
    
    def test_user_not_found(self):
        """Тест API-ответа, когда пользователь не найден."""
        url = f'/api/users/999999/children/{self.child.id}/sleep/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Пользователь не найден')
    
    def test_child_not_found(self):
        """Тест API-ответа, когда ребенок не найден."""
        url = f'/api/users/{self.user.id}/children/999999/sleep/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Ребенок не найден')
    
    def test_child_does_not_belong_to_user(self):
        """Тест API-ответа, когда ребенок не принадлежит пользователю."""
        # Создаем другого пользователя
        session = db_manager.get_session()
        try:
            other_user = User(
                telegram_id=987654321,
                username='otheruser',
                first_name='Other',
                last_name='User'
            )
            session.add(other_user)
            session.commit()
            session.refresh(other_user)
            
            # Пытаемся получить сессии сна с другим пользователем
            url = f'/api/users/{other_user.id}/children/{self.child.id}/sleep/'
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 403)
            data = json.loads(response.content)
            self.assertEqual(data['error'], 'Ребенок не принадлежит этому пользователю')
            
            # Удаляем другого пользователя
            session.delete(other_user)
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_sleep_session_not_found(self):
        """Тест API-ответа, когда сессия сна не найдена."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/999999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Сессия сна не найдена')


if __name__ == '__main__':
    unittest.main()