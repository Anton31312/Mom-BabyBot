#!/usr/bin/env python
"""
Тест для проверки production настроек
"""
import os
import sys
import django

def test_django_setup():
    """Тест настройки Django"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
        django.setup()
        print("✅ Django настроен корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка настройки Django: {e}")
        return False

def test_database_connection():
    """Тест подключения к базе данных"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✅ Django база данных подключена")
                return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Django БД: {e}")
        return False

def test_sqlalchemy_setup():
    """Тест настройки SQLAlchemy"""
    try:
        from django.conf import settings
        database_url = os.getenv('DATABASE_URL', '')
        
        if not database_url:
            print("⚠️ DATABASE_URL не установлена")
            return False
            
        if database_url.startswith('sqlite'):
            print("⚠️ Используется SQLite вместо PostgreSQL")
            return False
            
        print(f"✅ DATABASE_URL настроена: {database_url[:30]}...")
        
        # Проверяем SQLAlchemy engine
        engine = settings.SQLALCHEMY_ENGINE
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ SQLAlchemy подключение работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка SQLAlchemy: {e}")
        return False

def test_redis_connection():
    """Тест подключения к Redis"""
    try:
        from django.core.cache import cache
        cache.set('test_key', 'test_value', 30)
        value = cache.get('test_key')
        if value == 'test_value':
            print("✅ Redis подключение работает")
            return True
        else:
            print("❌ Redis не возвращает правильные данные")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Redis: {e}")
        return False

def test_environment_variables():
    """Тест переменных окружения"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'TELEGRAM_BOT_TOKEN'
    ]
    
    all_good = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: установлена")
        else:
            print(f"❌ {var}: НЕ УСТАНОВЛЕНА")
            all_good = False
    
    return all_good

def main():
    print("🧪 Тестирование production настроек...\n")
    
    tests = [
        ("Django Setup", test_django_setup),
        ("Environment Variables", test_environment_variables),
        ("Database Connection", test_database_connection),
        ("SQLAlchemy Setup", test_sqlalchemy_setup),
        ("Redis Connection", test_redis_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Неожиданная ошибка в {test_name}: {e}")
            results.append(False)
    
    print(f"\n📊 Результаты: {sum(results)}/{len(results)} тестов прошли")
    
    if all(results):
        print("🎉 Все тесты прошли успешно!")
        return 0
    else:
        print("⚠️ Некоторые тесты не прошли")
        return 1

if __name__ == "__main__":
    sys.exit(main())