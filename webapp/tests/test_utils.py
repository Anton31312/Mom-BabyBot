"""
Тесты для утилитарных функций веб-приложения.

Этот модуль содержит тесты для различных утилитарных функций,
используемых в веб-приложении.
"""

import unittest
from datetime import datetime
from django.test import TestCase
from webapp.utils.date_utils import parse_datetime
from webapp.utils.model_utils import child_to_dict, measurement_to_dict
from botapp.models_child import Child, Measurement

class ParseDateTimeTests(TestCase):
    """Тесты для функции parse_datetime."""
    
    def test_parse_datetime_valid_formats(self):
        """Тест парсинга даты в различных форматах."""
        # ISO формат с временем
        self.assertEqual(
            parse_datetime('2023-01-15T14:30:45'),
            datetime(2023, 1, 15, 14, 30, 45)
        )
        
        # ISO формат с миллисекундами
        self.assertEqual(
            parse_datetime('2023-01-15T14:30:45.123'),
            datetime(2023, 1, 15, 14, 30, 45, 123000)
        )
        
        # Формат с пробелом
        self.assertEqual(
            parse_datetime('2023-01-15 14:30:45'),
            datetime(2023, 1, 15, 14, 30, 45)
        )
        
        # Только дата
        self.assertEqual(
            parse_datetime('2023-01-15'),
            datetime(2023, 1, 15)
        )
        
        # Русский формат даты
        self.assertEqual(
            parse_datetime('15.01.2023'),
            datetime(2023, 1, 15)
        )
        
        # Русский формат с временем
        self.assertEqual(
            parse_datetime('15.01.2023 14:30'),
            datetime(2023, 1, 15, 14, 30)
        )
    
    def test_parse_datetime_invalid_formats(self):
        """Тест парсинга невалидных форматов даты."""
        self.assertIsNone(parse_datetime(''))
        self.assertIsNone(parse_datetime(None))
        self.assertIsNone(parse_datetime('invalid-date'))
        self.assertIsNone(parse_datetime('2023/01/15'))
        self.assertIsNone(parse_datetime('15-01-2023'))

class DictConversionTests(TestCase):
    """Тесты для функций конвертации объектов в словари."""
    
    def test_child_to_dict(self):
        """Тест конвертации объекта Child в словарь."""
        # Создаем мок-объект Child
        child = Child()
        child.id = 1
        child.user_id = 100
        child.name = "Тестовый ребенок"
        child.birth_date = datetime(2022, 1, 15)
        child.gender = "male"
        child.created_at = datetime(2023, 1, 1)
        child.updated_at = datetime(2023, 1, 2)
        
        # Добавляем свойства
        child.age_in_months = 12
        child.age_display = "1 год"
        
        # Конвертируем в словарь
        result = child_to_dict(child)
        
        # Проверяем результат
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['user_id'], 100)
        self.assertEqual(result['name'], "Тестовый ребенок")
        self.assertEqual(result['birth_date'], "2022-01-15T00:00:00")
        self.assertEqual(result['gender'], "male")
        self.assertEqual(result['age_in_months'], 12)
        self.assertEqual(result['age_display'], "1 год")
        self.assertEqual(result['created_at'], "2023-01-01T00:00:00")
        self.assertEqual(result['updated_at'], "2023-01-02T00:00:00")
    
    def test_measurement_to_dict(self):
        """Тест конвертации объекта Measurement в словарь."""
        # Создаем мок-объект Measurement
        measurement = Measurement()
        measurement.id = 1
        measurement.child_id = 100
        measurement.date = datetime(2023, 1, 15)
        measurement.height = 75.5
        measurement.weight = 9.2
        measurement.head_circumference = 45.0
        measurement.notes = "Плановое измерение"
        
        # Конвертируем в словарь
        result = measurement_to_dict(measurement)
        
        # Проверяем результат
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['child_id'], 100)
        self.assertEqual(result['date'], "2023-01-15T00:00:00")
        self.assertEqual(result['height'], 75.5)
        self.assertEqual(result['weight'], 9.2)
        self.assertEqual(result['head_circumference'], 45.0)
        self.assertEqual(result['notes'], "Плановое измерение")

if __name__ == '__main__':
    unittest.main()