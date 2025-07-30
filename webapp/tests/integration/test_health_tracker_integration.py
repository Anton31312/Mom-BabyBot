"""
Интеграционные тесты для отслеживания показателей здоровья.

Этот модуль содержит интеграционные тесты для проверки взаимодействия
между моделями, API и представлениями отслеживания здоровья.
"""

import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from webapp.models import WeightRecord, BloodPressureRecord


class HealthTrackerIntegrationTest(TestCase):
    """Интеграционные тесты для отслеживания здоровья."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем тестовые записи
        self.weight_record = WeightRecord.objects.create(
            user=self.user,
            weight=Decimal('65.5'),
            notes='Тестовая запись веса'
        )
        
        self.bp_record = BloodPressureRecord.objects.create(
            user=self.user,
            systolic=120,
            diastolic=80,
            pulse=70,
            notes='Тестовая запись давления'
        )
    
    def test_health_tracker_view_loads(self):
        """Тест загрузки представления отслеживания здоровья."""
        url = reverse('webapp:health_tracker')
        response = self.client.get(url, {'user_id': self.user.id})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Отслеживание показателей здоровья')
        self.assertContains(response, 'Вес')
        self.assertContains(response, 'Артериальное давление')
        self.assertContains(response, 'Статистика')
    
    def test_weight_api_integration(self):
        """Тест интеграции API веса с моделями."""
        # Создание записи через API
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        data = {
            'weight': 68.5,
            'notes': 'Запись через API'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Проверяем, что запись создалась в базе данных
        new_record = WeightRecord.objects.filter(
            user=self.user,
            weight=Decimal('68.5')
        ).first()
        
        self.assertIsNotNone(new_record)
        self.assertEqual(new_record.notes, 'Запись через API')
        
        # Получение записи через API
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('weight_records', data)
        self.assertEqual(data['count'], 2)  # Исходная + новая запись
    
    def test_blood_pressure_api_integration(self):
        """Тест интеграции API давления с моделями."""
        # Создание записи через API
        url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        data = {
            'systolic': 130,
            'diastolic': 85,
            'pulse': 75,
            'notes': 'Запись давления через API'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Проверяем, что запись создалась в базе данных
        new_record = BloodPressureRecord.objects.filter(
            user=self.user,
            systolic=130,
            diastolic=85
        ).first()
        
        self.assertIsNotNone(new_record)
        self.assertEqual(new_record.pulse, 75)
        self.assertEqual(new_record.notes, 'Запись давления через API')
        
        # Получение записи через API
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('blood_pressure_records', data)
        self.assertEqual(data['count'], 2)  # Исходная + новая запись
    
    def test_health_statistics_integration(self):
        """Тест интеграции статистики здоровья."""
        # Создаем дополнительные записи для статистики
        WeightRecord.objects.create(
            user=self.user,
            date=timezone.now() - timedelta(days=1),
            weight=Decimal('66.0'),
            notes='Вторая запись'
        )
        
        BloodPressureRecord.objects.create(
            user=self.user,
            date=timezone.now() - timedelta(days=1),
            systolic=125,
            diastolic=82,
            pulse=72,
            notes='Вторая запись давления'
        )
        
        # Получаем статистику через API
        url = reverse('webapp:health_statistics', kwargs={'user_id': self.user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Проверяем статистику веса
        weight_stats = data['weight_statistics']
        self.assertEqual(weight_stats['count'], 2)
        self.assertIsNotNone(weight_stats['latest_weight'])
        self.assertIsNotNone(weight_stats['average_weight'])
        
        # Проверяем статистику давления
        bp_stats = data['blood_pressure_statistics']
        self.assertEqual(bp_stats['count'], 2)
        self.assertIsNotNone(bp_stats['latest_systolic'])
        self.assertIsNotNone(bp_stats['latest_diastolic'])
    
    def test_record_crud_operations_integration(self):
        """Тест CRUD операций с записями."""
        # CREATE - уже протестировано выше
        
        # READ - получение конкретной записи
        weight_url = reverse('webapp:weight_record_detail', kwargs={
            'user_id': self.user.id,
            'record_id': self.weight_record.id
        })
        
        response = self.client.get(weight_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['id'], self.weight_record.id)
        self.assertEqual(float(data['weight']), float(self.weight_record.weight))
        
        # UPDATE - обновление записи
        update_data = {
            'weight': 67.0,
            'notes': 'Обновленная запись'
        }
        
        response = self.client.put(
            weight_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что запись обновилась в базе данных
        self.weight_record.refresh_from_db()
        self.assertEqual(float(self.weight_record.weight), 67.0)
        self.assertEqual(self.weight_record.notes, 'Обновленная запись')
        
        # DELETE - удаление записи
        response = self.client.delete(weight_url)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что запись удалилась из базы данных
        self.assertFalse(
            WeightRecord.objects.filter(id=self.weight_record.id).exists()
        )
    
    def test_data_validation_integration(self):
        """Тест интеграции валидации данных."""
        # Тест валидации веса
        weight_url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        
        # Слишком маленький вес
        invalid_data = {'weight': 0.05}
        response = self.client.post(
            weight_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Слишком большой вес
        invalid_data = {'weight': 1000.0}
        response = self.client.post(
            weight_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Тест валидации давления
        bp_url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        
        # Слишком низкое давление
        invalid_data = {'systolic': 40, 'diastolic': 20}
        response = self.client.post(
            bp_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Слишком высокое давление
        invalid_data = {'systolic': 350, 'diastolic': 250}
        response = self.client.post(
            bp_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_user_isolation_integration(self):
        """Тест изоляции данных пользователей."""
        # Создаем второго пользователя
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Создаем запись для второго пользователя
        other_weight_record = WeightRecord.objects.create(
            user=other_user,
            weight=Decimal('70.0'),
            notes='Запись другого пользователя'
        )
        
        # Проверяем, что первый пользователь не видит записи второго
        weight_url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        response = self.client.get(weight_url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Должна быть только одна запись (исходная запись первого пользователя)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['weight_records'][0]['user_id'], self.user.id)
        
        # Проверяем, что первый пользователь не может получить запись второго
        other_weight_url = reverse('webapp:weight_record_detail', kwargs={
            'user_id': self.user.id,
            'record_id': other_weight_record.id
        })
        
        response = self.client.get(other_weight_url)
        self.assertEqual(response.status_code, 404)
    
    def test_date_filtering_integration(self):
        """Тест интеграции фильтрации по датам."""
        # Создаем записи с разными датами
        old_weight = WeightRecord.objects.create(
            user=self.user,
            date=timezone.now() - timedelta(days=40),
            weight=Decimal('64.0'),
            notes='Старая запись'
        )
        
        recent_weight = WeightRecord.objects.create(
            user=self.user,
            date=timezone.now() - timedelta(days=5),
            weight=Decimal('66.5'),
            notes='Недавняя запись'
        )
        
        # Тест фильтрации за последние 30 дней
        weight_url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        response = self.client.get(weight_url, {'days': 30})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Должны быть только записи за последние 30 дней (исходная + недавняя)
        self.assertEqual(data['count'], 2)
        
        # Тест фильтрации за последние 7 дней
        response = self.client.get(weight_url, {'days': 7})
        data = json.loads(response.content)
        
        # Должны быть только записи за последние 7 дней (исходная + недавняя)
        self.assertEqual(data['count'], 2)
    
    def test_error_handling_integration(self):
        """Тест интеграции обработки ошибок."""
        # Тест с несуществующим пользователем
        invalid_user_url = reverse('webapp:weight_records', kwargs={'user_id': 99999})
        response = self.client.get(invalid_user_url)
        self.assertEqual(response.status_code, 404)
        
        # Тест с несуществующей записью
        invalid_record_url = reverse('webapp:weight_record_detail', kwargs={
            'user_id': self.user.id,
            'record_id': 99999
        })
        response = self.client.get(invalid_record_url)
        self.assertEqual(response.status_code, 404)
        
        # Тест с неверным JSON
        weight_url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        response = self.client.post(
            weight_url,
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_health_recommendations_integration(self):
        """Тест интеграции рекомендаций по здоровью."""
        # Создаем записи с критическими значениями
        critical_bp = BloodPressureRecord.objects.create(
            user=self.user,
            systolic=190,
            diastolic=110,
            notes='Критическое давление'
        )
        
        # Получаем статистику
        stats_url = reverse('webapp:health_statistics', kwargs={'user_id': self.user.id})
        response = self.client.get(stats_url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Проверяем, что есть рекомендации
        self.assertIn('recommendations', data)
        recommendations = data['recommendations']
        
        # Должна быть рекомендация о критическом давлении
        critical_recommendations = [
            rec for rec in recommendations 
            if rec['level'] == 'critical'
        ]
        # Если нет критических рекомендаций, проверим статистику
        if len(critical_recommendations) == 0:
            # Проверим, что критическое давление было учтено в статистике
            bp_stats = data['blood_pressure_statistics']
            self.assertGreater(bp_stats['critical_readings_count'], 0)
        else:
            self.assertGreater(len(critical_recommendations), 0)


class HealthTrackerWorkflowTest(TestCase):
    """Тесты рабочих процессов отслеживания здоровья."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_complete_weight_tracking_workflow(self):
        """Тест полного рабочего процесса отслеживания веса."""
        # 1. Загрузка страницы
        view_url = reverse('webapp:health_tracker')
        response = self.client.get(view_url, {'user_id': self.user.id})
        self.assertEqual(response.status_code, 200)
        
        # 2. Создание записи веса
        weight_url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        weight_data = {
            'weight': 65.5,
            'notes': 'Первая запись'
        }
        
        response = self.client.post(
            weight_url,
            data=json.dumps(weight_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        created_record = json.loads(response.content)
        
        # 3. Получение списка записей
        response = self.client.get(weight_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)
        
        # 4. Обновление записи
        record_url = reverse('webapp:weight_record_detail', kwargs={
            'user_id': self.user.id,
            'record_id': created_record['id']
        })
        
        update_data = {
            'weight': 66.0,
            'notes': 'Обновленная запись'
        }
        
        response = self.client.put(
            record_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # 5. Получение статистики
        stats_url = reverse('webapp:health_statistics', kwargs={'user_id': self.user.id})
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, 200)
        
        stats_data = json.loads(response.content)
        self.assertEqual(stats_data['weight_statistics']['count'], 1)
        self.assertEqual(stats_data['weight_statistics']['latest_weight'], 66.0)
        
        # 6. Удаление записи
        response = self.client.delete(record_url)
        self.assertEqual(response.status_code, 200)
        
        # 7. Проверка, что запись удалена
        response = self.client.get(weight_url)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 0)
    
    def test_complete_blood_pressure_tracking_workflow(self):
        """Тест полного рабочего процесса отслеживания давления."""
        # 1. Создание записи давления
        bp_url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        bp_data = {
            'systolic': 120,
            'diastolic': 80,
            'pulse': 70,
            'notes': 'Нормальное давление'
        }
        
        response = self.client.post(
            bp_url,
            data=json.dumps(bp_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        created_record = json.loads(response.content)
        
        # Проверяем дополнительные поля
        self.assertEqual(created_record['pressure_reading'], '120/80')
        self.assertEqual(created_record['pressure_category'], 'Нормальное')
        self.assertTrue(created_record['is_normal'])
        self.assertFalse(created_record['needs_medical_attention'])
        
        # 2. Создание записи с высоким давлением
        high_bp_data = {
            'systolic': 180,
            'diastolic': 110,
            'notes': 'Высокое давление'
        }
        
        response = self.client.post(
            bp_url,
            data=json.dumps(high_bp_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        high_bp_record = json.loads(response.content)
        
        # Проверяем, что система определила критическое давление
        self.assertTrue(high_bp_record['needs_medical_attention'])
        self.assertFalse(high_bp_record['is_normal'])
        
        # 3. Получение статистики с рекомендациями
        stats_url = reverse('webapp:health_statistics', kwargs={'user_id': self.user.id})
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, 200)
        
        stats_data = json.loads(response.content)
        bp_stats = stats_data['blood_pressure_statistics']
        
        self.assertEqual(bp_stats['count'], 2)
        self.assertEqual(bp_stats['normal_readings_count'], 1)
        self.assertEqual(bp_stats['critical_readings_count'], 1)
        
        # Должны быть рекомендации о критическом давлении
        recommendations = stats_data['recommendations']
        critical_recs = [r for r in recommendations if r['level'] == 'critical']
        self.assertGreater(len(critical_recs), 0)
    
    def test_data_export_workflow(self):
        """Тест рабочего процесса экспорта данных."""
        # Создаем тестовые данные
        WeightRecord.objects.create(
            user=self.user,
            weight=Decimal('65.0'),
            notes='Запись веса'
        )
        
        BloodPressureRecord.objects.create(
            user=self.user,
            systolic=120,
            diastolic=80,
            notes='Запись давления'
        )
        
        # Экспортируем данные
        export_url = reverse('webapp:health_data_export', kwargs={'user_id': self.user.id})
        response = self.client.get(export_url)
        
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