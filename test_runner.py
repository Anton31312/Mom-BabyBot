"""
Скрипт для запуска модульных тестов.

Этот скрипт запускает модульные тесты для веб-интерфейса материнского ухода,
используя обнаружение тестов для избежания проблем с циклическими импортами.
"""

import unittest
import os
import sys


def run_tests():
    """Запускает модульные тесты, обнаруженные в директориях с тестами."""
    # Определяем директории с тестами
    test_dirs = [
        'webapp/tests',
        'botapp/tests'
    ]
    
    # Создаем загрузчик тестов
    loader = unittest.TestLoader()
    
    # Создаем тестовый набор
    test_suite = unittest.TestSuite()
    
    # Добавляем тесты из каждой директории
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            print(f"Поиск тестов в директории: {test_dir}")
            discovered_tests = loader.discover(test_dir, pattern="test_*.py")
            test_suite.addTest(discovered_tests)
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Возвращаем код выхода
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())