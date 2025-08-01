#!/usr/bin/env python
"""
Тестовый скрипт для проверки интеграции SQLAlchemy с Django.

Этот скрипт тестирует базовую функциональность интеграции SQLAlchemy
для обеспечения правильной работы всех компонентов.
"""

import os
import sys
import django
from pathlib import Path

# Добавление директории проекта в Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')
django.setup()

from django.conf import settings
from mom_baby_bot.sqlalchemy_utils import get_sqlalchemy_session, check_database_connection
from botapp.models import User

def test_database_connection():
    """Тестирование подключения к базе данных."""
    print("Testing database connection...")
    result = check_database_connection()
    print(f"Database connection: {'✅ PASSED' if result else '❌ FAILED'}")
    return result

def test_sqlalchemy_session():
    """Тестирование создания сессии SQLAlchemy и базовых операций."""
    print("Testing SQLAlchemy session...")
    try:
        with get_sqlalchemy_session() as session:
            # Тестирование базового запроса
            user_count = session.query(User).count()
            print(f"Current user count: {user_count}")
            
            # Тестирование создания пользователя (без коммита, чтобы избежать тестовых данных)
            test_user = User(
                telegram_id=999999999,
                username="test_user",
                first_name="Test",
                last_name="User"
            )
            session.add(test_user)
            session.flush()  # Flush, но не коммитим
            
            # Проверка добавления пользователя в сессию
            found_user = session.query(User).filter_by(telegram_id=999999999).first()
            if found_user:
                print("✅ User creation and query test PASSED")
                # Откат для избежания сохранения тестовых данных
                session.rollback()
                return True
            else:
                print("❌ User creation test FAILED")
                return False
                
    except Exception as e:
        print(f"❌ SQLAlchemy session test FAILED: {e}")
        return False

def test_sqlalchemy_engine():
    """Тестирование конфигурации движка SQLAlchemy."""
    print("Testing SQLAlchemy engine configuration...")
    try:
        engine = settings.SQLALCHEMY_ENGINE
        print(f"Database URL: {engine.url}")
        print(f"Pool size: {engine.pool.size()}")
        print("✅ SQLAlchemy engine configuration PASSED")
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy engine test FAILED: {e}")
        return False

def main():
    """Запуск всех тестов."""
    print("=" * 50)
    print("SQLAlchemy Integration Test")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_sqlalchemy_engine,
        test_sqlalchemy_session,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} FAILED with exception: {e}")
            results.append(False)
        print("-" * 30)
    
    # Сводка
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! SQLAlchemy integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests FAILED. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())