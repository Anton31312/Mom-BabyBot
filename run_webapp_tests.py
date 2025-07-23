"""
Скрипт для запуска тестов веб-приложения.

Этот скрипт запускает все тесты для веб-приложения, включая
модульные тесты и тесты API.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    # Настройка Django для запуска тестов
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mom_baby_bot.settings'
    django.setup()
    
    # Получаем класс тестового раннера
    TestRunner = get_runner(settings)
    
    # Создаем экземпляр тестового раннера
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    # Запускаем тесты
    print("Запуск тестов веб-приложения...")
    failures = test_runner.run_tests(["webapp.tests"])
    
    # Выходим с соответствующим кодом
    sys.exit(bool(failures))