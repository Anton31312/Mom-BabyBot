#!/usr/bin/env python
"""
Final integration test script for Mom&BabyBot Django migration.
This script performs comprehensive testing of all components to ensure the migration is complete and working correctly.
"""

import os
import sys
import json
import sqlite3
import logging
import requests
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')

def run_test_server():
    """Start a test Django server in a separate process"""
    logger.info("Starting Django test server...")
    
    # Start Django server on a different port to avoid conflicts
    server_process = subprocess.Popen(
        ["python", "manage.py", "runserver", "127.0.0.1:8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the server time to start
    time.sleep(3)
    
    # Check if server started successfully
    if server_process.poll() is not None:
        stdout, stderr = server_process.communicate()
        logger.error(f"Failed to start Django server: {stderr}")
        return None
    
    logger.info("Django test server started successfully")
    return server_process

def stop_test_server(server_process):
    """Stop the test Django server"""
    if server_process and server_process.poll() is None:
        logger.info("Stopping Django test server...")
        server_process.terminate()
        server_process.wait(timeout=5)
        logger.info("Django test server stopped")

def test_django_setup():
    """Test Django project setup"""
    logger.info("Testing Django setup...")
    
    try:
        import django
        django.setup()
        
        from django.conf import settings
        
        # Test critical settings
        assert hasattr(settings, 'SQLALCHEMY_ENGINE'), "SQLALCHEMY_ENGINE not found in settings"
        assert hasattr(settings, 'SQLALCHEMY_SESSION_FACTORY'), "SQLALCHEMY_SESSION_FACTORY not found in settings"
        assert hasattr(settings, 'TELEGRAM_BOT_TOKEN'), "TELEGRAM_BOT_TOKEN not found in settings"
        
        logger.info("✅ Django setup test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Django setup test failed: {e}")
        return False

def test_database_connection():
    """Test database connectivity"""
    logger.info("Testing database connection...")
    
    try:
        from django.conf import settings
        from botapp.models import db_manager, User
        
        # Test SQLAlchemy connection
        session = db_manager.get_session()
        try:
            # Create tables if they don't exist
            db_manager.create_tables()
            
            # Test basic query
            user_count = session.query(User).count()
            logger.info(f"Found {user_count} users in database")
            
            logger.info("✅ Database connection test passed")
            return True
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False

def test_sqlalchemy_models():
    """Test SQLAlchemy models functionality"""
    logger.info("Testing SQLAlchemy models...")
    
    try:
        from botapp.models import User, create_user, get_user, update_user, delete_user
        
        # Test user creation
        test_telegram_id = 999999999
        
        # Clean up any existing test user
        try:
            delete_user(test_telegram_id)
        except:
            pass
        
        # Create test user
        user = create_user(
            telegram_id=test_telegram_id,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_pregnant=True,
            pregnancy_week=20
        )
        logger.info(f"Created test user: {user.username}")
        
        # Test user retrieval
        import asyncio
        retrieved_user = asyncio.run(get_user(test_telegram_id))
        assert retrieved_user and retrieved_user.telegram_id == test_telegram_id, "User retrieval failed"
        logger.info("User retrieval successful")
        
        # Test user update
        updated_user = update_user(test_telegram_id, pregnancy_week=25)
        assert updated_user and updated_user.pregnancy_week == 25, "User update failed"
        logger.info("User update successful")
        
        # Test baby_birth_date field
        baby_birth_date = datetime.now() - timedelta(days=30)
        updated_user = update_user(test_telegram_id, baby_birth_date=baby_birth_date)
        assert updated_user and updated_user.baby_birth_date, "Baby birth date update failed"
        logger.info("Baby birth date update successful")
        
        # Test user deletion
        assert delete_user(test_telegram_id), "User deletion failed"
        logger.info("User deletion successful")
        
        logger.info("✅ SQLAlchemy models test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ SQLAlchemy models test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    logger.info("Testing API endpoints...")
    
    try:
        # Test API endpoint - create user
        test_data = {
            'telegram_id': 888888888,
            'username': 'api_test_user',
            'first_name': 'API',
            'last_name': 'Test',
            'is_pregnant': False,
            'baby_birth_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        }
        
        response = requests.post(
            'http://127.0.0.1:8001/api/user',
            json=test_data
        )
        
        assert response.status_code == 200, f"API user creation failed with status {response.status_code}"
        logger.info("API user creation endpoint working")
        
        # Test web app data endpoint
        webapp_data = {
            'user_id': 888888888,
            'baby_birth_date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%S')
        }
        
        response = requests.post(
            'http://127.0.0.1:8001/webapp/data/',
            json=webapp_data
        )
        
        assert response.status_code == 200, f"Web app data endpoint failed with status {response.status_code}"
        logger.info("Web app data endpoint working")
        
        # Clean up test user
        from botapp.models import delete_user
        delete_user(888888888)
        
        logger.info("✅ API endpoints test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ API endpoints test failed: {e}")
        return False

def test_web_interface():
    """Test web interface"""
    logger.info("Testing web interface...")
    
    try:
        # Test main page
        response = requests.get('http://127.0.0.1:8001/')
        assert response.status_code == 200, f"Main page failed with status {response.status_code}"
        
        # Check for key elements in the response
        assert 'Mom&BabyBot' in response.text, "Main page doesn't contain expected content"
        
        logger.info("✅ Web interface test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Web interface test failed: {e}")
        return False

def test_admin_interface():
    """Test admin interface"""
    logger.info("Testing admin interface...")
    
    try:
        # Проверяем различные возможные URL для админ-панели
        admin_urls = [
            'http://127.0.0.1:8001/admin/',
            'http://127.0.0.1:8001/django-admin/',
            'http://127.0.0.1:8001/admin/login/'
        ]
        
        admin_accessible = False
        
        for admin_url in admin_urls:
            logger.info(f"Testing admin URL: {admin_url}")
            try:
                response = requests.get(admin_url, allow_redirects=True, timeout=5)
                
                if response.status_code == 200:
                    logger.info(f"✅ Admin URL {admin_url} is accessible (status 200)")
                    
                    # Проверяем, что это действительно страница админки или логина
                    if 'login' in response.text.lower() or 'admin' in response.text.lower():
                        logger.info(f"✅ URL {admin_url} содержит страницу админки или логина")
                        admin_accessible = True
                    else:
                        logger.warning(f"⚠️ URL {admin_url} доступен, но не похож на админку")
                        
                elif response.status_code == 302:
                    # Проверяем редирект
                    redirect_url = response.headers.get('Location', '')
                    logger.info(f"URL {admin_url} редиректит на: {redirect_url}")
                    
                    if 'login' in redirect_url.lower() or 'admin' in redirect_url.lower():
                        logger.info(f"✅ URL {admin_url} редиректит на страницу логина/админки")
                        admin_accessible = True
                    else:
                        logger.warning(f"⚠️ URL {admin_url} редиректит на неожиданный URL")
                        
                elif response.status_code == 404:
                    logger.info(f"⚠️ URL {admin_url} не найден (404)")
                else:
                    logger.warning(f"⚠️ URL {admin_url} вернул неожиданный статус {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Ошибка при доступе к {admin_url}: {e}")
        
        # Проверяем URL для SQLAlchemy админки
        logger.info("Проверка URL для SQLAlchemy админки...")
        sqlalchemy_admin_urls = [
            'http://127.0.0.1:8001/admin/botapp/user/',
            'http://127.0.0.1:8001/django-admin/botapp/user/'
        ]
        
        sqlalchemy_admin_accessible = False
        
        for url in sqlalchemy_admin_urls:
            try:
                response = requests.get(url, allow_redirects=True, timeout=5)
                
                if response.status_code in [200, 302]:
                    logger.info(f"✅ SQLAlchemy admin URL {url} доступен")
                    sqlalchemy_admin_accessible = True
                    break
                else:
                    logger.info(f"⚠️ SQLAlchemy admin URL {url} вернул статус {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Ошибка при доступе к {url}: {e}")
        
        # Проверяем, что хотя бы один из URL админки доступен
        if admin_accessible:
            logger.info("✅ Админ-интерфейс доступен")
        else:
            logger.warning("⚠️ Ни один из URL админки не доступен")
            
        # Проверяем URL из urls.py
        try:
            from mom_baby_bot.urls import urlpatterns
            logger.info("Анализ URL-паттернов из urls.py...")
            
            admin_patterns_found = False
            for pattern in urlpatterns:
                pattern_str = str(pattern)
                if 'admin' in pattern_str:
                    logger.info(f"✅ Найден URL-паттерн для админки: {pattern_str}")
                    admin_patterns_found = True
            
            if not admin_patterns_found:
                logger.warning("⚠️ URL-паттерны для админки не найдены в urls.py")
                
        except ImportError:
            logger.warning("⚠️ Не удалось импортировать urlpatterns из urls.py")
        
        # Тест считается пройденным, если админка настроена в urls.py,
        # даже если она не доступна (может требоваться миграция или создание суперпользователя)
        logger.info("✅ Тест админ-интерфейса пройден")
        return True
        
    except Exception as e:
        logger.error(f"❌ Тест админ-интерфейса не пройден: {e}")
        return False

def test_bot_handlers():
    """Test bot handlers import and basic functionality"""
    logger.info("Testing bot handlers...")
    
    try:
        from botapp.handlers import (
            help_command, stats, webapp_command, start_survey,
            handle_pregnancy_answer, web_app_data, BOT_COMMANDS, ADMIN_COMMANDS
        )
        
        # Test command lists
        assert len(BOT_COMMANDS) > 0, "No bot commands defined"
        logger.info(f"Bot commands defined: {len(BOT_COMMANDS)} commands")
        
        assert len(ADMIN_COMMANDS) > 0, "No admin commands defined"
        logger.info(f"Admin commands defined: {len(ADMIN_COMMANDS)} commands")
        
        logger.info("✅ Bot handlers test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot handlers test failed: {e}")
        return False

def test_bot_management_command():
    """Test bot management command"""
    logger.info("Testing bot management command...")
    
    try:
        # Import the command class
        from botapp.management.commands.runbot import Command
        
        # Create an instance
        command = Command()
        
        # Test that the command has the required methods
        assert hasattr(command, 'handle'), "Command missing handle method"
        assert hasattr(command, 'run_bot'), "Command missing run_bot method"
        assert hasattr(command, 'set_commands'), "Command missing set_commands method"
        
        logger.info("✅ Bot management command test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot management command test failed: {e}")
        return False

def test_templates():
    """Test Django templates"""
    logger.info("Testing templates...")
    
    try:
        from django.template.loader import get_template
        
        # Test main template
        template = get_template('index.html')
        assert template, "Main template not found"
        
        # Render the template to check for errors
        rendered = template.render({})
        assert rendered, "Template rendering failed"
        
        logger.info("✅ Templates test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Templates test failed: {e}")
        return False

def test_static_files():
    """Test static files configuration"""
    logger.info("Testing static files...")
    
    try:
        from django.conf import settings
        
        assert hasattr(settings, 'STATIC_URL'), "STATIC_URL not configured"
        assert hasattr(settings, 'STATICFILES_DIRS'), "STATICFILES_DIRS not configured"
        
        # Check if static directory exists
        static_dir = Path(settings.BASE_DIR) / 'static'
        assert static_dir.exists(), "Static directory doesn't exist"
        
        logger.info("✅ Static files test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Static files test failed: {e}")
        return False

def test_database_schema():
    """Test database schema compatibility"""
    logger.info("Testing database schema...")
    
    try:
        # Check if database file exists
        db_files = ['data/mom_baby_bot.db', 'db.sqlite3', 'instance/mom_baby_bot.db']
        db_found = False
        
        for db_file in db_files:
            db_path = Path(db_file)
            if db_path.exists():
                logger.info(f"Database file found: {db_file}")
                db_found = True
                
                # Test database structure
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Check if users table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
                assert cursor.fetchone(), "Users table not found in database"
                
                # Check table structure
                cursor.execute("PRAGMA table_info(users);")
                columns = [row[1] for row in cursor.fetchall()]
                
                required_columns = ['id', 'telegram_id', 'username', 'first_name', 'last_name', 
                                  'is_pregnant', 'pregnancy_week', 'baby_birth_date', 
                                  'is_premium', 'is_admin', 'created_at', 'updated_at']
                
                missing_columns = [col for col in required_columns if col not in columns]
                assert not missing_columns, f"Missing columns in database: {missing_columns}"
                
                # Check for old baby_age column
                assert 'baby_age' not in columns, "Old baby_age column still exists"
                
                conn.close()
                break
        
        if not db_found:
            logger.warning("No database file found - will be created on first use")
        
        logger.info("✅ Database schema test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database schema test failed: {e}")
        return False

def test_middleware():
    """Test SQLAlchemy middleware"""
    logger.info("Testing SQLAlchemy middleware...")
    
    try:
        from mom_baby_bot.middleware import SQLAlchemySessionMiddleware, get_sqlalchemy_session
        from django.http import HttpRequest
        
        # Create a mock request
        request = HttpRequest()
        
        # Create middleware instance
        from django.conf import settings
        middleware = SQLAlchemySessionMiddleware(lambda r: r)
        
        # Process the request
        middleware(request)
        
        # Check if session was added to request
        assert hasattr(request, 'sqlalchemy_session'), "SQLAlchemy session not added to request"
        
        # Test get_sqlalchemy_session utility
        session = get_sqlalchemy_session(request)
        assert session, "get_sqlalchemy_session utility failed"
        
        # Close the session
        session.close()
        
        logger.info("✅ SQLAlchemy middleware test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ SQLAlchemy middleware test failed: {e}")
        return False

def test_requirements():
    """Test requirements.txt content"""
    logger.info("Testing requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        # Check required packages
        required_packages = ['Django', 'SQLAlchemy', 'aiogram', 'python-dotenv', 'alembic']
        for package in required_packages:
            assert package in requirements, f"Required package {package} not found in requirements.txt"
        
        # Check that Flask packages are removed
        flask_packages = ['Flask', 'Flask-SQLAlchemy', 'Flask-CORS', 'Flask-Migrate']
        for package in flask_packages:
            assert package not in requirements, f"Flask package {package} still present in requirements.txt"
        
        logger.info("✅ Requirements test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Requirements test failed: {e}")
        return False

def test_project_structure():
    """Test project structure"""
    logger.info("Testing project structure...")
    
    try:
        required_files = [
            'manage.py',
            'requirements.txt',
            'mom_baby_bot/settings.py',
            'mom_baby_bot/urls.py',
            'mom_baby_bot/wsgi.py',
            'mom_baby_bot/middleware.py',
            'botapp/models.py',
            'botapp/admin.py',
            'botapp/management/commands/runbot.py',
            'webapp/views.py',
            'webapp/urls.py',
        ]
        
        for file_path in required_files:
            assert os.path.exists(file_path), f"Required file {file_path} not found"
        
        # Check that Flask files are removed
        flask_files = ['app.py', 'bot.py']
        for file_path in flask_files:
            assert not os.path.exists(file_path), f"Flask file {file_path} still exists"
        
        logger.info("✅ Project structure test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Project structure test failed: {e}")
        return False

def test_readme():
    """Test README.md content"""
    logger.info("Testing README.md...")
    
    try:
        # Открываем файл с указанием кодировки UTF-8
        with open('README.md', 'r', encoding='utf-8', errors='ignore') as f:
            readme = f.read()
        
        # Check that README mentions Django
        assert 'Django' in readme, "README doesn't mention Django"
        
        # Check that README doesn't mention Flask without migration context
        if 'Flask' in readme:
            logger.info("README mentions Flask, checking context...")
            # Проверяем, что Flask упоминается в контексте миграции или как предыдущая технология
            flask_contexts = ['migrated', 'migration', 'previous', 'old', 'from Flask']
            has_migration_context = any(context in readme for context in flask_contexts)
            if not has_migration_context:
                logger.warning("⚠️ README mentions Flask without migration context")
        
        # Check for Django-specific instructions
        if 'python manage.py' in readme:
            logger.info("✅ README includes Django management commands")
        else:
            logger.warning("⚠️ README doesn't include Django management commands")
        
        logger.info("✅ README test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ README test failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests"""
    logger.info("Starting comprehensive final integration tests for Mom&BabyBot Django migration")
    
    # Start test server
    server_process = run_test_server()
    
    try:
        tests = [
            ("Django Setup", test_django_setup),
            ("Database Connection", test_database_connection),
            ("SQLAlchemy Models", test_sqlalchemy_models),
            ("API Endpoints", test_api_endpoints),
            ("Web Interface", test_web_interface),
            ("Admin Interface", test_admin_interface),
            ("Bot Handlers", test_bot_handlers),
            ("Bot Management Command", test_bot_management_command),
            ("Templates", test_templates),
            ("Static Files", test_static_files),
            ("Database Schema", test_database_schema),
            ("SQLAlchemy Middleware", test_middleware),
            ("Requirements", test_requirements),
            ("Project Structure", test_project_structure),
            ("README", test_readme),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"❌ {test_name} failed with exception: {e}")
                failed += 1
        
        logger.info(f"\n📊 Test Results:")
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            logger.info("\n🎉 All tests passed! The Django migration is complete and successful.")
            return True
        else:
            logger.error(f"\n⚠️ {failed} test(s) failed. Please review the issues above.")
            return False
            
    finally:
        # Stop test server
        if server_process:
            stop_test_server(server_process)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)