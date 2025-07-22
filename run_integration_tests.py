#!/usr/bin/env python
"""
Скрипт для запуска интеграционных тестов веб-интерфейса материнского ухода.
"""

import os
import sys
import unittest
import django
from pathlib import Path

# Добавляем корень проекта в путь Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')

# Инициализируем Django
django.setup()

def run_integration_tests():
    """Запускает все интеграционные тесты."""
    print("🚀 Запуск интеграционных тестов для веб-интерфейса материнского ухода\n")
    
    # Создаем тестовый загрузчик
    test_loader = unittest.TestLoader()
    
    # Загружаем тесты из модулей
    test_suite = unittest.TestSuite()
    
    # Добавляем интеграционные тесты из webapp/tests
    webapp_tests_path = os.path.join(project_root, 'webapp', 'tests')
    integration_test_modules = [
        'test_integration',
        'test_api_integration',
        'test_sync_integration'
    ]
    
    for module_name in integration_test_modules:
        try:
            module_path = f'webapp.tests.{module_name}'
            tests = test_loader.loadTestsFromName(module_path)
            test_suite.addTest(tests)
            print(f"✅ Загружены тесты из модуля {module_path}")
        except Exception as e:
            print(f"❌ Ошибка загрузки тестов из модуля {module_path}: {e}")
    
    # Запускаем тесты
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Выводим результаты
    print(f"\n📊 Результаты тестирования:")
    print(f"✅ Успешно: {result.testsRun - len(result.errors) - len(result.failures)}")
    print(f"❌ Ошибки: {len(result.errors)}")
    print(f"❌ Неудачи: {len(result.failures)}")
    
    if result.wasSuccessful():
        print("\n🎉 Все интеграционные тесты пройдены успешно!")
        return 0
    else:
        print("\n⚠️ Некоторые интеграционные тесты не пройдены. Проверьте ошибки выше.")
        return 1

if __name__ == "__main__":
    sys.exit(run_integration_tests())