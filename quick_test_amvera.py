#!/usr/bin/env python
"""
Быстрый тест для Amvera
"""
import os
import sys
import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s')
logger = logging.getLogger(__name__)

def quick_db_test():
    """Быстрый тест базы данных"""
    logger.info("🧪 Быстрый тест базы данных...")
    
    # Пробуем создать базу данных в текущей директории
    db_path = os.path.join(os.getcwd(), 'test_amvera.db')
    
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        
        # Удаляем тестовый файл
        os.remove(db_path)
        
        logger.info("✅ База данных работает в текущей директории")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка базы данных: {e}")
        return False

def check_environment():
    """Проверка переменных окружения"""
    logger.info("🔧 Проверка переменных окружения...")
    
    required_vars = ['DJANGO_SETTINGS_MODULE']
    optional_vars = ['SECRET_KEY', 'TELEGRAM_BOT_TOKEN']
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"❌ Отсутствуют переменные: {missing}")
        return False
    
    logger.info("✅ Переменные окружения в порядке")
    return True

def check_directories():
    """Проверка директорий"""
    logger.info("📁 Проверка директорий...")
    
    dirs_to_check = [
        '/data',
        '/tmp',
        os.getcwd()
    ]
    
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            logger.info(f"✅ {dir_path} существует")
        else:
            logger.warning(f"⚠️ {dir_path} не существует")
    
    return True

def main():
    logger.info("🚀 Быстрый тест для Amvera\n")
    
    tests = [
        ("Check Directories", check_directories),
        ("Check Environment", check_environment),
        ("Quick DB Test", quick_db_test),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} прошел")
        else:
            logger.error(f"❌ {test_name} не прошел")
    
    logger.info(f"\n🎉 Результат: {passed}/{total} тестов прошли")
    
    if passed == total:
        logger.info("✅ Все тесты прошли успешно!")
        return 0
    else:
        logger.error("❌ Некоторые тесты не прошли")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 