#!/usr/bin/env python
"""
Финальный тест всей системы
"""
import os
import sys
import django
import subprocess

def test_django_startup():
    """Тест запуска Django без ошибок SQLAlchemy"""
    print("🧪 Тест запуска Django...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
        django.setup()
        
        from django.conf import settings
        print(f"✅ Django запущен: DEBUG={settings.DEBUG}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка запуска Django: {e}")
        return False

def test_django_migrations():
    """Тест Django миграций"""
    print("\n🧪 Тест Django миграций...")
    
    try:
        result = subprocess.run([
            'python', 'manage.py', 'migrate', '--noinput'
        ], capture_output=True, text=True, env={
            **os.environ,
            'DJANGO_SETTINGS_MODULE': 'mom_baby_bot.settings_prod'
        })
        
        if result.returncode == 0:
            print("✅ Django миграции работают")
            return True
        else:
            print(f"❌ Ошибка миграций: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования миграций: {e}")
        return False

def test_sqlalchemy_init():
    """Тест инициализации SQLAlchemy"""
    print("\n🧪 Тест инициализации SQLAlchemy...")
    
    try:
        result = subprocess.run([
            'python', 'manage.py', 'init_sqlalchemy'
        ], capture_output=True, text=True, env={
            **os.environ,
            'DJANGO_SETTINGS_MODULE': 'mom_baby_bot.settings_prod'
        })
        
        if result.returncode == 0:
            print("✅ SQLAlchemy инициализация работает")
            return True
        else:
            print(f"❌ Ошибка инициализации SQLAlchemy: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования SQLAlchemy: {e}")
        return False

def test_health_endpoint():
    """Тест health endpoint"""
    print("\n🧪 Тест health endpoint...")
    
    try:
        from mom_baby_bot.urls import health_check
        from django.http import HttpRequest
        
        request = HttpRequest()
        response = health_check(request)
        
        if response.status_code == 200:
            print("✅ Health endpoint работает")
            return True
        else:
            print(f"❌ Health endpoint вернул статус: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка health endpoint: {e}")
        return False

def test_sqlite_database():
    """Тест SQLite базы данных"""
    print("\n🧪 Тест SQLite базы данных...")
    
    try:
        import sqlite3
        db_path = '/app/data/mom_baby_bot.db'
        
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Тестируем подключение
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        conn.close()
        
        print(f"✅ SQLite база данных работает, таблиц: {len(tables)}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка SQLite базы данных: {e}")
        return False

def main():
    print("🔍 Финальное тестирование всей системы\n")
    
    tests = [
        ("SQLite Database", test_sqlite_database),
        ("Django Startup", test_django_startup),
        ("Django Migrations", test_django_migrations),
        ("SQLAlchemy Init", test_sqlalchemy_init),
        ("Health Endpoint", test_health_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"--- {test_name} ---")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Неожиданная ошибка в {test_name}: {e}")
            results.append(False)
    
    print(f"\n📊 Итоговый результат: {sum(results)}/{len(results)} тестов прошли")
    
    if all(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Система готова к развертыванию на Amvera!")
        print("\n📋 Что нужно для развертывания:")
        print("1. Установить переменную SECRET_KEY в панели Amvera")
        print("2. Установить ALLOWED_HOSTS с вашим доменом")
        print("3. Опционально: TELEGRAM_BOT_TOKEN и другие переменные для бота")
        print("4. Развернуть проект - SQLite база создастся автоматически")
        return 0
    else:
        print("⚠️ Некоторые тесты не прошли. Исправьте проблемы перед развертыванием.")
        return 1

if __name__ == "__main__":
    sys.exit(main())