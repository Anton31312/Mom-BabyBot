#!/usr/bin/env python
"""
Полная диагностика для Amvera
"""
import os
import sys
import sqlite3
import logging
import subprocess
import platform

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s')
logger = logging.getLogger(__name__)

def system_info():
    """Информация о системе"""
    logger.info("🖥️ Информация о системе...")
    
    info = {
        "Platform": platform.platform(),
        "Python Version": platform.python_version(),
        "Architecture": platform.architecture(),
        "Current Directory": os.getcwd(),
        "User": os.getenv('USER', 'unknown'),
        "Home": os.getenv('HOME', 'unknown'),
    }
    
    for key, value in info.items():
        logger.info(f"{key}: {value}")
    
    return True

def check_permissions():
    """Проверка прав доступа"""
    logger.info("🔐 Проверка прав доступа...")
    
    paths_to_check = [
        '/app',
        '/app/data',
        '/tmp',
        '/var/tmp',
        os.getcwd()
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            try:
                # Проверяем права на чтение
                os.listdir(path)
                logger.info(f"✅ {path} - доступен для чтения")
                
                # Проверяем права на запись
                test_file = os.path.join(path, 'test_write.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logger.info(f"✅ {path} - доступен для записи")
                
            except Exception as e:
                logger.error(f"❌ {path} - проблемы с правами: {e}")
        else:
            logger.warning(f"⚠️ {path} - не существует")
    
    return True

def check_sqlite():
    """Проверка SQLite"""
    logger.info("🗄️ Проверка SQLite...")
    
    try:
        import sqlite3
        logger.info(f"✅ SQLite версия: {sqlite3.sqlite_version}")
        
        # Тестируем создание базы данных
        test_paths = [
            '/app/data/test.db',
            os.path.join(os.getcwd(), 'test.db'),
            '/tmp/test.db',
            '/var/tmp/test.db'
        ]
        
        for path in test_paths:
            try:
                conn = sqlite3.connect(path, timeout=5)
                cursor = conn.cursor()
                cursor.execute('SELECT sqlite_version()')
                version = cursor.fetchone()[0]
                conn.close()
                os.remove(path)  # Удаляем тестовый файл
                logger.info(f"✅ SQLite работает по пути: {path} (версия: {version})")
                break
            except Exception as e:
                logger.warning(f"⚠️ SQLite не работает по пути {path}: {e}")
        else:
            logger.error("❌ SQLite не работает ни по одному пути")
            return False
        
        return True
        
    except ImportError:
        logger.error("❌ SQLite не установлен")
        return False

def check_django():
    """Проверка Django"""
    logger.info("🐍 Проверка Django...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
        import django
        django.setup()
        
        from django.conf import settings
        from django import get_version
        
        logger.info(f"✅ Django версия: {get_version()}")
        logger.info(f"✅ DEBUG: {settings.DEBUG}")
        logger.info(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка Django: {e}")
        return False

def check_environment_variables():
    """Проверка переменных окружения"""
    logger.info("🔧 Проверка переменных окружения...")
    
    env_vars = {
        'DJANGO_SETTINGS_MODULE': 'Обязательная',
        'SECRET_KEY': 'Обязательная',
        'TELEGRAM_BOT_TOKEN': 'Опциональная',
        'WEBHOOK_URL': 'Опциональная',
        'WEBAPP_URL': 'Опциональная',
        'ADMIN_IDS': 'Опциональная',
        'DEBUG': 'Опциональная',
        'PORT': 'Опциональная',
    }
    
    missing_required = []
    present_optional = []
    
    for var, status in env_vars.items():
        value = os.getenv(var)
        if value:
            if status == 'Обязательная':
                logger.info(f"✅ {var}: установлена")
            else:
                logger.info(f"✅ {var}: установлена (опциональная)")
                present_optional.append(var)
        else:
            if status == 'Обязательная':
                logger.error(f"❌ {var}: отсутствует (обязательная)")
                missing_required.append(var)
            else:
                logger.warning(f"⚠️ {var}: не установлена (опциональная)")
    
    if missing_required:
        logger.error(f"❌ Отсутствуют обязательные переменные: {missing_required}")
        return False
    
    logger.info("✅ Все обязательные переменные окружения установлены")
    return True

def check_dependencies():
    """Проверка зависимостей"""
    logger.info("📦 Проверка зависимостей...")
    
    required_packages = [
        'django',
        'sqlalchemy',
        'gunicorn',
        'whitenoise'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package}: установлен")
        except ImportError:
            logger.error(f"❌ {package}: не установлен")
            missing.append(package)
    
    if missing:
        logger.error(f"❌ Отсутствуют пакеты: {missing}")
        return False
    
    logger.info("✅ Все зависимости установлены")
    return True

def main():
    logger.info("🚀 Полная диагностика для Amvera\n")
    
    checks = [
        ("System Info", system_info),
        ("Check Permissions", check_permissions),
        ("Check SQLite", check_sqlite),
        ("Check Dependencies", check_dependencies),
        ("Check Environment Variables", check_environment_variables),
        ("Check Django", check_django),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        logger.info(f"\n--- {check_name} ---")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"❌ Ошибка в {check_name}: {e}")
            results.append((check_name, False))
    
    # Выводим итоговый отчет
    logger.info("\n" + "="*50)
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    logger.info("="*50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ НЕ ПРОШЕЛ"
        logger.info(f"{check_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nРезультат: {passed}/{total} проверок прошли")
    
    if passed == total:
        logger.info("🎉 Все проверки прошли успешно!")
        logger.info("✅ Система готова к работе на Amvera")
        return 0
    else:
        logger.error("❌ Некоторые проверки не прошли")
        logger.error("⚠️ Рекомендуется исправить проблемы перед деплоем")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 