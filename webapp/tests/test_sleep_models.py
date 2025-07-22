"""
Тесты для моделей таймера сна.

Этот модуль содержит тесты для модели SleepSession и связанных функций.
"""

import unittest
from datetime import datetime, timedelta
from botapp.models import db_manager, User
from botapp.models_child import Child
from botapp.models_timers import (
    SleepSession,
    get_sleep_sessions, create_sleep_session, end_sleep_session
)


class SleepModelTestCase(unittest.TestCase):
    """Тестовый случай для модели SleepSession и связанных функций."""
    
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
        
        # Создаем тестового ребенка
        self.child = Child(
            user_id=self.user.id,
            name='Test Child',
            birth_date=datetime.utcnow() - timedelta(days=180),  # 6 месяцев
            gender='male'
        )
        self.session.add(self.child)
        self.session.commit()
        self.session.refresh(self.child)
        
        # Создаем тестовую сессию сна
        self.sleep_session = SleepSession(
            child_id=self.child.id,
            start_time=datetime.utcnow() - timedelta(hours=2),
            type='day',
            quality=4,
            notes='Тестовая сессия сна'
        )
        self.session.add(self.sleep_session)
        self.session.commit()
        self.session.refresh(self.sleep_session)
    
    def tearDown(self):
        """Очистка тестовых данных."""
        # Удаляем тестовую сессию сна
        sleep_session = self.session.query(SleepSession).filter_by(id=self.sleep_session.id).first()
        if sleep_session:
            self.session.delete(sleep_session)
        
        # Удаляем тестового ребенка
        child = self.session.query(Child).filter_by(id=self.child.id).first()
        if child:
            self.session.delete(child)
        
        # Удаляем тестового пользователя
        user = self.session.query(User).filter_by(id=self.user.id).first()
        if user:
            self.session.delete(user)
        
        self.session.commit()
        db_manager.close_session(self.session)
    
    def test_create_sleep_session(self):
        """Тест создания сессии сна."""
        # Создаем новую сессию сна
        new_sleep_session = create_sleep_session(
            child_id=self.child.id,
            type='night',
            quality=5,
            notes='Новая тестовая сессия сна'
        )
        
        # Проверяем, что сессия была создана
        self.assertIsNotNone(new_sleep_session)
        self.assertEqual(new_sleep_session.child_id, self.child.id)
        self.assertEqual(new_sleep_session.type, 'night')
        self.assertEqual(new_sleep_session.quality, 5)
        self.assertEqual(new_sleep_session.notes, 'Новая тестовая сессия сна')
        self.assertIsNone(new_sleep_session.end_time)
        
        # Проверяем, что сессия есть в базе данных
        session = db_manager.get_session()
        try:
            sleep_session_from_db = session.query(SleepSession).filter_by(id=new_sleep_session.id).first()
            self.assertIsNotNone(sleep_session_from_db)
            
            # Удаляем созданную сессию
            session.delete(sleep_session_from_db)
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_sleep_sessions(self):
        """Тест получения сессий сна ребенка."""
        # Создаем дополнительную сессию сна
        additional_sleep_session = create_sleep_session(
            child_id=self.child.id,
            type='night',
            notes='Дополнительная сессия сна'
        )
        
        # Получаем все сессии сна ребенка
        sleep_sessions = get_sleep_sessions(self.child.id)
        
        # Проверяем, что получены обе сессии
        self.assertEqual(len(sleep_sessions), 2)
        
        # Проверяем, что сессии отсортированы по времени начала (сначала новые)
        self.assertEqual(sleep_sessions[0].id, additional_sleep_session.id)
        
        # Удаляем дополнительную сессию
        session = db_manager.get_session()
        try:
            sleep_session_from_db = session.query(SleepSession).filter_by(id=additional_sleep_session.id).first()
            if sleep_session_from_db:
                session.delete(sleep_session_from_db)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_end_sleep_session(self):
        """Тест завершения сессии сна."""
        # Завершаем сессию сна
        updated_sleep_session = end_sleep_session(
            session_id=self.sleep_session.id,
            quality=5
        )
        
        # Проверяем, что сессия завершена
        self.assertIsNotNone(updated_sleep_session.end_time)
        self.assertEqual(updated_sleep_session.quality, 5)
        
        # Проверяем расчет продолжительности
        self.assertIsNotNone(updated_sleep_session.duration)
        self.assertGreater(updated_sleep_session.duration, 0)
    
    def test_sleep_session_properties(self):
        """Тест свойств модели SleepSession."""
        # Завершаем сессию для тестирования свойств
        self.sleep_session.end_time = datetime.utcnow()
        self.session.commit()
        self.session.refresh(self.sleep_session)
        
        # Проверяем свойство duration
        self.assertIsNotNone(self.sleep_session.duration)
        self.assertGreater(self.sleep_session.duration, 0)
        
        # Проверяем, что продолжительность примерно 2 часа (с погрешностью)
        self.assertAlmostEqual(self.sleep_session.duration, 120, delta=10)


if __name__ == '__main__':
    unittest.main()