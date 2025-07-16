from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLAlchemy setup
Base = declarative_base()

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(64))
    first_name = Column(String(64))
    last_name = Column(String(64))
    is_pregnant = Column(Boolean, default=False)
    pregnancy_week = Column(Integer)
    baby_birth_date = Column(DateTime)  # Обновлено с baby_age на baby_birth_date
    is_premium = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.telegram_id}>'
# SQLAlchemy utilities for Django context
class SQLAlchemyManager:
    """Утилиты для работы с SQLAlchemy в Django контексте"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Настройка SQLAlchemy engine"""
        database_url = os.getenv('DATABASE_URL', 'sqlite:///mom_baby_bot.db')
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Создание всех таблиц"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Получение новой сессии SQLAlchemy"""
        return self.Session()
    
    def close_session(self, session):
        """Закрытие сессии"""
        if session:
            session.close()

# Глобальный экземпляр менеджера
db_manager = SQLAlchemyManager()

# Утилитарные функции для работы с пользователями
def get_sqlalchemy_session():
    """Получение новой сессии SQLAlchemy для использования в handlers"""
    return db_manager.get_session()

async def get_user(telegram_id: int) -> User:
    """Получение пользователя по telegram_id"""
    session = db_manager.get_session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user
    finally:
        db_manager.close_session(session)

def create_user(telegram_id: int, username: str = None, first_name: str = None, 
                last_name: str = None, **kwargs) -> User:
    """Создание нового пользователя"""
    session = db_manager.get_session()
    try:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)

def update_user(telegram_id: int, **kwargs) -> User:
    """Обновление данных пользователя"""
    session = db_manager.get_session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(user)
        return user
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)

def delete_user(telegram_id: int) -> bool:
    """Удаление пользователя"""
    session = db_manager.get_session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            session.delete(user)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)