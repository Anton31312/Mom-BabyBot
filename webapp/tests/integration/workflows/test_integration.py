"""
Интеграционные тесты для веб-интерфейса материнского ухода.

Этот модуль содержит интеграционные тесты, проверяющие взаимодействие между различными
компонентами системы и API-интерфейсами.
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


class MaternalCareIntegrationTestCase(TestCase):
    """Интеграционные тесты для веб-интерфейса материнского ухода."""
    
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
            
            # Создаем тестовую вакцину
            self.vaccine = Vaccine(
                name='Test Vaccine',
                description='Test vaccine description',
                recommended_age='6 месяцев',
                is_mandatory=True
            )
            session.add(self.vaccine)
            session.commit()
            session.refresh(self.vaccine)
            
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
            
            # Удаляем тестовую вакцину
            session.query(Vaccine).filter_by(id=self.vaccine.id).delete()
            
            # Удаляем тестового пользователя
            session.query(User).filter_by(id=self.user.id).delete()
            
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_user_child_integration(self):
        """Тест интеграции между пользователем и профилями детей."""
        # 1. Получаем список детей пользователя
        url = f'/api/users/{self.user.id}/children/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('children', data)
        self.assertEqual(len(data['children']), 1)
        self.assertEqual(data['children'][0]['id'], self.child.id)
        self.assertEqual(data['children'][0]['name'], 'Test Child')
        
        # 2. Добавляем измерение для ребенка
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
        
        # 3. Проверяем, что измерение добавлено
        url = f'/api/users/{self.user.id}/children/{self.child.id}/measurements/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('measurements', data)
        self.assertEqual(len(data['measurements']), 1)
        self.assertEqual(data['measurements'][0]['height'], 68.5)
        self.assertEqual(data['measurements'][0]['weight'], 8.2)
        self.assertEqual(data['measurements'][0]['head_circumference'], 43.0)
    
    def test_contraction_kick_integration(self):
        """Тест интеграции между счетчиками схваток и шевелений."""
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
        
        # 3. Создаем сессию шевелений
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
        
        # 4. Добавляем события шевелений
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
        
        # 5. Проверяем, что обе сессии доступны для пользователя
        url = f'/api/users/{self.user.id}/contractions/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['contractions']), 1)
        self.assertEqual(len(data['contractions'][0]['events']), 3)
        
        url = f'/api/users/{self.user.id}/kicks/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['kicks']), 1)
        self.assertEqual(len(data['kicks'][0]['events']), 5)
        
        # 6. Завершаем обе сессии
        url = f'/api/users/{self.user.id}/contractions/{contraction_id}/'
        response = self.client.put(
            url,
            data=json.dumps({'end_session': True}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        url = f'/api/users/{self.user.id}/kicks/{kick_id}/'
        response = self.client.put(
            url,
            data=json.dumps({'end_session': True}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_sleep_feeding_integration(self):
        """Тест интеграции между таймером сна и отслеживанием кормления."""
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
        
        # 2. Завершаем сессию сна через 30 минут
        sleep_end_time = datetime.now() + timedelta(minutes=30)
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/{sleep_id}/'
        response = self.client.put(
            url,
            data=json.dumps({
                'end_time': sleep_end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'notes': 'Завершенная сессия сна'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # 3. Создаем сессию кормления
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/'
        feeding_data = {
            'type': 'breast',
            'breast': 'left',
            'duration': 15,  # минут
            'notes': 'Тестовая сессия кормления'
        }
        response = self.client.post(
            url,
            data=json.dumps(feeding_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        feeding_id = json.loads(response.content)['id']
        
        # 4. Создаем еще одну сессию кормления, но из бутылочки
        url = f'/api/users/{self.user.id}/children/{self.child.id}/feeding/'
        feeding_data = {
            'type': 'bottle',
            'amount': 120,  # мл
            'notes': 'Тестовая сессия кормления из бутылочки'
        }
        response = self.client.post(
            url,
            data=json.dumps(feeding_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # 5. Проверяем, что все сессии доступны
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['sleep_sessions']), 1)
        self.assertEqual(data['sleep_sessions'][0]['type'], 'day')
        self.assertIsNotNone(data['sleep_sessions'][0]['end_time'])
        
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
        self.assertEqual(breast_feedings[0]['duration'], 15)
        self.assertEqual(bottle_feedings[0]['amount'], 120)
    
    def test_vaccine_integration(self):
        """Тест интеграции календаря прививок с профилем ребенка."""
        # 1. Получаем список доступных вакцин
        url = '/api/vaccines/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('vaccines', data)
        self.assertGreaterEqual(len(data['vaccines']), 1)  # Должна быть хотя бы наша тестовая вакцина
        
        # 2. Отмечаем вакцину как сделанную для ребенка
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/'
        vaccine_data = {
            'vaccine_id': self.vaccine.id,
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
        
        # 3. Проверяем, что прививка отмечена для ребенка
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('vaccines', data)
        self.assertEqual(len(data['vaccines']), 1)
        self.assertEqual(data['vaccines'][0]['vaccine_id'], self.vaccine.id)
        self.assertEqual(data['vaccines'][0]['notes'], 'Тестовая прививка')
        self.assertTrue(data['vaccines'][0]['is_completed'])
    
    def test_complex_user_flow(self):
        """Тест комплексного пользовательского сценария."""
        # 1. Создаем второго ребенка
        url = f'/api/users/{self.user.id}/children/'
        child_data = {
            'name': 'Second Child',
            'birth_date': datetime.now() - timedelta(days=30)  # 1 месяц
        }
        response = self.client.post(
            url,
            data=json.dumps(child_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        second_child_id = json.loads(response.content)['id']
        
        # 2. Добавляем измерения для обоих детей
        # Для первого ребенка
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
        
        # Для второго ребенка
        url = f'/api/users/{self.user.id}/children/{second_child_id}/measurements/'
        measurement_data = {
            'height': 54.0,  # см
            'weight': 4.1,   # кг
            'head_circumference': 37.0  # см
        }
        response = self.client.post(
            url,
            data=json.dumps(measurement_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        
        # 3. Создаем сессию сна для первого ребенка
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
        sleep_id = json.loads(response.content)['id']
        
        # 4. Создаем сессию кормления для второго ребенка
        url = f'/api/users/{self.user.id}/children/{second_child_id}/feeding/'
        feeding_data = {
            'type': 'breast',
            'breast': 'right',
            'duration': 20,  # минут
            'notes': 'Грудное кормление'
        }
        response = self.client.post(
            url,
            data=json.dumps(feeding_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        
        # 5. Создаем сессию схваток для пользователя (беременная женщина)
        url = f'/api/users/{self.user.id}/contractions/'
        contraction_data = {
            'notes': 'Схватки'
        }
        response = self.client.post(
            url,
            data=json.dumps(contraction_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        contraction_id = json.loads(response.content)['id']
        
        # Добавляем события схваток
        url = f'/api/users/{self.user.id}/contractions/{contraction_id}/events/'
        for i in range(3):
            event_data = {
                'duration': 30 + i*10,
                'intensity': 5 + i
            }
            response = self.client.post(
                url,
                data=json.dumps(event_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
        
        # 6. Проверяем, что все данные доступны через API
        # Проверяем список детей
        url = f'/api/users/{self.user.id}/children/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['children']), 2)
        
        # Проверяем измерения первого ребенка
        url = f'/api/users/{self.user.id}/children/{self.child.id}/measurements/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['measurements']), 1)
        
        # Проверяем сессию сна
        url = f'/api/users/{self.user.id}/children/{self.child.id}/sleep/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['sleep_sessions']), 1)
        
        # Проверяем сессию кормления
        url = f'/api/users/{self.user.id}/children/{second_child_id}/feeding/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['feeding_sessions']), 1)
        
        # Проверяем сессию схваток
        url = f'/api/users/{self.user.id}/contractions/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['contractions']), 1)
        self.assertEqual(len(data['contractions'][0]['events']), 3)
        
        # 7. Очистка - удаляем второго ребенка
        session = db_manager.get_session()
        try:
            # Удаляем все связанные данные
            session.query(Measurement).filter_by(child_id=second_child_id).delete()
            session.query(FeedingSession).filter_by(child_id=second_child_id).delete()
            session.query(SleepSession).filter_by(child_id=second_child_id).delete()
            session.query(ChildVaccine).filter_by(child_id=second_child_id).delete()
            
            # Удаляем второго ребенка
            session.query(Child).filter_by(id=second_child_id).delete()
            
            session.commit()
        finally:
            db_manager.close_session(session)


class APIErrorHandlingTestCase(TestCase):
    """Тесты обработки ошибок в API."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
    
    def test_nonexistent_user(self):
        """Тест запроса к несуществующему пользователю."""
        url = '/api/users/999999/children/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_invalid_data(self):
        """Тест отправки некорректных данных."""
        url = '/api/users/1/children/'
        invalid_data = {
            'name': '',  # Пустое имя
            'birth_date': 'not-a-date'  # Некорректная дата
        }
        response = self.client.post(
            url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_method_not_allowed(self):
        """Тест использования неподдерживаемого HTTP-метода."""
        url = '/api/vaccines/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()