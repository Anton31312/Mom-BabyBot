#!/usr/bin/env python
"""
Скрипт для проверки подключения к базе данных
"""
import os
import sys
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
django.setup()

def check_django_db():
    """Проверка подключения к Django базе данных"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✅ Django PostgreSQL подключение работает")
                return True
    except Exception as e:
        print(f"❌ Django PostgreSQL подключение не работает: {e}")
        return False

def check_sqlalchemy_db():
    """Проверка подключения к SQLAlchemy базе данных"""
    try:
        from sqlalchemy import text
        from mom_baby_bot.settings import SQLALCHEMY_ENGINE
        
        with SQLALCHEMY_ENGINE.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if result.fetchone():
                print("✅ SQLAlchemy PostgreSQL подключение работает")
                return True
    except Exception as e:
        print(f"❌ SQLAlchemy PostgreSQL подключение не работает: {e}")
        return False

def check_redis():
    """Проверка подключения к Redis"""
    try:
        from django.core.cache import cache
        cache.set('test_key', 'test_value', 30)
        value = cache.get('test_key')
        if value == 'test_value':
            print("✅ Redis подключение работает")
            return True
    except Exception as e:
        print(f"❌ Redis подключение не работает: {e}")
        return False

def main():
    print("🔍 Проверка подключений к базам данных...\n")
    
    # Показываем переменные окружения
    print("📋 Переменные окружения:")
    database_url = os.getenv('DATABASE_URL', 'НЕ УСТАНОВЛЕНА')
    redis_url = os.getenv('REDIS_URL', 'НЕ УСТАНОВЛЕНА')
    print(f"DATABASE_URL: {database_url[:50]}{'...' if len(database_url) > 50 else ''}")
    print(f"REDIS_URL: {redis_url[:50]}{'...' if len(redis_url) > 50 else ''}")
    print()
    
    # Проверяем подключения
    django_ok = check_django_db()
    sqlalchemy_ok = check_sqlalchemy_db()
    redis_ok = check_redis()
    
    print()
    if django_ok and sqlalchemy_ok and redis_ok:
        print("🎉 Все подключения работают корректно!")
        return 0
    else:
        print("⚠️ Обнаружены проблемы с подключениями")
        return 1

if __name__ == "__main__":
    sys.exit(main())