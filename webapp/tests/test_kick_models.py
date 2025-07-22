"""
Тесты для моделей счетчика шевелений.

Этот модуль содержит тесты для моделей Kick и KickEvent и связанных функций.
"""

import unittest
from datetime import datetime, timedelta
from botapp.models import db_manager, User
from botapp.models_timers import (
    Kick, KickEvent,
    get_kick_sessions, create_kick_session,
    end_kick_session, add_kick_event
)


class KickModelTestCase(unittest.TestCase):
    """Тестовый случай для моделей Kick и KickEvent и связанных функций."""
    
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
        
        # Создаем тестовую сессию шевелений
        self.kick = Kick(
            user_id=self.user.id,
            start_time=datetime.utcnow() - timedelta(hours=1),
            notes='Тестовая сессия шевелений'
        )
        self.session.add(self.kick)
        self.session.commit()
        self.session.refresh(self.kick)
        
        # Создаем тестовые события шевелений
        self.events = []
        for i in range(3):
            event = KickEvent(
                session_id=self.kick.id,
                timestamp=datetime.utcnow() - timedelta(minutes=50 - i*10),
                intensity=5 + i  # 5, 6, 7 из 10
            )
            self.session.add(event)
            self.events.append(event)
        self.session.commit()
        for event in self.events:
            self.session.refresh(event)
    
    def tearDown(self):
        """Очистка тестовых данных."""
        # Удаляем тестовые события шевелений
        for event in self.events:
            event_obj = self.session.query(KickEvent).filter_by(id=event.id).first()
            if event_obj:
                self.session.delete(event_obj)
        
        # Удаляем тестовую сессию шевелений
        kick = self.session.query(Kick).filter_by(id=self.kick.id).first()
        if kick:
            self.session.delete(kick)
        
        # Удаляем тестового пользователя
        user = self.session.query(User).filter_by(id=self.user.id).first()
        if user:
            self.session.delete(user)
        
        self.session.commit()
        db_manager.close_session(self.session)
    
    def test_create_kick_session(self):
        """Тест создания сессии шевелений."""
        # Создаем новую сессию шевелений
        new_kick = create_kick_session(
            user_id=self.user.id,
            notes='Новая тестовая сессия шевелений'
        )
        
        # Проверяем, что сессия была создана
        self.assertIsNotNone(new_kick)
        self.assertEqual(new_kick.user_id, self.user.id)
        self.assertEqual(new_kick.notes, 'Новая тестовая сессия шевелений')
        self.assertIsNone(new_kick.end_time)
        
        # Проверяем, что сессия есть в базе данных
        session = db_manager.get_session()
        try:
            kick_from_db = session.query(Kick).filter_by(id=new_kick.id).first()
            self.assertIsNotNone(kick_from_db)
            
            # Удаляем созданную сессию
            session.delete(kick_from_db)
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_kick_sessions(self):
        """Тест получения сессий шевелений пользователя."""
        # Создаем дополнительную сессию шевелений
        additional_kick = create_kick_session(
            user_id=self.user.id,
            notes='Дополнительная сессия шевелений'
        )
        
        # Получаем все сессии шевелений пользователя
        kicks = get_kick_sessions(self.user.id)
        
        # Проверяем, что получены обе сессии
        self.assertEqual(len(kicks), 2)
        
        # Проверяем, что сессии отсортированы по времени начала (сначала новые)
        self.assertEqual(kicks[0].id, additional_kick.id)
        
        # Удаляем дополнительную сессию
        session = db_manager.get_session()
        try:
            kick_from_db = session.query(Kick).filter_by(id=additional_kick.id).first()
            if kick_from_db:
                session.delete(kick_from_db)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_end_kick_session(self):
        """Тест завершения сессии шевелений."""
        # Завершаем сессию шевелений
        updated_kick = end_kick_session(self.kick.id)
        
        # Проверяем, что сессия завершена
        self.assertIsNotNone(updated_kick.end_time)
        
        # Проверяем расчет продолжительности
        self.assertIsNotNone(updated_kick.duration)
        self.assertGreater(updated_kick.duration, 0)
    
    def test_add_kick_event(self):
        """Тест добавления события шевеления."""
        # Добавляем новое событие шевеления
        new_event = add_kick_event(
            session_id=self.kick.id,
            intensity=8
        )
        
        # Проверяем, что событие было создано
        self.assertIsNotNone(new_event)
        self.assertEqual(new_event.session_id, self.kick.id)
        self.assertEqual(new_event.intensity, 8)
        
        # Проверяем, что событие есть в базе данных
        session = db_manager.get_session()
        try:
            event_from_db = session.query(KickEvent).filter_by(id=new_event.id).first()
            self.assertIsNotNone(event_from_db)
            
            # Удаляем созданное событие
            session.delete(event_from_db)
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_kick_properties(self):
        """Тест свойств модели Kick."""
        # Завершаем сессию для тестирования свойств
        self.kick.end_time = datetime.utcnow()
        self.session.commit()
        self.session.refresh(self.kick)
        
        # Проверяем свойство count
        self.assertEqual(self.kick.count, 3)
        
        # Проверяем свойство duration
        self.assertIsNotNone(self.kick.duration)
        self.assertGreater(self.kick.duration, 0)


if __name__ == '__main__':
    unittest.main()