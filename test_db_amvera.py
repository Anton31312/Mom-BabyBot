#!/usr/bin/env python
"""
Тестирование базы данных на Amvera
"""
import os
import sys
import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_creation():
    """Тестирование создания базы данных"""
    logger.info("🧪 Тестирование создания базы данных...")
    
    # Пробуем несколько путей для базы данных
    possible_paths = [
        '/app/data/mom_baby_bot.db',
        os.path.join(os.getcwd(), 'mom_baby_bot.db'),
        '/tmp/mom_baby_bot.db',
        '/var/tmp/mom_baby_bot.db'
    ]
    
    for db_path in possible_paths:
        db_dir = os.path.dirname(db_path)
        logger.info(f"Тестируем путь: {db_path}")
        
        try:
            # Создаем директорию если не существует
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Создана директория: {db_dir}")
            
            # Пробуем создать файл базы данных
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            # Создаем тестовую таблицу
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Вставляем тестовые данные
            cursor.execute('INSERT INTO test_table (name) VALUES (?)', ('test',))
            
            # Читаем данные
            cursor.execute('SELECT * FROM test_table')
            result = cursor.fetchall()
            
            # Удаляем тестовую таблицу
            cursor.execute('DROP TABLE test_table')
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ База данных работает по пути: {db_path}")
            logger.info(f"Результат теста: {result}")
            
            # Устанавливаем переменную окружения
            os.environ['DATABASE_PATH'] = db_path
            return True
            
        except Exception as e:
            logger.warning(f"Не удалось использовать путь {db_path}: {e}")
            continue
    
    logger.error("❌ Не удалось создать базу данных ни по одному пути")
    return False

def test_django_integration():
    """Тестирование интеграции с Django"""
    logger.info("🧪 Тестирование интеграции с Django...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
        import django
        django.setup()
        
        from django.conf import settings
        logger.info(f"✅ Django настроен")
        logger.info(f"База данных Django: {settings.DATABASES['default']['NAME']}")
        logger.info(f"SQLAlchemy URL: {getattr(settings, 'SQLALCHEMY_DATABASE_URL', 'Not set')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка интеграции с Django: {e}")
        return False

def main():
    logger.info("🚀 Тестирование базы данных на Amvera\n")
    
    tests = [
        ("Test Database Creation", test_database_creation),
        ("Test Django Integration", test_django_integration),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        if not test_func():
            logger.error(f"❌ Тест '{test_name}' не прошел")
            return 1
    
    logger.info("\n🎉 Все тесты прошли успешно!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 