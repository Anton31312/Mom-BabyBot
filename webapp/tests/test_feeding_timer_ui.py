"""
Тесты для пользовательского интерфейса таймеров кормления.

Этот модуль содержит тесты для проверки функциональности
пользовательского интерфейса таймеров кормления.
"""

import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from botapp.models import User as BotUser
from botapp.models_child import Child
from botapp.models_timers import FeedingSession
from webapp.utils.db_utils import get_db_manager
import json
from datetime import datetime, timedelta


class FeedingTimerUITestCase(TestCase):
    """Тесты для пользовательского интерфейса таймеров кормления."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        
        # Создаем тестового пользователя
        self.db_manager = get_db_manager()
        session = self.db_manager.get_session()
        
        try:
            self.user = BotUser(
                telegram_id=12345,
                username='testuser',
                first_name='Test',
                last_name='User'
            )
            session.add(self.user)
            session.commit()
            session.refresh(self.user)
            
            # Создаем тестового ребенка
            self.child = Child(
                user_id=self.user.id,
                name='Test Child',
                birth_date=datetime.now().date() - timedelta(days=30)
            )
            session.add(self.child)
            session.commit()
            session.refresh(self.child)
            
        finally:
            self.db_manager.close_session(session)
    
    def tearDown(self):
        """Очистка тестовых данных."""
        session = self.db_manager.get_session()
        try:
            # Удаляем все сессии кормления
            session.query(FeedingSession).filter_by(child_id=self.child.id).delete()
            # Удаляем ребенка
            session.query(Child).filter_by(id=self.child.id).delete()
            # Удаляем пользователя
            session.query(BotUser).filter_by(id=self.user.id).delete()
            session.commit()
        finally:
            self.db_manager.close_session(session)
    
    def test_feeding_tracker_page_loads(self):
        """Тест загрузки страницы отслеживания кормления."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Таймеры кормления')
        self.assertContains(response, 'Левая грудь')
        self.assertContains(response, 'Правая грудь')
    
    def test_timer_interface_elements_present(self):
        """Тест наличия элементов интерфейса таймеров."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем наличие основных элементов таймера
        self.assertContains(response, 'id="leftTimer"')
        self.assertContains(response, 'id="rightTimer"')
        self.assertContains(response, 'id="leftStartBtn"')
        self.assertContains(response, 'id="rightStartBtn"')
        self.assertContains(response, 'id="leftPauseBtn"')
        self.assertContains(response, 'id="rightPauseBtn"')
        self.assertContains(response, 'id="switchToLeftBtn"')
        self.assertContains(response, 'id="switchToRightBtn"')
        self.assertContains(response, 'id="stopSessionBtn"')
    
    def test_start_feeding_timer_api(self):
        """Тест API запуска таймера кормления."""
        url = reverse('webapp:start_feeding_timer', args=[self.user.id, self.child.id])
        
        data = {
            'breast': 'left'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertIn('session_id', response_data)
        self.assertIn('session_data', response_data)
        self.assertEqual(response_data['breast'], 'left')
        
        # Проверяем, что сессия создана в базе данных
        session = self.db_manager.get_session()
        try:
            feeding_session = session.query(FeedingSession).filter_by(
                id=response_data['session_id']
            ).first()
            
            self.assertIsNotNone(feeding_session)
            self.assertTrue(feeding_session.left_timer_active)
            self.assertFalse(feeding_session.right_timer_active)
            self.assertEqual(feeding_session.last_active_breast, 'left')
        finally:
            self.db_manager.close_session(session)
    
    def test_pause_feeding_timer_api(self):
        """Тест API приостановки таймера кормления."""
        # Сначала создаем активную сессию
        session = self.db_manager.get_session()
        try:
            feeding_session = FeedingSession(
                child_id=self.child.id,
                timestamp=datetime.utcnow(),
                type='breast',
                left_timer_active=True,
                left_timer_start=datetime.utcnow(),
                last_active_breast='left'
            )
            session.add(feeding_session)
            session.commit()
            session.refresh(feeding_session)
            
            # Тестируем приостановку таймера
            url = reverse('webapp:pause_feeding_timer', args=[
                self.user.id, self.child.id, feeding_session.id
            ])
            
            data = {
                'breast': 'left'
            }
            
            response = self.client.post(
                url,
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            
            response_data = json.loads(response.content)
            self.assertIn('session_data', response_data)
            
            # Проверяем, что таймер приостановлен
            session.refresh(feeding_session)
            self.assertFalse(feeding_session.left_timer_active)
            self.assertIsNone(feeding_session.left_timer_start)
            self.assertGreater(feeding_session.left_breast_duration, 0)
            
        finally:
            self.db_manager.close_session(session)
    
    def test_switch_breast_api(self):
        """Тест API переключения между грудями."""
        # Создаем активную сессию с левой грудью
        session = self.db_manager.get_session()
        try:
            feeding_session = FeedingSession(
                child_id=self.child.id,
                timestamp=datetime.utcnow(),
                type='breast',
                left_timer_active=True,
                left_timer_start=datetime.utcnow(),
                left_breast_duration=60,  # 1 минута
                last_active_breast='left'
            )
            session.add(feeding_session)
            session.commit()
            session.refresh(feeding_session)
            
            # Тестируем переключение на правую грудь
            url = reverse('webapp:switch_breast', args=[
                self.user.id, self.child.id, feeding_session.id
            ])
            
            data = {
                'to_breast': 'right'
            }
            
            response = self.client.post(
                url,
                data=json.dumps(data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            
            response_data = json.loads(response.content)
            self.assertEqual(response_data['to_breast'], 'right')
            self.assertEqual(response_data['from_breast'], 'left')
            
            # Проверяем состояние в базе данных
            session.refresh(feeding_session)
            self.assertFalse(feeding_session.left_timer_active)
            self.assertTrue(feeding_session.right_timer_active)
            self.assertEqual(feeding_session.last_active_breast, 'right')
            self.assertIsNotNone(feeding_session.right_timer_start)
            
        finally:
            self.db_manager.close_session(session)
    
    def test_stop_feeding_session_api(self):
        """Тест API завершения сессии кормления."""
        # Создаем активную сессию
        session = self.db_manager.get_session()
        try:
            feeding_session = FeedingSession(
                child_id=self.child.id,
                timestamp=datetime.utcnow(),
                type='breast',
                left_timer_active=True,
                left_timer_start=datetime.utcnow(),
                left_breast_duration=120,  # 2 минуты
                right_breast_duration=90,  # 1.5 минуты
                last_active_breast='left'
            )
            session.add(feeding_session)
            session.commit()
            session.refresh(feeding_session)
            
            # Тестируем завершение сессии
            url = reverse('webapp:stop_feeding_session', args=[
                self.user.id, self.child.id, feeding_session.id
            ])
            
            response = self.client.post(url)
            
            self.assertEqual(response.status_code, 200)
            
            response_data = json.loads(response.content)
            self.assertIn('session_data', response_data)
            
            # Проверяем состояние в базе данных
            session.refresh(feeding_session)
            self.assertFalse(feeding_session.left_timer_active)
            self.assertFalse(feeding_session.right_timer_active)
            self.assertIsNotNone(feeding_session.end_time)
            self.assertIsNone(feeding_session.left_timer_start)
            self.assertIsNone(feeding_session.right_timer_start)
            
        finally:
            self.db_manager.close_session(session)
    
    def test_get_active_feeding_session_api(self):
        """Тест API получения активной сессии кормления."""
        # Тест без активной сессии
        url = reverse('webapp:get_active_feeding_session', args=[self.user.id, self.child.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['has_active_session'])
        self.assertIsNone(response_data['session_data'])
        
        # Создаем активную сессию
        session = self.db_manager.get_session()
        try:
            feeding_session = FeedingSession(
                child_id=self.child.id,
                timestamp=datetime.utcnow(),
                type='breast',
                left_timer_active=True,
                left_timer_start=datetime.utcnow(),
                last_active_breast='left'
            )
            session.add(feeding_session)
            session.commit()
            session.refresh(feeding_session)
            
            # Тест с активной сессией
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.content)
            self.assertTrue(response_data['has_active_session'])
            self.assertIsNotNone(response_data['session_data'])
            self.assertEqual(response_data['session_data']['id'], feeding_session.id)
            
        finally:
            self.db_manager.close_session(session)
    
    def test_timer_display_format(self):
        """Тест формата отображения времени в таймерах."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем, что таймеры инициализированы с 00:00
        self.assertContains(response, '00:00')
        
        # Проверяем наличие CSS классов для таймеров
        self.assertContains(response, 'timer-display')
        self.assertContains(response, 'timer-controls')
    
    def test_timer_css_classes(self):
        """Тест наличия CSS классов для таймеров."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем наличие основных CSS классов
        self.assertContains(response, 'timer-container')
        self.assertContains(response, 'glass-card')
        self.assertContains(response, 'neo-button')
    
    def test_error_handling_invalid_breast(self):
        """Тест обработки ошибок при неверном параметре груди."""
        url = reverse('webapp:start_feeding_timer', args=[self.user.id, self.child.id])
        
        data = {
            'breast': 'invalid'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
    
    def test_error_handling_nonexistent_session(self):
        """Тест обработки ошибок при несуществующей сессии."""
        url = reverse('webapp:pause_feeding_timer', args=[
            self.user.id, self.child.id, 99999
        ])
        
        data = {
            'breast': 'left'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)


if __name__ == '__main__':
    unittest.main()