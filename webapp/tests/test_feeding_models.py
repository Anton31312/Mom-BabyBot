"""
Тесты для моделей отслеживания кормления.

Этот модуль содержит тесты для модели FeedingSession и связанных функций.
"""

import unittest
from datetime import datetime, timedelta
from botapp.models import db_manager, User
from botapp.models_child import Child
from botapp.models_timers import FeedingSession


class FeedingModelTestCase(unittest.TestCase):
    """Тестовый случай для модели FeedingSession и связанных функций."""
    
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
        
        # Создаем тестовую сессию кормления грудью
        self.breast_feeding = FeedingSession(
            child_id=self.child.id,
            timestamp=datetime.utcnow() - timedelta(hours=3),
            type='breast',
            duration=20,
            breast='left',
            notes='Тестовое кормление грудью'
        )
        self.session.add(self.breast_feeding)
        
        # Создаем тестовую сессию кормления из бутылочки
        self.bottle_feeding = FeedingSession(
            child_id=self.child.id,
            timestamp=datetime.utcnow() - timedelta(hours=6),
            type='bottle',
            amount=120,
            milk_type='formula',
            notes='Тестовое кормление из бутылочки'
        )
        self.session.add(self.bottle_feeding)
        
        self.session.commit()
        self.session.refresh(self.breast_feeding)
        self.session.refresh(self.bottle_feeding)
    
    def tearDown(self):
        """Очистка тестовых данных."""
        # Удаляем тестовые сессии кормления
        breast_feeding = self.session.query(FeedingSession).filter_by(id=self.breast_feeding.id).first()
        if breast_feeding:
            self.session.delete(breast_feeding)
        
        bottle_feeding = self.session.query(FeedingSession).filter_by(id=self.bottle_feeding.id).first()
        if bottle_feeding:
            self.session.delete(bottle_feeding)
        
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
    
    def test_create_breast_feeding(self):
        """Тест создания сессии кормления грудью."""
        # Создаем новую сессию кормления грудью
        new_feeding = FeedingSession(
            child_id=self.child.id,
            timestamp=datetime.utcnow(),
            type='breast',
            duration=25,
            breast='right',
            notes='Новое тестовое кормление грудью'
        )
        self.session.add(new_feeding)
        self.session.commit()
        self.session.refresh(new_feeding)
        
        # Проверяем, что сессия была создана
        self.assertIsNotNone(new_feeding.id)
        self.assertEqual(new_feeding.child_id, self.child.id)
        self.assertEqual(new_feeding.type, 'breast')
        self.assertEqual(new_feeding.duration, 25)
        self.assertEqual(new_feeding.breast, 'right')
        self.assertEqual(new_feeding.notes, 'Новое тестовое кормление грудью')
        
        # Удаляем созданную сессию
        self.session.delete(new_feeding)
        self.session.commit()
    
    def test_create_bottle_feeding(self):
        """Тест создания сессии кормления из бутылочки."""
        # Создаем новую сессию кормления из бутылочки
        new_feeding = FeedingSession(
            child_id=self.child.id,
            timestamp=datetime.utcnow(),
            type='bottle',
            amount=150,
            milk_type='expressed',
            notes='Новое тестовое кормление из бутылочки'
        )
        self.session.add(new_feeding)
        self.session.commit()
        self.session.refresh(new_feeding)
        
        # Проверяем, что сессия была создана
        self.assertIsNotNone(new_feeding.id)
        self.assertEqual(new_feeding.child_id, self.child.id)
        self.assertEqual(new_feeding.type, 'bottle')
        self.assertEqual(new_feeding.amount, 150)
        self.assertEqual(new_feeding.milk_type, 'expressed')
        self.assertEqual(new_feeding.notes, 'Новое тестовое кормление из бутылочки')
        
        # Удаляем созданную сессию
        self.session.delete(new_feeding)
        self.session.commit()
    
    def test_get_feeding_sessions(self):
        """Тест получения сессий кормления ребенка."""
        # Получаем все сессии кормления ребенка
        feeding_sessions = self.session.query(FeedingSession).filter_by(child_id=self.child.id).all()
        
        # Проверяем, что получены обе сессии
        self.assertEqual(len(feeding_sessions), 2)
        
        # Проверяем, что есть сессия кормления грудью
        breast_sessions = [fs for fs in feeding_sessions if fs.type == 'breast']
        self.assertEqual(len(breast_sessions), 1)
        self.assertEqual(breast_sessions[0].id, self.breast_feeding.id)
        
        # Проверяем, что есть сессия кормления из бутылочки
        bottle_sessions = [fs for fs in feeding_sessions if fs.type == 'bottle']
        self.assertEqual(len(bottle_sessions), 1)
        self.assertEqual(bottle_sessions[0].id, self.bottle_feeding.id)
    
    def test_update_feeding_session(self):
        """Тест обновления сессии кормления."""
        # Обновляем сессию кормления грудью
        self.breast_feeding.duration = 30
        self.breast_feeding.breast = 'both'
        self.breast_feeding.notes = 'Обновленное тестовое кормление грудью'
        self.session.commit()
        self.session.refresh(self.breast_feeding)
        
        # Проверяем, что данные обновлены
        self.assertEqual(self.breast_feeding.duration, 30)
        self.assertEqual(self.breast_feeding.breast, 'both')
        self.assertEqual(self.breast_feeding.notes, 'Обновленное тестовое кормление грудью')
    
    def test_delete_feeding_session(self):
        """Тест удаления сессии кормления."""
        # Создаем сессию для удаления
        feeding_to_delete = FeedingSession(
            child_id=self.child.id,
            timestamp=datetime.utcnow(),
            type='breast',
            duration=15,
            breast='left',
            notes='Сессия для удаления'
        )
        self.session.add(feeding_to_delete)
        self.session.commit()
        self.session.refresh(feeding_to_delete)
        
        # Удаляем сессию
        self.session.delete(feeding_to_delete)
        self.session.commit()
        
        # Проверяем, что сессия удалена
        deleted_feeding = self.session.query(FeedingSession).filter_by(id=feeding_to_delete.id).first()
        self.assertIsNone(deleted_feeding)


if __name__ == '__main__':
    unittest.main()