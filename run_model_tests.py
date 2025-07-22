"""
Скрипт для запуска модульных тестов моделей.

Этот скрипт запускает модульные тесты для моделей веб-интерфейса материнского ухода.
"""

import unittest
from botapp.tests.test_models_child import TestChildModel
from botapp.tests.test_models_vaccine import TestVaccineModel
from webapp.tests.test_child_models import ChildModelTestCase, MeasurementModelTestCase
from webapp.tests.test_contraction_models import ContractionModelTestCase
from webapp.tests.test_kick_models import KickModelTestCase
from webapp.tests.test_sleep_models import SleepModelTestCase
from webapp.tests.test_feeding_models import FeedingModelTestCase


def run_tests():
    """Запускает модульные тесты моделей."""
    # Создаем тестовый набор
    test_suite = unittest.TestSuite()
    
    # Добавляем существующие тесты моделей
    test_suite.addTest(unittest.makeSuite(TestChildModel))
    test_suite.addTest(unittest.makeSuite(TestVaccineModel))
    
    # Добавляем новые тесты моделей
    test_suite.addTest(unittest.makeSuite(ChildModelTestCase))
    test_suite.addTest(unittest.makeSuite(MeasurementModelTestCase))
    test_suite.addTest(unittest.makeSuite(ContractionModelTestCase))
    test_suite.addTest(unittest.makeSuite(KickModelTestCase))
    test_suite.addTest(unittest.makeSuite(SleepModelTestCase))
    test_suite.addTest(unittest.makeSuite(FeedingModelTestCase))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Возвращаем код выхода
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    run_tests()