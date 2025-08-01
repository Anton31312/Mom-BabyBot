#!/usr/bin/env python
"""
Инициализация SQLite базы данных для Amvera
"""
import os
import sys
import django
import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_writable_db_path():
    """Находит доступный для записи путь для базы данных"""
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
            return db_path
            
        except Exception as e:
            logger.warning(f"Не удалось использовать путь {db_path}: {e}")
            continue
    
    raise Exception("Не удалось найти доступный путь для базы данных")

def create_sqlite_db(db_path):
    """Создание SQLite базы данных"""
    logger.info(f"🗄️ Создание SQLite базы данных: {db_path}")
    
    try:
        # Создаем базу данных
        conn = sqlite3.connect(db_path)
        conn.close()
        logger.info(f"✅ SQLite база данных создана: {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания SQLite базы: {e}")
        return False

def apply_django_migrations():
    """Применение Django миграций"""
    logger.info("📊 Применение Django миграций...")
    
    try:
        import subprocess
        result = subprocess.run([
            'python', 'manage.py', 'migrate', '--noinput'
        ], capture_output=True, text=True, env={
            **os.environ,
            'DJANGO_SETTINGS_MODULE': 'mom_baby_bot.settings_prod'
        })
        
        if result.returncode == 0:
            logger.info("✅ Django миграции применены")
            return True
        else:
            logger.error(f"❌ Ошибка применения миграций: {result.stderr}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка применения миграций: {e}")
        return False

def create_sqlalchemy_tables(db_path):
    """Создание таблиц SQLAlchemy"""
    logger.info("🏗️ Создание таблиц SQLAlchemy...")
    
    try:
        # Настройка Django если еще не настроен
        try:
            from django.conf import settings
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
                django.setup()
        except:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
            django.setup()
        
        from botapp.models import Base
        from sqlalchemy import create_engine
        
        # Создаем engine с правильным путем
        database_url = f'sqlite:///{db_path}'
        engine = create_engine(database_url, connect_args={
            'check_same_thread': False,
            'timeout': 20,
        })
        
        Base.metadata.create_all(engine)
        logger.info("✅ SQLAlchemy таблицы созданы")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания SQLAlchemy таблиц: {e}")
        return False

def main():
    logger.info("🚀 Инициализация SQLite базы данных для Amvera\n")
    
    try:
        # Находим доступный путь для базы данных
        db_path = find_writable_db_path()
        
        # Устанавливаем переменную окружения
        os.environ['DATABASE_PATH'] = db_path
        logger.info(f"Установлена переменная окружения DATABASE_PATH: {db_path}")
        
        steps = [
            ("Create SQLite DB", lambda: create_sqlite_db(db_path)),
            ("Apply Django Migrations", apply_django_migrations),
            ("Create SQLAlchemy Tables", lambda: create_sqlalchemy_tables(db_path)),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n--- {step_name} ---")
            if not step_func():
                logger.error(f"❌ Шаг '{step_name}' не выполнен")
                return 1
        
        logger.info("\n🎉 Инициализация SQLite завершена успешно!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 