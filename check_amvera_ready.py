#!/usr/bin/env python
"""
Проверка готовности к запуску на Amvera
"""
import os
import sys
import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_access():
    """Проверка доступа к базе данных"""
    logger.info("🗄️ Проверка доступа к базе данных...")
    
    # Пробуем несколько путей для базы данных
    possible_paths = [
        '/app/data/mom_baby_bot.db',
        os.path.join(os.getcwd(), 'mom_baby_bot.db'),
        '/tmp/mom_baby_bot.db',
        '/var/tmp/mom_baby_bot.db'
    ]
    
    for db_path in possible_paths:
        db_dir = os.path.dirname(db_path)
        logger.info(f"Проверяем путь: {db_path}")
        
        try:
            # Создаем директорию если не существует
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Создана директория: {db_dir}")
            
            # Пробуем создать файл базы данных
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
            
            logger.info(f"✅ База данных доступна по пути: {db_path}")
            # Устанавливаем переменную окружения
            os.environ['DATABASE_PATH'] = db_path
            return True
            
        except Exception as e:
            logger.warning(f"Не удалось использовать путь {db_path}: {e}")
            continue
    
    logger.error("❌ Не удалось найти доступный путь для базы данных")
    return False

def check_django_settings():
    """Проверка настроек Django"""
    logger.info("⚙️ Проверка настроек Django...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
        import django
        django.setup()
        
        from django.conf import settings
        logger.info(f"✅ Django настроен, DEBUG: {settings.DEBUG}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки Django: {e}")
        return False

def check_required_directories():
    """Проверка и создание необходимых директорий"""
    logger.info("📁 Проверка необходимых директорий...")
    
    required_dirs = [
        '/app/staticfiles',
        '/app/media',
        '/app/logs',
        '/app/data'
    ]
    
    for dir_path in required_dirs:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Создана директория: {dir_path}")
            else:
                logger.info(f"Директория существует: {dir_path}")
        except Exception as e:
            logger.warning(f"Не удалось создать директорию {dir_path}: {e}")
    
    return True

def check_environment_variables():
    """Проверка переменных окружения"""
    logger.info("🔧 Проверка переменных окружения...")
    
    required_vars = [
        'DJANGO_SETTINGS_MODULE',
        'SECRET_KEY'
    ]
    
    optional_vars = [
        'TELEGRAM_BOT_TOKEN',
        'WEBHOOK_URL',
        'WEBAPP_URL',
        'ADMIN_IDS'
    ]
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        logger.error(f"❌ Отсутствуют обязательные переменные окружения: {missing_required}")
        return False
    
    logger.info("✅ Обязательные переменные окружения установлены")
    
    # Проверяем опциональные переменные
    for var in optional_vars:
        if os.getenv(var):
            logger.info(f"✅ {var} установлена")
        else:
            logger.info(f"⚠️ {var} не установлена (опционально)")
    
    return True

def main():
    logger.info("🚀 Проверка готовности к запуску на Amvera\n")
    
    checks = [
        ("Check Required Directories", check_required_directories),
        ("Check Environment Variables", check_environment_variables),
        ("Check Django Settings", check_django_settings),
        ("Check Database Access", check_database_access),
    ]
    
    for check_name, check_func in checks:
        logger.info(f"\n--- {check_name} ---")
        if not check_func():
            logger.error(f"❌ Проверка '{check_name}' не прошла")
            return 1
    
    logger.info("\n🎉 Все проверки прошли успешно!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 