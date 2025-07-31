"""
Тесты для проверки переводов сообщений об ошибках.
"""

from django.test import TestCase
from django.utils import translation
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from webapp.forms import WeightRecordForm, BloodPressureRecordForm, FeedingSessionForm, UserRegistrationForm


class ErrorMessageTranslationTestCase(TestCase):
    """Тесты для проверки переводов сообщений об ошибках."""
    
    def setUp(self):
        """Настройка тестов."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_weight_form_error_translations(self):
        """Тест переводов ошибок формы веса."""
        with translation.override('ru'):
            # Тест пустой формы
            form = WeightRecordForm(data={})
            self.assertFalse(form.is_valid())
            
            # Тест отрицательного веса
            form = WeightRecordForm(data={'weight': -10})
            self.assertFalse(form.is_valid())
            self.assertIn('положительным', str(form.errors['weight']))
            
            # Тест слишком большого веса
            form = WeightRecordForm(data={'weight': 1500})
            self.assertFalse(form.is_valid())
            self.assertIn('999.99', str(form.errors['weight']))
    
    def test_blood_pressure_form_error_translations(self):
        """Тест переводов ошибок формы артериального давления."""
        with translation.override('ru'):
            # Тест пустой формы
            form = BloodPressureRecordForm(data={})
            self.assertFalse(form.is_valid())
            
            # Тест неправильного соотношения давлений
            form = BloodPressureRecordForm(data={
                'systolic': 80,
                'diastolic': 120
            })
            self.assertFalse(form.is_valid())
            self.assertIn('выше', str(form.errors['__all__']))
            
            # Тест слишком низкого систолического давления
            form = BloodPressureRecordForm(data={
                'systolic': 30,
                'diastolic': 80
            })
            self.assertFalse(form.is_valid())
            self.assertIn('не менее 50', str(form.errors['systolic']))
    
    def test_feeding_form_error_translations(self):
        """Тест переводов ошибок формы кормления."""
        with translation.override('ru'):
            # Тест кормления из бутылочки без указания количества
            form = FeedingSessionForm(data={
                'feeding_type': 'bottle',
                'amount': None
            })
            self.assertFalse(form.is_valid())
            self.assertIn('обязательно', str(form.errors['amount']))
            
            # Тест отрицательного количества
            form = FeedingSessionForm(data={
                'feeding_type': 'bottle',
                'amount': -50
            })
            self.assertFalse(form.is_valid())
            self.assertIn('положительным', str(form.errors['amount']))
    
    def test_user_registration_form_error_translations(self):
        """Тест переводов ошибок формы регистрации."""
        with translation.override('ru'):
            # Тест несовпадающих паролей
            form = UserRegistrationForm(data={
                'username': 'newuser',
                'email': 'new@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'password': 'testpass123',
                'password_confirm': 'differentpass'
            })
            self.assertFalse(form.is_valid())
            self.assertIn('не совпадают', str(form.errors['password_confirm']))
            
            # Тест слишком короткого пароля
            form = UserRegistrationForm(data={
                'username': 'newuser2',
                'email': 'new2@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'password': '123',
                'password_confirm': '123'
            })
            self.assertFalse(form.is_valid())
            self.assertIn('не менее 8', str(form.errors['password']))
            
            # Тест простого пароля
            form = UserRegistrationForm(data={
                'username': 'newuser3',
                'email': 'new3@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'password': 'password',
                'password_confirm': 'password'
            })
            self.assertFalse(form.is_valid())
            self.assertIn('простой', str(form.errors['password']))
    
    def test_validation_error_translation(self):
        """Тест переводов общих ошибок валидации."""
        with translation.override('ru'):
            # Проверяем переводы основных сообщений об ошибках
            self.assertEqual(_('This field is required.'), 'Это поле обязательно для заполнения.')
            self.assertEqual(_('Please enter a valid email address.'), 'Пожалуйста, введите корректный email адрес.')
            self.assertEqual(_('Passwords do not match.'), 'Пароли не совпадают.')
            self.assertEqual(_('Weight must be a positive number.'), 'Вес должен быть положительным числом.')
    
    def test_field_label_translations(self):
        """Тест переводов меток полей."""
        with translation.override('ru'):
            # Проверяем переводы меток полей
            self.assertEqual(_('Weight (kg)'), 'Вес (кг)')
            self.assertEqual(_('Systolic pressure'), 'Систолическое давление')
            self.assertEqual(_('Diastolic pressure'), 'Диастолическое давление')
            self.assertEqual(_('Feeding type'), 'Тип кормления')
            self.assertEqual(_('Username'), 'Имя пользователя')
    
    def test_help_text_translations(self):
        """Тест переводов текстов помощи."""
        with translation.override('ru'):
            # Проверяем переводы текстов помощи
            self.assertEqual(_('Enter your weight in kilograms'), 'Введите ваш вес в килограммах')
            self.assertEqual(_('Upper blood pressure value'), 'Верхнее значение артериального давления')
            self.assertEqual(_('Select the type of feeding'), 'Выберите тип кормления')
            self.assertEqual(_('Enter a unique username'), 'Введите уникальное имя пользователя')
    
    def test_choice_field_translations(self):
        """Тест переводов вариантов выбора."""
        with translation.override('ru'):
            # Проверяем переводы вариантов выбора
            self.assertEqual(_('Breast feeding'), 'Грудное вскармливание')
            self.assertEqual(_('Bottle feeding'), 'Кормление из бутылочки')
            self.assertEqual(_('Mixed feeding'), 'Смешанное кормление')
            self.assertEqual(_('Left breast'), 'Левая грудь')
            self.assertEqual(_('Right breast'), 'Правая грудь')
    
    def test_api_error_message_format(self):
        """Тест формата сообщений об ошибках API."""
        with translation.override('ru'):
            # Проверяем формат сообщения об ошибке валидации
            error_msg = _('Validation error: {}').format('Тестовая ошибка')
            self.assertEqual(error_msg, 'Ошибка валидации: Тестовая ошибка')
    
    def test_model_verbose_names(self):
        """Тест переводов verbose_name моделей."""
        with translation.override('ru'):
            # Проверяем переводы названий полей моделей
            self.assertEqual(_('User'), 'Пользователь')
            self.assertEqual(_('Start time'), 'Время начала')
            self.assertEqual(_('End time'), 'Время окончания')