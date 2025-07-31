from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from webapp.models import FetalDevelopmentInfo


class FetalDevelopmentInfoModelTest(TestCase):
    """
    Тесты для модели FetalDevelopmentInfo.
    
    Проверяет функциональность модели для хранения информации о развитии плода
    по неделям беременности (требование 10.3).
    """
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.test_data = {
            'week_number': 20,
            'title': '20-я неделя беременности',
            'fetal_size_description': 'Размером с банан',
            'fetal_length_mm': 118.0,
            'fetal_weight_g': 150.0,
            'organ_development': 'Развиваются легкие. Плод заглатывает амниотическую жидкость.',
            'maternal_changes': 'Середина беременности! Живот заметно округлился.',
            'common_symptoms': 'Шевеления хорошо ощущаются, возможны растяжки.',
            'recommendations': 'Используйте крем от растяжек, носите поддерживающий бюстгальтер.',
            'dos_and_donts': 'Можно: путешествовать. Нельзя: экстремальные развлечения.',
            'medical_checkups': 'Подробное УЗИ, оценка развития плода.',
            'interesting_facts': 'Это середина беременности - осталось столько же времени!'
        }
    
    def test_create_fetal_development_info(self):
        """Тест создания записи о развитии плода."""
        development_info = FetalDevelopmentInfo.objects.create(**self.test_data)
        
        self.assertEqual(development_info.week_number, 20)
        self.assertEqual(development_info.title, '20-я неделя беременности')
        self.assertEqual(development_info.fetal_length_mm, 118.0)
        self.assertEqual(development_info.fetal_weight_g, 150.0)
        self.assertTrue(development_info.is_active)
    
    def test_string_representation(self):
        """Тест строкового представления модели."""
        development_info = FetalDevelopmentInfo.objects.create(**self.test_data)
        expected_str = '20-я неделя: 20-я неделя беременности'
        self.assertEqual(str(development_info), expected_str)
    
    def test_week_number_validation(self):
        """Тест валидации номера недели."""
        # Тест минимального значения
        with self.assertRaises(ValidationError):
            development_info = FetalDevelopmentInfo(**{**self.test_data, 'week_number': 0})
            development_info.full_clean()
        
        # Тест максимального значения
        with self.assertRaises(ValidationError):
            development_info = FetalDevelopmentInfo(**{**self.test_data, 'week_number': 43})
            development_info.full_clean()
        
        # Тест валидных значений
        for week in [1, 20, 42]:
            development_info = FetalDevelopmentInfo(**{**self.test_data, 'week_number': week})
            development_info.full_clean()  # Не должно вызывать исключение
    
    def test_unique_week_number(self):
        """Тест уникальности номера недели."""
        FetalDevelopmentInfo.objects.create(**self.test_data)
        
        # Попытка создать запись с тем же номером недели должна вызвать ошибку
        with self.assertRaises(Exception):  # IntegrityError в реальной БД
            FetalDevelopmentInfo.objects.create(**self.test_data)
    
    def test_trimester_property(self):
        """Тест свойства trimester."""
        # Первый триместр
        dev_info_1 = FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': 8})
        self.assertEqual(dev_info_1.trimester, 1)
        
        # Второй триместр
        dev_info_2 = FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': 20})
        self.assertEqual(dev_info_2.trimester, 2)
        
        # Третий триместр
        dev_info_3 = FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': 35})
        self.assertEqual(dev_info_3.trimester, 3)
    
    def test_trimester_name_property(self):
        """Тест свойства trimester_name."""
        # Первый триместр
        dev_info_1 = FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': 8})
        self.assertEqual(dev_info_1.trimester_name, 'Первый триместр')
        
        # Второй триместр
        dev_info_2 = FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': 20})
        self.assertEqual(dev_info_2.trimester_name, 'Второй триместр')
        
        # Третий триместр
        dev_info_3 = FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': 35})
        self.assertEqual(dev_info_3.trimester_name, 'Третий триместр')
    
    def test_fetal_size_formatted_property(self):
        """Тест свойства fetal_size_formatted."""
        development_info = FetalDevelopmentInfo.objects.create(**self.test_data)
        
        expected = 'Размером с банан (11.8 см, 150 г)'
        self.assertEqual(development_info.fetal_size_formatted, expected)
    
    def test_fetal_size_formatted_with_small_measurements(self):
        """Тест форматирования размера для маленьких значений."""
        small_data = {**self.test_data, 'fetal_length_mm': 5.0, 'fetal_weight_g': 2.0}
        development_info = FetalDevelopmentInfo.objects.create(**small_data)
        
        expected = 'Размером с банан (5.0 мм, 2 г)'
        self.assertEqual(development_info.fetal_size_formatted, expected)
    
    def test_fetal_size_formatted_with_large_weight(self):
        """Тест форматирования размера для больших значений веса."""
        large_data = {**self.test_data, 'fetal_weight_g': 3200.0}
        development_info = FetalDevelopmentInfo.objects.create(**large_data)
        
        expected = 'Размером с банан (11.8 см, 3.20 кг)'
        self.assertEqual(development_info.fetal_size_formatted, expected)
    
    def test_fetal_size_formatted_without_measurements(self):
        """Тест форматирования размера без числовых измерений."""
        no_measurements_data = {
            **self.test_data, 
            'fetal_length_mm': None, 
            'fetal_weight_g': None
        }
        development_info = FetalDevelopmentInfo.objects.create(**no_measurements_data)
        
        expected = 'Размером с банан'
        self.assertEqual(development_info.fetal_size_formatted, expected)
    
    def test_fetal_size_formatted_without_description(self):
        """Тест форматирования размера без описания."""
        no_description_data = {
            **self.test_data, 
            'fetal_size_description': ''
        }
        development_info = FetalDevelopmentInfo.objects.create(**no_description_data)
        
        expected = '(11.8 см, 150 г)'
        self.assertEqual(development_info.fetal_size_formatted, expected)
    
    def test_get_development_summary(self):
        """Тест метода get_development_summary."""
        development_info = FetalDevelopmentInfo.objects.create(**self.test_data)
        
        summary = development_info.get_development_summary()
        self.assertIn('Развиваются легкие', summary)
        self.assertIn('размером с банан', summary.lower())
    
    def test_get_info_for_week_class_method(self):
        """Тест класс-метода get_info_for_week."""
        development_info = FetalDevelopmentInfo.objects.create(**self.test_data)
        
        # Тест получения существующей недели
        result = FetalDevelopmentInfo.get_info_for_week(20)
        self.assertEqual(result, development_info)
        
        # Тест получения несуществующей недели
        result = FetalDevelopmentInfo.get_info_for_week(25)
        self.assertIsNone(result)
    
    def test_get_weeks_range_class_method(self):
        """Тест класс-метода get_weeks_range."""
        # Создаем несколько записей
        for week in [18, 19, 20, 21, 22]:
            FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': week})
        
        # Тест получения диапазона
        result = FetalDevelopmentInfo.get_weeks_range(19, 21)
        self.assertEqual(result.count(), 3)
        self.assertEqual(list(result.values_list('week_number', flat=True)), [19, 20, 21])
    
    def test_get_by_trimester_class_method(self):
        """Тест класс-метода get_by_trimester."""
        # Создаем записи для разных триместров
        weeks_data = [
            (5, 1),   # Первый триместр
            (12, 1),  # Первый триместр
            (15, 2),  # Второй триместр
            (25, 2),  # Второй триместр
            (30, 3),  # Третий триместр
            (38, 3),  # Третий триместр
        ]
        
        for week, trimester in weeks_data:
            FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': week})
        
        # Тест первого триместра
        first_trimester = FetalDevelopmentInfo.get_by_trimester(1)
        self.assertEqual(first_trimester.count(), 2)
        
        # Тест второго триместра
        second_trimester = FetalDevelopmentInfo.get_by_trimester(2)
        self.assertEqual(second_trimester.count(), 2)
        
        # Тест третьего триместра
        third_trimester = FetalDevelopmentInfo.get_by_trimester(3)
        self.assertEqual(third_trimester.count(), 2)
        
        # Тест неверного триместра
        invalid_trimester = FetalDevelopmentInfo.get_by_trimester(4)
        self.assertEqual(invalid_trimester.count(), 0)
    
    def test_get_next_week_info(self):
        """Тест метода get_next_week_info."""
        # Создаем записи для недель 20 и 21
        dev_info_20 = FetalDevelopmentInfo.objects.create(**self.test_data)
        dev_info_21 = FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': 21})
        
        # Тест получения следующей недели
        next_week = dev_info_20.get_next_week_info()
        self.assertEqual(next_week, dev_info_21)
        
        # Тест для последней недели
        last_week_next = dev_info_21.get_next_week_info()
        self.assertIsNone(last_week_next)
    
    def test_get_previous_week_info(self):
        """Тест метода get_previous_week_info."""
        # Создаем записи для недель 19 и 20
        dev_info_19 = FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': 19})
        dev_info_20 = FetalDevelopmentInfo.objects.create(**self.test_data)
        
        # Тест получения предыдущей недели
        prev_week = dev_info_20.get_previous_week_info()
        self.assertEqual(prev_week, dev_info_19)
        
        # Тест для первой недели
        first_week_prev = dev_info_19.get_previous_week_info()
        self.assertIsNone(first_week_prev)
    
    def test_ordering(self):
        """Тест сортировки записей по номеру недели."""
        # Создаем записи в произвольном порядке
        weeks = [25, 10, 30, 5, 20]
        for week in weeks:
            FetalDevelopmentInfo.objects.create(**{**self.test_data, 'week_number': week})
        
        # Проверяем, что записи отсортированы по номеру недели
        all_records = FetalDevelopmentInfo.objects.all()
        week_numbers = list(all_records.values_list('week_number', flat=True))
        self.assertEqual(week_numbers, [5, 10, 20, 25, 30])
    
    def test_is_active_default(self):
        """Тест значения по умолчанию для поля is_active."""
        development_info = FetalDevelopmentInfo.objects.create(**self.test_data)
        self.assertTrue(development_info.is_active)
    
    def test_inactive_records_excluded_from_queries(self):
        """Тест исключения неактивных записей из запросов."""
        # Создаем активную и неактивную записи
        active_info = FetalDevelopmentInfo.objects.create(**self.test_data)
        inactive_info = FetalDevelopmentInfo.objects.create(
            **{**self.test_data, 'week_number': 21, 'is_active': False}
        )
        
        # Тест get_info_for_week исключает неактивные записи
        result = FetalDevelopmentInfo.get_info_for_week(21)
        self.assertIsNone(result)
        
        # Тест get_weeks_range исключает неактивные записи
        result = FetalDevelopmentInfo.get_weeks_range(20, 21)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), active_info)
    
    def test_meta_options(self):
        """Тест мета-опций модели."""
        meta = FetalDevelopmentInfo._meta
        self.assertEqual(meta.verbose_name, 'Информация о развитии плода')
        self.assertEqual(meta.verbose_name_plural, 'Информация о развитии плода')
        self.assertEqual(meta.ordering, ['week_number'])