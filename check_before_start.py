#!/usr/bin/env python
"""
Проверка готовности к запуску приложения
"""
import os
import sys
import django

def check_environment():
    """Проверка переменных окружения"""
    print("🔍 Проверка переменных окружения...")
    
    required_vars = ['SECRET_KEY', 'DATABASE_URL']
    optional_vars = ['REDIS_URL', 'TELEGRAM_BOT_TOKEN', 'ALLOWED_HOSTS']
    
    missing_required = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: установлена ({len(value)} символов)")
        else:
            print(f"❌ {var}: НЕ УСТАНОВЛЕНА")
            missing_required.append(var)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: установлена ({len(value)} символов)")
        else:
            print(f"⚠️ {var}: не установлена")
    
    return len(missing_required) == 0

def check_django():
    """Проверка Django"""
    print("\n🔍 Проверка Django...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
        django.setup()
        
        from django.conf import settings
        print(f"✅ Django настроен")
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"   DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка Django: {e}")
        return False

def check_database():
    """Проверка подключения к базе данных"""
    print("\n🔍 Проверка базы данных...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✅ Django база данных подключена")
                return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def check_imports():
    """Проверка импортов"""
    print("\n🔍 Проверка импортов...")
    
    try:
        from botapp.models import User
        from botapp.models_child import Child, Measurement
        from webapp.views import index
        print("✅ Основные модули импортируются")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def main():
    print("🧪 Проверка готовности к запуску...\n")
    
    checks = [
        ("Environment Variables", check_environment),
        ("Django Setup", check_django),
        ("Database Connection", check_database),
        ("Module Imports", check_imports),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Неожиданная ошибка в {check_name}: {e}")
            results.append(False)
    
    print(f"\n📊 Результат: {sum(results)}/{len(results)} проверок прошли")
    
    if all(results):
        print("🎉 Все проверки прошли! Приложение готово к запуску.")
        return 0
    else:
        print("⚠️ Некоторые проверки не прошли. Исправьте проблемы перед запуском.")
        return 1

if __name__ == "__main__":
    sys.exit(main())