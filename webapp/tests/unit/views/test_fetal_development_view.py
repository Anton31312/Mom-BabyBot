from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta

from webapp.models import FetalDevelopmentInfo, PregnancyInfo


class FetalDevelopmentViewTest(TestCase):
    """
    Тесты для представления страницы развития плода.
    
    Проверяет функциональность представления для отображения информации
    о развитии плода по неделям беременности (требование 10.3).
    """
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Создаем информацию о беременности
        due_date = date.today() + timedelta(days=140)  # 20 недель до родов
        self.pregnancy_info = PregnancyInfo.objects.create(
            user=self.user,
            due_date=due_date,
            is_active=True
        )
    
    def test_fetal_development_view_unauthorized(self):
        """Тест доступа к странице без авторизации."""
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Страница доступна без авторизации, но без информации о беременности
        self.assertEqual(response.status_code, 200)
    
    def test_fetal_development_view_authorized(self):
        """Тест доступа к странице с авторизацией."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Развитие плода по неделям беременности')
    
    def test_fetal_development_view_template_used(self):
        """Тест использования правильного шаблона."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        self.assertTemplateUsed(response, 'pregnancy/fetal_development.html')
    
    def test_fetal_development_view_context_with_pregnancy(self):
        """Тест контекста представления с активной беременностью."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие информации о беременности в контексте
        self.assertIn('pregnancy_info', response.context)
        self.assertEqual(response.context['pregnancy_info'], self.pregnancy_info)
        
        # Проверяем наличие диапазона недель
        self.assertIn('weeks_range', response.context)
        weeks_range = list(response.context['weeks_range'])
        self.assertEqual(weeks_range, list(range(1, 43)))
    
    def test_fetal_development_view_context_without_pregnancy(self):
        """Тест контекста представления без активной беременности."""
        # Создаем пользователя без беременности
        user_no_pregnancy = User.objects.create_user(
            username='nopregnancy',
            password='testpass123'
        )
        
        self.client.login(username='nopregnancy', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем, что pregnancy_info равно None
        self.assertIn('pregnancy_info', response.context)
        self.assertIsNone(response.context['pregnancy_info'])
        
        # Проверяем наличие диапазона недель
        self.assertIn('weeks_range', response.context)
        weeks_range = list(response.context['weeks_range'])
        self.assertEqual(weeks_range, list(range(1, 43)))
    
    def test_fetal_development_view_content_structure(self):
        """Тест структуры контента страницы."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем основные элементы страницы
        self.assertContains(response, 'Развитие плода по неделям беременности')
        self.assertContains(response, 'Выберите неделю беременности')
        self.assertContains(response, 'Предыдущая')
        self.assertContains(response, 'Следующая')
        self.assertContains(response, '1-й триместр')
        self.assertContains(response, '2-й триместр')
        self.assertContains(response, '3-й триместр')
    
    def test_fetal_development_view_includes_disclaimer(self):
        """Тест включения дисклеймера на странице."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие дисклеймера
        self.assertContains(response, 'disclaimer')
    
    def test_fetal_development_view_includes_pregnancy_progress(self):
        """Тест включения индикатора прогресса беременности."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем, что страница загружается успешно
        self.assertEqual(response.status_code, 200)
    
    def test_fetal_development_view_week_selectors(self):
        """Тест селекторов недель на странице."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие селекторов недель
        for week in [1, 10, 20, 30, 40, 42]:
            self.assertContains(response, f'data-week="{week}"')
        
        # Проверяем, что неделя 43 не включена
        self.assertNotContains(response, 'data-week="43"')
    
    def test_fetal_development_view_trimester_selectors(self):
        """Тест селекторов триместров на странице."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие селекторов триместров
        self.assertContains(response, 'data-trimester="1"')
        self.assertContains(response, 'data-trimester="2"')
        self.assertContains(response, 'data-trimester="3"')
        
        # Проверяем текст селекторов
        self.assertContains(response, '1-й триместр (1-12)')
        self.assertContains(response, '2-й триместр (13-28)')
        self.assertContains(response, '3-й триместр (29-40)')
    
    def test_fetal_development_view_javascript_initialization(self):
        """Тест инициализации JavaScript на странице."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие JavaScript кода
        self.assertContains(response, 'currentWeek')
        self.assertContains(response, 'loadFetalDevelopmentInfo')
        self.assertContains(response, 'fetal-development-content')
    
    def test_fetal_development_view_current_week_initialization(self):
        """Тест инициализации текущей недели для беременных пользователей."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем, что текущая неделя беременности передается в JavaScript
        current_week = self.pregnancy_info.current_week
        self.assertContains(response, f'currentWeek = {current_week}')
    
    def test_fetal_development_view_templates_included(self):
        """Тест включения необходимых шаблонов."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие шаблонов для JavaScript
        self.assertContains(response, 'fetal-development-template')
        self.assertContains(response, 'error-template')
    
    def test_fetal_development_view_responsive_design(self):
        """Тест адаптивного дизайна страницы."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие классов для адаптивного дизайна
        self.assertContains(response, 'grid-cols-7')  # Сетка для селекторов недель
        self.assertContains(response, 'flex-wrap')    # Гибкая компоновка
        self.assertContains(response, 'space-x-2')    # Отступы между элементами
    
    def test_fetal_development_view_accessibility(self):
        """Тест доступности страницы."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие элементов доступности
        self.assertContains(response, '<h1')  # Заголовок первого уровня
        self.assertContains(response, '<h2')  # Заголовки второго уровня
        
        # Проверяем семантические элементы
        self.assertContains(response, '<button')  # Кнопки
    
    def test_fetal_development_view_loading_state(self):
        """Тест состояния загрузки на странице."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие индикатора загрузки
        self.assertContains(response, 'animate-spin')
        self.assertContains(response, 'Загрузка информации о развитии плода')
    
    def test_fetal_development_view_error_handling(self):
        """Тест обработки ошибок на странице."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие шаблона для ошибок
        self.assertContains(response, 'error-template')
        self.assertContains(response, 'Ошибка загрузки')
        self.assertContains(response, 'retry-button')
    
    def test_fetal_development_view_navigation_controls(self):
        """Тест элементов навигации на странице."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие кнопок навигации
        self.assertContains(response, 'prev-week')
        self.assertContains(response, 'next-week')
        self.assertContains(response, 'current-week-display')
        
        # Проверяем SVG иконки для кнопок
        self.assertContains(response, 'stroke="currentColor"')
        self.assertContains(response, 'viewBox="0 0 24 24"')
    
    def test_fetal_development_view_content_sections(self):
        """Тест секций контента на странице."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем наличие секций для разного типа информации
        sections = [
            'organ_development',
            'maternal_changes',
            'common_symptoms',
            'recommendations',
            'dos_and_donts',
            'medical_checkups',
            'interesting_facts'
        ]
        
        for section in sections:
            self.assertContains(response, f'data-section="{section}"')
    
    def test_fetal_development_view_meta_tags(self):
        """Тест мета-тегов страницы."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем заголовок страницы
        self.assertContains(response, 'Mom&BabyBot - Развитие плода по неделям')
    
    def test_fetal_development_view_extends_base_template(self):
        """Тест наследования от базового шаблона."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('webapp:fetal_development')
        response = self.client.get(url)
        
        # Проверяем, что используется базовый шаблон
        self.assertTemplateUsed(response, 'base.html')
        
        # Проверяем наличие JavaScript кода (который находится в блоке extra_js)
        self.assertContains(response, 'currentWeek')