"""
Тесты для проверки системы переводов.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _


class TranslationTestCase(TestCase):
    """Тесты для проверки переводов интерфейса."""
    
    def setUp(self):
        """Настройка тестов."""
        self.client = Client()
    
    def test_russian_translation_activation(self):
        """Тест активации русского языка."""
        with translation.override('ru'):
            # Проверяем, что переводы загружаются
            self.assertEqual(_('Home'), 'Главная')
            self.assertEqual(_('Pregnancy'), 'Беременность')
            self.assertEqual(_('Tools'), 'Инструменты')
    
    def test_english_fallback(self):
        """Тест отката на английский язык."""
        with translation.override('en'):
            # Проверяем, что английские строки остаются без изменений
            self.assertEqual(_('Home'), 'Home')
            self.assertEqual(_('Pregnancy'), 'Pregnancy')
            self.assertEqual(_('Tools'), 'Tools')
    
    def test_index_page_translations(self):
        """Тест переводов на главной странице."""
        with translation.override('ru'):
            response = self.client.get(reverse('webapp:index'))
            self.assertEqual(response.status_code, 200)
            
            # Проверяем, что русские переводы присутствуют в HTML
            content = response.content.decode('utf-8')
            self.assertIn('Главная', content)
            self.assertIn('Беременность', content)
            self.assertIn('Инструменты', content)
    
    def test_navigation_translations(self):
        """Тест переводов в навигации."""
        with translation.override('ru'):
            response = self.client.get(reverse('webapp:index'))
            content = response.content.decode('utf-8')
            
            # Проверяем переводы пунктов меню
            self.assertIn('Счетчик схваток', content)
            self.assertIn('Счетчик шевелений', content)
            self.assertIn('Таймер сна', content)
            self.assertIn('Календарь прививок', content)
    
    def test_disclaimer_translations(self):
        """Тест переводов дисклеймера."""
        with translation.override('ru'):
            # Проверяем ключевые фразы дисклеймера
            attention = _('Attention!')
            disclaimer_text = _('All recommendations in the application are general and may not take into account individual characteristics. For personalized recommendations, consult a specialist.')
            
            self.assertEqual(attention, 'Внимание!')
            self.assertIn('рекомендации', disclaimer_text)
            self.assertIn('специалисту', disclaimer_text)
    
    def test_form_field_translations(self):
        """Тест переводов полей форм."""
        with translation.override('ru'):
            # Проверяем переводы общих полей форм
            self.assertEqual(_('Name'), 'Имя')
            self.assertEqual(_('Email'), 'Email')
            self.assertEqual(_('Date'), 'Дата')
            self.assertEqual(_('Time'), 'Время')
            self.assertEqual(_('Notes'), 'Заметки')
    
    def test_button_translations(self):
        """Тест переводов кнопок."""
        with translation.override('ru'):
            # Проверяем переводы кнопок
            self.assertEqual(_('Start'), 'Начать')
            self.assertEqual(_('Stop'), 'Остановить')
            self.assertEqual(_('Save'), 'Сохранить')
            self.assertEqual(_('Cancel'), 'Отмена')
            self.assertEqual(_('Open'), 'Открыть')
    
    def test_health_tracking_translations(self):
        """Тест переводов для отслеживания здоровья."""
        with translation.override('ru'):
            # Проверяем переводы медицинских терминов
            self.assertEqual(_('Weight'), 'Вес')
            self.assertEqual(_('Blood Pressure'), 'Артериальное давление')
            self.assertEqual(_('Systolic'), 'Систолическое')
            self.assertEqual(_('Diastolic'), 'Диастолическое')
            self.assertEqual(_('Pulse'), 'Пульс')
    
    def test_feeding_translations(self):
        """Тест переводов для отслеживания кормления."""
        with translation.override('ru'):
            # Проверяем переводы терминов кормления
            self.assertEqual(_('Feeding'), 'Кормление')
            self.assertEqual(_('Left Breast'), 'Левая грудь')
            self.assertEqual(_('Right Breast'), 'Правая грудь')
            self.assertEqual(_('Duration'), 'Продолжительность')
    
    def test_pregnancy_translations(self):
        """Тест переводов для беременности."""
        with translation.override('ru'):
            # Проверяем переводы терминов беременности
            self.assertEqual(_('Week'), 'Неделя')
            self.assertEqual(_('Trimester'), 'Триместр')
            self.assertEqual(_('Due Date'), 'Предполагаемая дата родов')
            self.assertEqual(_('Contractions'), 'Схватки')
            self.assertEqual(_('Kicks'), 'Шевеления')
    
    def test_validation_message_translations(self):
        """Тест переводов сообщений валидации."""
        with translation.override('ru'):
            # Проверяем переводы сообщений об ошибках
            required_msg = _('This field is required.')
            email_msg = _('Please enter a valid email address.')
            password_msg = _('Password is too short.')
            
            self.assertEqual(required_msg, 'Это поле обязательно для заполнения.')
            self.assertIn('email', email_msg)
            self.assertIn('Пароль', password_msg)
    
    def test_status_message_translations(self):
        """Тест переводов статусных сообщений."""
        with translation.override('ru'):
            # Проверяем переводы статусов
            self.assertEqual(_('Success'), 'Успешно')
            self.assertEqual(_('Error'), 'Ошибка')
            self.assertEqual(_('Loading'), 'Загрузка')
            self.assertEqual(_('Saved'), 'Сохранено')
    
    def test_time_unit_translations(self):
        """Тест переводов единиц времени."""
        with translation.override('ru'):
            # Проверяем переводы единиц времени
            self.assertEqual(_('seconds'), 'секунды')
            self.assertEqual(_('minutes'), 'минуты')
            self.assertEqual(_('hours'), 'часы')
            self.assertEqual(_('days'), 'дни')
            self.assertEqual(_('weeks'), 'недели')