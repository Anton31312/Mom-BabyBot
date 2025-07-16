#!/usr/bin/env python
"""
Скрипт для инициализации базы данных SQLAlchemy в Django проекте.

Этот скрипт может быть запущен как самостоятельный скрипт или
использован как часть Django management команд.

Использование:
    python init_db.py
    или
    python manage.py shell -c "import init_db; init_db.init_database()"
"""

import os
import sys
import logging
import django
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.inspection import inspect

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Добавление текущей директории в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')
django.setup()

# Импорт после настройки Django
from django.conf import settings
from botapp.models import Base, User
from mom_baby_bot.sqlalchemy_utils import get_sqlalchemy_session


def check_table_exists(engine, table_name):
    """
    Проверяет существование таблицы в базе данных.
    
    Args:
        engine: SQLAlchemy engine
        table_name: Имя таблицы для проверки
        
    Returns:
        bool: True если таблица существует, иначе False
    """
    try:
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при проверке таблицы {table_name}: {str(e)}")
        return False


def init_database(check_first=True):
    """
    Инициализирует базу данных, создавая все необходимые таблицы.
    
    Args:
        check_first: Если True, проверяет существование таблиц перед созданием
        
    Returns:
        bool: True если инициализация прошла успешно, иначе False
    """
    try:
        engine = settings.SQLALCHEMY_ENGINE
        
        # Проверка существования таблиц
        if check_first:
            tables_to_check = [table.__tablename__ for table in Base.__subclasses__()]
            existing_tables = []
            
            for table_name in tables_to_check:
                if check_table_exists(engine, table_name):
                    existing_tables.append(table_name)
            
            if existing_tables:
                logger.info(f"Найдены существующие таблицы: {', '.join(existing_tables)}")
                
                # Если все таблицы уже существуют, выходим
                if len(existing_tables) == len(tables_to_check):
                    logger.info("Все таблицы уже существуют. Инициализация не требуется.")
                    return True
        
        # Создание таблиц
        Base.metadata.create_all(bind=engine)
        logger.info("База данных успешно инициализирована")
        
        # Проверка создания таблиц
        for table in Base.__subclasses__():
            table_name = table.__tablename__
            if check_table_exists(engine, table_name):
                logger.info(f"Таблица {table_name} успешно создана")
            else:
                logger.error(f"Не удалось создать таблицу {table_name}")
                return False
        
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy при инициализации базы данных: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при инициализации базы данных: {str(e)}")
        return False


def create_test_user():
    """
    Создает тестового пользователя, если он не существует.
    Полезно для тестирования и разработки.
    """
    try:
        with get_sqlalchemy_session() as session:
            # Проверяем, существует ли тестовый пользователь
            test_user = session.query(User).filter_by(telegram_id=123456789).first()
            
            if not test_user:
                # Создаем тестового пользователя
                test_user = User(
                    telegram_id=123456789,
                    username="test_user",
                    first_name="Test",
                    last_name="User",
                    is_admin=True
                )
                session.add(test_user)
                session.commit()
                logger.info("Тестовый пользователь успешно создан")
            else:
                logger.info("Тестовый пользователь уже существует")
                
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при создании тестового пользователя: {str(e)}")


def main():
    """
    Основная функция для запуска из командной строки.
    """
    success = init_database()
    
    if success and settings.DEBUG:
        # В режиме отладки создаем тестового пользователя
        create_test_user()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())