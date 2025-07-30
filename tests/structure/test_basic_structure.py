#!/usr/bin/env python
"""
Basic structure and file verification test for Mom&BabyBot Django migration.
This script verifies the project structure and file contents without requiring Django to be installed.
"""

import os
import json
import sqlite3
from pathlib import Path

def test_project_structure():
    """Test that all required files and directories exist"""
    print("📁 Testing project structure...")
    
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
        'webapp/templates/index.html',
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist")
    return True

def test_requirements():
    """Test requirements.txt content"""
    print("\n📦 Testing requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = ['Django', 'SQLAlchemy', 'aiogram', 'python-dotenv', 'alembic']
        missing_packages = []
        
        for package in required_packages:
            if package not in requirements:
                missing_packages.append(package)
            else:
                print(f"✅ {package} found in requirements")
        
        if missing_packages:
            print(f"❌ Missing packages: {missing_packages}")
            return False
        
        # Check that Flask packages are removed
        flask_packages = ['Flask', 'Flask-SQLAlchemy', 'Flask-CORS', 'Flask-Migrate']
        found_flask = []
        
        for package in flask_packages:
            if package in requirements:
                found_flask.append(package)
        
        if found_flask:
            print(f"❌ Flask packages still present: {found_flask}")
            return False
        
        print("✅ Requirements.txt is properly updated")
        return True
        
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def test_django_settings():
    """Test Django settings configuration"""
    print("\n⚙️ Testing Django settings...")
    
    try:
        with open('mom_baby_bot/settings.py', 'r') as f:
            settings_content = f.read()
        
        required_settings = [
            'SQLALCHEMY_ENGINE',
            'SQLALCHEMY_SESSION_FACTORY',
            'TELEGRAM_BOT_TOKEN',
            'botapp',
            'webapp',
            'SQLAlchemySessionMiddleware'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if setting not in settings_content:
                missing_settings.append(setting)
            else:
                print(f"✅ {setting} configured")
        
        if missing_settings:
            print(f"❌ Missing settings: {missing_settings}")
            return False
        
        print("✅ Django settings properly configured")
        return True
        
    except Exception as e:
        print(f"❌ Error reading Django settings: {e}")
        return False

def test_sqlalchemy_models():
    """Test SQLAlchemy models structure"""
    print("\n📊 Testing SQLAlchemy models...")
    
    try:
        with open('botapp/models.py', 'r') as f:
            models_content = f.read()
        
        required_elements = [
            'class User(Base)',
            'baby_birth_date',  # Updated field name
            'SQLAlchemyManager',
            'get_sqlalchemy_session',
            'create_user',
            'update_user',
            'delete_user'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in models_content:
                missing_elements.append(element)
            else:
                print(f"✅ {element} found")
        
        if missing_elements:
            print(f"❌ Missing model elements: {missing_elements}")
            return False
        
        # Check that baby_age is replaced with baby_birth_date
        if 'baby_age' in models_content and 'baby_birth_date' not in models_content:
            print("❌ baby_age field not updated to baby_birth_date")
            return False
        
        print("✅ SQLAlchemy models properly structured")
        return True
        
    except Exception as e:
        print(f"❌ Error reading models: {e}")
        return False

def test_django_views():
    """Test Django views structure"""
    print("\n🌐 Testing Django views...")
    
    try:
        with open('webapp/views.py', 'r') as f:
            views_content = f.read()
        
        required_views = [
            'def index(request)',
            'def create_user(request)',
            'def web_app_data(request)',
            'from botapp.models import User',
            'JsonResponse',
            'parse_datetime'
        ]
        
        missing_views = []
        for view in required_views:
            if view not in views_content:
                missing_views.append(view)
            else:
                print(f"✅ {view} found")
        
        if missing_views:
            print(f"❌ Missing view elements: {missing_views}")
            return False
        
        print("✅ Django views properly structured")
        return True
        
    except Exception as e:
        print(f"❌ Error reading views: {e}")
        return False

def test_bot_handlers():
    """Test bot handlers structure"""
    print("\n🤖 Testing bot handlers...")
    
    try:
        with open('botapp/handlers/__init__.py', 'r') as f:
            init_content = f.read()
        
        required_imports = [
            'help_command',
            'stats',
            'webapp_command',
            'start_survey',
            'web_app_data',
            'handle_subscribe'
        ]
        
        missing_imports = []
        for import_name in required_imports:
            if import_name not in init_content:
                missing_imports.append(import_name)
            else:
                print(f"✅ {import_name} imported")
        
        if missing_imports:
            print(f"❌ Missing handler imports: {missing_imports}")
            return False
        
        print("✅ Bot handlers properly structured")
        return True
        
    except Exception as e:
        print(f"❌ Error reading bot handlers: {e}")
        return False

def test_database_compatibility():
    """Test database file and structure"""
    print("\n💾 Testing database compatibility...")
    
    db_files = ['mom_baby_bot.db', 'db.sqlite3', 'instance/mom_baby_bot.db']
    db_found = False
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"✅ Database file found: {db_file}")
            db_found = True
            
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Check if users table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
                if cursor.fetchone():
                    print("✅ Users table exists")
                    
                    # Check table structure
                    cursor.execute("PRAGMA table_info(users);")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    required_columns = ['id', 'telegram_id', 'username', 'first_name', 'last_name', 
                                      'is_pregnant', 'pregnancy_week', 'baby_birth_date', 
                                      'is_premium', 'is_admin', 'created_at', 'updated_at']
                    
                    missing_columns = [col for col in required_columns if col not in columns]
                    if not missing_columns:
                        print("✅ Database schema is compatible")
                    else:
                        print(f"⚠️ Missing columns: {missing_columns}")
                        
                    # Check for old baby_age column
                    if 'baby_age' in columns:
                        print("⚠️ Old baby_age column still exists - should be migrated to baby_birth_date")
                else:
                    print("⚠️ Users table not found")
                
                conn.close()
                
            except Exception as e:
                print(f"⚠️ Database check failed: {e}")
            
            break
    
    if not db_found:
        print("⚠️ No database file found - will be created on first use")
    
    return True

def test_url_configuration():
    """Test URL configuration"""
    print("\n🔗 Testing URL configuration...")
    
    try:
        # Test main URLs
        with open('mom_baby_bot/urls.py', 'r') as f:
            main_urls = f.read()
        
        if "include('webapp.urls')" in main_urls:
            print("✅ Webapp URLs included")
        else:
            print("❌ Webapp URLs not included")
            return False
        
        # Test webapp URLs
        with open('webapp/urls.py', 'r') as f:
            webapp_urls = f.read()
        
        required_patterns = [
            "path('', views.index",
            "path('api/user'",
            "path('webapp/data/'"
        ]
        
        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in webapp_urls:
                missing_patterns.append(pattern)
            else:
                print(f"✅ URL pattern found: {pattern}")
        
        if missing_patterns:
            print(f"❌ Missing URL patterns: {missing_patterns}")
            return False
        
        print("✅ URL configuration is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error reading URL configuration: {e}")
        return False

def test_templates():
    """Test template files"""
    print("\n📄 Testing templates...")
    
    template_files = [
        'webapp/templates/index.html',
        'webapp/templates/base.html'
    ]
    
    found_templates = []
    for template in template_files:
        if os.path.exists(template):
            found_templates.append(template)
            print(f"✅ {template} exists")
        else:
            print(f"⚠️ {template} not found")
    
    if not found_templates:
        print("❌ No templates found")
        return False
    
    # Check main template content
    try:
        with open('webapp/templates/index.html', 'r') as f:
            template_content = f.read()
        
        if '{% load static %}' in template_content or 'Django' in template_content:
            print("✅ Template uses Django syntax")
        else:
            print("⚠️ Template may not be fully converted to Django syntax")
        
    except Exception as e:
        print(f"⚠️ Error reading template: {e}")
    
    return True

def run_basic_tests():
    """Run all basic structure tests"""
    print("🚀 Starting basic structure verification for Mom&BabyBot Django migration\n")
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Requirements", test_requirements),
        ("Django Settings", test_django_settings),
        ("SQLAlchemy Models", test_sqlalchemy_models),
        ("Django Views", test_django_views),
        ("Bot Handlers", test_bot_handlers),
        ("Database Compatibility", test_database_compatibility),
        ("URL Configuration", test_url_configuration),
        ("Templates", test_templates),
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
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Basic Structure Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    return failed == 0

if __name__ == "__main__":
    success = run_basic_tests()
    
    if success:
        print("\n🎉 Basic structure verification passed!")
        print("\n📋 Manual Verification Checklist:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run Django migrations: python manage.py migrate")
        print("3. Create superuser: python manage.py createsuperuser")
        print("4. Test Django server: python manage.py runserver")
        print("5. Test bot: python manage.py runbot")
        print("6. Test web interface at http://localhost:8000")
        print("7. Test API endpoints with curl or Postman")
        print("8. Test admin interface at http://localhost:8000/admin")
    else:
        print("\n⚠️ Some basic structure issues found. Please fix them before proceeding.")