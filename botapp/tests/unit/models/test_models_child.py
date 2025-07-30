"""
Тесты для моделей профилей детей.

Этот модуль содержит тесты для моделей Child и Measurement.
"""

import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from botapp.models import Base, User
from botapp.models_child import Child, Measurement


class TestChildModels(unittest.TestCase):
    """Тестовые случаи для моделей Child и Measurement."""
    
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
            last_name='User'
        )
        self.session.add(self.test_user)
        self.session.commit()
    
    def tearDown(self):
        """Очистка после тестов."""
        self.session.close()
        Base.metadata.drop_all(self.engine)
    
    def test_create_child(self):
        """Тест создания профиля ребенка."""
        # Создаем ребенка
        child = Child(
            user_id=self.test_user.id,
            name='Test Child',
            birth_date=datetime.utcnow() - timedelta(days=365),  # 1 год
            gender='male'
        )
        self.session.add(child)
        self.session.commit()
        
        # Проверяем, что ребенок был создан
        saved_child = self.session.query(Child).filter_by(name='Test Child').first()
        self.assertIsNotNone(saved_child)
        self.assertEqual(saved_child.name, 'Test Child')
        self.assertEqual(saved_child.gender, 'male')
        self.assertEqual(saved_child.user_id, self.test_user.id)
    
    def test_child_age_calculation(self):
        """Тест свойств расчета возраста."""
        # Создаем ребенка с определенной датой рождения
        birth_date = datetime.utcnow() - timedelta(days=400)  # ~13 месяцев
        child = Child(
            user_id=self.test_user.id,
            name='Age Test Child',
            birth_date=birth_date
        )
        self.session.add(child)
        self.session.commit()
        
        # Тестируем свойство age_in_months
        self.assertAlmostEqual(child.age_in_months, 13, delta=1)  # Допускаем небольшую погрешность из-за расчетов дней
        
        # Тестируем свойство age_display
        self.assertIn('1 год', child.age_display)
    
    def test_create_measurement(self):
        """Тест создания измерений для ребенка."""
        # Создаем ребенка
        child = Child(
            user_id=self.test_user.id,
            name='Measurement Test Child'
        )
        self.session.add(child)
        self.session.commit()
        
        # Создаем измерение
        measurement = Measurement(
            child_id=child.id,
            height=75.5,
            weight=9.2,
            head_circumference=46.0,
            notes='Плановый осмотр'
        )
        self.session.add(measurement)
        self.session.commit()
        
        # Проверяем, что измерение было создано и связано с ребенком
        saved_measurement = self.session.query(Measurement).filter_by(child_id=child.id).first()
        self.assertIsNotNone(saved_measurement)
        self.assertEqual(saved_measurement.height, 75.5)
        self.assertEqual(saved_measurement.weight, 9.2)
        self.assertEqual(saved_measurement.head_circumference, 46.0)
        self.assertEqual(saved_measurement.notes, 'Плановый осмотр')
    
    def test_child_measurement_relationship(self):
        """Тест связи между моделями Child и Measurement."""
        # Создаем ребенка
        child = Child(
            user_id=self.test_user.id,
            name='Relationship Test Child'
        )
        self.session.add(child)
        self.session.commit()
        
        # Создаем несколько измерений
        for i in range(3):
            measurement = Measurement(
                child_id=child.id,
                height=70.0 + i,
                weight=8.0 + (i * 0.5),
                date=datetime.utcnow() - timedelta(days=i * 30)  # с интервалом в 30 дней
            )
            self.session.add(measurement)
        self.session.commit()
        
        # Проверяем, что измерения доступны через связь
        self.assertEqual(len(child.measurements), 3)
        
        # Проверяем каскадное удаление
        self.session.delete(child)
        self.session.commit()
        
        # Проверяем, что измерения также были удалены
        measurements = self.session.query(Measurement).filter_by(child_id=child.id).all()
        self.assertEqual(len(measurements), 0)
    
    def test_user_children_relationship(self):
        """Тест связи между моделями User и Child."""
        # Создаем несколько детей для тестового пользователя
        for i in range(3):
            child = Child(
                user_id=self.test_user.id,
                name=f'Ребенок {i+1}'
            )
            self.session.add(child)
        self.session.commit()
        
        # Обновляем пользователя из базы данных
        self.session.refresh(self.test_user)
        
        # Проверяем, что дети доступны через связь
        self.assertEqual(self.test_user.children.count(), 3)


if __name__ == '__main__':
    unittest.main()