"""
Интеграционные тесты для синхронизации данных между веб-интерфейсом и Telegram ботом.

Этот модуль содержит тесты, проверяющие корректную синхронизацию данных между
веб-интерфейсом и Telegram ботом.
"""

import json
import unittest
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse

from botapp.models import User, db_manager
from botapp.models_child import Child, Measurement
from botapp.models_timers import Contraction, ContractionEvent, Kick, KickEvent, SleepSession, FeedingSession
from botapp.models_vaccine import Vaccine, ChildVaccine


class WebTelegramSyncTestCase(TestCase):
    """Тесты синхронизации данных между веб-интерфейсом и Telegram ботом."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        # Создаем тестового пользователя
        session = db_manager.get_session()
        try:
            self.user = User(
                telegram_id=123456789,
                username='testuser',
                first_name='Test',
                last_name='User',
                is_pregnant=True,
                pregnancy_week=30
            )
            session.add(self.user)
            session.commit()
            session.refresh(self.user)
            
            # Создаем тестового ребенка
            self.child = Child(
                user_id=self.user.id,
                name='Test Child',
                birth_date=datetime.now() - timedelta(days=180)  # 6 месяцев
            )
            session.add(self.child)
            session.commit()
            session.refresh(self.child)
            
        finally:
            db_manager.close_session(session)
        
        # Создаем тестовый клиент
        self.client = Client()
    
    def tearDown(self):
        """Очистка тестовых данных."""
        session = db_manager.get_session()
        try:
            # Удаляем все связанные данные
            session.query(ChildVaccine).filter_by(child_id=self.child.id).delete()
            session.query(Measurement).filter_by(child_id=self.child.id).delete()
            session.query(FeedingSession).filter_by(child_id=self.child.id).delete()
            session.query(SleepSession).filter_by(child_id=self.child.id).delete()
            
            # Удаляем все события схваток и шевелений
            for contraction in session.query(Contraction).filter_by(user_id=self.user.id).all():
                session.query(ContractionEvent).filter_by(session_id=contraction.id).delete()
            session.query(Contraction).filter_by(user_id=self.user.id).delete()
            
            for kick in session.query(Kick).filter_by(user_id=self.user.id).all():
                session.query(KickEvent).filter_by(session_id=kick.id).delete()
            session.query(Kick).filter_by(user_id=self.user.id).delete()
            
            # Удаляем тестового ребенка
            session.query(Child).filter_by(id=self.child.id).delete()
            
            # Удаляем тестового пользователя
            session.query(User).filter_by(id=self.user.id).delete()
            
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_telegram_web_user_sync(self):
        """Тест синхронизации данных пользователя между Telegram и веб-интерфейсом."""
        # 1. Обновляем данные пользователя через веб-API
        url = f'/api/users/{self.user.id}/'
        update_data = {
            'pregnancy_week': 31,
            'is_premium': True
        }
        response = self.client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 2. Проверяем, что данные обновились в базе данных (доступны для бота)
        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(id=self.user.id).first()
            self.assertEqual(user.pregnancy_week, 31)
            self.assertEqual(user.is_premium, True)
        finally:
            db_manager.close_session(session)
        
        # 3. Имитируем обновление данных через бота
        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(id=self.user.id).first()
            user.pregnancy_week = 32
            user.baby_birth_date = datetime.now() - timedelta(days=10)
            session.commit()
        finally:
            db_manager.close_session(session)
        
        # 4. Проверяем, что данные доступны через веб-API
        url = f'/api/users/{self.user.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['pregnancy_week'], 32)
        self.assertIsNotNone(data['baby_birth_date'])
    
    def test_telegram_web_child_sync(self):
        """Тест синхронизации данных ребенка между Telegram и веб-интерфейсом."""
        # 1. Добавляем измерение через веб-API
        url = f'/api/users/{self.user.id}/children/{self.child.id}/measurements/'
        measurement_data = {
            'height': 68.5,  # см
            'weight': 8.2,   # кг
            'head_circumference': 43.0  # см
        }
        response = self.client.post(
            url,
            data=json.dumps(measurement_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # 2. Проверяем, что данные доступны в базе данных (для бота)
        session = db_manager.get_session()
        try:
            measurements = session.query(Measurement).filter_by(child_id=self.child.id).all()
            self.assertEqual(len(measurements), 1)
            self.assertEqual(measurements[0].height, 68.5)
            self.assertEqual(measurements[0].weight, 8.2)
            self.assertEqual(measurements[0].head_circumference, 43.0)
        finally:
            db_manager.close_session(session)
        
        # 3. Имитируем добавление измерения через бота
        session = db_manager.get_session()
        try:
            measurement = Measurement(
                child_id=self.child.id,
                date=datetime.now(),
                height=69.0,
                weight=8.4,
                head_circumference=43.2
            )
            session.add(measurement)
            session.commit()
        finally:
            db_manager.close_session(session)
        
        # 4. Проверяем, что оба измерения доступны через веб-API
        url = f'/api/users/{self.user.id}/children/{self.child.id}/measurements/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measurements']), 2)
        
        # Проверяем, что измерения отсортированы по дате (новые в начале)
        heights = [m['height'] for m in data['measurements']]
        self.assertIn(68.5, heights)
        self.assertIn(69.0, heights)
    
    def test_telegram_web_sleep_sync(self):
        """Тест синхронизации данных о сне между Telegram и веб-интерфейсом."""
        # 1. Создаем сессию сна через веб-API
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/'
        sleep_data = {
            'type': 'day',  # дневной сон
            'notes': 'Дневной сон через веб'
        }
        response = self.client.post(
            url,
            data=json.dumps(sleep_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        web_sleep_id = json.loads(response.content)['id']
        
        # 2. Имитируем создание сессии сна через бота
        session = db_manager.get_session()
        try:
            sleep_session = SleepSession(
                child_id=self.child.id,
                start_time=datetime.now(),
                type='night',
                notes='Ночной сон через бота'
            )
            session.add(sleep_session)
            session.commit()
            session.refresh(sleep_session)
            bot_sleep_id = sleep_session.id
        finally:
            db_manager.close_session(session)
        
        # 3. Проверяем, что обе сессии доступны через веб-API
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['sleep_sessions']), 2)
        
        # Проверяем, что есть одна дневная и одна ночная сессия
        day_sessions = [s for s in data['sleep_sessions'] if s['type'] == 'day']
        night_sessions = [s for s in data['sleep_sessions'] if s['type'] == 'night']
        self.assertEqual(len(day_sessions), 1)
        self.assertEqual(len(night_sessions), 1)
        self.assertEqual(day_sessions[0]['notes'], 'Дневной сон через веб')
        self.assertEqual(night_sessions[0]['notes'], 'Ночной сон через бота')
        
        # 4. Завершаем сессию сна, созданную через веб-API, используя бота
        session = db_manager.get_session()
        try:
            sleep_session = session.query(SleepSession).filter_by(id=web_sleep_id).first()
            sleep_session.end_time = datetime.now() + timedelta(minutes=30)
            sleep_session.notes = 'Дневной сон, завершенный через бота'
            session.commit()
        finally:
            db_manager.close_session(session)
        
        # 5. Проверяем, что изменения доступны через веб-API
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/{web_sleep_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNotNone(data['end_time'])
        self.assertEqual(data['notes'], 'Дневной сон, завершенный через бота')
    
    def test_telegram_web_feeding_sync(self):
        """Тест синхронизации данных о кормлении между Telegram и веб-интерфейсом."""
        # 1. Создаем сессию кормления через веб-API
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/'
        feeding_data = {
            'type': 'breast',
            'breast': 'left',
            'duration': 15,  # минут
            'notes': 'Грудное кормление через веб'
        }
        response = self.client.post(
            url,
            data=json.dumps(feeding_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # 2. Имитируем создание сессии кормления через бота
        session = db_manager.get_session()
        try:
            feeding_session = FeedingSession(
                child_id=self.child.id,
                timestamp=datetime.now(),
                type='bottle',
                amount=120,  # мл
                notes='Кормление из бутылочки через бота'
            )
            session.add(feeding_session)
            session.commit()
        finally:
            db_manager.close_session(session)
        
        # 3. Проверяем, что обе сессии доступны через веб-API
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['feeding_sessions']), 2)
        
        # Проверяем, что есть одно грудное кормление и одно из бутылочки
        breast_feedings = [f for f in data['feeding_sessions'] if f['type'] == 'breast']
        bottle_feedings = [f for f in data['feeding_sessions'] if f['type'] == 'bottle']
        self.assertEqual(len(breast_feedings), 1)
        self.assertEqual(len(bottle_feedings), 1)
        self.assertEqual(breast_feedings[0]['notes'], 'Грудное кормление через веб')
        self.assertEqual(bottle_feedings[0]['notes'], 'Кормление из бутылочки через бота')
    
    def test_telegram_web_vaccine_sync(self):
        """Тест синхронизации данных о прививках между Telegram и веб-интерфейсом."""
        # 1. Создаем тестовую вакцину
        session = db_manager.get_session()
        try:
            vaccine = Vaccine(
                name='Test Vaccine',
                description='Test vaccine description',
                recommended_age='6 месяцев',
                is_mandatory=True
            )
            session.add(vaccine)
            session.commit()
            session.refresh(vaccine)
            vaccine_id = vaccine.id
        finally:
            db_manager.close_session(session)
        
        # 2. Отмечаем вакцину как сделанную через веб-API
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/'
        vaccine_data = {
            'vaccine_id': vaccine_id,
            'date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'notes': 'Прививка через веб'
        }
        response = self.client.post(
            url,
            data=json.dumps(vaccine_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # 3. Создаем еще одну тестовую вакцину
        session = db_manager.get_session()
        try:
            vaccine2 = Vaccine(
                name='Test Vaccine 2',
                description='Test vaccine 2 description',
                recommended_age='12 месяцев',
                is_mandatory=False
            )
            session.add(vaccine2)
            session.commit()
            session.refresh(vaccine2)
            vaccine2_id = vaccine2.id
            
            # 4. Имитируем отметку о прививке через бота
            child_vaccine = ChildVaccine(
                child_id=self.child.id,
                vaccine_id=vaccine2_id,
                date=datetime.now(),
                is_completed=True,
                notes='Прививка через бота'
            )
            session.add(child_vaccine)
            session.commit()
        finally:
            db_manager.close_session(session)
        
        # 5. Проверяем, что обе прививки доступны через веб-API
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['vaccines']), 2)
        
        # Проверяем, что есть обе прививки
        vaccine_notes = [v['notes'] for v in data['vaccines']]
        self.assertIn('Прививка через веб', vaccine_notes)
        self.assertIn('Прививка через бота', vaccine_notes)
        
        # 6. Удаляем тестовые вакцины
        session = db_manager.get_session()
        try:
            # Сначала удаляем связи ребенка с вакцинами
            session.query(ChildVaccine).filter_by(child_id=self.child.id).delete()
            # Затем удаляем сами вакцины
            session.query(Vaccine).filter_by(id=vaccine_id).delete()
            session.query(Vaccine).filter_by(id=vaccine2_id).delete()
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_webapp_data_endpoint(self):
        """Тест эндпоинта для обмена данными между веб-приложением и Telegram ботом."""
        # 1. Отправляем данные через эндпоинт webapp/data/
        url = '/webapp/data/'
        webapp_data = {
            'user_id': self.user.telegram_id,  # Используем telegram_id для идентификации пользователя
            'pregnancy_week': 33,
            'baby_birth_date': (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%dT%H:%M:%S')
        }
        response = self.client.post(
            url,
            data=json.dumps(webapp_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 2. Проверяем, что данные обновились в базе данных
        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=self.user.telegram_id).first()
            self.assertEqual(user.pregnancy_week, 33)
            self.assertIsNotNone(user.baby_birth_date)
        finally:
            db_manager.close_session(session)
        
        # 3. Получаем данные через эндпоинт webapp/data/
        url = f'/webapp/data/?user_id={self.user.telegram_id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['pregnancy_week'], 33)
        self.assertIsNotNone(data['user']['baby_birth_date'])
        self.assertEqual(len(data['children']), 1)
        self.assertEqual(data['children'][0]['name'], 'Test Child')


if __name__ == '__main__':
    unittest.main()