#!/usr/bin/env python
"""
Тест исправления SQLite
"""
import os
import sys
import django

def test_directory_creation():
    """Тест создания директории"""
    print("🧪 Тест создания директории...")
    
    db_path = '/app/data/mom_baby_bot.db'
    db_dir = os.path.dirname(db_path)
    
    try:
        # Удаляем директорию если существует
        if os.path.exists(db_dir):
            import shutil
            shutil.rmtree(db_dir)
        
        # Создаем директорию
        os.makedirs(db_dir, exist_ok=True)
        
        if os.path.exists(db_dir):
            print(f"✅ Директория создана: {db_dir}")
            return True
        else:
            print(f"❌ Директория не создана: {db_dir}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка создания директории: {e}")
        return False

def test_sqlite_file_creation():
    """Тест создания файла SQLite"""
    print("\n🧪 Тест создания файла SQLite...")
    
    db_path = '/app/data/mom_baby_bot.db'
    
    try:
        # Удаляем файл если существует
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Создаем файл SQLite
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
        conn.commit()
        conn.close()
        
        if os.path.exists(db_path):
            print(f"✅ Файл SQLite создан: {db_path}")
            return True
        else:
            print(f"❌ Файл SQLite не создан: {db_path}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка создания файла SQLite: {e}")
        return False

def test_django_with_sqlite():
    """Тест Django с SQLite"""
    print("\n🧪 Тест Django с SQLite...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
        django.setup()
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        print(f"✅ Django SQLite работает: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Django SQLite: {e}")
        return False

def test_sqlalchemy_utils():
    """Тест SQLAlchemy utils"""
    print("\n🧪 Тест SQLAlchemy utils...")
    
    try:
        from mom_baby_bot.sqlalchemy_utils import check_database_connection, create_tables
        
        # Проверяем подключение
        if check_database_connection():
            print("✅ SQLAlchemy подключение работает")
            
            # Создаем таблицы
            create_tables()
            print("✅ SQLAlchemy таблицы созданы")
            return True
        else:
            print("❌ SQLAlchemy подключение не работает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка SQLAlchemy utils: {e}")
        return False

def main():
    print("🔍 Тестирование исправления SQLite\n")
    
    tests = [
        ("Directory Creation", test_directory_creation),
        ("SQLite File Creation", test_sqlite_file_creation),
        ("Django with SQLite", test_django_with_sqlite),
        ("SQLAlchemy Utils", test_sqlalchemy_utils),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Неожиданная ошибка в {test_name}: {e}")
            results.append(False)
    
    print(f"\n📊 Результат: {sum(results)}/{len(results)} тестов прошли")
    
    if all(results):
        print("🎉 Все тесты прошли! SQLite исправлен.")
        return 0
    else:
        print("⚠️ Некоторые тесты не прошли.")
        return 1

if __name__ == "__main__":
    sys.exit(main())