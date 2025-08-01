#!/usr/bin/env python
"""
Тест настройки SQLite
"""
import os
import sys
import django
import sqlite3


def test_sqlite_file():
    """Тест создания и доступа к файлу SQLite"""
    print("🧪 Тест файла SQLite...")

    db_path = '/app/data/mom_baby_bot.db'
    db_dir = os.path.dirname(db_path)

    try:
        # Создаем директорию
        os.makedirs(db_dir, exist_ok=True)
        print(f"✅ Директория создана: {db_dir}")

        # Проверяем доступ к SQLite
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)')
        cursor.execute('INSERT INTO test (id) VALUES (1)')
        cursor.execute('SELECT * FROM test')
        result = cursor.fetchall()
        conn.commit()
        conn.close()

        print(f"✅ SQLite работает: {result}")
        return True

    except Exception as e:
        print(f"❌ Ошибка SQLite: {e}")
        return False


def test_django_sqlite():
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


def test_sqlalchemy_sqlite():
    """Тест SQLAlchemy с SQLite"""
    print("\n🧪 Тест SQLAlchemy с SQLite...")

    try:
        from django.conf import settings

        if hasattr(settings, 'get_sqlalchemy_engine'):
            engine = settings.get_sqlalchemy_engine()
        else:
            from sqlalchemy import create_engine
            engine = create_engine('sqlite:////app/data/mom_baby_bot.db')

        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.fetchone()

        print(f"✅ SQLAlchemy SQLite работает: {value}")
        return True

    except Exception as e:
        print(f"❌ Ошибка SQLAlchemy SQLite: {e}")
        return False


def main():
    print("🔍 Тестирование настройки SQLite\n")

    tests = [
        ("SQLite File", test_sqlite_file),
        ("Django SQLite", test_django_sqlite),
        ("SQLAlchemy SQLite", test_sqlalchemy_sqlite),
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
        print("🎉 Все тесты прошли! SQLite настроен правильно.")
        return 0
    else:
        print("⚠️ Некоторые тесты не прошли.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
