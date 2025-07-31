"""
Тесты для утилит работы с беременностью.

Этот модуль содержит тесты для функций расчета недель беременности
и других утилитарных функций для работы с беременностью.
"""

from django.test import TestCase
from datetime import date, timedelta
from webapp.utils.pregnancy_utils import (
    calculate_pregnancy_start_date,
    calculate_current_pregnancy_week,
    calculate_current_day_of_week,
    calculate_days_until_due,
    calculate_weeks_until_due,
    determine_trimester,
    calculate_progress_percentage,
    is_pregnancy_overdue,
    is_pregnancy_full_term,
    is_pregnancy_preterm_risk,
    get_week_description,
    get_important_pregnancy_dates,
    get_pregnancy_milestones,
    calculate_estimated_conception_date,
    calculate_due_date_from_lmp,
    calculate_due_date_from_conception,
    get_pregnancy_week_range,
    is_high_risk_week,
    get_recommended_checkup_schedule,
)


class PregnancyUtilsTest(TestCase):
    """Тесты для утилит работы с беременностью."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.today = date.today()
        self.due_date = self.today + timedelta(days=140)  # 20 недель до родов
        self.lmp_date = self.today - timedelta(days=140)  # 20 недель назад
        self.conception_date = self.today - timedelta(days=126)  # 18 недель назад
    
    def test_calculate_pregnancy_start_date_with_lmp(self):
        """Тест расчета даты начала беременности с датой последней менструации."""
        start_date = calculate_pregnancy_start_date(
            due_date=self.due_date,
            last_menstrual_period=self.lmp_date
        )
        self.assertEqual(start_date, self.lmp_date)
    
    def test_calculate_pregnancy_start_date_with_conception(self):
        """Тест расчета даты начала беременности с датой зачатия."""
        start_date = calculate_pregnancy_start_date(
            due_date=self.due_date,
            conception_date=self.conception_date
        )
        expected_start = self.conception_date - timedelta(days=14)
        self.assertEqual(start_date, expected_start)
    
    def test_calculate_pregnancy_start_date_from_due_date(self):
        """Тест расчета даты начала беременности только от ПДР."""
        start_date = calculate_pregnancy_start_date(due_date=self.due_date)
        expected_start = self.due_date - timedelta(days=280)
        self.assertEqual(start_date, expected_start)
    
    def test_calculate_current_pregnancy_week(self):
        """Тест расчета текущей недели беременности."""
        # Беременность началась 10 недель назад
        start_date = self.today - timedelta(weeks=10)
        week = calculate_current_pregnancy_week(start_date, is_active=True)
        
        # Должно быть около 11 недели (10 полных + текущая)
        self.assertGreaterEqual(week, 10)
        self.assertLessEqual(week, 12)
    
    def test_calculate_current_pregnancy_week_inactive(self):
        """Тест расчета недели для неактивной беременности."""
        start_date = self.today - timedelta(weeks=10)
        week = calculate_current_pregnancy_week(start_date, is_active=False)
        self.assertIsNone(week)
    
    def test_calculate_current_pregnancy_week_future(self):
        """Тест расчета недели для будущей беременности."""
        start_date = self.today + timedelta(days=30)
        week = calculate_current_pregnancy_week(start_date, is_active=True)
        self.assertEqual(week, 0)
    
    def test_calculate_current_pregnancy_week_maximum(self):
        """Тест ограничения максимальной недели беременности."""
        start_date = self.today - timedelta(weeks=45)
        week = calculate_current_pregnancy_week(start_date, is_active=True)
        self.assertEqual(week, 42)
    
    def test_calculate_current_day_of_week(self):
        """Тест расчета текущего дня недели беременности."""
        start_date = self.today - timedelta(days=10)
        day = calculate_current_day_of_week(start_date, is_active=True)
        
        self.assertGreaterEqual(day, 1)
        self.assertLessEqual(day, 7)
    
    def test_calculate_days_until_due(self):
        """Тест расчета дней до ПДР."""
        days = calculate_days_until_due(self.due_date)
        expected_days = (self.due_date - self.today).days
        self.assertEqual(days, expected_days)
    
    def test_calculate_weeks_until_due(self):
        """Тест расчета недель до ПДР."""
        weeks = calculate_weeks_until_due(self.due_date)
        expected_weeks = calculate_days_until_due(self.due_date) // 7
        self.assertEqual(weeks, expected_weeks)
    
    def test_determine_trimester(self):
        """Тест определения триместра беременности."""
        self.assertEqual(determine_trimester(8), 1)
        self.assertEqual(determine_trimester(20), 2)
        self.assertEqual(determine_trimester(35), 3)
        self.assertIsNone(determine_trimester(None))
    
    def test_calculate_progress_percentage(self):
        """Тест расчета процента прогресса беременности."""
        # 20 недель = 50% прогресса
        progress = calculate_progress_percentage(20)
        self.assertEqual(progress, 50.0)
        
        # Максимум 100%
        progress = calculate_progress_percentage(45)
        self.assertEqual(progress, 100.0)
        
        # None возвращает 0
        progress = calculate_progress_percentage(None)
        self.assertEqual(progress, 0)
    
    def test_is_pregnancy_overdue(self):
        """Тест определения просроченной беременности."""
        overdue_date = self.today - timedelta(days=1)
        self.assertTrue(is_pregnancy_overdue(overdue_date))
        self.assertFalse(is_pregnancy_overdue(self.due_date))
    
    def test_is_pregnancy_full_term(self):
        """Тест определения доношенной беременности."""
        self.assertTrue(is_pregnancy_full_term(38))
        self.assertFalse(is_pregnancy_full_term(30))
        self.assertFalse(is_pregnancy_full_term(None))
    
    def test_is_pregnancy_preterm_risk(self):
        """Тест определения риска преждевременных родов."""
        self.assertTrue(is_pregnancy_preterm_risk(35))
        self.assertFalse(is_pregnancy_preterm_risk(38))
        self.assertFalse(is_pregnancy_preterm_risk(30))
        self.assertFalse(is_pregnancy_preterm_risk(None))
    
    def test_get_week_description(self):
        """Тест получения описания недели беременности."""
        descriptions = [
            (2, "2 неделя - Имплантация и раннее развитие"),
            (6, "6 неделя - Формирование основных органов"),
            (10, "10 неделя - Первый триместр, завершение органогенеза"),
            (15, "15 неделя - Второй триместр, активный рост"),
            (20, "20 неделя - Середина беременности"),
            (24, "24 неделя - Развитие легких и мозга"),
            (28, "28 неделя - Конец второго триместра"),
            (32, "32 неделя - Третий триместр, набор веса"),
            (36, "36 неделя - Подготовка к родам"),
            (39, "39 неделя - Доношенная беременность"),
            (42, "42 неделя - Переношенная беременность"),
        ]
        
        for week, expected in descriptions:
            with self.subTest(week=week):
                self.assertEqual(get_week_description(week), expected)
        
        # Тест для None и 0
        self.assertEqual(get_week_description(None), "Беременность неактивна")
        self.assertEqual(get_week_description(0), "Беременность еще не началась")
    
    def test_get_important_pregnancy_dates(self):
        """Тест получения важных дат беременности."""
        start_date = self.today - timedelta(days=140)
        dates = get_important_pregnancy_dates(start_date, self.due_date)
        
        expected_keys = [
            'start_date', 'first_trimester_end', 'second_trimester_end',
            'full_term_start', 'due_date', 'overdue_threshold'
        ]
        
        for key in expected_keys:
            self.assertIn(key, dates)
        
        self.assertEqual(dates['start_date'], start_date)
        self.assertEqual(dates['due_date'], self.due_date)
        self.assertEqual(dates['first_trimester_end'], start_date + timedelta(weeks=12))
        self.assertEqual(dates['second_trimester_end'], start_date + timedelta(weeks=28))
        self.assertEqual(dates['full_term_start'], start_date + timedelta(weeks=37))
        self.assertEqual(dates['overdue_threshold'], self.due_date + timedelta(weeks=2))
    
    def test_get_pregnancy_milestones(self):
        """Тест получения информации о вехах беременности."""
        milestones = get_pregnancy_milestones(20)
        
        expected_keys = [
            'implantation_complete', 'heart_beating', 'first_trimester_complete',
            'anatomy_scan_time', 'viability_threshold', 'second_trimester_complete',
            'third_trimester_started', 'full_term', 'overdue'
        ]
        
        for key in expected_keys:
            self.assertIn(key, milestones)
        
        # На 20 неделе
        self.assertTrue(milestones['implantation_complete'])
        self.assertTrue(milestones['heart_beating'])
        self.assertTrue(milestones['first_trimester_complete'])
        self.assertTrue(milestones['anatomy_scan_time'])
        self.assertFalse(milestones['viability_threshold'])
        self.assertFalse(milestones['second_trimester_complete'])
        self.assertFalse(milestones['third_trimester_started'])
        self.assertFalse(milestones['full_term'])
        self.assertFalse(milestones['overdue'])
        
        # Для None
        self.assertEqual(get_pregnancy_milestones(None), {})
    
    def test_calculate_estimated_conception_date(self):
        """Тест расчета предполагаемой даты зачатия."""
        conception = calculate_estimated_conception_date(self.due_date)
        expected = self.due_date - timedelta(days=266)
        self.assertEqual(conception, expected)
    
    def test_calculate_due_date_from_lmp(self):
        """Тест расчета ПДР от даты последней менструации."""
        due_date = calculate_due_date_from_lmp(self.lmp_date)
        expected = self.lmp_date + timedelta(days=280)
        self.assertEqual(due_date, expected)
    
    def test_calculate_due_date_from_conception(self):
        """Тест расчета ПДР от даты зачатия."""
        due_date = calculate_due_date_from_conception(self.conception_date)
        expected = self.conception_date + timedelta(days=266)
        self.assertEqual(due_date, expected)
    
    def test_get_pregnancy_week_range(self):
        """Тест получения диапазона дней для недели беременности."""
        week_start, week_end = get_pregnancy_week_range(1)
        self.assertEqual(week_start, 0)
        self.assertEqual(week_end, 6)
        
        week_start, week_end = get_pregnancy_week_range(2)
        self.assertEqual(week_start, 7)
        self.assertEqual(week_end, 13)
        
        # Тест для неправильного значения
        with self.assertRaises(ValueError):
            get_pregnancy_week_range(0)
    
    def test_is_high_risk_week(self):
        """Тест определения недель высокого риска."""
        # Первый триместр
        self.assertTrue(is_high_risk_week(8))
        
        # Нормальные недели
        self.assertFalse(is_high_risk_week(20))
        
        # Риск преждевременных родов
        self.assertTrue(is_high_risk_week(35))
        
        # Переношенность
        self.assertTrue(is_high_risk_week(42))
        
        # None
        self.assertFalse(is_high_risk_week(None))
    
    def test_get_recommended_checkup_schedule(self):
        """Тест получения рекомендуемого графика осмотров."""
        # До 28 недель
        schedule = get_recommended_checkup_schedule(20)
        self.assertEqual(schedule['frequency'], 'Каждые 4 недели')
        self.assertEqual(schedule['priority'], 'routine')
        
        # 28-36 недель
        schedule = get_recommended_checkup_schedule(32)
        self.assertEqual(schedule['frequency'], 'Каждые 2 недели')
        self.assertEqual(schedule['priority'], 'increased')
        
        # После 36 недель
        schedule = get_recommended_checkup_schedule(38)
        self.assertEqual(schedule['frequency'], 'Каждую неделю')
        self.assertEqual(schedule['priority'], 'high')
        
        # None
        self.assertEqual(get_recommended_checkup_schedule(None), {})
    
    def test_calculate_current_pregnancy_week_with_reference_date(self):
        """Тест расчета недели беременности с указанной датой."""
        start_date = date(2024, 1, 1)
        reference_date = date(2024, 3, 1)  # Примерно 9 недель спустя
        
        week = calculate_current_pregnancy_week(
            start_date=start_date,
            is_active=True,
            reference_date=reference_date
        )
        
        # Должно быть около 9-10 недель
        self.assertGreaterEqual(week, 8)
        self.assertLessEqual(week, 10)
    
    def test_calculate_days_until_due_with_reference_date(self):
        """Тест расчета дней до ПДР с указанной датой."""
        due_date = date(2024, 6, 1)
        reference_date = date(2024, 5, 1)  # За месяц до ПДР
        
        days = calculate_days_until_due(due_date, reference_date)
        self.assertEqual(days, 31)  # 31 день в мае
    
    def test_is_pregnancy_overdue_with_reference_date(self):
        """Тест определения просроченной беременности с указанной датой."""
        due_date = date(2024, 5, 1)
        reference_date = date(2024, 5, 5)  # Через 4 дня после ПДР
        
        self.assertTrue(is_pregnancy_overdue(due_date, reference_date))
        
        reference_date = date(2024, 4, 25)  # За неделю до ПДР
        self.assertFalse(is_pregnancy_overdue(due_date, reference_date))