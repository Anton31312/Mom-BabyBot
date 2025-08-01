#!/usr/bin/env python
"""
Скрипт для инициализации production окружения на Amvera
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
    django.setup()
    
    try:
        # Применяем миграции Django
        print("Применяем миграции Django...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        
        # Собираем статические файлы
        print("Собираем статические файлы...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--clear'])
        
        # Инициализируем базу данных SQLAlchemy если нужно
        try:
            from init_db import main as init_db_main
            print("Инициализируем базу данных SQLAlchemy...")
            init_db_main()
        except Exception as e:
            print(f"Предупреждение: не удалось инициализировать SQLAlchemy БД: {e}")
        
        print("Инициализация завершена успешно!")
        
    except Exception as e:
        print(f"Ошибка при инициализации: {e}")
        sys.exit(1)