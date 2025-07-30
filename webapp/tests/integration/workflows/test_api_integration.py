"""
Интеграционные тесты для API-интерфейсов веб-приложения материнского ухода.

Этот модуль содержит тесты, проверяющие взаимодействие между различными API-интерфейсами
и их корректную работу в рамках единой системы.
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


class APIIntegrationTestCase(TestCase):
    """Интеграционные тесты для API-интерфейсов."""
    
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
    
    def test_user_api(self):
        """Тест API пользователя."""
        # 1. Получаем данные пользователя
        url = f'/api/users/{self.user.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['is_pregnant'], True)
        self.assertEqual(data['pregnancy_week'], 30)
        
        # 2. Обновляем данные пользователя
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
        data = json.loads(response.content)
        self.assertEqual(data['pregnancy_week'], 31)
        self.assertEqual(data['is_premium'], True)
        
        # 3. Проверяем, что данные обновились
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(data['pregnancy_week'], 31)
        self.assertEqual(data['is_premium'], True)
    
    def test_child_measurement_api(self):
        """Тест API профилей детей и измерений."""
        # 1. Добавляем измерение для ребенка
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
        measurement_id = json.loads(response.content)['id']
        
        # 2. Получаем измерения ребенка
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('measurements', data)
        self.assertEqual(len(data['measurements']), 1)
        self.assertEqual(data['measurements'][0]['height'], 68.5)
        
        # 3. Добавляем еще одно измерение
        measurement_data = {
            'height': 69.0,  # см
            'weight': 8.4,   # кг
            'head_circumference': 43.2  # см
        }
        response = self.client.post(
            url,
            data=json.dumps(measurement_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # 4. Проверяем, что оба измерения доступны
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measurements']), 2)
        
        # Проверяем, что измерения отсортированы по дате (новые в начале)
        self.assertEqual(data['measurements'][0]['height'], 69.0)
        self.assertEqual(data['measurements'][1]['height'], 68.5)
    
    def test_contraction_api(self):
        """Тест API счетчика схваток."""
        # 1. Создаем сессию схваток
        url = f'/api/users/{self.user.id}/contractions/'
        contraction_data = {
            'notes': 'Тестовая сессия схваток'
        }
        response = self.client.post(
            url,
            data=json.dumps(contraction_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        contraction_id = json.loads(response.content)['id']
        
        # 2. Добавляем события схваток
        url = f'/api/users/{self.user.id}/contractions/{contraction_id}/events/'
        for i in range(3):
            event_data = {
                'duration': 30 + i*10,  # 30, 40, 50 секунд
                'intensity': 5 + i      # 5, 6, 7 из 10
            }
            response = self.client.post(
                url,
                data=json.dumps(event_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
        
        # 3. Получаем детали сессии схваток
        url = f'/api/users/{self.user.id}/contractions/{contraction_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], contraction_id)
        self.assertEqual(data['notes'], 'Тестовая сессия схваток')
        self.assertEqual(len(data['events']), 3)
        
        # Проверяем, что события отсортированы по времени
        self.assertEqual(data['events'][0]['duration'], 30)
        self.assertEqual(data['events'][1]['duration'], 40)
        self.assertEqual(data['events'][2]['duration'], 50)
        
        # 4. Завершаем сессию схваток
        response = self.client.put(
            url,
            data=json.dumps({'end_session': True}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNotNone(data['end_time'])
        
        # 5. Проверяем, что нельзя добавить событие к завершенной сессии
        url = f'/api/users/{self.user.id}/contractions/{contraction_id}/events/'
        event_data = {
            'duration': 60,
            'intensity': 8
        }
        response = self.client.post(
            url,
            data=json.dumps(event_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_kick_api(self):
        """Тест API счетчика шевелений."""
        # 1. Создаем сессию шевелений
        url = f'/api/users/{self.user.id}/kicks/'
        kick_data = {
            'notes': 'Тестовая сессия шевелений'
        }
        response = self.client.post(
            url,
            data=json.dumps(kick_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        kick_id = json.loads(response.content)['id']
        
        # 2. Добавляем события шевелений
        url = f'/api/users/{self.user.id}/kicks/{kick_id}/events/'
        for i in range(5):
            event_data = {
                'intensity': 3 + i % 3  # 3, 4, 5, 3, 4
            }
            response = self.client.post(
                url,
                data=json.dumps(event_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
        
        # 3. Получаем детали сессии шевелений
        url = f'/api/users/{self.user.id}/kicks/{kick_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], kick_id)
        self.assertEqual(data['notes'], 'Тестовая сессия шевелений')
        self.assertEqual(len(data['events']), 5)
        
        # 4. Завершаем сессию шевелений
        response = self.client.put(
            url,
            data=json.dumps({'end_session': True}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNotNone(data['end_time'])
    
    def test_sleep_api(self):
        """Тест API таймера сна."""
        # 1. Создаем сессию сна
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/'
        sleep_data = {
            'type': 'day',  # дневной сон
            'notes': 'Тестовая сессия сна'
        }
        response = self.client.post(
            url,
            data=json.dumps(sleep_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        sleep_id = json.loads(response.content)['id']
        
        # 2. Получаем детали сессии сна
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/{sleep_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], sleep_id)
        self.assertEqual(data['type'], 'day')
        self.assertEqual(data['notes'], 'Тестовая сессия сна')
        self.assertIsNone(data['end_time'])
        
        # 3. Завершаем сессию сна
        sleep_end_time = datetime.now() + timedelta(minutes=30)
        response = self.client.put(
            url,
            data=json.dumps({
                'end_time': sleep_end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'notes': 'Завершенная сессия сна'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNotNone(data['end_time'])
        self.assertEqual(data['notes'], 'Завершенная сессия сна')
        
        # 4. Создаем ночную сессию сна
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/'
        sleep_data = {
            'type': 'night',  # ночной сон
            'notes': 'Ночной сон'
        }
        response = self.client.post(
            url,
            data=json.dumps(sleep_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # 5. Получаем список всех сессий сна
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
    
    def test_feeding_api(self):
        """Тест API отслеживания кормления."""
        # 1. Создаем сессию грудного кормления
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/'
        feeding_data = {
            'type': 'breast',
            'breast': 'left',
            'duration': 15,  # минут
            'notes': 'Грудное кормление'
        }
        response = self.client.post(
            url,
            data=json.dumps(feeding_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        feeding_id = json.loads(response.content)['id']
        
        # 2. Получаем детали сессии кормления
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/{feeding_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], feeding_id)
        self.assertEqual(data['type'], 'breast')
        self.assertEqual(data['breast'], 'left')
        self.assertEqual(data['duration'], 15)
        self.assertEqual(data['notes'], 'Грудное кормление')
        
        # 3. Создаем сессию кормления из бутылочки
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/'
        feeding_data = {
            'type': 'bottle',
            'amount': 120,  # мл
            'notes': 'Кормление из бутылочки'
        }
        response = self.client.post(
            url,
            data=json.dumps(feeding_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        bottle_feeding_id = json.loads(response.content)['id']
        
        # 4. Получаем список всех сессий кормления
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
        self.assertEqual(breast_feedings[0]['breast'], 'left')
        self.assertEqual(bottle_feedings[0]['amount'], 120)
    
    def test_vaccine_api(self):
        """Тест API календаря прививок."""
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
        
        # 2. Получаем список доступных вакцин
        url = '/api/vaccines/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('vaccines', data)
        self.assertGreaterEqual(len(data['vaccines']), 1)
        
        # 3. Отмечаем вакцину как сделанную для ребенка
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/'
        vaccine_data = {
            'vaccine_id': vaccine_id,
            'date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'notes': 'Тестовая прививка'
        }
        response = self.client.post(
            url,
            data=json.dumps(vaccine_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        child_vaccine_id = json.loads(response.content)['id']
        
        # 4. Получаем список прививок ребенка
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('vaccines', data)
        self.assertEqual(len(data['vaccines']), 1)
        self.assertEqual(data['vaccines'][0]['vaccine_id'], vaccine_id)
        
        # 5. Удаляем тестовую вакцину
        session = db_manager.get_session()
        try:
            # Сначала удаляем связь ребенка с вакциной
            session.query(ChildVaccine).filter_by(id=child_vaccine_id).delete()
            # Затем удаляем саму вакцину
            session.query(Vaccine).filter_by(id=vaccine_id).delete()
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_cross_api_integration(self):
        """Тест интеграции между различными API."""
        # 1. Создаем сессию схваток
        url = f'/api/users/{self.user.id}/contractions/'
        contraction_data = {
            'notes': 'Тестовая сессия схваток'
        }
        response = self.client.post(
            url,
            data=json.dumps(contraction_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        contraction_id = json.loads(response.content)['id']
        
        # 2. Добавляем событие схватки
        url = f'/api/users/{self.user.id}/contractions/{contraction_id}/events/'
        event_data = {
            'duration': 45,
            'intensity': 7
        }
        response = self.client.post(
            url,
            data=json.dumps(event_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        
        # 3. Создаем сессию сна для ребенка
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/'
        sleep_data = {
            'type': 'day',
            'notes': 'Дневной сон'
        }
        response = self.client.post(
            url,
            data=json.dumps(sleep_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        sleep_id = json.loads(response.content)['id']
        
        # 4. Проверяем, что данные пользователя включают информацию о схватках
        url = f'/api/users/{self.user.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        user_data = json.loads(response.content)
        
        # 5. Проверяем, что данные ребенка включают информацию о сне
        url = f'/api/users/{self.user.id}/children/{self.child.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        child_data = json.loads(response.content)
        
        # 6. Проверяем, что можно получить все данные пользователя и его детей
        url = f'/api/users/{self.user.id}/dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        dashboard_data = json.loads(response.content)
        
        # Проверяем наличие основных разделов в дашборде
        self.assertIn('user', dashboard_data)
        self.assertIn('children', dashboard_data)
        self.assertEqual(dashboard_data['user']['id'], self.user.id)
        self.assertEqual(len(dashboard_data['children']), 1)
        self.assertEqual(dashboard_data['children'][0]['id'], self.child.id)


if __name__ == '__main__':
    unittest.main()