"""
Тесты для моделей счетчиков и таймеров.

Этот модуль содержит тесты для моделей Contraction, ContractionEvent, Kick, KickEvent,
SleepSession и FeedingSession.
"""

import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from botapp.models import Base, User
from botapp.models_child import Child
from botapp.models_timers import (
    Contraction, ContractionEvent,
    Kick, KickEvent,
    SleepSession,
    FeedingSession
)


class TestTimerModels(unittest.TestCase):
    """Тестовые случаи для моделей счетчиков и таймеров."""
    
    def setUp(self):
        """Настройка тестовой базы данных и сессии."""
        # Создаем базу данных SQLite в памяти для тестирования
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        
        # Создаем сессию
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Создаем тестового пользователя
        self.test_user = User(
            telegram_id=123456789,
            username='test_user',
            first_name='Test',
            last_name='User',
            is_pregnant=True,
            pregnancy_week=30
        )
        self.session.add(self.test_user)
        
        # Создаем тестового ребенка
        self.test_child = Child(
            user_id=1,  # ID будет 1 после коммита
            name='Test Child',
            birth_date=datetime.utcnow() - timedelta(days=180),  # 6 месяцев
            gender='female'
        )
        self.session.add(self.test_child)
        self.session.commit()
    
    def tearDown(self):
        """Очистка после тестов."""
        self.session.close()
        Base.metadata.drop_all(self.engine)
    
    def test_contraction_model(self):
        """Тест модели Contraction и ContractionEvent."""
        # Создаем сессию схваток
        contraction = Contraction(
            user_id=self.test_user.id,
            start_time=datetime.utcnow() - timedelta(hours=2),
            notes='Тестовая сессия схваток'
        )
        self.session.add(contraction)
        self.session.commit()
        
        # Добавляем события схваток
        for i in range(5):
            event = ContractionEvent(
                session_id=contraction.id,
                timestamp=datetime.utcnow() - timedelta(hours=2) + timedelta(minutes=i*15),
                duration=60 + i*10,  # от 60 до 100 секунд
                intensity=5 + i % 3  # от 5 до 7
            )
            self.session.add(event)
        self.session.commit()
        
        # Завершаем сессию схваток
        contraction.end_time = datetime.utcnow() - timedelta(hours=1)
        self.session.commit()
        
        # Проверяем, что сессия схваток была создана
        saved_contraction = self.session.query(Contraction).filter_by(id=contraction.id).first()
        self.assertIsNotNone(saved_contraction)
        self.assertEqual(saved_contraction.notes, 'Тестовая сессия схваток')
        
        # Проверяем, что события схваток были созданы и связаны с сессией
        self.assertEqual(len(saved_contraction.contraction_events), 5)
        
        # Проверяем свойства сессии схваток
        self.assertAlmostEqual(saved_contraction.duration, 60, delta=1)  # ~60 минут
        self.assertEqual(saved_contraction.count, 5)
        self.assertAlmostEqual(saved_contraction.average_interval, 15, delta=1)  # ~15 минут между схватками
    
    def test_kick_model(self):
        """Тест модели Kick и KickEvent."""
        # Создаем сессию шевелений
        kick = Kick(
            user_id=self.test_user.id,
            start_time=datetime.utcnow() - timedelta(hours=1),
            notes='Тестовая сессия шевелений'
        )
        self.session.add(kick)
        self.session.commit()
        
        # Добавляем события шевелений
        for i in range(10):
            event = KickEvent(
                session_id=kick.id,
                timestamp=datetime.utcnow() - timedelta(hours=1) + timedelta(minutes=i*5),
                intensity=3 + i % 5  # от 3 до 7
            )
            self.session.add(event)
        self.session.commit()
        
        # Завершаем сессию шевелений
        kick.end_time = datetime.utcnow() - timedelta(minutes=10)
        self.session.commit()
        
        # Проверяем, что сессия шевелений была создана
        saved_kick = self.session.query(Kick).filter_by(id=kick.id).first()
        self.assertIsNotNone(saved_kick)
        self.assertEqual(saved_kick.notes, 'Тестовая сессия шевелений')
        
        # Проверяем, что события шевелений были созданы и связаны с сессией
        self.assertEqual(len(saved_kick.kick_events), 10)
        
        # Проверяем свойства сессии шевелений
        self.assertAlmostEqual(saved_kick.duration, 50, delta=1)  # ~50 минут
        self.assertEqual(saved_kick.count, 10)
    
    def test_sleep_session_model(self):
        """Тест модели SleepSession."""
        # Создаем сессию сна
        sleep = SleepSession(
            child_id=self.test_child.id,
            start_time=datetime.utcnow() - timedelta(hours=3),
            type='night',
            quality=4,
            notes='Тестовая сессия сна'
        )
        self.session.add(sleep)
        self.session.commit()
        
        # Завершаем сессию сна
        sleep.end_time = datetime.utcnow() - timedelta(hours=1)
        self.session.commit()
        
        # Проверяем, что сессия сна была создана
        saved_sleep = self.session.query(SleepSession).filter_by(id=sleep.id).first()
        self.assertIsNotNone(saved_sleep)
        self.assertEqual(saved_sleep.type, 'night')
        self.assertEqual(saved_sleep.quality, 4)
        self.assertEqual(saved_sleep.notes, 'Тестовая сессия сна')
        
        # Проверяем свойства сессии сна
        self.assertAlmostEqual(saved_sleep.duration, 120, delta=1)  # ~120 минут
        
        # Проверяем связь с ребенком
        self.assertEqual(saved_sleep.child_id, self.test_child.id)
    
    def test_feeding_session_model(self):
        """Тест модели FeedingSession."""
        # Создаем сессию кормления грудью
        breast_feeding = FeedingSession(
            child_id=self.test_child.id,
            timestamp=datetime.utcnow() - timedelta(hours=4),
            type='breast',
            duration=20,
            breast='left',
            notes='Тестовое грудное кормление'
        )
        self.session.add(breast_feeding)
        
        # Создаем сессию кормления из бутылочки
        bottle_feeding = FeedingSession(
            child_id=self.test_child.id,
            timestamp=datetime.utcnow() - timedelta(hours=2),
            type='bottle',
            amount=120.0,
            food_type='Смесь',
            notes='Тестовое кормление из бутылочки'
        )
        self.session.add(bottle_feeding)
        self.session.commit()
        
        # Проверяем, что сессии кормления были созданы
        saved_breast_feeding = self.session.query(FeedingSession).filter_by(id=breast_feeding.id).first()
        self.assertIsNotNone(saved_breast_feeding)
        self.assertEqual(saved_breast_feeding.type, 'breast')
        self.assertEqual(saved_breast_feeding.duration, 20)
        self.assertEqual(saved_breast_feeding.breast, 'left')
        
        saved_bottle_feeding = self.session.query(FeedingSession).filter_by(id=bottle_feeding.id).first()
        self.assertIsNotNone(saved_bottle_feeding)
        self.assertEqual(saved_bottle_feeding.type, 'bottle')
        self.assertEqual(saved_bottle_feeding.amount, 120.0)
        self.assertEqual(saved_bottle_feeding.food_type, 'Смесь')
        
        # Проверяем связь с ребенком
        self.assertEqual(saved_breast_feeding.child_id, self.test_child.id)
        self.assertEqual(saved_bottle_feeding.child_id, self.test_child.id)
        
        # Проверяем, что кормления доступны через связь с ребенком
        self.session.refresh(self.test_child)
        self.assertEqual(len(self.test_child.feeding_sessions), 2)
    
    def test_user_contraction_relationship(self):
        """Тест связи между моделями User и Contraction."""
        # Создаем несколько сессий схваток для тестового пользователя
        for i in range(3):
            contraction = Contraction(
                user_id=self.test_user.id,
                start_time=datetime.utcnow() - timedelta(days=i),
                end_time=datetime.utcnow() - timedelta(days=i) + timedelta(hours=2)
            )
            self.session.add(contraction)
        self.session.commit()
        
        # Обновляем пользователя из базы данных
        self.session.refresh(self.test_user)
        
        # Проверяем, что сессии схваток доступны через связь
        self.assertEqual(len(self.test_user.contractions), 3)
    
    def test_user_kick_relationship(self):
        """Тест связи между моделями User и Kick."""
        # Создаем несколько сессий шевелений для тестового пользователя
        for i in range(3):
            kick = Kick(
                user_id=self.test_user.id,
                start_time=datetime.utcnow() - timedelta(days=i),
                end_time=datetime.utcnow() - timedelta(days=i) + timedelta(hours=1)
            )
            self.session.add(kick)
        self.session.commit()
        
        # Обновляем пользователя из базы данных
        self.session.refresh(self.test_user)
        
        # Проверяем, что сессии шевелений доступны через связь
        self.assertEqual(len(self.test_user.kicks), 3)
    
    def test_child_sleep_relationship(self):
        """Тест связи между моделями Child и SleepSession."""
        # Создаем несколько сессий сна для тестового ребенка
        for i in range(3):
            sleep = SleepSession(
                child_id=self.test_child.id,
                start_time=datetime.utcnow() - timedelta(days=i),
                end_time=datetime.utcnow() - timedelta(days=i) + timedelta(hours=3),
                type='day' if i % 2 == 0 else 'night'
            )
            self.session.add(sleep)
        self.session.commit()
        
        # Обновляем ребенка из базы данных
        self.session.refresh(self.test_child)
        
        # Проверяем, что сессии сна доступны через связь
        self.assertEqual(len(self.test_child.sleep_sessions), 3)
    
    def test_cascade_delete(self):
        """Тест каскадного удаления связанных записей."""
        # Создаем сессию схваток с событиями
        contraction = Contraction(user_id=self.test_user.id)
        self.session.add(contraction)
        self.session.commit()
        
        for i in range(5):
            event = ContractionEvent(session_id=contraction.id)
            self.session.add(event)
        self.session.commit()
        
        # Проверяем, что события созданы
        events_count = self.session.query(ContractionEvent).filter_by(session_id=contraction.id).count()
        self.assertEqual(events_count, 5)
        
        # Удаляем сессию схваток
        self.session.delete(contraction)
        self.session.commit()
        
        # Проверяем, что события также были удалены
        events_count = self.session.query(ContractionEvent).filter_by(session_id=contraction.id).count()
        self.assertEqual(events_count, 0)


if __name__ == '__main__':
    unittest.main()