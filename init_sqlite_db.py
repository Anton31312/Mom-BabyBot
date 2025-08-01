"""
Инициализация базы данных SQLite для локальной разработки.
"""

import os
import logging
import django
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Установка модуля настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')

# Инициализация Django
django.setup()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_sqlite_db():
    """Инициализация базы данных SQLite для локальной разработки."""
    try:
        from sqlalchemy import create_engine, text
        from botapp.models import Base

        # Создание движка базы данных SQLite
        engine = create_engine('sqlite:///data/mom_baby_bot.db', echo=True)

        # Создание всех таблиц
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)

        # Тестирование соединения
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 'Database initialized successfully'"))
            for row in result:
                logger.info(row[0])

        logger.info("SQLite database initialized successfully!")
        return True

    except Exception as e:
        logger.error(f"Error initializing SQLite database: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting SQLite database initialization...")
    success = init_sqlite_db()
    if success:
        logger.info("Database initialization completed successfully.")
    else:
        logger.error("Database initialization failed.")
