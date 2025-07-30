"""
Тесты для API эндпоинтов счетчика схваток.

Этот модуль содержит тесты для API эндпоинтов сессий схваток и событий схваток.
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse

from botapp.models import User, db_manager
from botapp.models_timers import Contraction, ContractionEvent


class ContractionAPITestCase(TestCase):
    """Тестовый случай для API эндпоинтов счетчика схваток."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        # Создаем тестового пользователя
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
            
            # Создаем тестовую сессию схваток
            self.contraction = Contraction(
                user_id=self.user.id,
                start_time=datetime.now() - timedelta(hours=1),
                notes='Тестовая сессия схваток'
            )
            session.add(self.contraction)
            session.commit()
            session.refresh(self.contraction)
            
            # Создаем тестовые события схваток
            self.events = []
            for i in range(3):
                event = ContractionEvent(
                    session_id=self.contraction.id,
                    timestamp=datetime.now() - timedelta(minutes=50 - i*10),
                    duration=30 + i*10,  # 30, 40, 50 секунд
                    intensity=5 + i  # 5, 6, 7 из 10
                )
                session.add(event)
                self.events.append(event)
            session.commit()
            for event in self.events:
                session.refresh(event)
        finally:
            db_manager.close_session(session)
        
        # Создаем тестовый клиент
        self.client = Client()
    
    def tearDown(self):
        """Очистка тестовых данных."""
        session = db_manager.get_session()
        try:
            # Удаляем тестовые события схваток
            for event in self.events:
                event_obj = session.query(ContractionEvent).filter_by(id=event.id).first()
                if event_obj:
                    session.delete(event_obj)
            
            # Удаляем тестовую сессию схваток
            contraction = session.query(Contraction).filter_by(id=self.contraction.id).first()
            if contraction:
                session.delete(contraction)
            
            # Удаляем тестового пользователя
            user = session.query(User).filter_by(id=self.user.id).first()
            if user:
                session.delete(user)
            
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_contraction_sessions(self):
        """Тест получения списка всех сессий схваток."""
        url = f'/api/users/{self.user.id}/contractions/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('contractions', data)
        self.assertEqual(len(data['contractions']), 1)
        self.assertEqual(data['contractions'][0]['id'], self.contraction.id)
        self.assertEqual(data['contractions'][0]['notes'], 'Тестовая сессия схваток')
        self.assertEqual(len(data['contractions'][0]['events']), 3)
    
    def test_create_contraction_session(self):
        """Тест создания новой сессии схваток."""
        url = f'/api/users/{self.user.id}/contractions/'
        data = {
            'notes': 'Новая сессия схваток'
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['user_id'], self.user.id)
        self.assertEqual(response_data['notes'], 'Новая сессия схваток')
        self.assertIsNone(response_data['end_time'])
        
        # Удаляем созданную сессию
        session = db_manager.get_session()
        try:
            contraction = session.query(Contraction).filter_by(id=response_data['id']).first()
            if contraction:
                session.delete(contraction)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_contraction_session_detail(self):
        """Тест получения конкретной сессии схваток."""
        url = f'/api/users/{self.user.id}/contractions/{self.contraction.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], self.contraction.id)
        self.assertEqual(data['notes'], 'Тестовая сессия схваток')
        self.assertEqual(len(data['events']), 3)
    
    def test_end_contraction_session(self):
        """Тест завершения сессии схваток."""
        url = f'/api/users/{self.user.id}/contractions/{self.contraction.id}/'
        data = {
            'end_session': True
        }
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsNotNone(response_data['end_time'])
    
    def test_add_contraction_event(self):
        """Тест добавления события схватки."""
        url = f'/api/users/{self.user.id}/contractions/{self.contraction.id}/events/'
        data = {
            'duration': 60,
            'intensity': 8
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['session_id'], self.contraction.id)
        self.assertEqual(response_data['duration'], 60)
        self.assertEqual(response_data['intensity'], 8)
        
        # Удаляем созданное событие
        session = db_manager.get_session()
        try:
            event = session.query(ContractionEvent).filter_by(id=response_data['id']).first()
            if event:
                session.delete(event)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_user_not_found(self):
        """Тест API-ответа, когда пользователь не найден."""
        url = '/api/users/999999/contractions/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Пользователь не найден')
    
    def test_contraction_session_not_found(self):
        """Тест API-ответа, когда сессия схваток не найдена."""
        url = f'/api/users/{self.user.id}/contractions/999999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Сессия схваток не найдена')
    
    def test_contraction_session_does_not_belong_to_user(self):
        """Тест API-ответа, когда сессия схваток не принадлежит пользователю."""
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
            
            # Пытаемся получить сессию схваток с другим пользователем
            url = f'/api/users/{other_user.id}/contractions/{self.contraction.id}/'
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 403)
            data = json.loads(response.content)
            self.assertEqual(data['error'], 'Сессия схваток не принадлежит этому пользователю')
            
            # Удаляем другого пользователя
            session.delete(other_user)
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_add_event_to_ended_session(self):
        """Тест API-ответа при попытке добавить событие к завершенной сессии."""
        # Завершаем сессию схваток
        session = db_manager.get_session()
        try:
            contraction = session.query(Contraction).filter_by(id=self.contraction.id).first()
            contraction.end_time = datetime.now()
            session.commit()
            
            # Пытаемся добавить событие к завершенной сессии
            url = f'/api/users/{self.user.id}/contractions/{self.contraction.id}/events/'
            data = {
                'duration': 60,
                'intensity': 8
            }
            response = self.client.post(
                url,
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data['error'], 'Невозможно добавить событие к завершенной сессии')
        finally:
            db_manager.close_session(session)


if __name__ == '__main__':
    unittest.main()