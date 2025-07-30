"""
Тесты для интеграции дисклеймера на страницы с рекомендациями
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class DisclaimerIntegrationTest(TestCase):
    """Тесты для проверки интеграции дисклеймера на страницы с рекомендациями"""

    def setUp(self):
        """Настройка тестового окружения"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_disclaimer_on_pregnancy_page(self):
        """Тест наличия дисклеймера на странице беременности"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('webapp:pregnancy'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'disclaimer-component')
        self.assertContains(response, 'glass-disclaimer')
        self.assertContains(response, 'Внимание!')
        self.assertContains(response, 'Все рекомендации в приложении являются общими')

    def test_disclaimer_on_nutrition_page(self):
        """Тест наличия дисклеймера на странице питания"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('webapp:nutrition'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'disclaimer-component')
        self.assertContains(response, 'glass-disclaimer')
        self.assertContains(response, 'Внимание!')
        self.assertContains(response, 'обратитесь к специалисту')

    def test_disclaimer_on_child_development_page(self):
        """Тест наличия дисклеймера на странице развития ребенка"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('webapp:child_development'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'disclaimer-component')
        self.assertContains(response, 'glass-disclaimer')
        self.assertContains(response, 'Внимание!')
        self.assertContains(response, 'персонализированных рекомендаций')

    def test_disclaimer_on_health_tracker_page(self):
        """Тест наличия дисклеймера на странице отслеживания здоровья"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('webapp:health_tracker'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'disclaimer-component')
        self.assertContains(response, 'glass-disclaimer')
        self.assertContains(response, 'Внимание!')

    def test_disclaimer_on_kick_counter_page(self):
        """Тест наличия дисклеймера на странице счетчика шевелений"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('webapp:kick_counter'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'disclaimer-component')
        self.assertContains(response, 'glass-disclaimer')
        self.assertContains(response, 'Внимание!')

    def test_disclaimer_appears_before_recommendations(self):
        """Тест того, что дисклеймер появляется перед рекомендациями"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('webapp:pregnancy'))
        
        content = response.content.decode('utf-8')
        disclaimer_pos = content.find('disclaimer-component')
        recommendations_pos = content.find('Рекомендации')
        
        self.assertGreater(disclaimer_pos, 0, "Дисклеймер должен присутствовать на странице")
        self.assertGreater(recommendations_pos, 0, "Рекомендации должны присутствовать на странице")
        self.assertLess(disclaimer_pos, recommendations_pos, "Дисклеймер должен появляться перед рекомендациями")

    def test_disclaimer_uses_glass_style(self):
        """Тест того, что дисклеймер использует стеклянный стиль"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('webapp:nutrition'))
        
        self.assertContains(response, 'glass-disclaimer')
        self.assertNotContains(response, 'neo-disclaimer')
        self.assertNotContains(response, 'default-disclaimer')

    def test_disclaimer_content_consistency(self):
        """Тест согласованности содержимого дисклеймера на разных страницах"""
        self.client.login(username='testuser', password='testpass123')
        
        pages = [
            reverse('webapp:pregnancy'),
            reverse('webapp:nutrition'),
            reverse('webapp:child_development'),
            reverse('webapp:health_tracker'),
            reverse('webapp:kick_counter')
        ]
        
        for page_url in pages:
            response = self.client.get(page_url)
            self.assertEqual(response.status_code, 200)
            
            # Проверяем, что содержимое дисклеймера присутствует на всех страницах
            content = response.content.decode('utf-8')
            self.assertIn('Внимание!', content)
            self.assertIn('Все рекомендации в приложении являются общими', content)
            self.assertIn('обратитесь к специалисту', content)