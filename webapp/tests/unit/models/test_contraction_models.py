"""
Тесты для моделей счетчика схваток.

Этот модуль содержит тесты для моделей Contraction и ContractionEvent и связанных функций.
"""

import unittest
from datetime import datetime, timedelta
from botapp.models import db_manager, User
from botapp.models_timers import (
    Contraction, ContractionEvent,
    get_contraction_sessions, create_contraction_session,
    end_contraction_session, add_contraction_event
)


class ContractionModelTestCase(unittest.TestCase):
    """Тестовый случай для моделей Contraction и ContractionEvent и связанных функций."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        # Создаем сессию
        self.session = db_manager.get_session()
        
        # Создаем тестового пользователя
        self.user = User(
            telegram_id=123456789,
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        self.session.add(self.user)
        self.session.commit()
        self.session.refresh(self.user)
        
        # Создаем тестовую сессию схваток
        self.contraction = Contraction(
            user_id=self.user.id,
            start_time=datetime.utcnow() - timedelta(hours=1),
            notes='Тестовая сессия схваток'
        )
        self.session.add(self.contraction)
        self.session.commit()
        self.session.refresh(self.contraction)
        
        # Создаем тестовые события схваток
        self.events = []
        for i in range(3):
            event = ContractionEvent(
                session_id=self.contraction.id,
                timestamp=datetime.utcnow() - timedelta(minutes=50 - i*10),
                duration=30 + i*10,  # 30, 40, 50 секунд
                intensity=5 + i  # 5, 6, 7 из 10
            )
            self.session.add(event)
            self.events.append(event)
        self.session.commit()
        for event in self.events:
            self.session.refresh(event)
    
    def tearDown(self):
        """Очистка тестовых данных."""
        # Удаляем тестовые события схваток
        for event in self.events:
            event_obj = self.session.query(ContractionEvent).filter_by(id=event.id).first()
            if event_obj:
                self.session.delete(event_obj)
        
        # Удаляем тестовую сессию схваток
        contraction = self.session.query(Contraction).filter_by(id=self.contraction.id).first()
        if contraction:
            self.session.delete(contraction)
        
        # Удаляем тестового пользователя
        user = self.session.query(User).filter_by(id=self.user.id).first()
        if user:
            self.session.delete(user)
        
        self.session.commit()
        db_manager.close_session(self.session)
    
    def test_create_contraction_session(self):
        """Тест создания сессии схваток."""
        # Создаем новую сессию схваток
        new_contraction = create_contraction_session(
            user_id=self.user.id,
            notes='Новая тестовая сессия схваток'
        )
        
        # Проверяем, что сессия была создана
        self.assertIsNotNone(new_contraction)
        self.assertEqual(new_contraction.user_id, self.user.id)
        self.assertEqual(new_contraction.notes, 'Новая тестовая сессия схваток')
        self.assertIsNone(new_contraction.end_time)
        
        # Проверяем, что сессия есть в базе данных
        session = db_manager.get_session()
        try:
            contraction_from_db = session.query(Contraction).filter_by(id=new_contraction.id).first()
            self.assertIsNotNone(contraction_from_db)
            
            # Удаляем созданную сессию
            session.delete(contraction_from_db)
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_contraction_sessions(self):
        """Тест получения сессий схваток пользователя."""
        # Создаем дополнительную сессию схваток
        additional_contraction = create_contraction_session(
            user_id=self.user.id,
            notes='Дополнительная сессия схваток'
        )
        
        # Получаем все сессии схваток пользователя
        contractions = get_contraction_sessions(self.user.id)
        
        # Проверяем, что получены обе сессии
        self.assertEqual(len(contractions), 2)
        
        # Проверяем, что сессии отсортированы по времени начала (сначала новые)
        self.assertEqual(contractions[0].id, additional_contraction.id)
        
        # Удаляем дополнительную сессию
        session = db_manager.get_session()
        try:
            contraction_from_db = session.query(Contraction).filter_by(id=additional_contraction.id).first()
            if contraction_from_db:
                session.delete(contraction_from_db)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_end_contraction_session(self):
        """Тест завершения сессии схваток."""
        # Завершаем сессию схваток
        updated_contraction = end_contraction_session(self.contraction.id)
        
        # Проверяем, что сессия завершена
        self.assertIsNotNone(updated_contraction.end_time)
        
        # Проверяем расчет продолжительности
        self.assertIsNotNone(updated_contraction.duration)
        self.assertGreater(updated_contraction.duration, 0)
    
    def test_add_contraction_event(self):
        """Тест добавления события схватки."""
        # Добавляем новое событие схватки
        new_event = add_contraction_event(
            session_id=self.contraction.id,
            duration=60,
            intensity=8
        )
        
        # Проверяем, что событие было создано
        self.assertIsNotNone(new_event)
        self.assertEqual(new_event.session_id, self.contraction.id)
        self.assertEqual(new_event.duration, 60)
        self.assertEqual(new_event.intensity, 8)
        
        # Проверяем, что событие есть в базе данных
        session = db_manager.get_session()
        try:
            event_from_db = session.query(ContractionEvent).filter_by(id=new_event.id).first()
            self.assertIsNotNone(event_from_db)
            
            # Удаляем созданное событие
            session.delete(event_from_db)
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_contraction_properties(self):
        """Тест свойств модели Contraction."""
        # Завершаем сессию для тестирования свойств
        self.contraction.end_time = datetime.utcnow()
        self.session.commit()
        self.session.refresh(self.contraction)
        
        # Проверяем свойство count
        self.assertEqual(self.contraction.count, 3)
        
        # Проверяем свойство duration
        self.assertIsNotNone(self.contraction.duration)
        self.assertGreater(self.contraction.duration, 0)
        
        # Проверяем свойство average_interval
        self.assertIsNotNone(self.contraction.average_interval)
        self.assertGreater(self.contraction.average_interval, 0)


if __name__ == '__main__':
    unittest.main()