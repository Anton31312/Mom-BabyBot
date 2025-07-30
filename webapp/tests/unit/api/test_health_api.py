"""
Тесты для API отслеживания показателей здоровья.

Этот модуль содержит тесты для API эндпоинтов работы с записями веса и артериального давления.
Соответствует требованиям 7.1 и 7.2 о возможности отслеживания веса и артериального давления.
"""

import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from webapp.models import WeightRecord, BloodPressureRecord


class WeightRecordsAPITest(TestCase):
    """Тесты для API записей веса."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Создаем тестовые записи веса с разными временными метками
        self.weight_record1 = WeightRecord.objects.create(
            user=self.user,
            date=timezone.now() - timedelta(minutes=10),
            weight=Decimal('65.5'),
            notes='Первая запись'
        )
        self.weight_record2 = WeightRecord.objects.create(
            user=self.user,
            date=timezone.now() - timedelta(minutes=5),
            weight=Decimal('66.0'),
            notes='Вторая запись'
        )
    
    def test_get_weight_records(self):
        """Тест получения списка записей веса."""
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('weight_records', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['weight_records']), 2)
        
        # Проверяем структуру данных
        record = data['weight_records'][0]
        self.assertIn('id', record)
        self.assertIn('user_id', record)
        self.assertIn('date', record)
        self.assertIn('weight', record)
        self.assertIn('notes', record)
    
    def test_get_weight_records_with_days_filter(self):
        """Тест получения записей веса с фильтром по дням."""
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        response = self.client.get(url, {'days': 1})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Должны получить записи за последний день
        self.assertIn('weight_records', data)
        self.assertEqual(data['count'], 2)  # Обе записи созданы сегодня
    
    def test_get_weight_records_nonexistent_user(self):
        """Тест получения записей веса для несуществующего пользователя."""
        url = reverse('webapp:weight_records', kwargs={'user_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_create_weight_record(self):
        """Тест создания новой записи веса."""
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        data = {
            'weight': 67.5,
            'notes': 'Новая запись веса'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        
        self.assertEqual(response_data['weight'], 67.5)
        self.assertEqual(response_data['notes'], 'Новая запись веса')
        self.assertEqual(response_data['user_id'], self.user.id)
        
        # Проверяем, что запись создалась в базе данных
        self.assertEqual(WeightRecord.objects.filter(user=self.user).count(), 3)
    
    def test_create_weight_record_invalid_weight(self):
        """Тест создания записи веса с неверным значением."""
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        data = {
            'weight': 'invalid',
            'notes': 'Неверный вес'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_create_weight_record_missing_weight(self):
        """Тест создания записи веса без обязательного поля."""
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        data = {
            'notes': 'Запись без веса'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)


class WeightRecordDetailAPITest(TestCase):
    """Тесты для API детальной информации о записи веса."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.weight_record = WeightRecord.objects.create(
            user=self.user,
            weight=Decimal('65.5'),
            notes='Тестовая запись'
        )
    
    def test_get_weight_record_detail(self):
        """Тест получения детальной информации о записи веса."""
        url = reverse('webapp:weight_record_detail', kwargs={
            'user_id': self.user.id,
            'record_id': self.weight_record.id
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['id'], self.weight_record.id)
        self.assertEqual(data['weight'], 65.5)
        self.assertEqual(data['notes'], 'Тестовая запись')
    
    def test_update_weight_record(self):
        """Тест обновления записи веса."""
        url = reverse('webapp:weight_record_detail', kwargs={
            'user_id': self.user.id,
            'record_id': self.weight_record.id
        })
        data = {
            'weight': 66.0,
            'notes': 'Обновленная запись'
        }
        
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertEqual(response_data['weight'], 66.0)
        self.assertEqual(response_data['notes'], 'Обновленная запись')
        
        # Проверяем обновление в базе данных
        self.weight_record.refresh_from_db()
        self.assertEqual(float(self.weight_record.weight), 66.0)
        self.assertEqual(self.weight_record.notes, 'Обновленная запись')
    
    def test_delete_weight_record(self):
        """Тест удаления записи веса."""
        url = reverse('webapp:weight_record_detail', kwargs={
            'user_id': self.user.id,
            'record_id': self.weight_record.id
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        
        # Проверяем, что запись удалилась из базы данных
        self.assertFalse(WeightRecord.objects.filter(id=self.weight_record.id).exists())


class BloodPressureRecordsAPITest(TestCase):
    """Тесты для API записей артериального давления."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем тестовые записи давления с разными временными метками
        self.bp_record1 = BloodPressureRecord.objects.create(
            user=self.user,
            date=timezone.now() - timedelta(minutes=10),
            systolic=120,
            diastolic=80,
            pulse=70,
            notes='Первая запись'
        )
        self.bp_record2 = BloodPressureRecord.objects.create(
            user=self.user,
            date=timezone.now() - timedelta(minutes=5),
            systolic=125,
            diastolic=82,
            notes='Вторая запись'
        )
    
    def test_get_blood_pressure_records(self):
        """Тест получения списка записей давления."""
        url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('blood_pressure_records', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['blood_pressure_records']), 2)
        
        # Проверяем структуру данных
        record = data['blood_pressure_records'][0]
        self.assertIn('id', record)
        self.assertIn('user_id', record)
        self.assertIn('date', record)
        self.assertIn('systolic', record)
        self.assertIn('diastolic', record)
        self.assertIn('pulse', record)
        self.assertIn('pressure_reading', record)
        self.assertIn('pressure_category', record)
        self.assertIn('is_normal', record)
        self.assertIn('needs_medical_attention', record)
    
    def test_create_blood_pressure_record(self):
        """Тест создания новой записи давления."""
        url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        data = {
            'systolic': 130,
            'diastolic': 85,
            'pulse': 75,
            'notes': 'Новая запись давления'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        
        self.assertEqual(response_data['systolic'], 130)
        self.assertEqual(response_data['diastolic'], 85)
        self.assertEqual(response_data['pulse'], 75)
        self.assertEqual(response_data['notes'], 'Новая запись давления')
        self.assertEqual(response_data['user_id'], self.user.id)
        
        # Проверяем, что запись создалась в базе данных
        self.assertEqual(BloodPressureRecord.objects.filter(user=self.user).count(), 3)
    
    def test_create_blood_pressure_record_without_pulse(self):
        """Тест создания записи давления без пульса."""
        url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        data = {
            'systolic': 115,
            'diastolic': 75,
            'notes': 'Запись без пульса'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        
        self.assertEqual(response_data['systolic'], 115)
        self.assertEqual(response_data['diastolic'], 75)
        self.assertIsNone(response_data['pulse'])
    
    def test_create_blood_pressure_record_missing_required_fields(self):
        """Тест создания записи давления без обязательных полей."""
        url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        data = {
            'systolic': 120,
            # Отсутствует diastolic
            'notes': 'Неполная запись'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)


class BloodPressureRecordDetailAPITest(TestCase):
    """Тесты для API детальной информации о записи давления."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.bp_record = BloodPressureRecord.objects.create(
            user=self.user,
            systolic=120,
            diastolic=80,
            pulse=70,
            notes='Тестовая запись'
        )
    
    def test_get_blood_pressure_record_detail(self):
        """Тест получения детальной информации о записи давления."""
        url = reverse('webapp:blood_pressure_record_detail', kwargs={
            'user_id': self.user.id,
            'record_id': self.bp_record.id
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['id'], self.bp_record.id)
        self.assertEqual(data['systolic'], 120)
        self.assertEqual(data['diastolic'], 80)
        self.assertEqual(data['pulse'], 70)
        self.assertEqual(data['notes'], 'Тестовая запись')
    
    def test_update_blood_pressure_record(self):
        """Тест обновления записи давления."""
        url = reverse('webapp:blood_pressure_record_detail', kwargs={
            'user_id': self.user.id,
            'record_id': self.bp_record.id
        })
        data = {
            'systolic': 125,
            'diastolic': 82,
            'pulse': 72,
            'notes': 'Обновленная запись'
        }
        
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertEqual(response_data['systolic'], 125)
        self.assertEqual(response_data['diastolic'], 82)
        self.assertEqual(response_data['pulse'], 72)
        self.assertEqual(response_data['notes'], 'Обновленная запись')
        
        # Проверяем обновление в базе данных
        self.bp_record.refresh_from_db()
        self.assertEqual(self.bp_record.systolic, 125)
        self.assertEqual(self.bp_record.diastolic, 82)
        self.assertEqual(self.bp_record.pulse, 72)
        self.assertEqual(self.bp_record.notes, 'Обновленная запись')
    
    def test_delete_blood_pressure_record(self):
        """Тест удаления записи давления."""
        url = reverse('webapp:blood_pressure_record_detail', kwargs={
            'user_id': self.user.id,
            'record_id': self.bp_record.id
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        
        # Проверяем, что запись удалилась из базы данных
        self.assertFalse(BloodPressureRecord.objects.filter(id=self.bp_record.id).exists())


class HealthStatisticsAPITest(TestCase):
    """Тесты для API статистики здоровья."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем записи веса с разными значениями и временными метками
        WeightRecord.objects.create(
            user=self.user, 
            date=timezone.now() - timedelta(days=2),
            weight=Decimal('65.0')
        )
        WeightRecord.objects.create(
            user=self.user, 
            date=timezone.now() - timedelta(days=1),
            weight=Decimal('66.0')
        )
        WeightRecord.objects.create(
            user=self.user, 
            date=timezone.now(),
            weight=Decimal('67.0')
        )
        
        # Создаем записи давления с разными категориями и временными метками
        BloodPressureRecord.objects.create(
            user=self.user, 
            date=timezone.now() - timedelta(hours=6),
            systolic=120, 
            diastolic=80
        )  # Нормальное
        BloodPressureRecord.objects.create(
            user=self.user, 
            date=timezone.now() - timedelta(hours=3),
            systolic=140, 
            diastolic=90
        )  # Высокое нормальное
        BloodPressureRecord.objects.create(
            user=self.user, 
            date=timezone.now(),
            systolic=160, 
            diastolic=100
        )  # Гипертония 1 степени
    
    def test_get_health_statistics(self):
        """Тест получения статистики здоровья."""
        url = reverse('webapp:health_statistics', kwargs={'user_id': self.user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Проверяем структуру ответа
        self.assertIn('period_days', data)
        self.assertIn('weight_statistics', data)
        self.assertIn('blood_pressure_statistics', data)
        self.assertIn('recommendations', data)
        
        # Проверяем статистику веса
        weight_stats = data['weight_statistics']
        self.assertEqual(weight_stats['count'], 3)
        self.assertEqual(weight_stats['latest_weight'], 67.0)
        self.assertEqual(weight_stats['average_weight'], 66.0)
        self.assertEqual(weight_stats['min_weight'], 65.0)
        self.assertEqual(weight_stats['max_weight'], 67.0)
        self.assertEqual(weight_stats['weight_change'], 2.0)
        self.assertEqual(weight_stats['trend'], 'increasing')
        
        # Проверяем статистику давления
        bp_stats = data['blood_pressure_statistics']
        self.assertEqual(bp_stats['count'], 3)
        self.assertEqual(bp_stats['latest_systolic'], 160)
        self.assertEqual(bp_stats['latest_diastolic'], 100)
        # Проверяем, что есть записи разных категорий
        self.assertGreaterEqual(bp_stats['normal_readings_count'], 1)
        self.assertGreaterEqual(bp_stats['high_readings_count'], 1)
    
    def test_get_health_statistics_with_custom_period(self):
        """Тест получения статистики за определенный период."""
        url = reverse('webapp:health_statistics', kwargs={'user_id': self.user.id})
        response = self.client.get(url, {'days': 7})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['period_days'], 7)
    
    def test_get_health_statistics_nonexistent_user(self):
        """Тест получения статистики для несуществующего пользователя."""
        url = reverse('webapp:health_statistics', kwargs={'user_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)


class HealthDataExportAPITest(TestCase):
    """Тесты для API экспорта данных о здоровье."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем тестовые данные
        WeightRecord.objects.create(user=self.user, weight=Decimal('65.0'))
        BloodPressureRecord.objects.create(user=self.user, systolic=120, diastolic=80)
    
    def test_export_health_data(self):
        """Тест экспорта данных о здоровье."""
        url = reverse('webapp:health_data_export', kwargs={'user_id': self.user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Проверяем структуру экспорта
        self.assertIn('user_id', data)
        self.assertIn('export_date', data)
        self.assertIn('weight_records', data)
        self.assertIn('blood_pressure_records', data)
        self.assertIn('total_weight_records', data)
        self.assertIn('total_bp_records', data)
        
        self.assertEqual(data['user_id'], self.user.id)
        self.assertEqual(data['total_weight_records'], 1)
        self.assertEqual(data['total_bp_records'], 1)
        self.assertEqual(len(data['weight_records']), 1)
        self.assertEqual(len(data['blood_pressure_records']), 1)
    
    def test_export_health_data_nonexistent_user(self):
        """Тест экспорта данных для несуществующего пользователя."""
        url = reverse('webapp:health_data_export', kwargs={'user_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)


class HealthAPIValidationTest(TestCase):
    """Тесты валидации для API здоровья."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_weight_record_with_extreme_values(self):
        """Тест создания записи веса с экстремальными значениями."""
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        
        # Тест с очень маленьким весом
        data = {'weight': 0.05}
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Тест с очень большим весом
        data = {'weight': 1000.0}
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_create_blood_pressure_record_with_extreme_values(self):
        """Тест создания записи давления с экстремальными значениями."""
        url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        
        # Тест с очень низким давлением
        data = {'systolic': 40, 'diastolic': 20}
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Тест с очень высоким давлением
        data = {'systolic': 350, 'diastolic': 250}
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_json_format(self):
        """Тест обработки неверного формата JSON."""
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        
        response = self.client.post(
            url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_invalid_date_format(self):
        """Тест обработки неверного формата даты."""
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        data = {
            'weight': 65.0,
            'date': 'invalid-date-format'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)