"""
Тесты для проверки доступа к технической документации.

Проверяет, что техническая документация доступна только администраторам.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
import os
from django.conf import settings


class TechnicalDocumentationAccessTestCase(TestCase):
    """Тесты доступа к технической документации"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        
        # Создаем обычного пользователя
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='regular@example.com',
            password='testpass123'
        )
        
        # Создаем администратора
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # URL для технической документации
        self.tech_doc_url = reverse('webapp:technical_documentation')
    
    def test_unauthenticated_user_redirected_to_login(self):
        """Неаутентифицированный пользователь должен быть перенаправлен на страницу входа"""
        response = self.client.get(self.tech_doc_url)
        
        # Проверяем, что происходит редирект
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что редирект ведет на страницу входа
        self.assertIn('/accounts/login/', response.url)
    
    def test_regular_user_access_forbidden(self):
        """Обычный пользователь не должен иметь доступ к технической документации"""
        # Входим как обычный пользователь
        self.client.login(username='regular_user', password='testpass123')
        
        response = self.client.get(self.tech_doc_url)
        
        # Проверяем, что доступ запрещен
        self.assertEqual(response.status_code, 403)
        
        # Проверяем содержимое ответа
        self.assertIn('Доступ запрещен', response.content.decode('utf-8'))
        self.assertIn('администраторам', response.content.decode('utf-8'))
    
    def test_admin_user_access_allowed(self):
        """Администратор должен иметь доступ к технической документации"""
        # Входим как администратор
        self.client.login(username='admin_user', password='adminpass123')
        
        response = self.client.get(self.tech_doc_url)
        
        # Проверяем, что доступ разрешен
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что используется правильный шаблон
        self.assertTemplateUsed(response, 'documentation/technical_documentation.html')
        
        # Проверяем наличие контекстных переменных
        self.assertIn('tech_doc_content', response.context)
        self.assertIn('user', response.context)
        
        # Проверяем, что пользователь в контексте - это администратор
        self.assertEqual(response.context['user'], self.admin_user)
        self.assertTrue(response.context['user'].is_staff)
    
    def test_admin_user_sees_content(self):
        """Администратор должен видеть содержимое технической документации"""
        # Входим как администратор
        self.client.login(username='admin_user', password='adminpass123')
        
        response = self.client.get(self.tech_doc_url)
        
        # Проверяем содержимое страницы
        content = response.content.decode('utf-8')
        
        # Проверяем наличие основных элементов страницы
        self.assertIn('Техническая документация', content)
        self.assertIn('Доступ для администраторов', content)
        self.assertIn('admin_user', content)  # Имя пользователя должно отображаться
        
        # Проверяем наличие ссылок на другие разделы документации
        self.assertIn('API Документация', content)
        self.assertIn('Архитектура', content)
        self.assertIn('Развертывание', content)
    
    def test_technical_documentation_file_loading(self):
        """Проверяем загрузку файла технической документации"""
        # Входим как администратор
        self.client.login(username='admin_user', password='adminpass123')
        
        response = self.client.get(self.tech_doc_url)
        
        # Проверяем, что контент загружен
        tech_doc_content = response.context['tech_doc_content']
        self.assertIsNotNone(tech_doc_content)
        
        # Если файл существует, проверяем, что контент не пустой
        tech_doc_path = os.path.join(settings.BASE_DIR, 'docs', 'technical_documentation.md')
        if os.path.exists(tech_doc_path):
            self.assertNotEqual(tech_doc_content, "Техническая документация не найдена.")
            self.assertNotEqual(tech_doc_content, "Ошибка при загрузке технической документации.")
        else:
            # Если файл не существует, проверяем сообщение об ошибке
            self.assertEqual(tech_doc_content, "Техническая документация не найдена.")
    
    def test_staff_user_without_superuser_access_allowed(self):
        """Пользователь с is_staff=True должен иметь доступ даже без is_superuser"""
        # Создаем пользователя только с is_staff=True
        staff_user = User.objects.create_user(
            username='staff_user',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True,
            is_superuser=False
        )
        
        # Входим как staff пользователь
        self.client.login(username='staff_user', password='staffpass123')
        
        response = self.client.get(self.tech_doc_url)
        
        # Проверяем, что доступ разрешен
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'documentation/technical_documentation.html')
    
    def test_superuser_without_staff_access_forbidden(self):
        """Пользователь с is_superuser=True но без is_staff=True не должен иметь доступ"""
        # Создаем пользователя только с is_superuser=True
        superuser_no_staff = User.objects.create_user(
            username='superuser_no_staff',
            email='superuser@example.com',
            password='superpass123',
            is_staff=False,
            is_superuser=True
        )
        
        # Входим как superuser без staff
        self.client.login(username='superuser_no_staff', password='superpass123')
        
        response = self.client.get(self.tech_doc_url)
        
        # Проверяем, что доступ запрещен (так как проверяется только is_staff)
        self.assertEqual(response.status_code, 403)
    
    def test_documentation_index_shows_admin_section_for_staff(self):
        """Главная страница документации должна показывать раздел для администраторов только staff пользователям"""
        doc_index_url = reverse('webapp:documentation')
        
        # Проверяем для обычного пользователя
        self.client.login(username='regular_user', password='testpass123')
        response = self.client.get(doc_index_url)
        content = response.content.decode('utf-8')
        self.assertNotIn('Для администраторов', content)
        
        # Проверяем для администратора
        self.client.login(username='admin_user', password='adminpass123')
        response = self.client.get(doc_index_url)
        content = response.content.decode('utf-8')
        self.assertIn('Для администраторов', content)
        self.assertIn('Техническая документация', content)
    
    def test_documentation_index_shows_admin_section_for_unauthenticated(self):
        """Главная страница документации не должна показывать раздел для администраторов неаутентифицированным пользователям"""
        doc_index_url = reverse('webapp:documentation')
        
        response = self.client.get(doc_index_url)
        content = response.content.decode('utf-8')
        self.assertNotIn('Для администраторов', content)
    
    def test_response_headers_and_security(self):
        """Проверяем заголовки безопасности в ответе"""
        # Входим как администратор
        self.client.login(username='admin_user', password='adminpass123')
        
        response = self.client.get(self.tech_doc_url)
        
        # Проверяем, что ответ успешный
        self.assertEqual(response.status_code, 200)
        
        # Проверяем Content-Type
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    def tearDown(self):
        """Очистка после тестов"""
        # Django автоматически очищает тестовую базу данных
        pass


class TechnicalDocumentationIntegrationTestCase(TestCase):
    """Интеграционные тесты для технической документации"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin_integration',
            email='admin_integration@example.com',
            password='adminpass123',
            is_staff=True
        )
    
    def test_full_workflow_admin_access(self):
        """Полный workflow доступа администратора к технической документации"""
        # 1. Переходим на главную страницу документации
        doc_index_url = reverse('webapp:documentation')
        response = self.client.get(doc_index_url)
        self.assertEqual(response.status_code, 200)
        
        # 2. Входим как администратор
        login_success = self.client.login(username='admin_integration', password='adminpass123')
        self.assertTrue(login_success)
        
        # 3. Снова переходим на главную страницу документации
        response = self.client.get(doc_index_url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Для администраторов', content)
        
        # 4. Переходим к технической документации
        tech_doc_url = reverse('webapp:technical_documentation')
        response = self.client.get(tech_doc_url)
        self.assertEqual(response.status_code, 200)
        
        # 5. Проверяем, что можем вернуться назад
        content = response.content.decode('utf-8')
        self.assertIn('Назад к документации', content)
        
        # 6. Проверяем ссылки на другие разделы
        self.assertIn('API Документация', content)
        self.assertIn('Архитектура', content)
        self.assertIn('Развертывание', content)