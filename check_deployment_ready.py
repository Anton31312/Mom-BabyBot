#!/usr/bin/env python
"""
Скрипт для проверки готовности проекта к развертыванию на Amvera
"""
import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Проверяет существование файла"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - НЕ НАЙДЕН")
        return False

def check_env_var(var_name, description, required=True):
    """Проверяет переменную окружения"""
    value = os.getenv(var_name)
    if value:
        print(f"✅ {description}: {var_name} = {value[:20]}{'...' if len(value) > 20 else ''}")
        return True
    elif required:
        print(f"❌ {description}: {var_name} - НЕ УСТАНОВЛЕНА")
        return False
    else:
        print(f"⚠️  {description}: {var_name} - не установлена (опционально)")
        return True

def main():
    print("🔍 Проверка готовности к развертыванию на Amvera...\n")
    
    all_good = True
    
    # Проверка файлов
    print("📁 Проверка файлов конфигурации:")
    files_to_check = [
        ("Dockerfile", "Docker конфигурация"),
        ("amvera.yml", "Конфигурация Amvera"),
        (".dockerignore", "Docker ignore файл"),
        ("requirements.txt", "Python зависимости"),
        ("manage.py", "Django manage скрипт"),
        ("mom_baby_bot/settings_prod.py", "Production настройки"),
        ("mom_baby_bot/wsgi.py", "WSGI конфигурация"),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_good = False
    
    print("\n🔧 Проверка переменных окружения:")
    
    # Обязательные переменные
    required_vars = [
        ("SECRET_KEY", "Django секретный ключ"),
        ("TELEGRAM_BOT_TOKEN", "Токен Telegram бота"),
        ("ADMIN_IDS", "ID администраторов"),
    ]
    
    for var_name, description in required_vars:
        if not check_env_var(var_name, description, required=True):
            all_good = False
    
    # Опциональные переменные
    optional_vars = [
        ("DEBUG", "Режим отладки"),
        ("ALLOWED_HOSTS", "Разрешенные хосты"),
        ("DATABASE_URL", "URL базы данных"),
        ("REDIS_URL", "URL Redis"),
        ("WEBHOOK_URL", "URL webhook"),
        ("WEBAPP_URL", "URL веб-приложения"),
    ]
    
    for var_name, description in optional_vars:
        check_env_var(var_name, description, required=False)
    
    print("\n📋 Рекомендации для Amvera:")
    print("1. Убедитесь, что код находится в Git репозитории")
    print("2. Установите все обязательные переменные окружения в панели Amvera")
    print("3. Amvera автоматически предоставит DATABASE_URL и REDIS_URL")
    print("4. Настройте ALLOWED_HOSTS с вашим доменом Amvera")
    print("5. Установите WEBHOOK_URL и WEBAPP_URL с вашим доменом")
    
    if all_good:
        print("\n🎉 Проект готов к развертыванию на Amvera!")
        return 0
    else:
        print("\n⚠️  Обнаружены проблемы. Исправьте их перед развертыванием.")
        return 1

if __name__ == "__main__":
    sys.exit(main())