#!/usr/bin/env python
"""
Инициализация SQLite базы данных
"""
import os
import sys
import django
import sqlite3

def create_sqlite_db():
    """Создание SQLite базы данных"""
    print("🗄️ Создание SQLite базы данных...")
    
    db_path = '/app/data/mom_baby_bot.db'
    db_dir = os.path.dirname(db_path)
    
    try:
        # Создаем директорию
        os.makedirs(db_dir, exist_ok=True)
        print(f"✅ Директория создана: {db_dir}")
        
        # Создаем базу данных
        conn = sqlite3.connect(db_path)
        conn.close()
        print(f"✅ SQLite база данных создана: {db_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания SQLite базы: {e}")
        return False

def apply_django_migrations():
    """Применение Django миграций"""
    print("\n📊 Применение Django миграций...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
        django.setup()
        
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        
        print("✅ Django миграции применены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка применения миграций: {e}")
        return False

def create_sqlalchemy_tables():
    """Создание таблиц SQLAlchemy"""
    print("\n🏗️ Создание таблиц SQLAlchemy...")
    
    try:
        from botapp.models import Base
        from django.conf import settings
        
        if hasattr(settings, 'get_sqlalchemy_engine'):
            engine = settings.get_sqlalchemy_engine()
        else:
            from sqlalchemy import create_engine
            engine = create_engine('sqlite:////app/data/mom_baby_bot.db')
        
        Base.metadata.create_all(engine)
        print("✅ SQLAlchemy таблицы созданы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания SQLAlchemy таблиц: {e}")
        return False

def main():
    print("🚀 Инициализация SQLite базы данных\n")
    
    steps = [
        ("Create SQLite DB", create_sqlite_db),
        ("Apply Django Migrations", apply_django_migrations),
        ("Create SQLAlchemy Tables", create_sqlalchemy_tables),
    ]
    
    for step_name, step_func in steps:
        print(f"\n--- {step_name} ---")
        if not step_func():
            print(f"❌ Шаг '{step_name}' не выполнен")
            return 1
    
    print("\n🎉 Инициализация SQLite завершена успешно!")
    return 0

if __name__ == "__main__":
    sys.exit(main())