"""
Тесты для Django модели FeedingSession веб-приложения.

Этот модуль содержит тесты для модели FeedingSession, которая отслеживает
сессии кормления с поддержкой двух таймеров для грудного вскармливания.
Тесты покрывают создание модели, валидацию полей, методы и свойства.
"""

import unittest
from datetime import timedelta, datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from webapp.models import FeedingSession


class FeedingSessionModelTest(TestCase):
    """Тесты для модели FeedingSession."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_feeding_session_creation(self):
        """Тест создания сессии кормления."""
        session = FeedingSession.objects.create(
            user=self.user,
            feeding_type='breast',
            notes='Тестовая сессия кормления'
        )
        
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.feeding_type, 'breast')
        self.assertEqual(session.notes, 'Тестовая сессия кормления')
        self.assertEqual(session.left_breast_duration, timedelta(0))
        self.assertEqual(session.right_breast_duration, timedelta(0))
        self.assertFalse(session.left_timer_active)
        self.assertFalse(session.right_timer_active)
        self.assertIsNone(session.end_time)
        self.assertIsNotNone(session.start_time)
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.updated_at)
    
    def test_feeding_session_str_representation(self):
        """Тест строкового представления модели."""
        session = FeedingSession.objects.create(user=self.user)
        expected_str = f'Кормление {self.user.username} - {session.start_time.strftime("%d.%m.%Y %H:%M")}'
        self.assertEqual(str(session), expected_str)
    
    def test_feeding_type_choices(self):
        """Тест выбора типа кормления."""
        # Тест валидного типа кормления
        session = FeedingSession.objects.create(
            user=self.user,
            feeding_type='bottle'
        )
        self.assertEqual(session.feeding_type, 'bottle')
        
        # Тест другого валидного типа
        session2 = FeedingSession.objects.create(
            user=self.user,
            feeding_type='mixed'
        )
        self.assertEqual(session2.feeding_type, 'mixed')
    
    def test_breast_choices(self):
        """Тест выбора груди."""
        session = FeedingSession.objects.create(
            user=self.user,
            last_active_breast='left'
        )
        self.assertEqual(session.last_active_breast, 'left')
        
        session.last_active_breast = 'right'
        session.save()
        self.assertEqual(session.last_active_breast, 'right')
        
        session.last_active_breast = 'both'
        session.save()
        self.assertEqual(session.last_active_breast, 'both')
    
    def test_total_duration_property(self):
        """Тест свойства total_duration."""
        session = FeedingSession.objects.create(
            user=self.user,
            left_breast_duration=timedelta(minutes=10),
            right_breast_duration=timedelta(minutes=15)
        )
        
        expected_total = timedelta(minutes=25)
        self.assertEqual(session.total_duration, expected_total)
    
    def test_is_active_property(self):
        """Тест свойства is_active."""
        session = FeedingSession.objects.create(user=self.user)
        
        # Изначально сессия неактивна
        self.assertFalse(session.is_active)
        
        # Активируем левый таймер
        session.left_timer_active = True
        session.save()
        self.assertTrue(session.is_active)
        
        # Деактивируем левый, активируем правый
        session.left_timer_active = False
        session.right_timer_active = True
        session.save()
        self.assertTrue(session.is_active)
        
        # Активируем оба таймера
        session.left_timer_active = True
        session.right_timer_active = True
        session.save()
        self.assertTrue(session.is_active)
        
        # Деактивируем оба
        session.left_timer_active = False
        session.right_timer_active = False
        session.save()
        self.assertFalse(session.is_active)
    
    def test_session_duration_property(self):
        """Тест свойства session_duration."""
        session = FeedingSession.objects.create(user=self.user)
        
        # Без end_time должно возвращать None
        self.assertIsNone(session.session_duration)
        
        # С end_time должно возвращать разность
        session.end_time = session.start_time + timedelta(minutes=30)
        session.save()
        self.assertEqual(session.session_duration, timedelta(minutes=30))
    
    def test_get_breast_duration_minutes(self):
        """Тест метода get_breast_duration_minutes."""
        session = FeedingSession.objects.create(
            user=self.user,
            left_breast_duration=timedelta(minutes=10, seconds=30),
            right_breast_duration=timedelta(minutes=15, seconds=45)
        )
        
        # Тест для левой груди
        left_minutes = session.get_breast_duration_minutes('left')
        self.assertEqual(left_minutes, 10.5)  # 10 минут 30 секунд = 10.5 минут
        
        # Тест для правой груди
        right_minutes = session.get_breast_duration_minutes('right')
        self.assertEqual(right_minutes, 15.75)  # 15 минут 45 секунд = 15.75 минут
        
        # Тест для неверного значения
        invalid_minutes = session.get_breast_duration_minutes('invalid')
        self.assertEqual(invalid_minutes, 0)
    
    def test_get_total_duration_minutes(self):
        """Тест метода get_total_duration_minutes."""
        session = FeedingSession.objects.create(
            user=self.user,
            left_breast_duration=timedelta(minutes=10),
            right_breast_duration=timedelta(minutes=15)
        )
        
        total_minutes = session.get_total_duration_minutes()
        self.assertEqual(total_minutes, 25.0)
    
    def test_get_breast_percentage(self):
        """Тест метода get_breast_percentage."""
        session = FeedingSession.objects.create(
            user=self.user,
            left_breast_duration=timedelta(minutes=10),
            right_breast_duration=timedelta(minutes=15)
        )
        
        # Тест процента для левой груди
        left_percentage = session.get_breast_percentage('left')
        self.assertEqual(left_percentage, 40.0)  # 10 из 25 минут = 40%
        
        # Тест процента для правой груди
        right_percentage = session.get_breast_percentage('right')
        self.assertEqual(right_percentage, 60.0)  # 15 из 25 минут = 60%
        
        # Тест для неверного значения
        invalid_percentage = session.get_breast_percentage('invalid')
        self.assertEqual(invalid_percentage, 0)
    
    def test_get_breast_percentage_zero_duration(self):
        """Тест метода get_breast_percentage при нулевой продолжительности."""
        session = FeedingSession.objects.create(user=self.user)
        
        # При нулевой общей продолжительности должно возвращать 0
        left_percentage = session.get_breast_percentage('left')
        self.assertEqual(left_percentage, 0)
        
        right_percentage = session.get_breast_percentage('right')
        self.assertEqual(right_percentage, 0)
    
    def test_model_meta_options(self):
        """Тест мета-опций модели."""
        # Создаем несколько сессий с разным временем
        session1 = FeedingSession.objects.create(user=self.user)
        session2 = FeedingSession.objects.create(user=self.user)
        
        # Проверяем сортировку по убыванию start_time
        sessions = FeedingSession.objects.all()
        self.assertTrue(sessions[0].start_time >= sessions[1].start_time)
        
        # Проверяем verbose_name
        self.assertEqual(FeedingSession._meta.verbose_name, 'Сессия кормления')
        self.assertEqual(FeedingSession._meta.verbose_name_plural, 'Сессии кормления')
    
    def test_timer_fields(self):
        """Тест полей таймеров."""
        now = timezone.now()
        session = FeedingSession.objects.create(
            user=self.user,
            left_timer_start=now,
            right_timer_start=now + timedelta(minutes=5),
            left_timer_active=True,
            right_timer_active=False
        )
        
        self.assertEqual(session.left_timer_start, now)
        self.assertEqual(session.right_timer_start, now + timedelta(minutes=5))
        self.assertTrue(session.left_timer_active)
        self.assertFalse(session.right_timer_active)
    
    def test_amount_field(self):
        """Тест поля количества."""
        session = FeedingSession.objects.create(
            user=self.user,
            feeding_type='bottle',
            amount=120.5
        )
        
        self.assertEqual(session.amount, 120.5)
        
        # Тест с None
        session2 = FeedingSession.objects.create(user=self.user)
        self.assertIsNone(session2.amount)
    
    def test_notes_field(self):
        """Тест поля заметок."""
        notes_text = "Ребенок хорошо кушал, без проблем"
        session = FeedingSession.objects.create(
            user=self.user,
            notes=notes_text
        )
        
        self.assertEqual(session.notes, notes_text)
        
        # Тест с пустыми заметками
        session2 = FeedingSession.objects.create(user=self.user)
        self.assertEqual(session2.notes, '')
    
    def test_cascade_delete(self):
        """Тест каскадного удаления при удалении пользователя."""
        session = FeedingSession.objects.create(user=self.user)
        session_id = session.id
        
        # Проверяем, что сессия существует
        self.assertTrue(FeedingSession.objects.filter(id=session_id).exists())
        
        # Удаляем пользователя
        self.user.delete()
        
        # Проверяем, что сессия тоже удалилась
        self.assertFalse(FeedingSession.objects.filter(id=session_id).exists())
    
    def test_default_values(self):
        """Тест значений по умолчанию."""
        session = FeedingSession.objects.create(user=self.user)
        
        self.assertEqual(session.feeding_type, 'breast')
        self.assertEqual(session.left_breast_duration, timedelta(0))
        self.assertEqual(session.right_breast_duration, timedelta(0))
        self.assertFalse(session.left_timer_active)
        self.assertFalse(session.right_timer_active)
        self.assertIsNone(session.left_timer_start)
        self.assertIsNone(session.right_timer_start)
        self.assertIsNone(session.last_active_breast)
        self.assertIsNone(session.amount)
        self.assertEqual(session.notes, '')


if __name__ == '__main__':
    unittest.main()