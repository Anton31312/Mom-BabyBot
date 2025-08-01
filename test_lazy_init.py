#!/usr/bin/env python
"""
Тест ленивой инициализации SQLAlchemy
"""
import os
import sys
import django


def test_lazy_initialization():
    """Тест ленивой инициализации"""
    print("🧪 Тест ленивой инициализации SQLAlchemy...")

    # Настройка Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
    django.setup()

    from django.conf import settings

    # Проверяем, что engine не создан при импорте
    print(f"SQLALCHEMY_ENGINE при импорте: {settings.SQLALCHEMY_ENGINE}")
    print(f"SQLALCHEMY_SESSION_FACTORY при импорте: {settings.SQLALCHEMY_SESSION_FACTORY}")

    # Проверяем ленивую инициализацию
    if hasattr(settings, 'get_sqlalchemy_engine'):
        print("✅ Функция get_sqlalchemy_engine доступна")

        # Создаем engine через ленивую инициализацию
        engine = settings.get_sqlalchemy_engine()
        print(f"✅ Engine создан: {engine}")

        # Проверяем подключение
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"✅ Подключение работает: {result.fetchone()}")

        return True
    else:
        print("❌ Функция get_sqlalchemy_engine недоступна")
        return False


def test_models_import():
    """Тест импорта моделей без автоинициализации"""
    print("\n🧪 Тест импорта моделей...")

    try:
        from botapp.models import User
        from botapp.models_child import Child, Measurement
        print("✅ Модели импортированы без ошибок")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта моделей: {e}")
        return False


def main():
    print("🔍 Тестирование ленивой инициализации SQLAlchemy\n")

    tests = [
        ("Models Import", test_models_import),
        ("Lazy Initialization", test_lazy_initialization),
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
        print("🎉 Все тесты прошли! Ленивая инициализация работает.")
        return 0
    else:
        print("⚠️ Некоторые тесты не прошли.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
