"""
Base models and utilities for SQLAlchemy integration.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройка SQLAlchemy
Base = declarative_base()

# Утилиты SQLAlchemy для контекста Django
class SQLAlchemyManager:
    """Утилиты для работы с SQLAlchemy в Django контексте"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Настройка SQLAlchemy engine"""
        try:
            # Принудительное использование SQLite для локальной разработки
            database_url = 'sqlite:///data/mom_baby_bot.db'
            logger.info(f"Connecting to database: {database_url}")
            
            self.engine = create_engine(
                database_url, 
                echo=False,
                connect_args={"check_same_thread": False}  # Необходимо для SQLite в многопоточной среде
            )
            self.Session = sessionmaker(bind=self.engine)
            logger.info("SQLAlchemy engine setup successful")
        except Exception as e:
            logger.error(f"Error setting up SQLAlchemy engine: {e}")
            raise
    
    def create_tables(self):
        """Создание всех таблиц"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self):
        """Получение новой сессии SQLAlchemy"""
        return self.Session()
    
    def close_session(self, session):
        """Закрытие сессии"""
        if session:
            session.close()

# Глобальный экземпляр менеджера
db_manager = SQLAlchemyManager()