#!/usr/bin/env python
"""
Скрипт для миграции данных из старой базы данных (с полем baby_age) в новую (с полем baby_birth_date).
Этот скрипт конвертирует значения baby_age в baby_birth_date для обеспечения совместимости.
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Устанавливаем Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')

def find_database_files():
    """Поиск файлов базы данных"""
    logger.info("Поиск файлов базы данных...")
    
    db_files = ['data/mom_baby_bot.db', 'db.sqlite3', 'instance/mom_baby_bot.db']
    found_dbs = []
    
    for db_file in db_files:
        db_path = Path(db_file)
        if db_path.exists():
            logger.info(f"✅ Найден файл базы данных: {db_file}")
            found_dbs.append(db_file)
    
    if not found_dbs:
        logger.warning("⚠️ Файлы базы данных не найдены.")
        return []
    
    return found_dbs

def check_table_structure(db_file):
    """Проверка структуры таблиц в базе данных"""
    logger.info(f"Проверка структуры таблиц в {db_file}...")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Проверяем наличие таблицы users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            logger.warning(f"⚠️ Таблица users не найдена в {db_file}")
            conn.close()
            return False, None
        
        # Проверяем наличие колонок
        cursor.execute("PRAGMA table_info(users);")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        has_baby_age = 'baby_age' in columns
        has_baby_birth_date = 'baby_birth_date' in columns
        
        if has_baby_age and not has_baby_birth_date:
            logger.info(f"✅ База данных {db_file} требует миграции (есть baby_age, нет baby_birth_date)")
            conn.close()
            return True, "add_column"
        elif has_baby_age and has_baby_birth_date:
            logger.info(f"✅ База данных {db_file} требует миграции данных (есть оба поля)")
            conn.close()
            return True, "migrate_data"
        elif not has_baby_age and has_baby_birth_date:
            logger.info(f"✅ База данных {db_file} уже мигрирована (есть только baby_birth_date)")
            conn.close()
            return False, None
        else:
            logger.warning(f"⚠️ В базе данных {db_file} отсутствуют оба поля")
            conn.close()
            return False, None
            
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке структуры базы данных {db_file}: {e}")
        return False, None

def add_baby_birth_date_column(db_file):
    """Добавление колонки baby_birth_date в таблицу users"""
    logger.info(f"Добавление колонки baby_birth_date в {db_file}...")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Добавляем колонку baby_birth_date
        cursor.execute("ALTER TABLE users ADD COLUMN baby_birth_date DATETIME;")
        conn.commit()
        
        logger.info(f"✅ Колонка baby_birth_date успешно добавлена в {db_file}")
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении колонки baby_birth_date в {db_file}: {e}")
        return False

def convert_age_to_birth_date(age_str):
    """Конвертация строки возраста в дату рождения"""
    try:
        if not age_str:
            return None
            
        # Удаляем все нечисловые символы
        age_str = ''.join(c for c in age_str if c.isdigit())
        
        if not age_str:
            return None
            
        age = int(age_str)
        
        # Предполагаем, что возраст указан в месяцах
        birth_date = datetime.now() - timedelta(days=age*30)
        return birth_date
        
    except Exception as e:
        logger.error(f"❌ Ошибка при конвертации возраста '{age_str}' в дату рождения: {e}")
        return None

def migrate_data(db_file):
    """Миграция данных из baby_age в baby_birth_date"""
    logger.info(f"Миграция данных в {db_file}...")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Получаем пользователей с заполненным baby_age и пустым baby_birth_date
        cursor.execute("SELECT id, baby_age FROM users WHERE baby_age IS NOT NULL AND baby_birth_date IS NULL;")
        users = cursor.fetchall()
        
        if not users:
            logger.info(f"✅ Нет пользователей для миграции в {db_file}")
            conn.close()
            return True
            
        logger.info(f"Найдено {len(users)} пользователей для миграции в {db_file}")
        
        # Обновляем каждого пользователя
        for user_id, baby_age in users:
            birth_date = convert_age_to_birth_date(baby_age)
            
            if birth_date:
                cursor.execute(
                    "UPDATE users SET baby_birth_date = ? WHERE id = ?;",
                    (birth_date.strftime('%Y-%m-%d %H:%M:%S'), user_id)
                )
                logger.info(f"✅ Пользователь {user_id}: возраст '{baby_age}' -> дата рождения '{birth_date}'")
            else:
                logger.warning(f"⚠️ Не удалось конвертировать возраст '{baby_age}' для пользователя {user_id}")
        
        conn.commit()
        logger.info(f"✅ Миграция данных в {db_file} успешно завершена")
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при миграции данных в {db_file}: {e}")
        return False

def migrate_sqlalchemy_models():
    """Миграция моделей SQLAlchemy"""
    logger.info("Миграция моделей SQLAlchemy...")
    
    try:
        import django
        django.setup()
        
        from botapp.models import db_manager
        
        # Создаем таблицы с новой структурой
        db_manager.create_tables()
        logger.info("✅ Таблицы SQLAlchemy успешно обновлены")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при миграции моделей SQLAlchemy: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("=" * 60)
    logger.info("Миграция данных из baby_age в baby_birth_date")
    logger.info("=" * 60)
    
    # Находим файлы базы данных
    db_files = find_database_files()
    
    if not db_files:
        logger.warning("Нет файлов базы данных для миграции")
        return
    
    # Мигрируем модели SQLAlchemy
    migrate_sqlalchemy_models()
    
    # Обрабатываем каждый файл базы данных
    for db_file in db_files:
        needs_migration, migration_type = check_table_structure(db_file)
        
        if needs_migration:
            if migration_type == "add_column":
                add_baby_birth_date_column(db_file)
                migrate_data(db_file)
            elif migration_type == "migrate_data":
                migrate_data(db_file)
        else:
            logger.info(f"База данных {db_file} не требует миграции")
    
    logger.info("=" * 60)
    logger.info("Миграция завершена!")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()