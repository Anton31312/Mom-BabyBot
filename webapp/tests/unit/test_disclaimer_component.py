"""
Тесты для компонента дисклеймера
"""

from django.test import TestCase
from django.template import Context, Template
from django.template.loader import get_template


class DisclaimerComponentTest(TestCase):
    """Тесты для компонента дисклеймера"""

    def test_disclaimer_renders_with_default_style(self):
        """Тест отображения дисклеймера с базовым стилем"""
        template = Template(
            "{% load static %}"
            "{% include 'components/disclaimer.html' %}"
        )
        rendered = template.render(Context({}))
        
        # Проверяем наличие основных элементов
        self.assertIn('disclaimer-component', rendered)
        self.assertIn('default-disclaimer', rendered)
        self.assertIn('Внимание!', rendered)
        self.assertIn('Все рекомендации в приложении являются общими', rendered)
        self.assertIn('обратитесь к специалисту', rendered)

    def test_disclaimer_renders_with_glass_style(self):
        """Тест отображения дисклеймера со стеклянным стилем"""
        template = Template(
            "{% load static %}"
            "{% include 'components/disclaimer.html' with style='glass' %}"
        )
        rendered = template.render(Context({}))
        
        # Проверяем наличие стеклянного стиля
        self.assertIn('glass-disclaimer', rendered)
        self.assertNotIn('default-disclaimer', rendered)
        self.assertNotIn('neo-disclaimer', rendered)

    def test_disclaimer_renders_with_neo_style(self):
        """Тест отображения дисклеймера с неоморфным стилем"""
        template = Template(
            "{% load static %}"
            "{% include 'components/disclaimer.html' with style='neo' %}"
        )
        rendered = template.render(Context({}))
        
        # Проверяем наличие неоморфного стиля
        self.assertIn('neo-disclaimer', rendered)
        self.assertNotIn('default-disclaimer', rendered)
        self.assertNotIn('glass-disclaimer', rendered)

    def test_disclaimer_renders_with_custom_class(self):
        """Тест отображения дисклеймера с дополнительным CSS классом"""
        template = Template(
            "{% load static %}"
            "{% include 'components/disclaimer.html' with custom_class='my-custom-class' %}"
        )
        rendered = template.render(Context({}))
        
        # Проверяем наличие дополнительного класса
        self.assertIn('my-custom-class', rendered)

    def test_disclaimer_renders_without_icon(self):
        """Тест отображения дисклеймера без иконки"""
        template = Template(
            "{% load static %}"
            "{% include 'components/disclaimer.html' with show_icon=False %}"
        )
        rendered = template.render(Context({}))
        
        # Проверяем отсутствие иконки
        self.assertNotIn('disclaimer-icon', rendered)
        self.assertNotIn('<svg', rendered)

    def test_disclaimer_renders_with_icon_by_default(self):
        """Тест отображения дисклеймера с иконкой по умолчанию"""
        template = Template(
            "{% load static %}"
            "{% include 'components/disclaimer.html' %}"
        )
        rendered = template.render(Context({}))
        
        # Проверяем наличие иконки по умолчанию
        self.assertIn('disclaimer-icon', rendered)
        self.assertIn('<svg', rendered)

    def test_disclaimer_content_structure(self):
        """Тест структуры содержимого дисклеймера"""
        template = Template(
            "{% load static %}"
            "{% include 'components/disclaimer.html' %}"
        )
        rendered = template.render(Context({}))
        
        # Проверяем структуру содержимого
        self.assertIn('disclaimer-content', rendered)
        self.assertIn('disclaimer-title', rendered)
        self.assertIn('disclaimer-message', rendered)
        
        # Проверяем правильный порядок элементов
        title_pos = rendered.find('disclaimer-title')
        message_pos = rendered.find('disclaimer-message')
        self.assertLess(title_pos, message_pos, "Заголовок должен идти перед сообщением")

    def test_disclaimer_accessibility(self):
        """Тест доступности дисклеймера"""
        template = Template(
            "{% load static %}"
            "{% include 'components/disclaimer.html' %}"
        )
        rendered = template.render(Context({}))
        
        # Проверяем наличие семантических элементов
        self.assertIn('<strong>', rendered)
        
        # Проверяем, что SVG иконка имеет правильные атрибуты
        self.assertIn('viewBox="0 0 24 24"', rendered)
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', rendered)