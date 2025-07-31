from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
import json

from webapp.models import FetalDevelopmentInfo, PregnancyInfo


class FetalDevelopmentAPITest(TestCase):
    """
    Тесты для API развития плода.
    
    Проверяет функциональность API для получения информации о развитии плода
    по неделям беременности (требование 10.3).
    """
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Создаем тестовые данные о развитии плода
        self.development_data = [
            {
                'week_number': 20,
                'title': '20-я неделя беременности',
                'fetal_size_description': 'Размером с банан',
                'fetal_length_mm': 118.0,
                'fetal_weight_g': 150.0,
                'organ_development': 'Развиваются легкие.',
                'maternal_changes': 'Живот заметно округлился.',
                'common_symptoms': 'Шевеления хорошо ощущаются.',
                'recommendations': 'Используйте крем от растяжек.',
                'dos_and_donts': 'Можно: путешествовать.',
                'medical_checkups': 'Подробное УЗИ.',
                'interesting_facts': 'Середина беременности!'
            },
            {
                'week_number': 21,
                'title': '21-я неделя беременности',
                'fetal_size_description': 'Размером с морковь',
                'fetal_length_mm': 128.0,
                'fetal_weight_g': 180.0,
                'organ_development': 'Развивается пищеварительная система.',
                'maternal_changes': 'Возможны проблемы со сном.',
                'common_symptoms': 'Изжога, одышка.',
                'recommendations': 'Спите на боку.',
                'dos_and_donts': 'Можно: пренатальная йога.',
                'medical_checkups': 'Регулярные визиты к врачу.',
                'interesting_facts': 'Плод может икать.'
            }
        ]
        
        # Создаем записи в базе данных
        for data in self.development_data:
            FetalDevelopmentInfo.objects.create(**data)
        
        # Создаем информацию о беременности
        due_date = date.today() + timedelta(days=140)  # 20 недель до родов
        self.pregnancy_info = PregnancyInfo.objects.create(
            user=self.user,
            due_date=due_date,
            is_active=True
        )
    
    def test_fetal_development_week_unauthorized(self):
        """Тест доступа к API без авторизации."""
        url = reverse('webapp:fetal_development_week', kwargs={'week_number': 20})
        response = self.client.get(url)
        
        # Должен перенаправить на страницу входа
        self.assertEqual(response.status_code, 302)
    
    def test_fetal_development_week_authorized(self):
        """Тест получения информации о конкретной неделе."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_week', kwargs={'week_number': 20})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['week_number'], 20)
        self.assertEqual(data['data']['title'], '20-я неделя беременности')
        self.assertEqual(data['data']['fetal_length_mm'], 118.0)
        self.assertEqual(data['data']['fetal_weight_g'], 150.0)
        self.assertEqual(data['data']['trimester'], 2)
        self.assertEqual(data['data']['trimester_name'], 'Второй триместр')
    
    def test_fetal_development_week_not_found(self):
        """Тест получения информации о несуществующей неделе."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_week', kwargs={'week_number': 25})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('не найдена', data['error'])
    
    def test_fetal_development_week_invalid_number(self):
        """Тест с неверным номером недели."""
        self.client.login(username='testuser', password='testpass123')
        
        # Тест с номером недели меньше 1
        url = reverse('webapp:fetal_development_week', kwargs={'week_number': 0})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('от 1 до 42', data['error'])
        
        # Тест с номером недели больше 42
        url = reverse('webapp:fetal_development_week', kwargs={'week_number': 43})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('от 1 до 42', data['error'])
    
    def test_fetal_development_current_with_pregnancy(self):
        """Тест получения информации о текущей неделе беременности."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_current')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Проверяем структуру ответа
        self.assertIn('current', data['data'])
        self.assertIn('previous', data['data'])
        self.assertIn('next', data['data'])
        self.assertIn('pregnancy_info', data['data'])
        
        # Проверяем информацию о текущей неделе
        current_week = data['data']['current']['week_number']
        expected_week = self.pregnancy_info.current_week
        self.assertEqual(current_week, expected_week)
        
        # Проверяем информацию о беременности
        pregnancy_data = data['data']['pregnancy_info']
        self.assertEqual(pregnancy_data['current_week'], expected_week)
        self.assertEqual(pregnancy_data['trimester'], 2)
    
    def test_fetal_development_current_without_pregnancy(self):
        """Тест получения информации без активной беременности."""
        # Создаем пользователя без беременности
        user_no_pregnancy = User.objects.create_user(
            username='nopregnancy',
            password='testpass123'
        )
        
        self.client.login(username='nopregnancy', password='testpass123')
        
        url = reverse('webapp:fetal_development_current')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('не найдена', data['error'])
    
    def test_fetal_development_list_all(self):
        """Тест получения списка всей информации о развитии."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['data']), 2)
        
        # Проверяем сортировку по номеру недели
        self.assertEqual(data['data'][0]['week_number'], 20)
        self.assertEqual(data['data'][1]['week_number'], 21)
    
    def test_fetal_development_list_by_trimester(self):
        """Тест получения списка по триместру."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_list')
        response = self.client.get(url, {'trimester': 2})
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 2)  # Обе недели во втором триместре
    
    def test_fetal_development_list_by_weeks_range(self):
        """Тест получения списка по диапазону недель."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_list')
        response = self.client.get(url, {'start_week': 20, 'end_week': 20})
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['data'][0]['week_number'], 20)
    
    def test_fetal_development_list_summary_only(self):
        """Тест получения краткой информации."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_list')
        response = self.client.get(url, {'summary_only': 'true'})
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Проверяем, что возвращается только краткая информация
        first_item = data['data'][0]
        self.assertIn('week_number', first_item)
        self.assertIn('title', first_item)
        self.assertIn('fetal_size_description', first_item)
        self.assertIn('development_summary', first_item)
        self.assertIn('trimester', first_item)
        self.assertIn('trimester_name', first_item)
        
        # Проверяем, что полная информация не включена
        self.assertNotIn('organ_development', first_item)
        self.assertNotIn('maternal_changes', first_item)
    
    def test_fetal_development_list_invalid_trimester(self):
        """Тест с неверным номером триместра."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_list')
        response = self.client.get(url, {'trimester': 4})
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('1, 2 или 3', data['error'])
    
    def test_fetal_development_list_invalid_weeks_range(self):
        """Тест с неверным диапазоном недель."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_list')
        response = self.client.get(url, {'start_week': 25, 'end_week': 20})
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Неверный диапазон', data['error'])
    
    def test_api_response_structure(self):
        """Тест структуры ответа API."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_week', kwargs={'week_number': 20})
        response = self.client.get(url)
        
        data = json.loads(response.content)
        
        # Проверяем обязательные поля в ответе
        required_fields = [
            'week_number', 'title', 'fetal_size_description', 'fetal_size_formatted',
            'fetal_length_mm', 'fetal_weight_g', 'organ_development', 'maternal_changes',
            'common_symptoms', 'recommendations', 'dos_and_donts', 'medical_checkups',
            'interesting_facts', 'trimester', 'trimester_name', 'development_summary'
        ]
        
        for field in required_fields:
            self.assertIn(field, data['data'])
    
    def test_api_handles_missing_data_gracefully(self):
        """Тест обработки отсутствующих данных."""
        # Создаем запись с минимальными данными
        minimal_data = {
            'week_number': 25,
            'title': '25-я неделя беременности',
            'fetal_size_description': '',
            'organ_development': '',
            'maternal_changes': '',
            'common_symptoms': '',
            'recommendations': '',
            'dos_and_donts': '',
            'medical_checkups': '',
            'interesting_facts': ''
        }
        FetalDevelopmentInfo.objects.create(**minimal_data)
        
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_week', kwargs={'week_number': 25})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['week_number'], 25)
    
    def test_api_content_type(self):
        """Тест типа контента ответа API."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_week', kwargs={'week_number': 20})
        response = self.client.get(url)
        
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_api_methods_allowed(self):
        """Тест разрешенных HTTP методов."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development_week', kwargs={'week_number': 20})
        
        # GET должен работать
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # POST не должен работать
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        
        # PUT не должен работать
        response = self.client.put(url)
        self.assertEqual(response.status_code, 405)
        
        # DELETE не должен работать
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 405)