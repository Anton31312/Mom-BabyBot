"""
Тесты для моделей профилей детей и измерений.

Этот модуль содержит тесты для моделей Child и Measurement и связанных функций.
"""

import unittest
from datetime import datetime, timedelta
from botapp.models import db_manager, User
from botapp.models_child import (
    Child, Measurement, 
    get_child, get_children_by_user, create_child, update_child, delete_child,
    get_measurements, create_measurement, update_measurement, delete_measurement
)


class ChildModelTestCase(unittest.TestCase):
    """Тестовый случай для модели Child и связанных функций."""
    
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
            birth_date=datetime.now() - timedelta(days=365),  # 1 год
            gender='male'
        )
        self.session.add(self.child)
        self.session.commit()
        self.session.refresh(self.child)
    
    def tearDown(self):
        """Очистка тестовых данных."""
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
    
    def test_create_child(self):
        """Тест создания профиля ребенка."""
        # Создаем нового ребенка
        new_child = create_child(
            user_id=self.user.id,
            name='New Test Child',
            birth_date=datetime.now() - timedelta(days=180),  # 6 месяцев
            gender='female'
        )
        
        # Проверяем, что ребенок был создан
        self.assertIsNotNone(new_child)
        self.assertEqual(new_child.name, 'New Test Child')
        self.assertEqual(new_child.gender, 'female')
        
        # Проверяем, что ребенок есть в базе данных
        child_from_db = get_child(new_child.id)
        self.assertIsNotNone(child_from_db)
        self.assertEqual(child_from_db.name, 'New Test Child')
        
        # Удаляем созданного ребенка
        delete_child(new_child.id)
    
    def test_get_child(self):
        """Тест получения ребенка по ID."""
        # Получаем ребенка по ID
        child = get_child(self.child.id)
        
        # Проверяем, что ребенок получен
        self.assertIsNotNone(child)
        self.assertEqual(child.id, self.child.id)
        self.assertEqual(child.name, 'Test Child')
        self.assertEqual(child.gender, 'male')
    
    def test_get_children_by_user(self):
        """Тест получения всех детей пользователя."""
        # Создаем еще одного ребенка для пользователя
        second_child = create_child(
            user_id=self.user.id,
            name='Second Test Child',
            birth_date=datetime.now() - timedelta(days=30),  # 1 месяц
            gender='female'
        )
        
        # Получаем всех детей пользователя
        children = get_children_by_user(self.user.id)
        
        # Проверяем, что получены оба ребенка
        self.assertEqual(len(children), 2)
        child_names = [child.name for child in children]
        self.assertIn('Test Child', child_names)
        self.assertIn('Second Test Child', child_names)
        
        # Удаляем второго ребенка
        delete_child(second_child.id)
    
    def test_update_child(self):
        """Тест обновления профиля ребенка."""
        # Обновляем данные ребенка
        updated_child = update_child(
            self.child.id,
            name='Updated Child Name',
            gender='female'
        )
        
        # Проверяем, что данные обновлены
        self.assertEqual(updated_child.name, 'Updated Child Name')
        self.assertEqual(updated_child.gender, 'female')
        
        # Проверяем, что данные обновлены в базе данных
        child_from_db = get_child(self.child.id)
        self.assertEqual(child_from_db.name, 'Updated Child Name')
        self.assertEqual(child_from_db.gender, 'female')
    
    def test_delete_child(self):
        """Тест удаления профиля ребенка."""
        # Создаем ребенка для удаления
        child_to_delete = create_child(
            user_id=self.user.id,
            name='Child To Delete'
        )
        
        # Удаляем ребенка
        result = delete_child(child_to_delete.id)
        
        # Проверяем, что удаление прошло успешно
        self.assertTrue(result)
        
        # Проверяем, что ребенка больше нет в базе данных
        deleted_child = get_child(child_to_delete.id)
        self.assertIsNone(deleted_child)
    
    def test_age_calculation(self):
        """Тест расчета возраста ребенка."""
        # Создаем ребенка с известным возрастом
        one_year_ago = datetime.now() - timedelta(days=365)
        child = create_child(
            user_id=self.user.id,
            name='Age Test Child',
            birth_date=one_year_ago
        )
        
        # Проверяем расчет возраста в месяцах
        self.assertAlmostEqual(child.age_in_months, 12, delta=1)  # Примерно 12 месяцев
        
        # Проверяем отображение возраста
        self.assertIn('1 год', child.age_display)
        
        # Удаляем тестового ребенка
        delete_child(child.id)


class MeasurementModelTestCase(unittest.TestCase):
    """Тестовый случай для модели Measurement и связанных функций."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        # Создаем сессию
        self.session = db_manager.get_session()
        
        # Создаем тестового пользователя
        self.user = User(
            telegram_id=987654321,
            username='measurementuser',
            first_name='Measurement',
            last_name='User'
        )
        self.session.add(self.user)
        self.session.commit()
        self.session.refresh(self.user)
        
        # Создаем тестового ребенка
        self.child = Child(
            user_id=self.user.id,
            name='Measurement Child',
            birth_date=datetime.now() - timedelta(days=180),  # 6 месяцев
            gender='female'
        )
        self.session.add(self.child)
        self.session.commit()
        self.session.refresh(self.child)
        
        # Создаем тестовое измерение
        self.measurement = Measurement(
            child_id=self.child.id,
            height=65.0,  # см
            weight=7.5,   # кг
            head_circumference=43.0,  # см
            date=datetime.now() - timedelta(days=7),
            notes='Тестовое измерение'
        )
        self.session.add(self.measurement)
        self.session.commit()
        self.session.refresh(self.measurement)
    
    def tearDown(self):
        """Очистка тестовых данных."""
        # Удаляем тестовое измерение
        measurement = self.session.query(Measurement).filter_by(id=self.measurement.id).first()
        if measurement:
            self.session.delete(measurement)
        
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
    
    def test_create_measurement(self):
        """Тест создания измерения."""
        # Создаем новое измерение
        new_measurement = create_measurement(
            child_id=self.child.id,
            height=67.0,
            weight=8.0,
            head_circumference=44.0,
            notes='Новое тестовое измерение'
        )
        
        # Проверяем, что измерение было создано
        self.assertIsNotNone(new_measurement)
        self.assertEqual(new_measurement.height, 67.0)
        self.assertEqual(new_measurement.weight, 8.0)
        self.assertEqual(new_measurement.head_circumference, 44.0)
        
        # Удаляем созданное измерение
        delete_measurement(new_measurement.id)
    
    def test_get_measurements(self):
        """Тест получения измерений ребенка."""
        # Создаем дополнительное измерение
        additional_measurement = create_measurement(
            child_id=self.child.id,
            height=68.0,
            weight=8.2,
            head_circumference=44.5,
            date=datetime.now()
        )
        
        # Получаем все измерения ребенка
        measurements = get_measurements(self.child.id)
        
        # Проверяем, что получены оба измерения
        self.assertEqual(len(measurements), 2)
        
        # Проверяем, что измерения отсортированы по дате (сначала новые)
        self.assertEqual(measurements[0].id, additional_measurement.id)
        
        # Удаляем дополнительное измерение
        delete_measurement(additional_measurement.id)
    
    def test_update_measurement(self):
        """Тест обновления измерения."""
        # Обновляем данные измерения
        updated_measurement = update_measurement(
            self.measurement.id,
            height=66.0,
            weight=7.8,
            notes='Обновленное измерение'
        )
        
        # Проверяем, что данные обновлены
        self.assertEqual(updated_measurement.height, 66.0)
        self.assertEqual(updated_measurement.weight, 7.8)
        self.assertEqual(updated_measurement.notes, 'Обновленное измерение')
        self.assertEqual(updated_measurement.head_circumference, 43.0)  # Не изменилось
    
    def test_delete_measurement(self):
        """Тест удаления измерения."""
        # Создаем измерение для удаления
        measurement_to_delete = create_measurement(
            child_id=self.child.id,
            height=70.0,
            weight=9.0
        )
        
        # Удаляем измерение
        result = delete_measurement(measurement_to_delete.id)
        
        # Проверяем, что удаление прошло успешно
        self.assertTrue(result)
        
        # Получаем все измерения и проверяем, что удаленного нет в списке
        measurements = get_measurements(self.child.id)
        measurement_ids = [m.id for m in measurements]
        self.assertNotIn(measurement_to_delete.id, measurement_ids)


if __name__ == '__main__':
    unittest.main()