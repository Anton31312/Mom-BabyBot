"""
Тесты для визуализации данных о здоровье.

Этот модуль содержит тесты для проверки функциональности визуализации
данных веса и артериального давления в виде графиков.
Соответствует требованию 7.3 и 7.4 о визуализации данных о здоровье.
"""

import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from webapp.models import WeightRecord, BloodPressureRecord


class HealthVisualizationTest(TestCase):
    """Тесты для визуализации данных о здоровье."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем тестовые данные для графиков
        self.create_test_data()
    
    def create_test_data(self):
        """Создание тестовых данных для визуализации."""
        # Создаем записи веса за последние 30 дней
        for i in range(30):
            date = timezone.now() - timedelta(days=i)
            weight = Decimal(f'{65 + (i % 10) * 0.5:.1f}')  # Вариация веса
            
            WeightRecord.objects.create(
                user=self.user,
                date=date,
                weight=weight,
                notes=f'Запись веса {i}'
            )
        
        # Создаем записи давления за последние 30 дней
        for i in range(30):
            date = timezone.now() - timedelta(days=i)
            systolic = 120 + (i % 20) - 10  # Вариация от 110 до 130
            diastolic = 80 + (i % 10) - 5   # Вариация от 75 до 85
            pulse = 70 + (i % 15) - 7       # Вариация от 63 до 78
            
            BloodPressureRecord.objects.create(
                user=self.user,
                date=date,
                systolic=systolic,
                diastolic=diastolic,
                pulse=pulse,
                notes=f'Запись давления {i}'
            )
    
    def test_health_tracker_page_contains_charts(self):
        """Тест наличия элементов графиков на странице."""
        url = reverse('webapp:health_tracker')
        response = self.client.get(url, {'user_id': self.user.id})
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие canvas элементов для графиков
        self.assertContains(response, 'id="weightChart"')
        self.assertContains(response, 'id="bloodPressureChart"')
        
        # Проверяем наличие Chart.js библиотеки
        self.assertContains(response, 'chart.js')
        
        # Проверяем наличие заголовков графиков
        self.assertContains(response, 'График изменения веса')
        self.assertContains(response, 'График изменения артериального давления')
    
    def test_weight_data_for_visualization(self):
        """Тест данных веса для визуализации."""
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        response = self.client.get(url, {'days': 30})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Проверяем, что данные подходят для визуализации
        self.assertIn('weight_records', data)
        records = data['weight_records']
        
        self.assertEqual(len(records), 30)
        
        # Проверяем структуру данных для графика
        for record in records:
            self.assertIn('id', record)
            self.assertIn('date', record)
            self.assertIn('weight', record)
            
            # Проверяем, что дата в правильном формате
            date_obj = datetime.fromisoformat(record['date'].replace('Z', '+00:00'))
            self.assertIsInstance(date_obj, datetime)
            
            # Проверяем, что вес является числом
            self.assertIsInstance(record['weight'], (int, float))
    
    def test_blood_pressure_data_for_visualization(self):
        """Тест данных давления для визуализации."""
        url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        response = self.client.get(url, {'days': 30})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Проверяем, что данные подходят для визуализации
        self.assertIn('blood_pressure_records', data)
        records = data['blood_pressure_records']
        
        self.assertEqual(len(records), 30)
        
        # Проверяем структуру данных для графика
        for record in records:
            self.assertIn('id', record)
            self.assertIn('date', record)
            self.assertIn('systolic', record)
            self.assertIn('diastolic', record)
            self.assertIn('pulse', record)
            
            # Проверяем, что дата в правильном формате
            date_obj = datetime.fromisoformat(record['date'].replace('Z', '+00:00'))
            self.assertIsInstance(date_obj, datetime)
            
            # Проверяем, что значения являются числами
            self.assertIsInstance(record['systolic'], int)
            self.assertIsInstance(record['diastolic'], int)
            if record['pulse'] is not None:
                self.assertIsInstance(record['pulse'], int)
    
    def test_data_sorting_for_charts(self):
        """Тест сортировки данных для графиков."""
        url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        response = self.client.get(url, {'days': 30})
        
        data = json.loads(response.content)
        records = data['weight_records']
        
        # Проверяем, что записи отсортированы по дате (новые первыми)
        dates = [datetime.fromisoformat(record['date'].replace('Z', '+00:00')) for record in records]
        
        for i in range(1, len(dates)):
            self.assertGreaterEqual(dates[i-1], dates[i], 
                                  "Записи должны быть отсортированы по дате (новые первыми)")
    
    def test_abnormal_values_identification(self):
        """Тест выделения значений вне нормы."""
        # Создаем записи с критическими значениями
        critical_bp = BloodPressureRecord.objects.create(
            user=self.user,
            date=timezone.now(),
            systolic=190,  # Критически высокое
            diastolic=110, # Критически высокое
            notes='Критическое давление'
        )
        
        low_bp = BloodPressureRecord.objects.create(
            user=self.user,
            date=timezone.now() - timedelta(hours=1),
            systolic=85,   # Низкое
            diastolic=55,  # Низкое
            notes='Низкое давление'
        )
        
        # Получаем данные через API
        url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        response = self.client.get(url, {'days': 1})
        
        data = json.loads(response.content)
        records = data['blood_pressure_records']
        
        # Находим критические записи
        critical_record = next((r for r in records if r['systolic'] == 190), None)
        low_record = next((r for r in records if r['systolic'] == 85), None)
        
        self.assertIsNotNone(critical_record)
        self.assertIsNotNone(low_record)
        
        # Проверяем, что система правильно определяет критические значения
        self.assertTrue(critical_record['needs_medical_attention'])
        self.assertTrue(low_record['needs_medical_attention'])
        
        # Проверяем категории давления
        self.assertIn('Гипертония', critical_record['pressure_category'])
        self.assertEqual(low_record['pressure_category'], 'Пониженное')
    
    def test_chart_data_with_different_periods(self):
        """Тест данных графиков для разных периодов."""
        periods = [7, 30, 90, 365]
        
        for days in periods:
            # Тест данных веса
            weight_url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
            response = self.client.get(weight_url, {'days': days})
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            
            # Проверяем, что количество записей не превышает запрошенный период
            records = data['weight_records']
            expected_count = min(days, 30)  # У нас есть только 30 записей
            self.assertEqual(len(records), expected_count)
            
            # Тест данных давления
            bp_url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
            response = self.client.get(bp_url, {'days': days})
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            
            records = data['blood_pressure_records']
            # Учитываем дополнительные записи, созданные в предыдущем тесте
            expected_count = min(days, BloodPressureRecord.objects.filter(user=self.user).count())
            self.assertEqual(len(records), expected_count)
    
    def test_empty_data_handling(self):
        """Тест обработки пустых данных для графиков."""
        # Создаем нового пользователя без данных
        empty_user = User.objects.create_user(
            username='emptyuser',
            email='empty@example.com',
            password='emptypass123'
        )
        
        # Тест пустых данных веса
        weight_url = reverse('webapp:weight_records', kwargs={'user_id': empty_user.id})
        response = self.client.get(weight_url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['weight_records']), 0)
        
        # Тест пустых данных давления
        bp_url = reverse('webapp:blood_pressure_records', kwargs={'user_id': empty_user.id})
        response = self.client.get(bp_url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['blood_pressure_records']), 0)
    
    def test_statistics_with_visualization_data(self):
        """Тест статистики с данными для визуализации."""
        url = reverse('webapp:health_statistics', kwargs={'user_id': self.user.id})
        response = self.client.get(url, {'days': 30})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Проверяем статистику веса
        weight_stats = data['weight_statistics']
        self.assertEqual(weight_stats['count'], 30)
        self.assertIsNotNone(weight_stats['latest_weight'])
        self.assertIsNotNone(weight_stats['average_weight'])
        self.assertIsNotNone(weight_stats['min_weight'])
        self.assertIsNotNone(weight_stats['max_weight'])
        
        # Проверяем статистику давления
        bp_stats = data['blood_pressure_statistics']
        self.assertGreaterEqual(bp_stats['count'], 30)  # Включая дополнительные записи
        self.assertIsNotNone(bp_stats['latest_systolic'])
        self.assertIsNotNone(bp_stats['latest_diastolic'])
        self.assertIsNotNone(bp_stats['average_systolic'])
        self.assertIsNotNone(bp_stats['average_diastolic'])
    
    def test_trend_calculation_data(self):
        """Тест данных для расчета трендов."""
        # Создаем данные с явным трендом (увеличение веса)
        trend_user = User.objects.create_user(
            username='trenduser',
            email='trend@example.com',
            password='trendpass123'
        )
        
        # Создаем записи с возрастающим весом
        for i in range(10):
            date = timezone.now() - timedelta(days=9-i)  # От старых к новым
            weight = Decimal(f'{60 + i * 0.5:.1f}')      # Увеличение на 0.5 кг каждый день
            
            WeightRecord.objects.create(
                user=trend_user,
                date=date,
                weight=weight,
                notes=f'Тренд запись {i}'
            )
        
        # Получаем статистику
        url = reverse('webapp:health_statistics', kwargs={'user_id': trend_user.id})
        response = self.client.get(url, {'days': 10})
        
        data = json.loads(response.content)
        weight_stats = data['weight_statistics']
        
        # Проверяем, что тренд определен как увеличивающийся
        self.assertEqual(weight_stats['trend'], 'increasing')
        self.assertGreater(weight_stats['weight_change'], 0)
        
        # Проверяем корректность расчета изменения
        expected_change = 4.5  # 9 дней * 0.5 кг/день
        self.assertAlmostEqual(weight_stats['weight_change'], expected_change, places=1)


class HealthVisualizationIntegrationTest(TestCase):
    """Интеграционные тесты визуализации здоровья."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_full_visualization_workflow(self):
        """Тест полного рабочего процесса визуализации."""
        # 1. Создание данных через API
        weight_url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        bp_url = reverse('webapp:blood_pressure_records', kwargs={'user_id': self.user.id})
        
        # Создаем несколько записей веса
        weight_data = [
            {'weight': 65.0, 'notes': 'Первая запись'},
            {'weight': 65.5, 'notes': 'Вторая запись'},
            {'weight': 66.0, 'notes': 'Третья запись'},
        ]
        
        for data in weight_data:
            response = self.client.post(
                weight_url,
                data=json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
        
        # Создаем несколько записей давления
        bp_data = [
            {'systolic': 120, 'diastolic': 80, 'pulse': 70, 'notes': 'Нормальное'},
            {'systolic': 130, 'diastolic': 85, 'pulse': 75, 'notes': 'Повышенное'},
            {'systolic': 125, 'diastolic': 82, 'pulse': 72, 'notes': 'Среднее'},
        ]
        
        for data in bp_data:
            response = self.client.post(
                bp_url,
                data=json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
        
        # 2. Проверка загрузки страницы с графиками
        view_url = reverse('webapp:health_tracker')
        response = self.client.get(view_url, {'user_id': self.user.id})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'weightChart')
        self.assertContains(response, 'bloodPressureChart')
        
        # 3. Проверка данных для графиков
        response = self.client.get(weight_url)
        weight_chart_data = json.loads(response.content)
        
        self.assertEqual(weight_chart_data['count'], 3)
        self.assertEqual(len(weight_chart_data['weight_records']), 3)
        
        response = self.client.get(bp_url)
        bp_chart_data = json.loads(response.content)
        
        self.assertEqual(bp_chart_data['count'], 3)
        self.assertEqual(len(bp_chart_data['blood_pressure_records']), 3)
        
        # 4. Проверка статистики для визуализации
        stats_url = reverse('webapp:health_statistics', kwargs={'user_id': self.user.id})
        response = self.client.get(stats_url)
        
        self.assertEqual(response.status_code, 200)
        stats_data = json.loads(response.content)
        
        # Проверяем, что статистика содержит данные для визуализации
        self.assertIn('weight_statistics', stats_data)
        self.assertIn('blood_pressure_statistics', stats_data)
        
        weight_stats = stats_data['weight_statistics']
        bp_stats = stats_data['blood_pressure_statistics']
        
        self.assertEqual(weight_stats['count'], 3)
        self.assertEqual(bp_stats['count'], 3)
        
        # Проверяем наличие данных для трендов
        self.assertIn('trend', weight_stats)
        self.assertIn('weight_change', weight_stats)
    
    def test_chart_data_consistency(self):
        """Тест согласованности данных между API и графиками."""
        # Создаем записи с известными значениями
        test_records = [
            {'date': timezone.now() - timedelta(days=2), 'weight': Decimal('65.0')},
            {'date': timezone.now() - timedelta(days=1), 'weight': Decimal('65.5')},
            {'date': timezone.now(), 'weight': Decimal('66.0')},
        ]
        
        created_records = []
        for record_data in test_records:
            record = WeightRecord.objects.create(
                user=self.user,
                date=record_data['date'],
                weight=record_data['weight'],
                notes='Тестовая запись'
            )
            created_records.append(record)
        
        # Получаем данные через API
        weight_url = reverse('webapp:weight_records', kwargs={'user_id': self.user.id})
        response = self.client.get(weight_url, {'days': 7})
        
        api_data = json.loads(response.content)
        api_records = api_data['weight_records']
        
        # Проверяем согласованность данных
        self.assertEqual(len(api_records), 3)
        
        # Сортируем записи по дате для сравнения
        api_records_sorted = sorted(api_records, key=lambda x: x['date'])
        created_records_sorted = sorted(created_records, key=lambda x: x.date)
        
        for api_record, db_record in zip(api_records_sorted, created_records_sorted):
            self.assertEqual(float(api_record['weight']), float(db_record.weight))
            
            # Проверяем, что даты совпадают (с учетом часового пояса)
            api_date = datetime.fromisoformat(api_record['date'].replace('Z', '+00:00'))
            db_date = db_record.date
            
            # Сравниваем с точностью до секунды
            self.assertLess(abs((api_date - db_date).total_seconds()), 1)