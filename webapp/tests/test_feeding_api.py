"""
Тесты для API эндпоинтов отслеживания кормления.

Этот модуль содержит тесты для API эндпоинтов сессий кормления.
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse

from botapp.models import User, db_manager
from botapp.models_child import Child
from botapp.models_timers import FeedingSession


class FeedingAPITestCase(TestCase):
    """Тестовый случай для API эндпоинтов отслеживания кормления."""
    
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
            
            # Создаем тестовую сессию кормления грудью
            self.breast_feeding = FeedingSession(
                child_id=self.child.id,
                timestamp=datetime.now() - timedelta(hours=3),
                type='breast',
                duration=20,
                breast='left',
                notes='Тестовое кормление грудью'
            )
            session.add(self.breast_feeding)
            
            # Создаем тестовую сессию кормления из бутылочки
            self.bottle_feeding = FeedingSession(
                child_id=self.child.id,
                timestamp=datetime.now() - timedelta(hours=6),
                type='bottle',
                amount=120,
                milk_type='formula',
                notes='Тестовое кормление из бутылочки'
            )
            session.add(self.bottle_feeding)
            
            # Создаем несколько сессий кормления за последнюю неделю для тестирования статистики
            for i in range(1, 6):
                # Кормление грудью
                breast_session = FeedingSession(
                    child_id=self.child.id,
                    timestamp=datetime.now() - timedelta(days=i, hours=3),
                    type='breast',
                    duration=15 + i,
                    breast='right' if i % 2 == 0 else 'left',
                    notes=f'Кормление грудью {i} дней назад'
                )
                session.add(breast_session)
                
                # Кормление из бутылочки
                bottle_session = FeedingSession(
                    child_id=self.child.id,
                    timestamp=datetime.now() - timedelta(days=i, hours=6),
                    type='bottle',
                    amount=100 + i*10,
                    milk_type='formula',
                    notes=f'Кормление из бутылочки {i} дней назад'
                )
                session.add(bottle_session)
            
            session.commit()
            session.refresh(self.breast_feeding)
            session.refresh(self.bottle_feeding)
        finally:
            db_manager.close_session(session)
        
        # Создаем тестовый клиент
        self.client = Client()
    
    def tearDown(self):
        """Очистка тестовых данных."""
        session = db_manager.get_session()
        try:
            # Удаляем все сессии кормления для ребенка
            feeding_sessions = session.query(FeedingSession).filter_by(child_id=self.child.id).all()
            for fs in feeding_sessions:
                session.delete(fs)
            
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
    
    def test_get_feeding_sessions(self):
        """Тест получения списка всех сессий кормления."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('feeding_sessions', data)
        # 2 основные сессии + 10 дополнительных (по 2 на каждый из 5 дней)
        self.assertEqual(len(data['feeding_sessions']), 12)
    
    def test_create_breast_feeding_session(self):
        """Тест создания новой сессии кормления грудью."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/'
        data = {
            'type': 'breast',
            'duration': 25,
            'breast': 'right',
            'notes': 'Новое кормление грудью'
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['child_id'], self.child.id)
        self.assertEqual(response_data['type'], 'breast')
        self.assertEqual(response_data['duration'], 25)
        self.assertEqual(response_data['breast'], 'right')
        self.assertEqual(response_data['notes'], 'Новое кормление грудью')
        
        # Удаляем созданную сессию
        session = db_manager.get_session()
        try:
            feeding_session = session.query(FeedingSession).filter_by(id=response_data['id']).first()
            if feeding_session:
                session.delete(feeding_session)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_create_bottle_feeding_session(self):
        """Тест создания новой сессии кормления из бутылочки."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/'
        data = {
            'type': 'bottle',
            'amount': 150,
            'milk_type': 'expressed',
            'notes': 'Новое кормление из бутылочки'
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['child_id'], self.child.id)
        self.assertEqual(response_data['type'], 'bottle')
        self.assertEqual(response_data['amount'], 150)
        self.assertEqual(response_data['milk_type'], 'expressed')
        self.assertEqual(response_data['notes'], 'Новое кормление из бутылочки')
        
        # Удаляем созданную сессию
        session = db_manager.get_session()
        try:
            feeding_session = session.query(FeedingSession).filter_by(id=response_data['id']).first()
            if feeding_session:
                session.delete(feeding_session)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_feeding_session_detail(self):
        """Тест получения конкретной сессии кормления."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/{self.breast_feeding.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], self.breast_feeding.id)
        self.assertEqual(data['type'], 'breast')
        self.assertEqual(data['duration'], 20)
        self.assertEqual(data['breast'], 'left')
        self.assertEqual(data['notes'], 'Тестовое кормление грудью')
    
    def test_update_feeding_session(self):
        """Тест обновления сессии кормления."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/{self.breast_feeding.id}/'
        data = {
            'duration': 30,
            'breast': 'both',
            'notes': 'Обновленное кормление грудью'
        }
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['duration'], 30)
        self.assertEqual(response_data['breast'], 'both')
        self.assertEqual(response_data['notes'], 'Обновленное кормление грудью')
    
    def test_delete_feeding_session(self):
        """Тест удаления сессии кормления."""
        # Создаем сессию для удаления
        session = db_manager.get_session()
        try:
            feeding_to_delete = FeedingSession(
                child_id=self.child.id,
                timestamp=datetime.now(),
                type='breast',
                duration=15,
                breast='left',
                notes='Сессия для удаления'
            )
            session.add(feeding_to_delete)
            session.commit()
            session.refresh(feeding_to_delete)
            feeding_id = feeding_to_delete.id
        finally:
            db_manager.close_session(session)
        
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/{feeding_id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Сессия кормления успешно удалена')
        
        # Проверяем, что сессия удалена из базы данных
        session = db_manager.get_session()
        try:
            feeding_session = session.query(FeedingSession).filter_by(id=feeding_id).first()
            self.assertIsNone(feeding_session)
        finally:
            db_manager.close_session(session)
    
    def test_feeding_statistics(self):
        """Тест получения статистики кормления."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/statistics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('today_count', data)
        self.assertIn('today_duration', data)
        self.assertIn('today_amount', data)
        self.assertIn('weekly_avg_count', data)
        self.assertIn('weekly_avg_duration', data)
        self.assertIn('weekly_avg_amount', data)
        self.assertIn('daily_stats', data)
        
        # Проверяем, что статистика за неделю содержит данные за 7 дней
        self.assertEqual(len(data['daily_stats']), 7)
    
    def test_user_not_found(self):
        """Тест API-ответа, когда пользователь не найден."""
        url = f'/api/users/999999/children/{self.child.id}/feeding/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Пользователь не найден')
    
    def test_child_not_found(self):
        """Тест API-ответа, когда ребенок не найден."""
        url = f'/api/users/{self.user.id}/children/999999/feeding/'
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
            
            # Пытаемся получить сессии кормления с другим пользователем
            url = f'/api/users/{other_user.id}/children/{self.child.id}/feeding/'
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 403)
            data = json.loads(response.content)
            self.assertEqual(data['error'], 'Ребенок не принадлежит этому пользователю')
            
            # Удаляем другого пользователя
            session.delete(other_user)
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_feeding_session_not_found(self):
        """Тест API-ответа, когда сессия кормления не найдена."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/999999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Сессия кормления не найдена')


if __name__ == '__main__':
    unittest.main()