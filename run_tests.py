"""
Скрипт для запуска всех модульных тестов.

Этот скрипт запускает все модульные тесты для веб-интерфейса материнского ухода.
"""

import os
import sys
import unittest
import django

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')
django.setup()

# Импортируем тесты моделей
from webapp.tests.test_child_models import ChildModelTestCase, MeasurementModelTestCase
from webapp.tests.test_contraction_models import ContractionModelTestCase
from webapp.tests.test_kick_models import KickModelTestCase
from webapp.tests.test_sleep_models import SleepModelTestCase
from webapp.tests.test_feeding_models import FeedingModelTestCase
from webapp.tests.test_vaccine_api import VaccineAPITestCase

# Импортируем тесты API
from webapp.tests.test_contraction_api import ContractionAPITestCase
from webapp.tests.test_kick_api import KickAPITestCase
from webapp.tests.test_sleep_api import SleepAPITestCase
from webapp.tests.test_feeding_api import FeedingAPITestCase
from webapp.tests.test_child_api import ChildAPITestCase


def run_tests():
    """Запускает все модульные тесты."""
    # Создаем тестовый набор
    test_suite = unittest.TestSuite()
    
    # Добавляем тесты моделей
    test_suite.addTest(unittest.makeSuite(ChildModelTestCase))
    test_suite.addTest(unittest.makeSuite(MeasurementModelTestCase))
    test_suite.addTest(unittest.makeSuite(ContractionModelTestCase))
    test_suite.addTest(unittest.makeSuite(KickModelTestCase))
    test_suite.addTest(unittest.makeSuite(SleepModelTestCase))
    test_suite.addTest(unittest.makeSuite(FeedingModelTestCase))
    
    # Добавляем тесты API
    test_suite.addTest(unittest.makeSuite(VaccineAPITestCase))
    test_suite.addTest(unittest.makeSuite(ContractionAPITestCase))
    test_suite.addTest(unittest.makeSuite(KickAPITestCase))
    test_suite.addTest(unittest.makeSuite(SleepAPITestCase))
    test_suite.addTest(unittest.makeSuite(FeedingAPITestCase))
    test_suite.addTest(unittest.makeSuite(ChildAPITestCase))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Возвращаем код выхода
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())