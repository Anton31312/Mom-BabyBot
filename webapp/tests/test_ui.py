"""
UI тесты для веб-интерфейса материнского ухода.

Этот модуль содержит тесты пользовательского интерфейса, проверяющие отображение
на разных устройствах, пользовательские сценарии и доступность интерфейса.
"""

import unittest
import time
from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta

from botapp.models import User, db_manager
from botapp.models_child import Child, Measurement
from botapp.models_timers import Contraction, ContractionEvent, Kick, KickEvent, SleepSession, FeedingSession
from botapp.models_vaccine import Vaccine, ChildVaccine


class UITestCase(StaticLiveServerTestCase):
    """Базовый класс для UI-тестов."""
    
    @classmethod
    def setUpClass(cls):
        """Настройка класса тестов."""
        super().setUpClass()
        
        # Настройка Chrome WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Запуск в безголовом режиме
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Создаем экземпляр WebDriver
        try:
            cls.browser = webdriver.Chrome(options=chrome_options)
        except WebDriverException:
            # Если Chrome не доступен, пробуем Firefox
            cls.browser = webdriver.Firefox(options=webdriver.FirefoxOptions().add_argument("--headless"))
        
        cls.browser.implicitly_wait(10)
    
    @classmethod
    def tearDownClass(cls):
        """Очистка после выполнения всех тестов класса."""
        cls.browser.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        # Создаем тестового пользователя
        session = db_manager.get_session()
        try:
            self.user = User(
                telegram_id=123456789,
                username='testuser',
                first_name='Test',
                last_name='User',
                is_pregnant=True,
                pregnancy_week=30
            )
            session.add(self.user)
            session.commit()
            session.refresh(self.user)
            
            # Создаем тестового ребенка
            self.child = Child(
                user_id=self.user.id,
                name='Test Child',
                birth_date=datetime.now() - timedelta(days=180)  # 6 месяцев
            )
            session.add(self.child)
            session.commit()
            session.refresh(self.child)
            
            # Создаем тестовую вакцину
            self.vaccine = Vaccine(
                name='Test Vaccine',
                description='Test vaccine description',
                recommended_age='6 месяцев',
                is_mandatory=True
            )
            session.add(self.vaccine)
            session.commit()
            session.refresh(self.vaccine)
            
        finally:
            db_manager.close_session(session)
    
    def tearDown(self):
        """Очистка после каждого теста."""
        session = db_manager.get_session()
        try:
            # Удаляем все связанные данные
            session.query(ChildVaccine).filter_by(child_id=self.child.id).delete()
            session.query(Measurement).filter_by(child_id=self.child.id).delete()
            session.query(FeedingSession).filter_by(child_id=self.child.id).delete()
            session.query(SleepSession).filter_by(child_id=self.child.id).delete()
            
            # Удаляем все события схваток и шевелений
            for contraction in session.query(Contraction).filter_by(user_id=self.user.id).all():
                session.query(ContractionEvent).filter_by(session_id=contraction.id).delete()
            session.query(Contraction).filter_by(user_id=self.user.id).delete()
            
            for kick in session.query(Kick).filter_by(user_id=self.user.id).all():
                session.query(KickEvent).filter_by(session_id=kick.id).delete()
            session.query(Kick).filter_by(user_id=self.user.id).delete()
            
            # Удаляем тестового ребенка
            session.query(Child).filter_by(id=self.child.id).delete()
            
            # Удаляем тестовую вакцину
            session.query(Vaccine).filter_by(id=self.vaccine.id).delete()
            
            # Удаляем тестового пользователя
            session.query(User).filter_by(id=self.user.id).delete()
            
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def wait_for_element(self, by, value, timeout=10):
        """Ожидание появления элемента на странице."""
        try:
            element = WebDriverWait(self.browser, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.fail(f"Элемент {value} не появился на странице за {timeout} секунд")


class ResponsiveDesignTestCase(UITestCase):
    """Тесты адаптивного дизайна для разных устройств."""
    
    def test_desktop_layout(self):
        """Тест отображения на десктопе."""
        # Устанавливаем размер окна для десктопа
        self.browser.set_window_size(1366, 768)
        
        # Открываем главную страницу
        self.browser.get(f"{self.live_server_url}/")
        
        # Проверяем, что навигационная панель отображается горизонтально
        nav = self.wait_for_element(By.CLASS_NAME, "navbar")
        self.assertTrue(nav.is_displayed())
        
        # Проверяем, что основной контент имеет многоколоночную структуру
        content = self.wait_for_element(By.CLASS_NAME, "content-container")
        self.assertTrue(content.is_displayed())
        
        # Проверяем, что карточки отображаются в несколько колонок
        cards = self.browser.find_elements(By.CLASS_NAME, "card")
        if cards:
            first_card = cards[0]
            # Получаем позицию первой карточки
            first_card_position = first_card.location
            
            # Если есть вторая карточка, проверяем, что она находится справа от первой
            if len(cards) > 1:
                second_card = cards[1]
                second_card_position = second_card.location
                
                # На десктопе карточки должны быть в одной строке (y примерно одинаковый)
                self.assertAlmostEqual(
                    first_card_position['y'], 
                    second_card_position['y'], 
                    delta=50  # Допускаем небольшую погрешность
                )
    
    def test_tablet_layout(self):
        """Тест отображения на планшете."""
        # Устанавливаем размер окна для планшета
        self.browser.set_window_size(768, 1024)
        
        # Открываем главную страницу
        self.browser.get(f"{self.live_server_url}/")
        
        # Проверяем, что навигационная панель отображается
        nav = self.wait_for_element(By.CLASS_NAME, "navbar")
        self.assertTrue(nav.is_displayed())
        
        # Проверяем, что основной контент имеет двухколоночную структуру
        content = self.wait_for_element(By.CLASS_NAME, "content-container")
        self.assertTrue(content.is_displayed())
        
        # Проверяем, что карточки отображаются в две колонки
        cards = self.browser.find_elements(By.CLASS_NAME, "card")
        if len(cards) > 2:
            first_card = cards[0]
            second_card = cards[1]
            third_card = cards[2]
            
            # Получаем позиции карточек
            first_card_position = first_card.location
            second_card_position = second_card.location
            third_card_position = third_card.location
            
            # Первые две карточки должны быть в одной строке
            self.assertAlmostEqual(
                first_card_position['y'], 
                second_card_position['y'], 
                delta=50
            )
            
            # Третья карточка должна быть ниже
            self.assertGreater(
                third_card_position['y'], 
                first_card_position['y'] + first_card.size['height'] - 50
            )
    
    def test_mobile_layout(self):
        """Тест отображения на мобильном устройстве."""
        # Устанавливаем размер окна для мобильного устройства
        self.browser.set_window_size(375, 667)  # iPhone 6/7/8
        
        # Открываем главную страницу
        self.browser.get(f"{self.live_server_url}/")
        
        # Проверяем, что навигационная панель отображается
        nav = self.wait_for_element(By.CLASS_NAME, "navbar")
        self.assertTrue(nav.is_displayed())
        
        # Проверяем, что меню-гамбургер отображается на мобильных устройствах
        hamburger = self.browser.find_elements(By.CLASS_NAME, "navbar-toggler")
        if hamburger:
            self.assertTrue(hamburger[0].is_displayed())
        
        # Проверяем, что карточки отображаются в одну колонку
        cards = self.browser.find_elements(By.CLASS_NAME, "card")
        if len(cards) > 1:
            first_card = cards[0]
            second_card = cards[1]
            
            # Получаем позиции карточек
            first_card_position = first_card.location
            second_card_position = second_card.location
            
            # На мобильном карточки должны быть одна под другой
            self.assertGreater(
                second_card_position['y'], 
                first_card_position['y']
            )


class UserFlowTestCase(UITestCase):
    """Тесты пользовательских сценариев."""
    
    def test_contraction_counter_flow(self):
        """Тест сценария использования счетчика схваток."""
        # Открываем страницу счетчика схваток
        self.browser.get(f"{self.live_server_url}/contractions/")
        
        # Проверяем, что страница загрузилась
        self.wait_for_element(By.CLASS_NAME, "contraction-counter")
        
        # Нажимаем кнопку "Начать"
        start_button = self.browser.find_element(By.ID, "start-contraction-session")
        start_button.click()
        
        # Проверяем, что сессия началась
        self.wait_for_element(By.ID, "contraction-session-active")
        
        # Нажимаем кнопку "Записать схватку" несколько раз
        record_button = self.browser.find_element(By.ID, "record-contraction")
        for _ in range(3):
            record_button.click()
            time.sleep(1)  # Небольшая пауза между нажатиями
        
        # Проверяем, что схватки записаны
        contraction_events = self.browser.find_elements(By.CLASS_NAME, "contraction-event")
        self.assertEqual(len(contraction_events), 3)
        
        # Нажимаем кнопку "Завершить"
        end_button = self.browser.find_element(By.ID, "end-contraction-session")
        end_button.click()
        
        # Проверяем, что сессия завершена и отображается статистика
        self.wait_for_element(By.CLASS_NAME, "contraction-statistics")
    
    def test_child_profile_flow(self):
        """Тест сценария управления профилем ребенка."""
        # Открываем страницу профилей детей
        self.browser.get(f"{self.live_server_url}/children/")
        
        # Проверяем, что страница загрузилась
        self.wait_for_element(By.CLASS_NAME, "children-profiles")
        
        # Нажимаем кнопку "Добавить ребенка"
        add_button = self.browser.find_element(By.ID, "add-child")
        add_button.click()
        
        # Заполняем форму создания профиля ребенка
        self.wait_for_element(By.ID, "child-form")
        
        name_input = self.browser.find_element(By.ID, "child-name")
        name_input.send_keys("Test Child 2")
        
        birth_date_input = self.browser.find_element(By.ID, "child-birth-date")
        birth_date_input.send_keys((datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        
        # Отправляем форму
        submit_button = self.browser.find_element(By.ID, "submit-child")
        submit_button.click()
        
        # Проверяем, что профиль создан и отображается в списке
        self.wait_for_element(By.CLASS_NAME, "child-profile-card")
        child_cards = self.browser.find_elements(By.CLASS_NAME, "child-profile-card")
        self.assertGreaterEqual(len(child_cards), 1)
        
        # Открываем профиль ребенка
        child_cards[0].click()
        
        # Проверяем, что страница профиля загрузилась
        self.wait_for_element(By.CLASS_NAME, "child-profile-details")
        
        # Добавляем измерение
        add_measurement_button = self.browser.find_element(By.ID, "add-measurement")
        add_measurement_button.click()
        
        # Заполняем форму измерения
        self.wait_for_element(By.ID, "measurement-form")
        
        height_input = self.browser.find_element(By.ID, "measurement-height")
        height_input.send_keys("68.5")
        
        weight_input = self.browser.find_element(By.ID, "measurement-weight")
        weight_input.send_keys("8.2")
        
        head_input = self.browser.find_element(By.ID, "measurement-head")
        head_input.send_keys("43.0")
        
        # Отправляем форму
        submit_button = self.browser.find_element(By.ID, "submit-measurement")
        submit_button.click()
        
        # Проверяем, что измерение добавлено и отображается в списке
        self.wait_for_element(By.CLASS_NAME, "measurement-item")
        measurements = self.browser.find_elements(By.CLASS_NAME, "measurement-item")
        self.assertGreaterEqual(len(measurements), 1)
    
    def test_sleep_timer_flow(self):
        """Тест сценария использования таймера сна."""
        # Открываем страницу таймера сна
        self.browser.get(f"{self.live_server_url}/sleep/")
        
        # Проверяем, что страница загрузилась
        self.wait_for_element(By.CLASS_NAME, "sleep-timer")
        
        # Выбираем ребенка из списка
        child_select = self.browser.find_element(By.ID, "child-select")
        child_select.click()
        
        # Выбираем первого ребенка в списке
        child_option = self.wait_for_element(By.CSS_SELECTOR, "#child-select option")
        child_option.click()
        
        # Выбираем тип сна
        sleep_type_select = self.browser.find_element(By.ID, "sleep-type")
        sleep_type_select.click()
        
        # Выбираем дневной сон
        day_option = self.wait_for_element(By.CSS_SELECTOR, "#sleep-type option[value='day']")
        day_option.click()
        
        # Нажимаем кнопку "Начать"
        start_button = self.browser.find_element(By.ID, "start-sleep")
        start_button.click()
        
        # Проверяем, что таймер запущен
        self.wait_for_element(By.ID, "sleep-timer-active")
        
        # Ждем несколько секунд
        time.sleep(3)
        
        # Нажимаем кнопку "Завершить"
        end_button = self.browser.find_element(By.ID, "end-sleep")
        end_button.click()
        
        # Проверяем, что сессия завершена и отображается в истории
        self.wait_for_element(By.CLASS_NAME, "sleep-history")
        sleep_sessions = self.browser.find_elements(By.CLASS_NAME, "sleep-session")
        self.assertGreaterEqual(len(sleep_sessions), 1)


class AccessibilityTestCase(UITestCase):
    """Тесты доступности интерфейса."""
    
    def test_semantic_html(self):
        """Тест использования семантического HTML."""
        # Открываем главную страницу
        self.browser.get(f"{self.live_server_url}/")
        
        # Проверяем наличие основных семантических элементов
        semantic_elements = [
            "header", "nav", "main", "footer", "section", "article", "aside"
        ]
        
        for element in semantic_elements:
            elements = self.browser.find_elements(By.TAG_NAME, element)
            self.assertGreaterEqual(
                len(elements), 
                0, 
                f"Семантический элемент {element} не найден на странице"
            )
    
    def test_image_alt_attributes(self):
        """Тест наличия alt-атрибутов у изображений."""
        # Открываем главную страницу
        self.browser.get(f"{self.live_server_url}/")
        
        # Проверяем, что все изображения имеют alt-атрибуты
        images = self.browser.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt = img.get_attribute("alt")
            self.assertIsNotNone(alt, "Изображение без alt-атрибута")
            self.assertNotEqual(alt, "", "Изображение с пустым alt-атрибутом")
    
    def test_form_labels(self):
        """Тест наличия меток у полей форм."""
        # Открываем страницу с формой (например, добавление ребенка)
        self.browser.get(f"{self.live_server_url}/children/add/")
        
        # Проверяем, что все поля ввода имеют связанные метки
        inputs = self.browser.find_elements(By.TAG_NAME, "input")
        for input_field in inputs:
            if input_field.get_attribute("type") not in ["submit", "button", "hidden"]:
                input_id = input_field.get_attribute("id")
                if input_id:
                    label = self.browser.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                    self.assertGreaterEqual(
                        len(label), 
                        1, 
                        f"Поле ввода с id={input_id} не имеет связанной метки"
                    )
    
    def test_keyboard_navigation(self):
        """Тест навигации с помощью клавиатуры."""
        # Открываем главную страницу
        self.browser.get(f"{self.live_server_url}/")
        
        # Находим все интерактивные элементы
        interactive_elements = self.browser.find_elements(By.CSS_SELECTOR, "a, button, input, select, textarea")
        
        # Проверяем, что можно перемещаться между элементами с помощью Tab
        body = self.browser.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.TAB)
        
        # Проверяем, что первый элемент получил фокус
        active_element = self.browser.switch_to.active_element
        self.assertIn(active_element, interactive_elements)
        
        # Проверяем, что можно перемещаться к следующему элементу
        active_element.send_keys(Keys.TAB)
        new_active_element = self.browser.switch_to.active_element
        self.assertNotEqual(active_element, new_active_element)
    
    def test_color_contrast(self):
        """Тест контрастности цветов (базовая проверка)."""
        # Открываем главную страницу
        self.browser.get(f"{self.live_server_url}/")
        
        # Проверяем контрастность текста и фона для основных элементов
        elements_to_check = [
            "body", "h1", "h2", "h3", "p", "a", "button"
        ]
        
        for element_tag in elements_to_check:
            elements = self.browser.find_elements(By.TAG_NAME, element_tag)
            for element in elements:
                # Получаем цвет текста и фона
                text_color = element.value_of_css_property("color")
                background_color = element.value_of_css_property("background-color")
                
                # Проверяем, что цвета определены
                self.assertIsNotNone(text_color)
                self.assertIsNotNone(background_color)
                
                # Здесь можно добавить более сложную проверку контрастности,
                # но для этого потребуется дополнительная библиотека для анализа цветов


if __name__ == '__main__':
    unittest.main()