"""
Тесты для моделей отслеживания показателей здоровья.

Этот модуль содержит тесты для моделей WeightRecord и BloodPressureRecord,
которые соответствуют требованиям 7.1 и 7.2 о возможности отслеживания
веса и артериального давления.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from webapp.models import WeightRecord, BloodPressureRecord


class WeightRecordModelTest(TestCase):
    """Тесты для модели WeightRecord."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.test_date = timezone.now()
    
    def test_create_weight_record(self):
        """Тест создания записи веса."""
        weight_record = WeightRecord.objects.create(
            user=self.user,
            date=self.test_date,
            weight=Decimal('65.50'),
            notes='Тестовая запись веса'
        )
        
        self.assertEqual(weight_record.user, self.user)
        self.assertEqual(weight_record.weight, Decimal('65.50'))
        self.assertEqual(weight_record.notes, 'Тестовая запись веса')
        self.assertIsNotNone(weight_record.created_at)
        self.assertIsNotNone(weight_record.updated_at)
    
    def test_weight_record_str_representation(self):
        """Тест строкового представления записи веса."""
        weight_record = WeightRecord.objects.create(
            user=self.user,
            date=self.test_date,
            weight=Decimal('70.25')
        )
        
        expected_str = f'{self.user.username} - 70.25 кг ({self.test_date.strftime("%d.%m.%Y %H:%M")})'
        self.assertEqual(str(weight_record), expected_str)
    
    def test_weight_kg_property(self):
        """Тест свойства weight_kg."""
        weight_record = WeightRecord.objects.create(
            user=self.user,
            date=self.test_date,
            weight=Decimal('68.75')
        )
        
        self.assertEqual(weight_record.weight_kg, 68.75)
        self.assertIsInstance(weight_record.weight_kg, float)
    
    def test_is_within_normal_range_method(self):
        """Тест метода проверки нормального диапазона веса."""
        weight_record = WeightRecord.objects.create(
            user=self.user,
            date=self.test_date,
            weight=Decimal('65.00')
        )
        
        # Тест в пределах нормы
        self.assertTrue(weight_record.is_within_normal_range(60.0, 70.0))
        
        # Тест ниже нормы
        self.assertFalse(weight_record.is_within_normal_range(70.0, 80.0))
        
        # Тест выше нормы
        self.assertFalse(weight_record.is_within_normal_range(50.0, 60.0))
        
        # Тест без заданных границ
        self.assertIsNone(weight_record.is_within_normal_range())
        self.assertIsNone(weight_record.is_within_normal_range(min_weight=60.0))
        self.assertIsNone(weight_record.is_within_normal_range(max_weight=70.0))
    
    def test_weight_validation_min_value(self):
        """Тест валидации минимального значения веса."""
        with self.assertRaises(ValidationError):
            weight_record = WeightRecord(
                user=self.user,
                date=self.test_date,
                weight=Decimal('0.05')  # Меньше минимального значения 0.1
            )
            weight_record.full_clean()
    
    def test_weight_validation_max_value(self):
        """Тест валидации максимального значения веса."""
        with self.assertRaises(ValidationError):
            weight_record = WeightRecord(
                user=self.user,
                date=self.test_date,
                weight=Decimal('1000.00')  # Больше максимального значения 999.99
            )
            weight_record.full_clean()
    
    def test_weight_record_ordering(self):
        """Тест сортировки записей веса по дате (новые первыми)."""
        # Создаем записи с разными датами
        date1 = timezone.now() - timedelta(days=2)
        date2 = timezone.now() - timedelta(days=1)
        date3 = timezone.now()
        
        record1 = WeightRecord.objects.create(
            user=self.user, date=date1, weight=Decimal('65.0')
        )
        record2 = WeightRecord.objects.create(
            user=self.user, date=date2, weight=Decimal('66.0')
        )
        record3 = WeightRecord.objects.create(
            user=self.user, date=date3, weight=Decimal('67.0')
        )
        
        records = list(WeightRecord.objects.all())
        self.assertEqual(records[0], record3)  # Самая новая запись первая
        self.assertEqual(records[1], record2)
        self.assertEqual(records[2], record1)
    
    def test_unique_together_constraint(self):
        """Тест ограничения уникальности пользователь+дата."""
        # Создаем первую запись
        WeightRecord.objects.create(
            user=self.user,
            date=self.test_date,
            weight=Decimal('65.0')
        )
        
        # Попытка создать вторую запись с теми же пользователем и датой
        with self.assertRaises(Exception):  # IntegrityError в реальной БД
            WeightRecord.objects.create(
                user=self.user,
                date=self.test_date,
                weight=Decimal('66.0')
            )


class BloodPressureRecordModelTest(TestCase):
    """Тесты для модели BloodPressureRecord."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.test_date = timezone.now()
    
    def test_create_blood_pressure_record(self):
        """Тест создания записи артериального давления."""
        bp_record = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date,
            systolic=120,
            diastolic=80,
            pulse=70,
            notes='Тестовая запись давления'
        )
        
        self.assertEqual(bp_record.user, self.user)
        self.assertEqual(bp_record.systolic, 120)
        self.assertEqual(bp_record.diastolic, 80)
        self.assertEqual(bp_record.pulse, 70)
        self.assertEqual(bp_record.notes, 'Тестовая запись давления')
        self.assertIsNotNone(bp_record.created_at)
        self.assertIsNotNone(bp_record.updated_at)
    
    def test_blood_pressure_record_without_pulse(self):
        """Тест создания записи давления без пульса."""
        bp_record = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date,
            systolic=110,
            diastolic=70
        )
        
        self.assertEqual(bp_record.systolic, 110)
        self.assertEqual(bp_record.diastolic, 70)
        self.assertIsNone(bp_record.pulse)
    
    def test_blood_pressure_record_str_representation(self):
        """Тест строкового представления записи давления."""
        # С пульсом
        bp_record_with_pulse = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date,
            systolic=120,
            diastolic=80,
            pulse=75
        )
        
        expected_str_with_pulse = f'{self.user.username} - 120/80, пульс 75 ({self.test_date.strftime("%d.%m.%Y %H:%M")})'
        self.assertEqual(str(bp_record_with_pulse), expected_str_with_pulse)
        
        # Без пульса
        bp_record_without_pulse = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date + timedelta(minutes=1),  # Чтобы избежать конфликта unique_together
            systolic=115,
            diastolic=75
        )
        
        expected_str_without_pulse = f'{self.user.username} - 115/75 ({(self.test_date + timedelta(minutes=1)).strftime("%d.%m.%Y %H:%M")})'
        self.assertEqual(str(bp_record_without_pulse), expected_str_without_pulse)
    
    def test_pressure_reading_property(self):
        """Тест свойства pressure_reading."""
        bp_record = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date,
            systolic=130,
            diastolic=85
        )
        
        self.assertEqual(bp_record.pressure_reading, '130/85')
    
    def test_is_systolic_normal_method(self):
        """Тест метода проверки нормального систолического давления."""
        # Нормальное давление
        bp_normal = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date,
            systolic=120,
            diastolic=80
        )
        self.assertEqual(bp_normal.is_systolic_normal(), 'normal')
        
        # Низкое давление
        bp_low = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date + timedelta(minutes=1),
            systolic=85,
            diastolic=60
        )
        self.assertEqual(bp_low.is_systolic_normal(), 'low')
        
        # Высокое давление
        bp_high = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date + timedelta(minutes=2),
            systolic=150,
            diastolic=95
        )
        self.assertEqual(bp_high.is_systolic_normal(), 'high')
    
    def test_is_diastolic_normal_method(self):
        """Тест метода проверки нормального диастолического давления."""
        # Нормальное давление
        bp_normal = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date,
            systolic=120,
            diastolic=75
        )
        self.assertEqual(bp_normal.is_diastolic_normal(), 'normal')
        
        # Низкое давление
        bp_low = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date + timedelta(minutes=1),
            systolic=110,
            diastolic=55
        )
        self.assertEqual(bp_low.is_diastolic_normal(), 'low')
        
        # Высокое давление
        bp_high = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date + timedelta(minutes=2),
            systolic=130,
            diastolic=95
        )
        self.assertEqual(bp_high.is_diastolic_normal(), 'high')
    
    def test_is_pressure_normal_method(self):
        """Тест метода проверки нормального давления в целом."""
        # Нормальное давление
        bp_normal = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date,
            systolic=120,
            diastolic=80
        )
        self.assertTrue(bp_normal.is_pressure_normal())
        
        # Высокое систолическое
        bp_high_sys = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date + timedelta(minutes=1),
            systolic=150,
            diastolic=80
        )
        self.assertFalse(bp_high_sys.is_pressure_normal())
        
        # Высокое диастолическое
        bp_high_dia = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date + timedelta(minutes=2),
            systolic=120,
            diastolic=95
        )
        self.assertFalse(bp_high_dia.is_pressure_normal())
    
    def test_get_pressure_category_method(self):
        """Тест метода определения категории давления."""
        test_cases = [
            (85, 55, 'Пониженное'),
            (110, 70, 'Нормальное'),
            (125, 80, 'Повышенное нормальное'),
            (135, 85, 'Высокое нормальное'),
            (150, 95, 'Гипертония 1 степени'),
            (170, 105, 'Гипертония 2 степени'),
            (190, 115, 'Гипертония 3 степени'),
        ]
        
        for i, (systolic, diastolic, expected_category) in enumerate(test_cases):
            bp_record = BloodPressureRecord.objects.create(
                user=self.user,
                date=self.test_date + timedelta(minutes=i),
                systolic=systolic,
                diastolic=diastolic
            )
            self.assertEqual(bp_record.get_pressure_category(), expected_category)
    
    def test_needs_medical_attention_method(self):
        """Тест метода определения необходимости медицинского внимания."""
        # Критически высокое давление
        bp_critical_high = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date,
            systolic=185,
            diastolic=115
        )
        self.assertTrue(bp_critical_high.needs_medical_attention())
        
        # Критически низкое давление
        bp_critical_low = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date + timedelta(minutes=1),
            systolic=85,
            diastolic=55
        )
        self.assertTrue(bp_critical_low.needs_medical_attention())
        
        # Нормальное давление
        bp_normal = BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date + timedelta(minutes=2),
            systolic=120,
            diastolic=80
        )
        self.assertFalse(bp_normal.needs_medical_attention())
    
    def test_systolic_validation(self):
        """Тест валидации систолического давления."""
        # Слишком низкое
        with self.assertRaises(ValidationError):
            bp_record = BloodPressureRecord(
                user=self.user,
                date=self.test_date,
                systolic=45,  # Меньше минимального значения 50
                diastolic=70
            )
            bp_record.full_clean()
        
        # Слишком высокое
        with self.assertRaises(ValidationError):
            bp_record = BloodPressureRecord(
                user=self.user,
                date=self.test_date,
                systolic=350,  # Больше максимального значения 300
                diastolic=70
            )
            bp_record.full_clean()
    
    def test_diastolic_validation(self):
        """Тест валидации диастолического давления."""
        # Слишком низкое
        with self.assertRaises(ValidationError):
            bp_record = BloodPressureRecord(
                user=self.user,
                date=self.test_date,
                systolic=120,
                diastolic=25  # Меньше минимального значения 30
            )
            bp_record.full_clean()
        
        # Слишком высокое
        with self.assertRaises(ValidationError):
            bp_record = BloodPressureRecord(
                user=self.user,
                date=self.test_date,
                systolic=120,
                diastolic=250  # Больше максимального значения 200
            )
            bp_record.full_clean()
    
    def test_pulse_validation(self):
        """Тест валидации пульса."""
        # Слишком низкий
        with self.assertRaises(ValidationError):
            bp_record = BloodPressureRecord(
                user=self.user,
                date=self.test_date,
                systolic=120,
                diastolic=80,
                pulse=25  # Меньше минимального значения 30
            )
            bp_record.full_clean()
        
        # Слишком высокий
        with self.assertRaises(ValidationError):
            bp_record = BloodPressureRecord(
                user=self.user,
                date=self.test_date,
                systolic=120,
                diastolic=80,
                pulse=300  # Больше максимального значения 250
            )
            bp_record.full_clean()
    
    def test_blood_pressure_record_ordering(self):
        """Тест сортировки записей давления по дате (новые первыми)."""
        # Создаем записи с разными датами
        date1 = timezone.now() - timedelta(days=2)
        date2 = timezone.now() - timedelta(days=1)
        date3 = timezone.now()
        
        record1 = BloodPressureRecord.objects.create(
            user=self.user, date=date1, systolic=120, diastolic=80
        )
        record2 = BloodPressureRecord.objects.create(
            user=self.user, date=date2, systolic=125, diastolic=82
        )
        record3 = BloodPressureRecord.objects.create(
            user=self.user, date=date3, systolic=118, diastolic=78
        )
        
        records = list(BloodPressureRecord.objects.all())
        self.assertEqual(records[0], record3)  # Самая новая запись первая
        self.assertEqual(records[1], record2)
        self.assertEqual(records[2], record1)
    
    def test_unique_together_constraint_blood_pressure(self):
        """Тест ограничения уникальности пользователь+дата для давления."""
        # Создаем первую запись
        BloodPressureRecord.objects.create(
            user=self.user,
            date=self.test_date,
            systolic=120,
            diastolic=80
        )
        
        # Попытка создать вторую запись с теми же пользователем и датой
        with self.assertRaises(Exception):  # IntegrityError в реальной БД
            BloodPressureRecord.objects.create(
                user=self.user,
                date=self.test_date,
                systolic=125,
                diastolic=82
            )


class HealthModelsIntegrationTest(TestCase):
    """Интеграционные тесты для моделей здоровья."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_related_name_access(self):
        """Тест доступа к записям через related_name."""
        # Создаем записи веса
        WeightRecord.objects.create(
            user=self.user,
            weight=Decimal('65.0')
        )
        WeightRecord.objects.create(
            user=self.user,
            weight=Decimal('66.0')
        )
        
        # Создаем записи давления
        BloodPressureRecord.objects.create(
            user=self.user,
            systolic=120,
            diastolic=80
        )
        BloodPressureRecord.objects.create(
            user=self.user,
            systolic=125,
            diastolic=82
        )
        
        # Проверяем доступ через related_name
        self.assertEqual(self.user.weight_records.count(), 2)
        self.assertEqual(self.user.blood_pressure_records.count(), 2)
        
        # Проверяем, что записи принадлежат правильному пользователю
        for weight_record in self.user.weight_records.all():
            self.assertEqual(weight_record.user, self.user)
        
        for bp_record in self.user.blood_pressure_records.all():
            self.assertEqual(bp_record.user, self.user)
    
    def test_cascade_delete(self):
        """Тест каскадного удаления записей при удалении пользователя."""
        # Создаем записи
        WeightRecord.objects.create(
            user=self.user,
            weight=Decimal('65.0')
        )
        BloodPressureRecord.objects.create(
            user=self.user,
            systolic=120,
            diastolic=80
        )
        
        # Проверяем, что записи созданы
        self.assertEqual(WeightRecord.objects.count(), 1)
        self.assertEqual(BloodPressureRecord.objects.count(), 1)
        
        # Удаляем пользователя
        self.user.delete()
        
        # Проверяем, что записи тоже удалились
        self.assertEqual(WeightRecord.objects.count(), 0)
        self.assertEqual(BloodPressureRecord.objects.count(), 0)