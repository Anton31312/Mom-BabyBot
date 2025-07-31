"""
Тесты для модели PregnancyInfo.

Этот модуль содержит тесты для модели PregnancyInfo, которая используется
для хранения информации о беременности и расчета недель беременности.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from webapp.models import PregnancyInfo


class PregnancyInfoModelTest(TestCase):
    """Тесты для модели PregnancyInfo."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем тестовую беременность с ПДР через 20 недель (140 дней)
        self.due_date = date.today() + timedelta(days=140)
        self.pregnancy = PregnancyInfo.objects.create(
            user=self.user,
            due_date=self.due_date
        )
    
    def test_pregnancy_creation(self):
        """Тест создания записи о беременности."""
        self.assertEqual(self.pregnancy.user, self.user)
        self.assertEqual(self.pregnancy.due_date, self.due_date)
        self.assertTrue(self.pregnancy.is_active)
        self.assertIsNotNone(self.pregnancy.created_at)
        self.assertIsNotNone(self.pregnancy.updated_at)
    
    def test_string_representation(self):
        """Тест строкового представления модели."""
        expected = f'Беременность {self.user.username} - ПДР: {self.due_date.strftime("%d.%m.%Y")}'
        self.assertEqual(str(self.pregnancy), expected)
    
    def test_start_date_calculation_from_due_date(self):
        """Тест расчета даты начала беременности от ПДР."""
        expected_start = self.due_date - timedelta(days=280)
        self.assertEqual(self.pregnancy.start_date, expected_start)
    
    def test_start_date_with_last_menstrual_period(self):
        """Тест расчета даты начала с указанной датой последней менструации."""
        user2 = User.objects.create_user('user2', 'user2@test.com', 'pass')
        lmp_date = date.today() - timedelta(days=140)  # 20 недель назад
        pregnancy = PregnancyInfo.objects.create(
            user=user2,
            due_date=self.due_date,
            last_menstrual_period=lmp_date
        )
        self.assertEqual(pregnancy.start_date, lmp_date)
    
    def test_start_date_with_conception_date(self):
        """Тест расчета даты начала с указанной датой зачатия."""
        user3 = User.objects.create_user('user3', 'user3@test.com', 'pass')
        conception_date = date.today() - timedelta(days=126)  # 18 недель назад
        expected_start = conception_date - timedelta(days=14)
        pregnancy = PregnancyInfo.objects.create(
            user=user3,
            due_date=self.due_date,
            conception_date=conception_date
        )
        self.assertEqual(pregnancy.start_date, expected_start)
    
    def test_current_week_calculation(self):
        """Тест расчета текущей недели беременности."""
        user4 = User.objects.create_user('user4', 'user4@test.com', 'pass')
        # Создаем беременность, которая началась 10 недель назад
        start_date = date.today() - timedelta(weeks=10)
        due_date = start_date + timedelta(days=280)
        pregnancy = PregnancyInfo.objects.create(
            user=user4,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        
        # Текущая неделя должна быть около 11 (10 полных недель + текущая)
        current_week = pregnancy.current_week
        self.assertGreaterEqual(current_week, 10)
        self.assertLessEqual(current_week, 12)
    
    def test_current_week_inactive_pregnancy(self):
        """Тест расчета недели для неактивной беременности."""
        self.pregnancy.is_active = False
        self.pregnancy.save()
        self.assertIsNone(self.pregnancy.current_week)
    
    def test_current_week_future_pregnancy(self):
        """Тест расчета недели для будущей беременности."""
        user5 = User.objects.create_user('user5', 'user5@test.com', 'pass')
        future_start = date.today() + timedelta(days=30)
        future_due = future_start + timedelta(days=280)
        pregnancy = PregnancyInfo.objects.create(
            user=user5,
            due_date=future_due,
            last_menstrual_period=future_start
        )
        self.assertEqual(pregnancy.current_week, 0)
    
    def test_current_week_maximum_limit(self):
        """Тест ограничения максимальной недели беременности."""
        user6 = User.objects.create_user('user6', 'user6@test.com', 'pass')
        # Создаем беременность, которая началась 45 недель назад
        start_date = date.today() - timedelta(weeks=45)
        due_date = start_date + timedelta(days=280)
        pregnancy = PregnancyInfo.objects.create(
            user=user6,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        
        # Максимальная неделя должна быть ограничена 42
        self.assertEqual(pregnancy.current_week, 42)
    
    def test_current_day_of_week(self):
        """Тест расчета текущего дня недели беременности."""
        user7 = User.objects.create_user('user7', 'user7@test.com', 'pass')
        # Создаем беременность, которая началась 10 дней назад
        start_date = date.today() - timedelta(days=10)
        due_date = start_date + timedelta(days=280)
        pregnancy = PregnancyInfo.objects.create(
            user=user7,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        
        # День недели должен быть от 1 до 7
        day_of_week = pregnancy.current_day_of_week
        self.assertGreaterEqual(day_of_week, 1)
        self.assertLessEqual(day_of_week, 7)
    
    def test_days_until_due(self):
        """Тест расчета дней до ПДР."""
        days_until = self.pregnancy.days_until_due
        expected_days = (self.due_date - date.today()).days
        self.assertEqual(days_until, expected_days)
    
    def test_weeks_until_due(self):
        """Тест расчета недель до ПДР."""
        weeks_until = self.pregnancy.weeks_until_due
        expected_weeks = self.pregnancy.days_until_due // 7
        self.assertEqual(weeks_until, expected_weeks)
    
    def test_trimester_calculation(self):
        """Тест определения триместра беременности."""
        # Тест первого триместра (неделя 8)
        user8 = User.objects.create_user('user8', 'user8@test.com', 'pass')
        start_date = date.today() - timedelta(weeks=8)
        due_date = start_date + timedelta(days=280)
        pregnancy1 = PregnancyInfo.objects.create(
            user=user8,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        self.assertEqual(pregnancy1.trimester, 1)
        
        # Тест второго триместра (неделя 20)
        user9 = User.objects.create_user('user9', 'user9@test.com', 'pass')
        start_date = date.today() - timedelta(weeks=20)
        due_date = start_date + timedelta(days=280)
        pregnancy2 = PregnancyInfo.objects.create(
            user=user9,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        self.assertEqual(pregnancy2.trimester, 2)
        
        # Тест третьего триместра (неделя 35)
        user10 = User.objects.create_user('user10', 'user10@test.com', 'pass')
        start_date = date.today() - timedelta(weeks=35)
        due_date = start_date + timedelta(days=280)
        pregnancy3 = PregnancyInfo.objects.create(
            user=user10,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        self.assertEqual(pregnancy3.trimester, 3)
    
    def test_progress_percentage(self):
        """Тест расчета процента прогресса беременности."""
        user11 = User.objects.create_user('user11', 'user11@test.com', 'pass')
        # Создаем беременность на 20 неделе
        start_date = date.today() - timedelta(weeks=20)
        due_date = start_date + timedelta(days=280)
        pregnancy = PregnancyInfo.objects.create(
            user=user11,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        
        # Прогресс должен быть около 50% (20 недель из 40)
        progress = pregnancy.progress_percentage
        self.assertGreaterEqual(progress, 45)
        self.assertLessEqual(progress, 55)
    
    def test_progress_percentage_maximum(self):
        """Тест ограничения максимального процента прогресса."""
        user12 = User.objects.create_user('user12', 'user12@test.com', 'pass')
        # Создаем переношенную беременность (45 недель)
        start_date = date.today() - timedelta(weeks=45)
        due_date = start_date + timedelta(days=280)
        pregnancy = PregnancyInfo.objects.create(
            user=user12,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        
        # Прогресс не должен превышать 100%
        self.assertEqual(pregnancy.progress_percentage, 100)
    
    def test_is_overdue(self):
        """Тест определения просроченной беременности."""
        user13 = User.objects.create_user('user13', 'user13@test.com', 'pass')
        # Создаем просроченную беременность (ПДР была вчера)
        overdue_date = date.today() - timedelta(days=1)
        pregnancy = PregnancyInfo.objects.create(
            user=user13,
            due_date=overdue_date
        )
        self.assertTrue(pregnancy.is_overdue)
        
        # Текущая беременность не должна быть просроченной
        self.assertFalse(self.pregnancy.is_overdue)
    
    def test_is_full_term(self):
        """Тест определения доношенной беременности."""
        user14 = User.objects.create_user('user14', 'user14@test.com', 'pass')
        # Создаем доношенную беременность (38 недель)
        start_date = date.today() - timedelta(weeks=38)
        due_date = start_date + timedelta(days=280)
        pregnancy = PregnancyInfo.objects.create(
            user=user14,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        self.assertTrue(pregnancy.is_full_term)
        
        # Создаем недоношенную беременность (30 недель)
        user15 = User.objects.create_user('user15', 'user15@test.com', 'pass')
        start_date = date.today() - timedelta(weeks=30)
        due_date = start_date + timedelta(days=280)
        pregnancy2 = PregnancyInfo.objects.create(
            user=user15,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        self.assertFalse(pregnancy2.is_full_term)
    
    def test_is_preterm_risk(self):
        """Тест определения риска преждевременных родов."""
        user16 = User.objects.create_user('user16', 'user16@test.com', 'pass')
        # Создаем беременность с риском преждевременных родов (35 недель)
        start_date = date.today() - timedelta(weeks=35)
        due_date = start_date + timedelta(days=280)
        pregnancy = PregnancyInfo.objects.create(
            user=user16,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        self.assertTrue(pregnancy.is_preterm_risk)
        
        # Создаем доношенную беременность (38 недель)
        user17 = User.objects.create_user('user17', 'user17@test.com', 'pass')
        start_date = date.today() - timedelta(weeks=38)
        due_date = start_date + timedelta(days=280)
        pregnancy2 = PregnancyInfo.objects.create(
            user=user17,
            due_date=due_date,
            last_menstrual_period=start_date
        )
        self.assertFalse(pregnancy2.is_preterm_risk)
    
    def test_get_week_description(self):
        """Тест получения описания недели беременности."""
        # Тест для разных недель
        test_cases = [
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
        
        for week, expected_description in test_cases:
            # Создаем дату начала так, чтобы получить точно нужную неделю
            # Неделя = (дни с начала беременности // 7) + 1
            # Значит, для недели N нужно (N-1) * 7 дней с начала
            days_since_start = (week - 1) * 7
            start_date = date.today() - timedelta(days=days_since_start)
            due_date = start_date + timedelta(days=280)
            pregnancy = PregnancyInfo.objects.create(
                user=User.objects.create_user(f'userweek{week}', f'userweek{week}@test.com', 'pass'),
                due_date=due_date,
                last_menstrual_period=start_date
            )
            actual_description = pregnancy.get_week_description()
            self.assertEqual(actual_description, expected_description, 
                           f"Week {week}: expected '{expected_description}', got '{actual_description}'")
    
    def test_get_important_dates(self):
        """Тест получения важных дат беременности."""
        important_dates = self.pregnancy.get_important_dates()
        
        # Проверяем, что все ключи присутствуют
        expected_keys = [
            'start_date', 'first_trimester_end', 'second_trimester_end',
            'full_term_start', 'due_date', 'overdue_threshold'
        ]
        for key in expected_keys:
            self.assertIn(key, important_dates)
        
        # Проверяем правильность расчета дат
        start_date = self.pregnancy.start_date
        self.assertEqual(important_dates['start_date'], start_date)
        self.assertEqual(important_dates['due_date'], self.due_date)
        self.assertEqual(
            important_dates['first_trimester_end'],
            start_date + timedelta(weeks=12)
        )
        self.assertEqual(
            important_dates['second_trimester_end'],
            start_date + timedelta(weeks=28)
        )
        self.assertEqual(
            important_dates['full_term_start'],
            start_date + timedelta(weeks=37)
        )
        self.assertEqual(
            important_dates['overdue_threshold'],
            self.due_date + timedelta(weeks=2)
        )
    
    def test_get_active_pregnancies(self):
        """Тест получения активных беременностей."""
        # Создаем дополнительную активную беременность
        user2 = User.objects.create_user('user2', 'user2@test.com', 'pass')
        pregnancy2 = PregnancyInfo.objects.create(
            user=user2,
            due_date=date.today() + timedelta(days=200)
        )
        
        # Создаем неактивную беременность
        user3 = User.objects.create_user('user3', 'user3@test.com', 'pass')
        pregnancy3 = PregnancyInfo.objects.create(
            user=user3,
            due_date=date.today() + timedelta(days=100),
            is_active=False
        )
        
        active_pregnancies = PregnancyInfo.get_active_pregnancies()
        
        # Должно быть 2 активные беременности
        self.assertEqual(active_pregnancies.count(), 2)
        self.assertIn(self.pregnancy, active_pregnancies)
        self.assertIn(pregnancy2, active_pregnancies)
        self.assertNotIn(pregnancy3, active_pregnancies)
    
    def test_create_pregnancy_method(self):
        """Тест метода создания беременности."""
        user2 = User.objects.create_user('user2', 'user2@test.com', 'pass')
        due_date = date.today() + timedelta(days=200)
        lmp_date = date.today() - timedelta(days=80)
        
        # Создаем первую беременность
        pregnancy1 = PregnancyInfo.create_pregnancy(
            user=user2,
            due_date=due_date,
            last_menstrual_period=lmp_date
        )
        
        self.assertEqual(pregnancy1.user, user2)
        self.assertEqual(pregnancy1.due_date, due_date)
        self.assertEqual(pregnancy1.last_menstrual_period, lmp_date)
        self.assertTrue(pregnancy1.is_active)
        
        # Создаем вторую беременность для того же пользователя
        new_due_date = date.today() + timedelta(days=250)
        pregnancy2 = PregnancyInfo.create_pregnancy(
            user=user2,
            due_date=new_due_date
        )
        
        # Первая беременность должна стать неактивной
        pregnancy1.refresh_from_db()
        self.assertFalse(pregnancy1.is_active)
        
        # Вторая беременность должна быть активной
        self.assertTrue(pregnancy2.is_active)
        self.assertEqual(pregnancy2.due_date, new_due_date)
    
    def test_foreign_key_relationship(self):
        """Тест отношения внешнего ключа с пользователем."""
        # Проверяем, что можно получить информацию о беременности через пользователя
        active_pregnancy = PregnancyInfo.get_active_pregnancy(self.user)
        self.assertEqual(active_pregnancy, self.pregnancy)
        
        # Проверяем, что можно создать несколько беременностей для одного пользователя
        # но только одна может быть активной
        pregnancy2 = PregnancyInfo.objects.create(
            user=self.user,
            due_date=date.today() + timedelta(days=200),
            is_active=False
        )
        
        # Активная беременность должна остаться прежней
        active_pregnancy = PregnancyInfo.get_active_pregnancy(self.user)
        self.assertEqual(active_pregnancy, self.pregnancy)
        
        # Всего беременностей должно быть 2
        total_pregnancies = PregnancyInfo.objects.filter(user=self.user).count()
        self.assertEqual(total_pregnancies, 2)
    
    def test_should_notify_new_week(self):
        """Тест метода определения необходимости уведомления о новой неделе."""
        # Пока метод возвращает False (будет реализован в задаче 11.4)
        self.assertFalse(self.pregnancy.should_notify_new_week())