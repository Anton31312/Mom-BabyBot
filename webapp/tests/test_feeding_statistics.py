"""
Тесты для статистики кормления.

Этот модуль содержит тесты для проверки функциональности
отображения статистики кормления согласно требованию 6.4.
"""

import unittest
import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from botapp.models import User as BotUser
from botapp.models_child import Child
from botapp.models_timers import FeedingSession
from webapp.utils.db_utils import get_db_manager


class FeedingStatisticsTestCase(TestCase):
    """Тесты для статистики кормления."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        
        # Создаем уникальный telegram_id для каждого теста
        import random
        self.telegram_id = random.randint(100000, 999999)
        
        # Создаем тестового пользователя
        self.db_manager = get_db_manager()
        session = self.db_manager.get_session()
        
        try:
            self.user = BotUser(
                telegram_id=self.telegram_id,
                username=f'testuser_{self.telegram_id}',
                first_name='Test',
                last_name='User'
            )
            session.add(self.user)
            session.commit()
            session.refresh(self.user)
            
            # Сохраняем ID пользователя для использования в тестах
            self.user_id = self.user.id
            
            # Создаем тестового ребенка
            self.child = Child(
                user_id=self.user_id,
                name='Test Child',
                birth_date=datetime.now().date() - timedelta(days=30)
            )
            session.add(self.child)
            session.commit()
            session.refresh(self.child)
            
            # Сохраняем ID ребенка для использования в тестах
            self.child_id = self.child.id
            
        finally:
            self.db_manager.close_session(session)
    
    def tearDown(self):
        """Очистка тестовых данных."""
        session = self.db_manager.get_session()
        try:
            # Удаляем все сессии кормления
            session.query(FeedingSession).filter_by(child_id=self.child_id).delete()
            # Удаляем ребенка
            session.query(Child).filter_by(id=self.child_id).delete()
            # Удаляем пользователя
            session.query(BotUser).filter_by(id=self.user_id).delete()
            session.commit()
        finally:
            self.db_manager.close_session(session)
    
    def create_test_feeding_sessions(self):
        """Создает тестовые сессии кормления для проверки статистики."""
        session = self.db_manager.get_session()
        try:
            # Создаем сессии за сегодня
            today = datetime.now()
            
            # Сессия 1: Левая грудь 15 минут
            session1 = FeedingSession(
                child_id=self.child_id,
                timestamp=today - timedelta(hours=2),
                type='breast',
                left_breast_duration=900,  # 15 минут в секундах
                right_breast_duration=0,
                end_time=today - timedelta(hours=2) + timedelta(minutes=15)
            )
            session.add(session1)
            
            # Сессия 2: Правая грудь 20 минут
            session2 = FeedingSession(
                child_id=self.child_id,
                timestamp=today - timedelta(hours=4),
                type='breast',
                left_breast_duration=0,
                right_breast_duration=1200,  # 20 минут в секундах
                end_time=today - timedelta(hours=4) + timedelta(minutes=20)
            )
            session.add(session2)
            
            # Сессия 3: Обе груди (10 минут левая, 12 минут правая)
            session3 = FeedingSession(
                child_id=self.child_id,
                timestamp=today - timedelta(hours=6),
                type='breast',
                left_breast_duration=600,  # 10 минут в секундах
                right_breast_duration=720,  # 12 минут в секундах
                end_time=today - timedelta(hours=6) + timedelta(minutes=22)
            )
            session.add(session3)
            
            # Сессия 4: Кормление из бутылочки
            session4 = FeedingSession(
                child_id=self.child_id,
                timestamp=today - timedelta(hours=1),
                type='bottle',
                amount=120,
                end_time=today - timedelta(hours=1) + timedelta(minutes=10)
            )
            session.add(session4)
            
            # Создаем сессии за вчера
            yesterday = today - timedelta(days=1)
            
            # Сессия 5: Левая грудь 18 минут (вчера)
            session5 = FeedingSession(
                child_id=self.child_id,
                timestamp=yesterday - timedelta(hours=2),
                type='breast',
                left_breast_duration=1080,  # 18 минут в секундах
                right_breast_duration=0,
                end_time=yesterday - timedelta(hours=2) + timedelta(minutes=18)
            )
            session.add(session5)
            
            # Сессия 6: Правая грудь 25 минут (вчера)
            session6 = FeedingSession(
                child_id=self.child_id,
                timestamp=yesterday - timedelta(hours=4),
                type='breast',
                left_breast_duration=0,
                right_breast_duration=1500,  # 25 минут в секундах
                end_time=yesterday - timedelta(hours=4) + timedelta(minutes=25)
            )
            session.add(session6)
            
            session.commit()
            
        finally:
            self.db_manager.close_session(session)
    
    def test_feeding_statistics_api_empty_data(self):
        """Тест API статистики кормления без данных."""
        url = reverse('webapp:feeding_statistics', args=[self.user_id, self.child_id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Проверяем, что все значения равны 0 при отсутствии данных
        self.assertEqual(data['today_count'], 0)
        self.assertEqual(data['today_breast_count'], 0)
        self.assertEqual(data['today_bottle_count'], 0)
        self.assertEqual(data['today_duration'], 0)
        self.assertEqual(data['today_left_breast_duration'], 0)
        self.assertEqual(data['today_right_breast_duration'], 0)
        self.assertEqual(data['today_amount'], 0)
        self.assertEqual(data['today_left_breast_percentage'], 0)
        self.assertEqual(data['today_right_breast_percentage'], 0)
        
        self.assertEqual(data['weekly_total_count'], 0)
        self.assertEqual(data['weekly_avg_count'], 0)
        self.assertEqual(data['weekly_avg_duration'], 0)
        self.assertEqual(data['weekly_avg_session_duration'], 0)
        
        self.assertFalse(data['has_data'])
        self.assertIsInstance(data['daily_stats'], list)
        self.assertEqual(len(data['daily_stats']), 7)  # 7 дней недели
    
    def test_feeding_statistics_api_with_data(self):
        """Тест API статистики кормления с данными."""
        # Создаем тестовые данные
        self.create_test_feeding_sessions()
        
        url = reverse('webapp:feeding_statistics', args=[self.user_id, self.child_id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Проверяем статистику за сегодня
        self.assertEqual(data['today_count'], 4)  # 3 грудных + 1 бутылочка
        self.assertEqual(data['today_breast_count'], 3)
        self.assertEqual(data['today_bottle_count'], 1)
        
        # Проверяем продолжительность за сегодня
        # Левая грудь: 15 + 0 + 10 = 25 минут
        # Правая грудь: 0 + 20 + 12 = 32 минуты
        # Общая: 25 + 32 = 57 минут
        self.assertEqual(data['today_left_breast_duration'], 25.0)
        self.assertEqual(data['today_right_breast_duration'], 32.0)
        self.assertEqual(data['today_duration'], 57.0)
        
        # Проверяем проценты
        # Левая грудь: 25/57 * 100 ≈ 43.9%
        # Правая грудь: 32/57 * 100 ≈ 56.1%
        self.assertAlmostEqual(data['today_left_breast_percentage'], 43.9, places=1)
        self.assertAlmostEqual(data['today_right_breast_percentage'], 56.1, places=1)
        
        # Проверяем объем из бутылочки
        self.assertEqual(data['today_amount'], 120.0)
        
        # Проверяем недельную статистику
        self.assertEqual(data['weekly_total_count'], 6)  # 5 грудных + 1 бутылочка
        self.assertEqual(data['weekly_breast_count'], 5)
        self.assertEqual(data['weekly_bottle_count'], 1)
        
        # Проверяем недельную продолжительность
        # Левая грудь: 25 (сегодня) + 18 (вчера) = 43 минуты
        # Правая грудь: 32 (сегодня) + 25 (вчера) = 57 минут
        # Общая: 43 + 57 = 100 минут
        self.assertEqual(data['weekly_left_breast_duration'], 43.0)
        self.assertEqual(data['weekly_right_breast_duration'], 57.0)
        self.assertEqual(data['weekly_total_duration'], 100.0)
        
        # Проверяем средние значения за неделю
        self.assertAlmostEqual(data['weekly_avg_count'], 6/7, places=1)
        self.assertAlmostEqual(data['weekly_avg_duration'], 100/7, places=1)
        self.assertAlmostEqual(data['weekly_avg_left_breast_duration'], 43/7, places=1)
        self.assertAlmostEqual(data['weekly_avg_right_breast_duration'], 57/7, places=1)
        
        # Проверяем статистику сессий
        # Средняя продолжительность сессии: (15+20+22+18+25)/5 = 20 минут
        self.assertEqual(data['weekly_avg_session_duration'], 20.0)
        self.assertEqual(data['weekly_longest_session'], 25.0)  # Правая грудь вчера
        self.assertEqual(data['weekly_shortest_session'], 15.0)  # Левая грудь сегодня
        
        # Проверяем наличие данных
        self.assertTrue(data['has_data'])
        
        # Проверяем данные для графика
        self.assertIsInstance(data['daily_stats'], list)
        self.assertEqual(len(data['daily_stats']), 7)
        
        # Проверяем данные за сегодня в daily_stats
        today_data = None
        for day_data in data['daily_stats']:
            if day_data['count'] == 4:  # Сегодняшний день
                today_data = day_data
                break
        
        self.assertIsNotNone(today_data)
        self.assertEqual(today_data['count'], 4)
        self.assertEqual(today_data['breast_duration'], 57.0)
        self.assertEqual(today_data['left_breast_duration'], 25.0)
        self.assertEqual(today_data['right_breast_duration'], 32.0)
        self.assertEqual(today_data['bottle_amount'], 120.0)
    
    def test_feeding_statistics_api_user_not_found(self):
        """Тест API статистики кормления с несуществующим пользователем."""
        url = reverse('webapp:feeding_statistics', args=[99999, self.child_id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Пользователь не найден')
    
    def test_feeding_statistics_api_child_not_found(self):
        """Тест API статистики кормления с несуществующим ребенком."""
        url = reverse('webapp:feeding_statistics', args=[self.user_id, 99999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Ребенок не найден')
    
    def test_feeding_statistics_api_child_not_belongs_to_user(self):
        """Тест API статистики кормления с ребенком, не принадлежащим пользователю."""
        # Создаем другого пользователя и ребенка
        session = self.db_manager.get_session()
        try:
            other_user = BotUser(
                telegram_id=54321,
                username='otheruser',
                first_name='Other',
                last_name='User'
            )
            session.add(other_user)
            session.commit()
            session.refresh(other_user)
            
            other_child = Child(
                user_id=other_user.id,
                name='Other Child',
                birth_date=datetime.now().date() - timedelta(days=60)
            )
            session.add(other_child)
            session.commit()
            session.refresh(other_child)
            
            # Пытаемся получить статистику чужого ребенка
            url = reverse('webapp:feeding_statistics', args=[self.user_id, other_child.id])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 403)
            
            data = json.loads(response.content)
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'Ребенок не принадлежит этому пользователю')
            
            # Очищаем созданные данные
            session.query(Child).filter_by(id=other_child.id).delete()
            session.query(BotUser).filter_by(id=other_user.id).delete()
            session.commit()
            
        finally:
            self.db_manager.close_session(session)
    
    def test_feeding_statistics_breast_percentage_calculation(self):
        """Тест правильности расчета процентов для каждой груди."""
        # Создаем сессию только с левой грудью
        session = self.db_manager.get_session()
        try:
            today = datetime.now()
            
            session1 = FeedingSession(
                child_id=self.child_id,
                timestamp=today - timedelta(hours=1),
                type='breast',
                left_breast_duration=1800,  # 30 минут
                right_breast_duration=0,
                end_time=today - timedelta(hours=1) + timedelta(minutes=30)
            )
            session.add(session1)
            session.commit()
            
        finally:
            self.db_manager.close_session(session)
        
        url = reverse('webapp:feeding_statistics', args=[self.user_id, self.child_id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # При кормлении только левой грудью, левая должна быть 100%, правая 0%
        self.assertEqual(data['today_left_breast_percentage'], 100.0)
        self.assertEqual(data['today_right_breast_percentage'], 0.0)
        self.assertEqual(data['today_left_breast_duration'], 30.0)
        self.assertEqual(data['today_right_breast_duration'], 0.0)
    
    def test_feeding_statistics_mixed_feeding_types(self):
        """Тест статистики при смешанном типе кормления."""
        session = self.db_manager.get_session()
        try:
            today = datetime.now()
            
            # Грудное вскармливание
            session1 = FeedingSession(
                child_id=self.child_id,
                timestamp=today - timedelta(hours=2),
                type='breast',
                left_breast_duration=600,  # 10 минут
                right_breast_duration=900,  # 15 минут
                end_time=today - timedelta(hours=2) + timedelta(minutes=25)
            )
            session.add(session1)
            
            # Кормление из бутылочки смесью
            session2 = FeedingSession(
                child_id=self.child_id,
                timestamp=today - timedelta(hours=4),
                type='bottle',
                amount=150,
                milk_type='formula',
                end_time=today - timedelta(hours=4) + timedelta(minutes=15)
            )
            session.add(session2)
            
            # Кормление из бутылочки сцеженным молоком
            session3 = FeedingSession(
                child_id=self.child_id,
                timestamp=today - timedelta(hours=6),
                type='bottle',
                amount=100,
                milk_type='expressed',
                end_time=today - timedelta(hours=6) + timedelta(minutes=10)
            )
            session.add(session3)
            
            session.commit()
            
        finally:
            self.db_manager.close_session(session)
        
        url = reverse('webapp:feeding_statistics', args=[self.user_id, self.child_id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Проверяем общую статистику
        self.assertEqual(data['today_count'], 3)
        self.assertEqual(data['today_breast_count'], 1)
        self.assertEqual(data['today_bottle_count'], 2)
        
        # Проверяем продолжительность грудного вскармливания
        self.assertEqual(data['today_left_breast_duration'], 10.0)
        self.assertEqual(data['today_right_breast_duration'], 15.0)
        self.assertEqual(data['today_duration'], 25.0)
        
        # Проверяем общий объем из бутылочки
        self.assertEqual(data['today_amount'], 250.0)  # 150 + 100
        
        # Проверяем проценты грудей
        self.assertAlmostEqual(data['today_left_breast_percentage'], 40.0, places=1)  # 10/25 * 100
        self.assertAlmostEqual(data['today_right_breast_percentage'], 60.0, places=1)  # 15/25 * 100
    
    def test_feeding_statistics_weekly_averages(self):
        """Тест правильности расчета средних значений за неделю."""
        # Создаем данные на несколько дней
        session = self.db_manager.get_session()
        try:
            base_time = datetime.now()
            
            # Создаем по одной сессии на каждый из последних 3 дней
            for i in range(3):
                day_offset = timedelta(days=i)
                session_time = base_time - day_offset
                
                feeding_session = FeedingSession(
                    child_id=self.child_id,
                    timestamp=session_time,
                    type='breast',
                    left_breast_duration=600,  # 10 минут каждый день
                    right_breast_duration=900,  # 15 минут каждый день
                    end_time=session_time + timedelta(minutes=25)
                )
                session.add(feeding_session)
            
            session.commit()
            
        finally:
            self.db_manager.close_session(session)
        
        url = reverse('webapp:feeding_statistics', args=[self.user_id, self.child_id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Проверяем недельную статистику
        self.assertEqual(data['weekly_total_count'], 3)
        self.assertEqual(data['weekly_left_breast_duration'], 30.0)  # 10 * 3
        self.assertEqual(data['weekly_right_breast_duration'], 45.0)  # 15 * 3
        self.assertEqual(data['weekly_total_duration'], 75.0)  # 25 * 3
        
        # Проверяем средние значения (делим на 7 дней)
        self.assertAlmostEqual(data['weekly_avg_count'], 3/7, places=1)
        self.assertAlmostEqual(data['weekly_avg_duration'], 75/7, places=1)
        self.assertAlmostEqual(data['weekly_avg_left_breast_duration'], 30/7, places=1)
        self.assertAlmostEqual(data['weekly_avg_right_breast_duration'], 45/7, places=1)
        
        # Проверяем статистику сессий
        self.assertEqual(data['weekly_avg_session_duration'], 25.0)  # Все сессии по 25 минут
        self.assertEqual(data['weekly_longest_session'], 25.0)
        self.assertEqual(data['weekly_shortest_session'], 25.0)


if __name__ == '__main__':
    unittest.main()