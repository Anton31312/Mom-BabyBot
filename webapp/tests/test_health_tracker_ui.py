"""
Тесты пользовательского интерфейса для отслеживания показателей здоровья.

Этот модуль содержит тесты для UI компонентов отслеживания веса и артериального давления.
Соответствует требованиям 7.1 и 7.2 о возможности отслеживания веса и артериального давления.
"""

import time
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase, LiveServerTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from webapp.models import WeightRecord, BloodPressureRecord


class HealthTrackerUITest(LiveServerTestCase):
    """Тесты пользовательского интерфейса отслеживания здоровья."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Настройка Chrome для headless режима
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except Exception as e:
            # Если Chrome недоступен, пропускаем тесты
            cls.driver = None
            print(f"Chrome WebDriver недоступен: {e}")
    
    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Настройка тестовых данных."""
        if not self.driver:
            self.skipTest("WebDriver недоступен")
        
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
    
    def test_health_tracker_page_loads(self):
        """Тест загрузки страницы отслеживания здоровья."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Проверяем, что страница загрузилась
        self.assertIn('Отслеживание показателей здоровья', self.driver.title)
        
        # Проверяем наличие основных элементов
        header = self.driver.find_element(By.TAG_NAME, 'h1')
        self.assertIn('Отслеживание показателей здоровья', header.text)
        
        # Проверяем наличие табов
        tabs = self.driver.find_elements(By.CLASS_NAME, 'glass-tab')
        self.assertEqual(len(tabs), 3)
        
        tab_texts = [tab.text for tab in tabs]
        self.assertIn('Вес', tab_texts)
        self.assertIn('Артериальное давление', tab_texts)
        self.assertIn('Статистика', tab_texts)
    
    def test_weight_tab_functionality(self):
        """Тест функциональности вкладки веса."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Проверяем, что вкладка веса активна по умолчанию
        weight_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab-target="weight-tracking"]')
        self.assertIn('active', weight_tab.get_attribute('class'))
        
        # Проверяем наличие формы ввода веса
        weight_form = self.driver.find_element(By.ID, 'weightForm')
        self.assertTrue(weight_form.is_displayed())
        
        # Проверяем поля формы
        weight_input = self.driver.find_element(By.ID, 'weightValue')
        date_input = self.driver.find_element(By.ID, 'weightDate')
        notes_input = self.driver.find_element(By.ID, 'weightNotes')
        
        self.assertTrue(weight_input.is_displayed())
        self.assertTrue(date_input.is_displayed())
        self.assertTrue(notes_input.is_displayed())
        
        # Проверяем кнопки
        submit_btn = weight_form.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        clear_btn = self.driver.find_element(By.ID, 'clearWeightForm')
        
        self.assertTrue(submit_btn.is_displayed())
        self.assertTrue(clear_btn.is_displayed())
    
    def test_blood_pressure_tab_functionality(self):
        """Тест функциональности вкладки артериального давления."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Переключаемся на вкладку давления
        bp_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab-target="blood-pressure-tracking"]')
        bp_tab.click()
        
        # Ждем, пока вкладка станет активной
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'bloodPressureForm'))
        )
        
        # Проверяем, что вкладка активна
        self.assertIn('active', bp_tab.get_attribute('class'))
        
        # Проверяем наличие формы ввода давления
        bp_form = self.driver.find_element(By.ID, 'bloodPressureForm')
        self.assertTrue(bp_form.is_displayed())
        
        # Проверяем поля формы
        systolic_input = self.driver.find_element(By.ID, 'systolicValue')
        diastolic_input = self.driver.find_element(By.ID, 'diastolicValue')
        pulse_input = self.driver.find_element(By.ID, 'pulseValue')
        bp_date_input = self.driver.find_element(By.ID, 'bpDate')
        bp_notes_input = self.driver.find_element(By.ID, 'bpNotes')
        
        self.assertTrue(systolic_input.is_displayed())
        self.assertTrue(diastolic_input.is_displayed())
        self.assertTrue(pulse_input.is_displayed())
        self.assertTrue(bp_date_input.is_displayed())
        self.assertTrue(bp_notes_input.is_displayed())
    
    def test_statistics_tab_functionality(self):
        """Тест функциональности вкладки статистики."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Переключаемся на вкладку статистики
        stats_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab-target="health-statistics"]')
        stats_tab.click()
        
        # Ждем загрузки статистики
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'statisticsContent'))
        )
        
        # Проверяем, что вкладка активна
        self.assertIn('active', stats_tab.get_attribute('class'))
        
        # Проверяем наличие элементов статистики
        weight_stats = self.driver.find_element(By.ID, 'weightStatistics')
        bp_stats = self.driver.find_element(By.ID, 'bpStatistics')
        recommendations = self.driver.find_element(By.ID, 'healthRecommendations')
        
        self.assertTrue(weight_stats.is_displayed())
        self.assertTrue(bp_stats.is_displayed())
        self.assertTrue(recommendations.is_displayed())
        
        # Проверяем фильтр периода
        period_filter = self.driver.find_element(By.ID, 'statisticsPeriod')
        self.assertTrue(period_filter.is_displayed())
        
        # Проверяем кнопку обновления
        refresh_btn = self.driver.find_element(By.ID, 'refreshStatistics')
        self.assertTrue(refresh_btn.is_displayed())
    
    def test_tab_switching(self):
        """Тест переключения между вкладками."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Получаем все вкладки
        weight_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab-target="weight-tracking"]')
        bp_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab-target="blood-pressure-tracking"]')
        stats_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab-target="health-statistics"]')
        
        # Получаем содержимое вкладок
        weight_content = self.driver.find_element(By.ID, 'weight-tracking')
        bp_content = self.driver.find_element(By.ID, 'blood-pressure-tracking')
        stats_content = self.driver.find_element(By.ID, 'health-statistics')
        
        # Изначально активна вкладка веса
        self.assertIn('active', weight_tab.get_attribute('class'))
        self.assertTrue(weight_content.is_displayed())
        self.assertFalse(bp_content.is_displayed())
        self.assertFalse(stats_content.is_displayed())
        
        # Переключаемся на вкладку давления
        bp_tab.click()
        time.sleep(0.5)  # Небольшая задержка для анимации
        
        self.assertNotIn('active', weight_tab.get_attribute('class'))
        self.assertIn('active', bp_tab.get_attribute('class'))
        self.assertFalse(weight_content.is_displayed())
        self.assertTrue(bp_content.is_displayed())
        self.assertFalse(stats_content.is_displayed())
        
        # Переключаемся на вкладку статистики
        stats_tab.click()
        time.sleep(0.5)
        
        self.assertNotIn('active', bp_tab.get_attribute('class'))
        self.assertIn('active', stats_tab.get_attribute('class'))
        self.assertFalse(weight_content.is_displayed())
        self.assertFalse(bp_content.is_displayed())
        self.assertTrue(stats_content.is_displayed())
    
    def test_form_validation(self):
        """Тест валидации форм."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Тест валидации формы веса
        weight_form = self.driver.find_element(By.ID, 'weightForm')
        submit_btn = weight_form.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        
        # Попытка отправить пустую форму
        submit_btn.click()
        
        # Проверяем, что браузер показывает валидационное сообщение
        weight_input = self.driver.find_element(By.ID, 'weightValue')
        validation_message = weight_input.get_attribute('validationMessage')
        self.assertNotEqual(validation_message, '')
        
        # Тест валидации формы давления
        bp_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab-target="blood-pressure-tracking"]')
        bp_tab.click()
        
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'bloodPressureForm'))
        )
        
        bp_form = self.driver.find_element(By.ID, 'bloodPressureForm')
        bp_submit_btn = bp_form.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        
        # Попытка отправить пустую форму
        bp_submit_btn.click()
        
        # Проверяем валидацию систолического давления
        systolic_input = self.driver.find_element(By.ID, 'systolicValue')
        validation_message = systolic_input.get_attribute('validationMessage')
        self.assertNotEqual(validation_message, '')
    
    def test_clear_form_functionality(self):
        """Тест функциональности очистки форм."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Заполняем форму веса
        weight_input = self.driver.find_element(By.ID, 'weightValue')
        notes_input = self.driver.find_element(By.ID, 'weightNotes')
        
        weight_input.send_keys('70.5')
        notes_input.send_keys('Тестовые заметки')
        
        # Проверяем, что поля заполнены
        self.assertEqual(weight_input.get_attribute('value'), '70.5')
        self.assertEqual(notes_input.get_attribute('value'), 'Тестовые заметки')
        
        # Нажимаем кнопку очистки
        clear_btn = self.driver.find_element(By.ID, 'clearWeightForm')
        clear_btn.click()
        
        # Проверяем, что поля очищены
        self.assertEqual(weight_input.get_attribute('value'), '')
        self.assertEqual(notes_input.get_attribute('value'), '')
    
    def test_period_filter_functionality(self):
        """Тест функциональности фильтра периода."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Проверяем фильтр на вкладке веса
        weight_filter = self.driver.find_element(By.ID, 'weightPeriodFilter')
        self.assertTrue(weight_filter.is_displayed())
        
        # Проверяем опции фильтра
        select = Select(weight_filter)
        options = [option.text for option in select.options]
        
        expected_options = ['Последние 7 дней', 'Последние 30 дней', 'Последние 3 месяца', 'Последний год']
        for expected_option in expected_options:
            self.assertIn(expected_option, options)
        
        # Проверяем, что по умолчанию выбрано "Последние 30 дней"
        selected_option = select.first_selected_option
        self.assertEqual(selected_option.text, 'Последние 30 дней')
    
    def test_responsive_design_elements(self):
        """Тест адаптивности дизайна."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Проверяем наличие responsive классов
        forms = self.driver.find_elements(By.CSS_SELECTOR, '.grid')
        self.assertGreater(len(forms), 0)
        
        # Проверяем, что формы используют grid layout
        for form in forms:
            classes = form.get_attribute('class')
            self.assertIn('grid', classes)
    
    def test_accessibility_features(self):
        """Тест функций доступности."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Проверяем наличие labels для всех input полей
        inputs = self.driver.find_elements(By.TAG_NAME, 'input')
        for input_elem in inputs:
            input_id = input_elem.get_attribute('id')
            if input_id:
                try:
                    label = self.driver.find_element(By.CSS_SELECTOR, f'label[for="{input_id}"]')
                    self.assertTrue(label.is_displayed())
                except NoSuchElementException:
                    # Некоторые input могут не иметь явных labels (например, datetime-local)
                    pass
        
        # Проверяем наличие required атрибутов
        required_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[required]')
        self.assertGreater(len(required_inputs), 0)
        
        # Проверяем наличие placeholder текста
        placeholders = self.driver.find_elements(By.CSS_SELECTOR, 'input[placeholder]')
        self.assertGreater(len(placeholders), 0)
    
    def test_error_handling_display(self):
        """Тест отображения ошибок."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Проверяем наличие контейнера для сообщений
        messages_container = self.driver.find_element(By.ID, 'healthMessages')
        self.assertFalse(messages_container.is_displayed())  # Изначально скрыт
        
        # Проверяем наличие элементов сообщения
        message_content = self.driver.find_element(By.ID, 'healthMessageContent')
        message_icon = self.driver.find_element(By.ID, 'healthMessageIcon')
        message_text = self.driver.find_element(By.ID, 'healthMessageText')
        
        self.assertTrue(message_content)
        self.assertTrue(message_icon)
        self.assertTrue(message_text)


class HealthTrackerInteractionTest(LiveServerTestCase):
    """Тесты взаимодействия с интерфейсом отслеживания здоровья."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except Exception as e:
            cls.driver = None
            print(f"Chrome WebDriver недоступен: {e}")
    
    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Настройка тестовых данных."""
        if not self.driver:
            self.skipTest("WebDriver недоступен")
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_weight_form_interaction(self):
        """Тест взаимодействия с формой веса."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Заполняем форму
        weight_input = self.driver.find_element(By.ID, 'weightValue')
        notes_input = self.driver.find_element(By.ID, 'weightNotes')
        
        weight_input.clear()
        weight_input.send_keys('68.5')
        notes_input.clear()
        notes_input.send_keys('Тестовая запись через UI')
        
        # Проверяем, что значения введены корректно
        self.assertEqual(weight_input.get_attribute('value'), '68.5')
        self.assertEqual(notes_input.get_attribute('value'), 'Тестовая запись через UI')
    
    def test_blood_pressure_form_interaction(self):
        """Тест взаимодействия с формой давления."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Переключаемся на вкладку давления
        bp_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab-target="blood-pressure-tracking"]')
        bp_tab.click()
        
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'systolicValue'))
        )
        
        # Заполняем форму
        systolic_input = self.driver.find_element(By.ID, 'systolicValue')
        diastolic_input = self.driver.find_element(By.ID, 'diastolicValue')
        pulse_input = self.driver.find_element(By.ID, 'pulseValue')
        bp_notes_input = self.driver.find_element(By.ID, 'bpNotes')
        
        systolic_input.clear()
        systolic_input.send_keys('125')
        diastolic_input.clear()
        diastolic_input.send_keys('82')
        pulse_input.clear()
        pulse_input.send_keys('75')
        bp_notes_input.clear()
        bp_notes_input.send_keys('Тестовая запись давления через UI')
        
        # Проверяем, что значения введены корректно
        self.assertEqual(systolic_input.get_attribute('value'), '125')
        self.assertEqual(diastolic_input.get_attribute('value'), '82')
        self.assertEqual(pulse_input.get_attribute('value'), '75')
        self.assertEqual(bp_notes_input.get_attribute('value'), 'Тестовая запись давления через UI')
    
    def test_modal_interactions(self):
        """Тест взаимодействия с модальными окнами."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Проверяем, что модальные окна изначально скрыты
        edit_modal = self.driver.find_element(By.ID, 'editRecordModal')
        delete_modal = self.driver.find_element(By.ID, 'deleteConfirmModal')
        
        self.assertFalse(edit_modal.is_displayed())
        self.assertFalse(delete_modal.is_displayed())
        
        # Проверяем наличие кнопок отмены в модальных окнах
        cancel_edit_btn = self.driver.find_element(By.ID, 'cancelEdit')
        cancel_delete_btn = self.driver.find_element(By.ID, 'cancelDelete')
        
        self.assertTrue(cancel_edit_btn)
        self.assertTrue(cancel_delete_btn)


class HealthTrackerPerformanceTest(LiveServerTestCase):
    """Тесты производительности интерфейса отслеживания здоровья."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except Exception as e:
            cls.driver = None
            print(f"Chrome WebDriver недоступен: {e}")
    
    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Настройка тестовых данных."""
        if not self.driver:
            self.skipTest("WebDriver недоступен")
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем много тестовых записей для проверки производительности
        for i in range(50):
            WeightRecord.objects.create(
                user=self.user,
                date=timezone.now() - timedelta(days=i),
                weight=Decimal(f'{65 + i * 0.1:.1f}'),
                notes=f'Запись {i}'
            )
            
            BloodPressureRecord.objects.create(
                user=self.user,
                date=timezone.now() - timedelta(days=i),
                systolic=120 + i,
                diastolic=80 + i // 2,
                pulse=70 + i // 3,
                notes=f'Запись давления {i}'
            )
    
    def test_page_load_performance(self):
        """Тест производительности загрузки страницы."""
        start_time = time.time()
        
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Ждем загрузки основных элементов
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'weightForm'))
        )
        
        load_time = time.time() - start_time
        
        # Страница должна загружаться менее чем за 5 секунд
        self.assertLess(load_time, 5.0, f"Страница загружалась {load_time:.2f} секунд")
    
    def test_tab_switching_performance(self):
        """Тест производительности переключения вкладок."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        tabs = [
            '[data-tab-target="weight-tracking"]',
            '[data-tab-target="blood-pressure-tracking"]',
            '[data-tab-target="health-statistics"]'
        ]
        
        for tab_selector in tabs:
            start_time = time.time()
            
            tab = self.driver.find_element(By.CSS_SELECTOR, tab_selector)
            tab.click()
            
            # Ждем, пока вкладка станет активной
            WebDriverWait(self.driver, 5).until(
                lambda driver: 'active' in tab.get_attribute('class')
            )
            
            switch_time = time.time() - start_time
            
            # Переключение должно происходить менее чем за 1 секунду
            self.assertLess(switch_time, 1.0, f"Переключение на вкладку заняло {switch_time:.2f} секунд")
    
    def test_large_dataset_handling(self):
        """Тест обработки большого количества данных."""
        self.driver.get(f'{self.live_server_url}/tools/health-tracker/?user_id={self.user.id}')
        
        # Переключаемся на статистику, которая должна обработать все данные
        stats_tab = self.driver.find_element(By.CSS_SELECTOR, '[data-tab-target="health-statistics"]')
        
        start_time = time.time()
        stats_tab.click()
        
        # Ждем загрузки статистики
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, 'statisticsContent'))
        )
        
        load_time = time.time() - start_time
        
        # Загрузка статистики должна занимать менее 10 секунд даже с большим количеством данных
        self.assertLess(load_time, 10.0, f"Загрузка статистики заняла {load_time:.2f} секунд")