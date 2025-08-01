#!/usr/bin/env python
"""
Comprehensive integration test script for Mom&BabyBot Django migration.
This script tests all major functionality to ensure the migration was successful.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import django
        print(f"✅ Django {django.get_version()} imported successfully")
    except ImportError as e:
        print(f"❌ Django import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy {sqlalchemy.__version__} imported successfully")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import aiogram
        print(f"✅ Aiogram {aiogram.__version__} imported successfully")
    except ImportError as e:
        print(f"❌ Aiogram import failed: {e}")
        return False
    
    return True

def test_django_setup():
    """Test Django project setup"""
    print("\n🔧 Testing Django setup...")
    
    try:
        import django
        django.setup()
        print("✅ Django setup completed successfully")
        
        from django.conf import settings
        print(f"✅ Django settings loaded: {settings.SECRET_KEY[:10]}...")
        
        # Test SQLAlchemy integration
        if hasattr(settings, 'SQLALCHEMY_ENGINE'):
            print("✅ SQLAlchemy engine configured in Django settings")
        else:
            print("❌ SQLAlchemy engine not found in Django settings")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def test_database_connection():
    """Test database connectivity"""
    print("\n💾 Testing database connection...")
    
    try:
        from django.conf import settings
        from botapp.models import db_manager, User
        
        # Test SQLAlchemy connection
        session = db_manager.get_session()
        try:
            # Create tables if they don't exist
            db_manager.create_tables()
            print("✅ Database tables created/verified")
            
            # Test basic query
            user_count = session.query(User).count()
            print(f"✅ Database query successful: {user_count} users found")
            
            return True
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_sqlalchemy_models():
    """Test SQLAlchemy models functionality"""
    print("\n📊 Testing SQLAlchemy models...")
    
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
        print(f"✅ User created: {user.username}")
        
        # Test user retrieval
        import asyncio
        retrieved_user = asyncio.run(get_user(test_telegram_id))
        if retrieved_user and retrieved_user.telegram_id == test_telegram_id:
            print("✅ User retrieval successful")
        else:
            print("❌ User retrieval failed")
            return False
        
        # Test user update
        updated_user = update_user(test_telegram_id, pregnancy_week=25)
        if updated_user and updated_user.pregnancy_week == 25:
            print("✅ User update successful")
        else:
            print("❌ User update failed")
            return False
        
        # Test user deletion
        if delete_user(test_telegram_id):
            print("✅ User deletion successful")
        else:
            print("❌ User deletion failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy models test failed: {e}")
        return False

def test_django_views():
    """Test Django views and URL routing"""
    print("\n🌐 Testing Django views...")
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Test main page
        try:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Main page accessible")
            else:
                print(f"❌ Main page returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Main page test failed: {e}")
            return False
        
        # Test API endpoint - create user
        try:
            test_data = {
                'telegram_id': 888888888,
                'username': 'api_test_user',
                'first_name': 'API',
                'last_name': 'Test',
                'is_pregnant': False,
                'baby_birth_date': '2023-01-01T00:00:00'
            }
            
            response = client.post(
                '/api/user',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                print("✅ API user creation endpoint working")
            else:
                print(f"❌ API user creation returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API endpoint test failed: {e}")
            return False
        
        # Test web app data endpoint
        try:
            webapp_data = {
                'user_id': 888888888,
                'baby_birth_date': '2023-06-01T00:00:00'
            }
            
            response = client.post(
                '/webapp/data/',
                data=json.dumps(webapp_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                print("✅ Web app data endpoint working")
            else:
                print(f"❌ Web app data endpoint returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Web app data endpoint test failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Django views test failed: {e}")
        return False

def test_bot_handlers():
    """Test bot handlers import and basic functionality"""
    print("\n🤖 Testing bot handlers...")
    
    try:
        from botapp.handlers import (
            help_command, stats, webapp_command, start_survey,
            handle_pregnancy_answer, web_app_data, BOT_COMMANDS, ADMIN_COMMANDS
        )
        print("✅ Bot handlers imported successfully")
        
        # Test command lists
        if len(BOT_COMMANDS) > 0:
            print(f"✅ Bot commands defined: {len(BOT_COMMANDS)} commands")
        else:
            print("❌ No bot commands defined")
            return False
        
        if len(ADMIN_COMMANDS) > len(BOT_COMMANDS):
            print(f"✅ Admin commands defined: {len(ADMIN_COMMANDS)} commands")
        else:
            print("❌ Admin commands not properly defined")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Bot handlers test failed: {e}")
        return False

def test_templates():
    """Test Django templates"""
    print("\n📄 Testing templates...")
    
    try:
        from django.template.loader import get_template
        
        # Test main template
        template = get_template('index.html')
        if template:
            print("✅ Main template (index.html) found and loadable")
        else:
            print("❌ Main template not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False

def test_static_files():
    """Test static files configuration"""
    print("\n📁 Testing static files...")
    
    try:
        from django.conf import settings
        
        if hasattr(settings, 'STATIC_URL') and settings.STATIC_URL:
            print(f"✅ Static URL configured: {settings.STATIC_URL}")
        else:
            print("❌ Static URL not configured")
            return False
        
        if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
            print(f"✅ Static files directories configured: {len(settings.STATICFILES_DIRS)} directories")
        else:
            print("❌ Static files directories not configured")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Static files test failed: {e}")
        return False

def test_admin_interface():
    """Test Django admin interface"""
    print("\n👤 Testing admin interface...")
    
    try:
        from django.test import Client
        
        client = Client()
        
        # Test admin login page
        response = client.get('/admin/')
        if response.status_code in [200, 302]:  # 302 for redirect to login
            print("✅ Admin interface accessible")
        else:
            print(f"❌ Admin interface returned status {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Admin interface test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variables and configuration"""
    print("\n🔧 Testing environment configuration...")
    
    try:
        from django.conf import settings
        
        # Check critical settings
        if settings.SECRET_KEY:
            print("✅ SECRET_KEY configured")
        else:
            print("❌ SECRET_KEY not configured")
            return False
        
        if hasattr(settings, 'SQLALCHEMY_DATABASE_URL'):
            print(f"✅ Database URL configured: {settings.SQLALCHEMY_DATABASE_URL[:20]}...")
        else:
            print("❌ Database URL not configured")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Environment configuration test failed: {e}")
        return False

def test_data_compatibility():
    """Test data compatibility with existing database"""
    print("\n🔄 Testing data compatibility...")
    
    try:
        # Check if database file exists
        db_files = ['data/mom_baby_bot.db', 'db.sqlite3', 'instance/mom_baby_bot.db']
        db_found = False
        
        for db_file in db_files:
            if os.path.exists(db_file):
                print(f"✅ Database file found: {db_file}")
                db_found = True
                
                # Test database structure
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    # Check if users table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
                    if cursor.fetchone():
                        print("✅ Users table exists in database")
                        
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
                            print(f"⚠️ Missing columns in database: {missing_columns}")
                    else:
                        print("⚠️ Users table not found in database")
                    
                    conn.close()
                    
                except Exception as e:
                    print(f"⚠️ Database structure check failed: {e}")
                
                break
        
        if not db_found:
            print("⚠️ No database file found - will be created on first use")
        
        return True
        
    except Exception as e:
        print(f"❌ Data compatibility test failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting comprehensive integration tests for Mom&BabyBot Django migration\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Django Setup", test_django_setup),
        ("Database Connection", test_database_connection),
        ("SQLAlchemy Models", test_sqlalchemy_models),
        ("Django Views", test_django_views),
        ("Bot Handlers", test_bot_handlers),
        ("Templates", test_templates),
        ("Static Files", test_static_files),
        ("Admin Interface", test_admin_interface),
        ("Environment Config", test_environment_variables),
        ("Data Compatibility", test_data_compatibility),
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
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! The Django migration is successful.")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)