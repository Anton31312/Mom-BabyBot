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
        # Не инициализируем engine автоматически
    
    def setup_engine(self, database_url=None):
        """Настройка SQLAlchemy engine (вызывается вручную)"""
        try:
            # Получаем URL базы данных
            if database_url is None:
                database_url = os.getenv('DATABASE_URL', 'sqlite:///data/mom_baby_bot.db')
            
            logger.info(f"Connecting to database: {database_url}")
            
            # Настройки для разных типов баз данных
            if database_url.startswith('sqlite'):
                engine_options = {
                    'echo': False,
                    'connect_args': {"check_same_thread": False}
                }
            elif database_url.startswith('postgresql'):
                engine_options = {
                    'echo': False,
                    'pool_pre_ping': True,
                    'pool_recycle': 300,
                    'pool_size': 5,
                    'max_overflow': 10
                }
            else:
                engine_options = {
                    'echo': False,
                    'pool_pre_ping': True,
                    'pool_recycle': 300
                }
            
            self.engine = create_engine(database_url, **engine_options)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("SQLAlchemy engine setup successful")
        except Exception as e:
            logger.error(f"Error setting up SQLAlchemy engine: {e}")
            raise
    
    def create_tables(self):
        """Создание всех таблиц"""
        try:
            if self.engine is None:
                raise Exception("Engine not initialized. Call setup_engine() first.")
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self):
        """Получение новой сессии SQLAlchemy"""
        if self.Session is None:
            raise Exception("Session factory not initialized. Call setup_engine() first.")
        return self.Session()
    
    def close_session(self, session):
        """Закрытие сессии"""
        if session:
            session.close()

# Глобальный экземпляр менеджера
db_manager = SQLAlchemyManager()