"""
Тесты для компонента визуального индикатора прогресса беременности.

Этот модуль содержит тесты для проверки корректности отображения
и функционирования компонента pregnancy_progress_indicator.html.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.template import Template
from django.template.loader import render_to_string
from datetime import date, timedelta
from webapp.models import PregnancyInfo


class PregnancyProgressIndicatorTest(TestCase):
    """Тесты для компонента визуального индикатора прогресса беременности."""
    
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
    
    def test_component_renders_with_active_pregnancy(self):
        """Тест отображения компонента с активной беременностью."""
        context = {
            'pregnancy_info': self.pregnancy_info,
            'style': 'glass',
            'show_details': True,
            'compact': False
        }
        
        rendered = render_to_string('components/pregnancy_progress_indicator.html', context)
        
        # Проверяем, что компонент отображается
        self.assertIn('pregnancy-progress-indicator', rendered)
        self.assertIn('glass-style', rendered)
        self.assertIn('Прогресс беременности', rendered)
        
        # Проверяем, что отображается информация о неделе
        self.assertIn('неделя', rendered)
        self.assertIn('progress-ring', rendered)
        
        # Проверяем, что отображается линейный прогресс
        self.assertIn('linear-progress', rendered)
        self.assertIn('progress-fill', rendered)
    
    def test_component_renders_with_neo_style(self):
        """Тест отображения компонента в neo стиле."""
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': self.pregnancy_info,
            'style': 'neo',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что применяется neo стиль
        self.assertIn('neo-style', rendered)
        self.assertNotIn('glass-style', rendered)
    
    def test_component_renders_in_compact_mode(self):
        """Тест отображения компонента в компактном режиме."""
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': self.pregnancy_info,
            'style': 'glass',
            'show_details': True,
            'compact': True
        })
        
        rendered = template.render(context)
        
        # Проверяем, что применяется компактный режим
        self.assertIn('compact', rendered)
        self.assertIn('compact-actions', rendered)
        self.assertIn('Подробнее', rendered)
    
    def test_component_without_details(self):
        """Тест отображения компонента без детальной информации."""
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': self.pregnancy_info,
            'style': 'glass',
            'show_details': False,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что детальная информация не отображается
        self.assertNotIn('progress-details', rendered)
        self.assertNotIn('milestones', rendered)
        self.assertNotIn('Предполагаемая дата родов', rendered)
    
    def test_component_with_inactive_pregnancy(self):
        """Тест отображения компонента с неактивной беременностью."""
        # Деактивируем беременность
        self.pregnancy_info.is_active = False
        self.pregnancy_info.save()
        
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': self.pregnancy_info,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что отображается неактивное состояние
        self.assertIn('inactive', rendered)
        self.assertIn('Информация о беременности', rendered)
        self.assertIn('Настроить', rendered)
    
    def test_component_without_pregnancy_info(self):
        """Тест отображения компонента без информации о беременности."""
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': None,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что отображается неактивное состояние
        self.assertIn('inactive', rendered)
        self.assertIn('Добавьте информацию о беременности', rendered)
    
    def test_progress_calculation(self):
        """Тест корректности расчета прогресса."""
        # Создаем беременность на 20 неделе
        current_week = self.pregnancy_info.current_week
        progress_percentage = self.pregnancy_info.progress_percentage
        
        # Проверяем, что прогресс рассчитывается корректно
        self.assertIsInstance(current_week, int)
        self.assertGreater(current_week, 0)
        self.assertLessEqual(current_week, 42)
        
        self.assertIsInstance(progress_percentage, (int, float))
        self.assertGreaterEqual(progress_percentage, 0)
        self.assertLessEqual(progress_percentage, 100)
    
    def test_trimester_information(self):
        """Тест отображения информации о триместре."""
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': self.pregnancy_info,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что отображается информация о триместре
        trimester = self.pregnancy_info.current_trimester
        if trimester:
            self.assertIn(f'{trimester} триместр', rendered)
    
    def test_milestone_display(self):
        """Тест отображения вех развития."""
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': self.pregnancy_info,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что отображаются вехи развития
        self.assertIn('milestones', rendered)
        self.assertIn('Достигнутые вехи', rendered)
        
        # Проверяем наличие конкретных вех в зависимости от недели
        milestones = self.pregnancy_info.milestones
        if milestones.get('heart_beating'):
            self.assertIn('Сердце бьется', rendered)
    
    def test_high_risk_warning(self):
        """Тест отображения предупреждения о высоком риске."""
        # Создаем беременность на раннем сроке (высокий риск)
        early_due_date = date.today() + timedelta(days=245)  # ~5 недель
        early_pregnancy = PregnancyInfo.objects.create(
            user=self.user,
            due_date=early_due_date,
            is_active=True
        )
        
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': early_pregnancy,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что отображается предупреждение о высоком риске
        if early_pregnancy.is_high_risk_week:
            self.assertIn('warning', rendered)
            self.assertIn('Важный период', rendered)
    
    def test_full_term_indication(self):
        """Тест отображения индикации доношенной беременности."""
        # Создаем доношенную беременность (37+ недель)
        full_term_due_date = date.today() + timedelta(days=21)  # ~37 недель
        full_term_pregnancy = PregnancyInfo.objects.create(
            user=self.user,
            due_date=full_term_due_date,
            is_active=True
        )
        
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': full_term_pregnancy,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что отображается индикация доношенной беременности
        if full_term_pregnancy.is_full_term:
            self.assertIn('success', rendered)
            self.assertIn('Доношенная беременность', rendered)
    
    def test_progress_markers(self):
        """Тест отображения маркеров прогресса."""
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': self.pregnancy_info,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что отображаются маркеры триместров
        self.assertIn('progress-markers', rendered)
        self.assertIn('12 нед', rendered)  # Конец первого триместра
        self.assertIn('28 нед', rendered)  # Конец второго триместра
        self.assertIn('37 нед', rendered)  # Доношенная беременность
    
    def test_responsive_design_classes(self):
        """Тест наличия классов для адаптивного дизайна."""
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': self.pregnancy_info,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что в CSS есть медиа-запросы для адаптивности
        self.assertIn('@media (max-width: 768px)', rendered)
        self.assertIn('@media (max-width: 480px)', rendered)
    
    def test_javascript_functionality(self):
        """Тест наличия JavaScript функциональности."""
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': self.pregnancy_info,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что есть JavaScript функции
        self.assertIn('showPregnancyDetails', rendered)
        self.assertIn('setupPregnancy', rendered)
        self.assertIn('DOMContentLoaded', rendered)
    
    def test_animation_elements(self):
        """Тест наличия элементов анимации."""
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': self.pregnancy_info,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем, что есть элементы для анимации
        self.assertIn('transition:', rendered)
        self.assertIn('stroke-dasharray', rendered)
        self.assertIn('transform:', rendered)


class PregnancyProgressIndicatorIntegrationTest(TestCase):
    """Интеграционные тесты для компонента визуального индикатора прогресса беременности."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_component_with_different_pregnancy_stages(self):
        """Тест компонента на разных стадиях беременности."""
        stages = [
            (280, 'Начало беременности'),  # 1 неделя
            (210, 'Первый триместр'),      # ~10 недель
            (140, 'Второй триместр'),      # ~20 недель
            (70, 'Третий триместр'),       # ~30 недель
            (21, 'Доношенная'),            # ~37 недель
            (-7, 'Просроченная'),          # 41 неделя
        ]
        
        template = get_template('components/pregnancy_progress_indicator.html')
        
        for days_until_due, stage_name in stages:
            with self.subTest(stage=stage_name):
                # Создаем беременность для каждой стадии
                due_date = date.today() + timedelta(days=days_until_due)
                pregnancy = PregnancyInfo.objects.create(
                    user=self.user,
                    due_date=due_date,
                    is_active=True
                )
                
                context = Context({
                    'pregnancy_info': pregnancy,
                    'style': 'glass',
                    'show_details': True,
                    'compact': False
                })
                
                rendered = template.render(context)
                
                # Проверяем, что компонент отображается для каждой стадии
                self.assertIn('pregnancy-progress-indicator', rendered)
                self.assertIn('progress-ring', rendered)
                
                # Проверяем корректность расчетов
                current_week = pregnancy.current_week
                self.assertIsInstance(current_week, int)
                self.assertGreater(current_week, 0)
                
                # Очищаем для следующего теста
                pregnancy.delete()
    
    def test_component_accessibility(self):
        """Тест доступности компонента."""
        due_date = date.today() + timedelta(days=140)
        pregnancy_info = PregnancyInfo.objects.create(
            user=self.user,
            due_date=due_date,
            is_active=True
        )
        
        template = get_template('components/pregnancy_progress_indicator.html')
        context = Context({
            'pregnancy_info': pregnancy_info,
            'style': 'glass',
            'show_details': True,
            'compact': False
        })
        
        rendered = template.render(context)
        
        # Проверяем наличие семантических элементов
        self.assertIn('<h3', rendered)  # Заголовки
        self.assertIn('aria-', rendered)  # ARIA атрибуты (если добавлены)
        
        # Проверяем контрастность (наличие четких цветов)
        self.assertIn('color:', rendered)
        self.assertIn('background:', rendered)