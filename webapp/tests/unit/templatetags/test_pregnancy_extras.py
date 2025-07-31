"""
Тесты для дополнительных тегов и фильтров для шаблонов беременности.

Этот модуль содержит тесты для проверки корректности работы
пользовательских тегов и фильтров Django для работы с данными о беременности.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.template import Context, Template
from datetime import date, timedelta
from webapp.models import PregnancyInfo
from webapp.templatetags.pregnancy_extras import (
    multiply, pregnancy_week, pregnancy_progress, pregnancy_trimester,
    days_until_due, days_pregnant, is_high_risk, is_full_term,
    current_day_of_week, format_pregnancy_duration, pregnancy_status_class,
    trimester_color, safe_percentage
)


class PregnancyExtrasTest(TestCase):
    """Тесты для дополнительных тегов и фильтров беременности."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем беременность на 20 неделе (середина)
        due_date = date.today() + timedelta(days=140)  # ~20 недель до родов
        self.pregnancy_info = PregnancyInfo.objects.create(
            user=self.user,
            due_date=due_date,
            is_active=True
        )
    
    def test_multiply_filter(self):
        """Тест фильтра умножения."""
        result = multiply(5, 3)
        self.assertEqual(result, 15)
        
        result = multiply(3.14, 2)
        self.assertEqual(result, 6.28)
        
        # Тест с некорректными данными
        result = multiply('invalid', 2)
        self.assertEqual(result, 0)
    
    def test_pregnancy_week_filter(self):
        """Тест фильтра получения недели беременности."""
        week = pregnancy_week(self.pregnancy_info)
        self.assertIsInstance(week, int)
        self.assertGreater(week, 0)
        self.assertLessEqual(week, 42)
        
        # Тест с None
        week = pregnancy_week(None)
        self.assertIsNone(week)
    
    def test_pregnancy_progress_filter(self):
        """Тест фильтра получения прогресса беременности."""
        progress = pregnancy_progress(self.pregnancy_info)
        self.assertIsInstance(progress, (int, float))
        self.assertGreaterEqual(progress, 0)
        self.assertLessEqual(progress, 100)
        
        # Тест с None
        progress = pregnancy_progress(None)
        self.assertEqual(progress, 0)
    
    def test_pregnancy_trimester_filter(self):
        """Тест фильтра получения триместра беременности."""
        trimester = pregnancy_trimester(self.pregnancy_info)
        self.assertIn(trimester, [1, 2, 3])
        
        # Тест с None
        trimester = pregnancy_trimester(None)
        self.assertIsNone(trimester)
    
    def test_days_until_due_filter(self):
        """Тест фильтра получения дней до ПДР."""
        days = days_until_due(self.pregnancy_info)
        self.assertIsInstance(days, int)
        
        # Тест с None
        days = days_until_due(None)
        self.assertIsNone(days)
    
    def test_days_pregnant_filter(self):
        """Тест фильтра получения дней беременности."""
        days = days_pregnant(self.pregnancy_info)
        self.assertIsInstance(days, int)
        self.assertGreaterEqual(days, 0)
        
        # Тест с None
        days = days_pregnant(None)
        self.assertEqual(days, 0)
    
    def test_is_high_risk_filter(self):
        """Тест фильтра определения высокого риска."""
        risk = is_high_risk(self.pregnancy_info)
        self.assertIsInstance(risk, bool)
        
        # Тест с None
        risk = is_high_risk(None)
        self.assertFalse(risk)
    
    def test_is_full_term_filter(self):
        """Тест фильтра определения доношенности."""
        full_term = is_full_term(self.pregnancy_info)
        self.assertIsInstance(full_term, bool)
        
        # Тест с None
        full_term = is_full_term(None)
        self.assertFalse(full_term)
    
    def test_current_day_of_week_filter(self):
        """Тест фильтра получения дня недели беременности."""
        day = current_day_of_week(self.pregnancy_info)
        self.assertIsInstance(day, int)
        self.assertGreaterEqual(day, 0)
        self.assertLessEqual(day, 7)
        
        # Тест с None
        day = current_day_of_week(None)
        self.assertEqual(day, 0)
    
    def test_format_pregnancy_duration_filter(self):
        """Тест фильтра форматирования продолжительности беременности."""
        # Тест с днями
        result = format_pregnancy_duration(5)
        self.assertEqual(result, "5 дн.")
        
        # Тест с неделями
        result = format_pregnancy_duration(14)
        self.assertEqual(result, "2 нед.")
        
        # Тест с неделями и днями
        result = format_pregnancy_duration(16)
        self.assertEqual(result, "2 нед. 2 дн.")
        
        # Тест с нулем
        result = format_pregnancy_duration(0)
        self.assertEqual(result, "0 дней")
        
        # Тест с отрицательным числом
        result = format_pregnancy_duration(-5)
        self.assertEqual(result, "0 дней")
    
    def test_pregnancy_status_class_filter(self):
        """Тест фильтра получения CSS класса статуса беременности."""
        status_class = pregnancy_status_class(self.pregnancy_info)
        self.assertIn(status_class, [
            'first-trimester', 'second-trimester', 'third-trimester', 
            'full-term', 'overdue', 'inactive'
        ])
        
        # Тест с None
        status_class = pregnancy_status_class(None)
        self.assertEqual(status_class, "inactive")
    
    def test_trimester_color_filter(self):
        """Тест фильтра получения цвета триместра."""
        color1 = trimester_color(1)
        self.assertEqual(color1, "#ff9a9e")
        
        color2 = trimester_color(2)
        self.assertEqual(color2, "#a8edea")
        
        color3 = trimester_color(3)
        self.assertEqual(color3, "#ffd89b")
        
        # Тест с неизвестным триместром
        color_unknown = trimester_color(4)
        self.assertEqual(color_unknown, "#e2e8f0")
    
    def test_safe_percentage_filter(self):
        """Тест фильтра безопасного процента."""
        # Нормальное значение
        result = safe_percentage(50)
        self.assertEqual(result, 50)
        
        # Значение больше максимума
        result = safe_percentage(150, 100)
        self.assertEqual(result, 100)
        
        # Отрицательное значение
        result = safe_percentage(-10)
        self.assertEqual(result, 0)
        
        # Некорректное значение
        result = safe_percentage('invalid')
        self.assertEqual(result, 0)
    
    def test_template_integration(self):
        """Тест интеграции фильтров в шаблоне."""
        template = Template("""
            {% load pregnancy_extras %}
            Week: {{ pregnancy_info|pregnancy_week }}
            Progress: {{ pregnancy_info|pregnancy_progress }}%
            Trimester: {{ pregnancy_info|pregnancy_trimester }}
            Days until due: {{ pregnancy_info|days_until_due }}
            Days pregnant: {{ pregnancy_info|days_pregnant }}
            Status class: {{ pregnancy_info|pregnancy_status_class }}
        """)
        
        context = Context({'pregnancy_info': self.pregnancy_info})
        rendered = template.render(context)
        
        # Проверяем, что все фильтры работают
        self.assertIn('Week:', rendered)
        self.assertIn('Progress:', rendered)
        self.assertIn('Trimester:', rendered)
        self.assertIn('Days until due:', rendered)
        self.assertIn('Days pregnant:', rendered)
        self.assertIn('Status class:', rendered)


class PregnancyExtrasEdgeCasesTest(TestCase):
    """Тесты граничных случаев для дополнительных тегов и фильтров беременности."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_early_pregnancy(self):
        """Тест фильтров для ранней беременности."""
        # Создаем беременность на 5 неделе
        due_date = date.today() + timedelta(days=245)  # ~35 недель до родов
        early_pregnancy = PregnancyInfo.objects.create(
            user=self.user,
            due_date=due_date,
            is_active=True
        )
        
        week = pregnancy_week(early_pregnancy)
        self.assertLessEqual(week, 12)  # Первый триместр
        
        trimester = pregnancy_trimester(early_pregnancy)
        self.assertEqual(trimester, 1)
        
        status_class = pregnancy_status_class(early_pregnancy)
        self.assertEqual(status_class, 'first-trimester')
    
    def test_late_pregnancy(self):
        """Тест фильтров для поздней беременности."""
        # Создаем беременность на 38 неделе (доношенная)
        due_date = date.today() + timedelta(days=14)  # ~2 недели до родов
        late_pregnancy = PregnancyInfo.objects.create(
            user=self.user,
            due_date=due_date,
            is_active=True
        )
        
        week = pregnancy_week(late_pregnancy)
        self.assertGreaterEqual(week, 37)  # Доношенная
        
        trimester = pregnancy_trimester(late_pregnancy)
        self.assertEqual(trimester, 3)
        
        full_term = is_full_term(late_pregnancy)
        self.assertTrue(full_term)
        
        status_class = pregnancy_status_class(late_pregnancy)
        self.assertEqual(status_class, 'full-term')
    
    def test_overdue_pregnancy(self):
        """Тест фильтров для просроченной беременности."""
        # Создаем просроченную беременность
        due_date = date.today() - timedelta(days=7)  # ПДР неделю назад
        overdue_pregnancy = PregnancyInfo.objects.create(
            user=self.user,
            due_date=due_date,
            is_active=True
        )
        
        week = pregnancy_week(overdue_pregnancy)
        self.assertGreaterEqual(week, 40)
        
        days_until = days_until_due(overdue_pregnancy)
        self.assertLess(days_until, 0)  # Отрицательное значение
        
        status_class = pregnancy_status_class(overdue_pregnancy)
        self.assertIn(status_class, ['full-term', 'overdue'])
    
    def test_inactive_pregnancy(self):
        """Тест фильтров для неактивной беременности."""
        # Создаем неактивную беременность
        due_date = date.today() + timedelta(days=140)
        inactive_pregnancy = PregnancyInfo.objects.create(
            user=self.user,
            due_date=due_date,
            is_active=False
        )
        
        week = pregnancy_week(inactive_pregnancy)
        self.assertIsNone(week)
        
        progress = pregnancy_progress(inactive_pregnancy)
        self.assertEqual(progress, 0)
        
        status_class = pregnancy_status_class(inactive_pregnancy)
        self.assertEqual(status_class, 'inactive')