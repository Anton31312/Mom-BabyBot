"""
Интеграционные тесты для пользовательского интерфейса таймеров кормления.

Этот модуль содержит простые интеграционные тесты для проверки
основной функциональности пользовательского интерфейса таймеров кормления.
"""

import unittest
from django.test import TestCase, Client
from django.urls import reverse


class FeedingTimerIntegrationTestCase(TestCase):
    """Интеграционные тесты для пользовательского интерфейса таймеров кормления."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
    
    def test_feeding_tracker_page_loads(self):
        """Тест загрузки страницы отслеживания кормления."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Отслеживание кормления')
    
    def test_timer_interface_elements_present(self):
        """Тест наличия элементов интерфейса таймеров."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем наличие основных элементов таймера
        self.assertContains(response, 'Таймеры кормления')
        self.assertContains(response, 'Левая грудь')
        self.assertContains(response, 'Правая грудь')
        self.assertContains(response, 'id="leftTimer"')
        self.assertContains(response, 'id="rightTimer"')
        self.assertContains(response, 'id="leftStartBtn"')
        self.assertContains(response, 'id="rightStartBtn"')
        self.assertContains(response, 'id="leftPauseBtn"')
        self.assertContains(response, 'id="rightPauseBtn"')
        self.assertContains(response, 'id="switchToLeftBtn"')
        self.assertContains(response, 'id="switchToRightBtn"')
        self.assertContains(response, 'id="stopSessionBtn"')
    
    def test_timer_css_classes(self):
        """Тест наличия CSS классов для таймеров."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем наличие основных CSS классов
        self.assertContains(response, 'timer-container')
        self.assertContains(response, 'timer-display')
        self.assertContains(response, 'timer-controls')
        self.assertContains(response, 'glass-card')
        self.assertContains(response, 'neo-button')
    
    def test_timer_display_format(self):
        """Тест формата отображения времени в таймерах."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем, что таймеры инициализированы с 00:00
        self.assertContains(response, '00:00')
    
    def test_feeding_tracker_javascript_included(self):
        """Тест включения JavaScript файла для таймеров."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем наличие JavaScript функций
        self.assertContains(response, 'initializeTimers')
        self.assertContains(response, 'startTimer')
        self.assertContains(response, 'pauseTimer')
        self.assertContains(response, 'switchBreast')
        self.assertContains(response, 'stopSession')
    
    def test_feeding_tracker_css_included(self):
        """Тест включения CSS файла для таймеров."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем наличие ссылки на CSS файл
        self.assertContains(response, 'feeding-timer.css')
    
    def test_manual_entry_form_present(self):
        """Тест наличия формы ручного ввода данных."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем наличие формы ручного ввода
        self.assertContains(response, 'Ручной ввод данных')
        self.assertContains(response, 'id="breastFeedingForm"')
        self.assertContains(response, 'id="breastFeedingDate"')
        self.assertContains(response, 'id="breastFeedingDuration"')
        self.assertContains(response, 'id="breastFeedingNotes"')
    
    def test_active_session_info_present(self):
        """Тест наличия информации об активной сессии."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем наличие элементов информации об активной сессии
        self.assertContains(response, 'id="activeSessionInfo"')
        self.assertContains(response, 'id="sessionStartTime"')
        self.assertContains(response, 'id="totalSessionTime"')
    
    def test_timer_total_time_displays(self):
        """Тест наличия отображения общего времени для каждого таймера."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем наличие элементов общего времени
        self.assertContains(response, 'id="leftTotalTime"')
        self.assertContains(response, 'id="rightTotalTime"')
    
    def test_responsive_design_classes(self):
        """Тест наличия классов для адаптивного дизайна."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        # Проверяем наличие классов для адаптивного дизайна
        self.assertContains(response, 'grid-cols-1')
        self.assertContains(response, 'md:grid-cols-2')
        self.assertContains(response, 'space-y-4')
        self.assertContains(response, 'space-x-4')


if __name__ == '__main__':
    unittest.main()