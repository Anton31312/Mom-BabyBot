"""
Тесты для SQLAlchemy моделей в Django контексте
"""
import os
from datetime import datetime, timedelta
from django.test import TestCase
from unittest.mock import patch, MagicMock

from .models import User, db_manager, get_user, create_user, update_user, delete_user


class SQLAlchemyModelTestCase(TestCase):
    """Базовый класс для тестов SQLAlchemy моделей"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        # Настраиваем тестовую базу данных в памяти
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        
        # Пересоздаем менеджер БД для тестов
        db_manager._setup_engine()
        db_manager.create_tables()
    
    def tearDown(self):
        """Очистка после тестов"""
        # Очищаем базу данных
        session = db_manager.get_session()
        try:
            session.query(User).delete()
            session.commit()
        finally:
            db_manager.close_session(session)


class UserModelTests(SQLAlchemyModelTestCase):
    """Тесты для модели User"""
    
    def test_user_creation_basic(self):
        """Тест создания базового пользователя"""
        session = db_manager.get_session()
        try:
            user = User(
                telegram_id=123456789,
                username='testuser',
                first_name='Test',
                last_name='User'
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            self.assertIsNotNone(user.id)
            self.assertEqual(user.telegram_id, 123456789)
            self.assertEqual(user.username, 'testuser')
            self.assertEqual(user.first_name, 'Test')
            self.assertEqual(user.last_name, 'User')
            self.assertFalse(user.is_pregnant)  # default value
            self.assertFalse(user.is_premium)  # default value
            self.assertFalse(user.is_admin)    # default value
            self.assertIsNotNone(user.created_at)
            self.assertIsNotNone(user.updated_at)
            
        finally:
            db_manager.close_session(session)
    
    def test_user_creation_pregnant(self):
        """Тест создания беременной пользовательницы"""
        session = db_manager.get_session()
        try:
            user = User(
                telegram_id=987654321,
                username='pregnant_user',
                is_pregnant=True,
                pregnancy_week=20
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            self.assertTrue(user.is_pregnant)
            self.assertEqual(user.pregnancy_week, 20)
            self.assertIsNone(user.baby_birth_date)
            
        finally:
            db_manager.close_session(session)
    
    def test_user_creation_with_baby(self):
        """Тест создания пользовательницы с ребенком"""
        birth_date = datetime(2023, 6, 1, 10, 30)
        session = db_manager.get_session()
        try:
            user = User(
                telegram_id=555666777,
                username='mom_user',
                is_pregnant=False,
                baby_birth_date=birth_date
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            self.assertFalse(user.is_pregnant)
            self.assertEqual(user.baby_birth_date, birth_date)
            self.assertIsNone(user.pregnancy_week)
            
        finally:
            db_manager.close_session(session)
    
    def test_user_unique_telegram_id(self):
        """Тест уникальности telegram_id"""
        session = db_manager.get_session()
        try:
            # Создаем первого пользователя
            user1 = User(telegram_id=111222333, username='user1')
            session.add(user1)
            session.commit()
            
            # Пытаемся создать второго пользователя с тем же telegram_id
            user2 = User(telegram_id=111222333, username='user2')
            session.add(user2)
            
            with self.assertRaises(Exception):  # Должна возникнуть ошибка уникальности
                session.commit()
                
        finally:
            session.rollback()
            db_manager.close_session(session)
    
    def test_user_repr(self):
        """Тест строкового представления пользователя"""
        user = User(telegram_id=123456789)
        self.assertEqual(repr(user), '<User 123456789>')
    
    def test_user_updated_at_auto_update(self):
        """Тест автоматического обновления updated_at"""
        session = db_manager.get_session()
        try:
            user = User(telegram_id=123456789, username='testuser')
            session.add(user)
            session.commit()
            session.refresh(user)
            
            original_updated_at = user.updated_at
            
            # Небольшая задержка для различия времени
            import time
            time.sleep(0.01)
            
            # Обновляем пользователя
            user.username = 'updated_user'
            session.commit()
            session.refresh(user)
            
            self.assertGreater(user.updated_at, original_updated_at)
            
        finally:
            db_manager.close_session(session)


class SQLAlchemyManagerTests(SQLAlchemyModelTestCase):
    """Тесты для SQLAlchemyManager"""
    
    def test_manager_initialization(self):
        """Тест инициализации менеджера"""
        self.assertIsNotNone(db_manager.engine)
        self.assertIsNotNone(db_manager.Session)
    
    def test_get_session(self):
        """Тест получения сессии"""
        session = db_manager.get_session()
        self.assertIsNotNone(session)
        db_manager.close_session(session)
    
    def test_create_tables(self):
        """Тест создания таблиц"""
        # Таблицы уже созданы в setUp, проверяем что можем создать пользователя
        session = db_manager.get_session()
        try:
            user = User(telegram_id=123456789)
            session.add(user)
            session.commit()
            
            # Если дошли до сюда, значит таблицы созданы корректно
            self.assertTrue(True)
            
        finally:
            db_manager.close_session(session)
    
    def test_session_management(self):
        """Тест управления сессиями"""
        session1 = db_manager.get_session()
        session2 = db_manager.get_session()
        
        # Сессии должны быть разными объектами
        self.assertIsNot(session1, session2)
        
        db_manager.close_session(session1)
        db_manager.close_session(session2)


class UserUtilityFunctionsTests(SQLAlchemyModelTestCase):
    """Тесты для утилитарных функций работы с пользователями"""
    
    def test_create_user_function(self):
        """Тест функции создания пользователя"""
        user = create_user(
            telegram_id=123456789,
            username='testuser',
            first_name='Test',
            is_pregnant=True,
            pregnancy_week=15
        )
        
        self.assertIsNotNone(user.id)
        self.assertEqual(user.telegram_id, 123456789)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertTrue(user.is_pregnant)
        self.assertEqual(user.pregnancy_week, 15)
    
    def test_create_user_with_kwargs(self):
        """Тест создания пользователя с дополнительными параметрами"""
        birth_date = datetime(2023, 5, 1)
        user = create_user(
            telegram_id=987654321,
            username='mom_user',
            baby_birth_date=birth_date,
            is_premium=True
        )
        
        self.assertEqual(user.baby_birth_date, birth_date)
        self.assertTrue(user.is_premium)
    
    def test_get_user_existing(self):
        """Тест получения существующего пользователя"""
        # Создаем пользователя
        created_user = create_user(telegram_id=123456789, username='testuser')
        
        # Получаем пользователя
        import asyncio
        retrieved_user = asyncio.run(get_user(123456789))
        
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.telegram_id, created_user.telegram_id)
        self.assertEqual(retrieved_user.username, created_user.username)
    
    def test_get_user_nonexistent(self):
        """Тест получения несуществующего пользователя"""
        import asyncio
        user = asyncio.run(get_user(999999999))
        
        self.assertIsNone(user)
    
    def test_update_user_existing(self):
        """Тест обновления существующего пользователя"""
        # Создаем пользователя
        create_user(telegram_id=123456789, username='testuser', is_pregnant=False)
        
        # Обновляем пользователя
        updated_user = update_user(
            telegram_id=123456789,
            is_pregnant=True,
            pregnancy_week=25,
            is_premium=True
        )
        
        self.assertIsNotNone(updated_user)
        self.assertTrue(updated_user.is_pregnant)
        self.assertEqual(updated_user.pregnancy_week, 25)
        self.assertTrue(updated_user.is_premium)
    
    def test_update_user_nonexistent(self):
        """Тест обновления несуществующего пользователя"""
        updated_user = update_user(
            telegram_id=999999999,
            username='nonexistent'
        )
        
        self.assertIsNone(updated_user)
    
    def test_update_user_invalid_field(self):
        """Тест обновления пользователя с невалидным полем"""
        # Создаем пользователя
        create_user(telegram_id=123456789, username='testuser')
        
        # Пытаемся обновить несуществующее поле
        updated_user = update_user(
            telegram_id=123456789,
            nonexistent_field='value',
            username='updated_user'  # валидное поле
        )
        
        # Пользователь должен быть обновлен, но только валидные поля
        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user.username, 'updated_user')
        self.assertFalse(hasattr(updated_user, 'nonexistent_field'))
    
    def test_delete_user_existing(self):
        """Тест удаления существующего пользователя"""
        # Создаем пользователя
        create_user(telegram_id=123456789, username='testuser')
        
        # Удаляем пользователя
        result = delete_user(123456789)
        
        self.assertTrue(result)
        
        # Проверяем, что пользователь действительно удален
        import asyncio
        deleted_user = asyncio.run(get_user(123456789))
        self.assertIsNone(deleted_user)
    
    def test_delete_user_nonexistent(self):
        """Тест удаления несуществующего пользователя"""
        result = delete_user(999999999)
        self.assertFalse(result)


class DatabaseTransactionTests(SQLAlchemyModelTestCase):
    """Тесты транзакций базы данных"""
    
    def test_transaction_rollback_on_error(self):
        """Тест отката транзакции при ошибке"""
        session = db_manager.get_session()
        try:
            # Создаем пользователя
            user1 = User(telegram_id=123456789, username='user1')
            session.add(user1)
            session.commit()
            
            # Начинаем новую транзакцию
            user2 = User(telegram_id=987654321, username='user2')
            session.add(user2)
            
            # Пытаемся добавить пользователя с дублирующимся telegram_id
            user3 = User(telegram_id=123456789, username='duplicate')  # Дубликат
            session.add(user3)
            
            with self.assertRaises(Exception):
                session.commit()
            
            # После ошибки делаем rollback
            session.rollback()
            
            # Проверяем, что user2 не был сохранен из-за rollback
            users = session.query(User).all()
            self.assertEqual(len(users), 1)  # Только user1
            self.assertEqual(users[0].username, 'user1')
            
        finally:
            db_manager.close_session(session)
    
    def test_create_user_function_rollback(self):
        """Тест отката в функции create_user при ошибке"""
        # Создаем первого пользователя
        create_user(telegram_id=123456789, username='user1')
        
        # Пытаемся создать пользователя с дублирующимся telegram_id
        with self.assertRaises(Exception):
            create_user(telegram_id=123456789, username='duplicate')
        
        # Проверяем, что в базе остался только первый пользователь
        session = db_manager.get_session()
        try:
            users = session.query(User).all()
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0].username, 'user1')
        finally:
            db_manager.close_session(session)
    
    def test_update_user_function_rollback(self):
        """Тест отката в функции update_user при ошибке"""
        # Создаем пользователя
        create_user(telegram_id=123456789, username='testuser')
        
        # Мокаем ошибку в процессе обновления
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Настраиваем мок для возврата пользователя
            mock_user = MagicMock()
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
            
            # Настраиваем ошибку при commit
            mock_session.commit.side_effect = Exception("Database error")
            
            with self.assertRaises(Exception):
                update_user(telegram_id=123456789, username='updated')
            
            # Проверяем, что rollback был вызван
            mock_session.rollback.assert_called_once()


class DatabaseConnectionTests(SQLAlchemyModelTestCase):
    """Тесты подключения к базе данных"""
    
    def test_database_url_from_environment(self):
        """Тест использования DATABASE_URL из переменных окружения"""
        test_url = 'sqlite:///test_custom.db'
        
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            # Создаем новый менеджер для тестирования
            from .models import SQLAlchemyManager
            test_manager = SQLAlchemyManager()
            
            # Проверяем, что URL был использован
            self.assertIn('test_custom.db', str(test_manager.engine.url))
    
    def test_default_database_url(self):
        """Тест использования дефолтного DATABASE_URL"""
        # Временно удаляем DATABASE_URL из окружения
        original_url = os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        try:
            from .models import SQLAlchemyManager
            test_manager = SQLAlchemyManager()
            
            # Проверяем, что используется дефолтный URL
            self.assertIn('mom_baby_bot.db', str(test_manager.engine.url))
            
        finally:
            # Восстанавливаем оригинальное значение
            if original_url:
                os.environ['DATABASE_URL'] = original_url


class ModelIntegrationTests(SQLAlchemyModelTestCase):
    """Интеграционные тесты моделей"""
    
    def test_full_user_lifecycle(self):
        """Тест полного жизненного цикла пользователя"""
        telegram_id = 123456789
        
        # 1. Создание пользователя
        user = create_user(
            telegram_id=telegram_id,
            username='lifecycle_user',
            first_name='Test',
            is_pregnant=True,
            pregnancy_week=10
        )
        
        self.assertIsNotNone(user.id)
        self.assertEqual(user.telegram_id, telegram_id)
        self.assertTrue(user.is_pregnant)
        self.assertEqual(user.pregnancy_week, 10)
        
        # 2. Получение пользователя
        import asyncio
        retrieved_user = asyncio.run(get_user(telegram_id))
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.id, user.id)
        
        # 3. Обновление пользователя
        updated_user = update_user(
            telegram_id=telegram_id,
            pregnancy_week=30,
            is_premium=True
        )
        
        self.assertEqual(updated_user.pregnancy_week, 30)
        self.assertTrue(updated_user.is_premium)
        
        # 4. Удаление пользователя
        delete_result = delete_user(telegram_id)
        self.assertTrue(delete_result)
        
        # 5. Проверка, что пользователь удален
        deleted_user = asyncio.run(get_user(telegram_id))
        self.assertIsNone(deleted_user)
    
    def test_multiple_users_management(self):
        """Тест управления несколькими пользователями"""
        # Создаем несколько пользователей
        users_data = [
            {'telegram_id': 111111111, 'username': 'user1', 'is_pregnant': True},
            {'telegram_id': 222222222, 'username': 'user2', 'is_pregnant': False},
            {'telegram_id': 333333333, 'username': 'user3', 'is_premium': True},
        ]
        
        created_users = []
        for data in users_data:
            user = create_user(**data)
            created_users.append(user)
        
        # Проверяем, что все пользователи созданы
        session = db_manager.get_session()
        try:
            all_users = session.query(User).all()
            self.assertEqual(len(all_users), 3)
            
            # Проверяем конкретных пользователей
            user1 = session.query(User).filter_by(telegram_id=111111111).first()
            self.assertTrue(user1.is_pregnant)
            
            user2 = session.query(User).filter_by(telegram_id=222222222).first()
            self.assertFalse(user2.is_pregnant)
            
            user3 = session.query(User).filter_by(telegram_id=333333333).first()
            self.assertTrue(user3.is_premium)
            
        finally:
            db_manager.close_session(session)
    
    def test_concurrent_operations(self):
        """Тест одновременных операций с базой данных"""
        # Создаем пользователя
        create_user(telegram_id=123456789, username='concurrent_user')
        
        # Симулируем одновременные операции с разными сессиями
        session1 = db_manager.get_session()
        session2 = db_manager.get_session()
        
        try:
            # Получаем пользователя в обеих сессиях
            user1 = session1.query(User).filter_by(telegram_id=123456789).first()
            user2 = session2.query(User).filter_by(telegram_id=123456789).first()
            
            self.assertIsNotNone(user1)
            self.assertIsNotNone(user2)
            self.assertEqual(user1.telegram_id, user2.telegram_id)
            
            # Обновляем в разных сессиях
            user1.username = 'updated_by_session1'
            user2.is_premium = True
            
            session1.commit()
            session2.commit()
            
            # Проверяем финальное состояние
            session3 = db_manager.get_session()
            try:
                final_user = session3.query(User).filter_by(telegram_id=123456789).first()
                # Последнее изменение должно быть сохранено
                self.assertTrue(final_user.is_premium)
            finally:
                db_manager.close_session(session3)
                
        finally:
            db_manager.close_session(session1)
            db_manager.close_session(session2)