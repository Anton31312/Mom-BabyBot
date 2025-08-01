"""
Модели для уведомлений.

Этот модуль содержит SQLAlchemy модели для управления уведомлениями
и интеграции с Telegram ботом.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from botapp.models_base import Base, db_manager


class NotificationPreference(Base):
    """
    Модель предпочтений уведомлений пользователя.
    
    Эта модель хранит настройки уведомлений пользователя для различных событий
    в приложении, таких как таймеры, счетчики и напоминания.
    """
    __tablename__ = 'notification_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Общие настройки
    enabled = Column(Boolean, default=True)
    telegram_enabled = Column(Boolean, default=True)
    web_enabled = Column(Boolean, default=True)
    
    # Настройки для конкретных типов уведомлений
    sleep_timer_notifications = Column(Boolean, default=True)
    feeding_timer_notifications = Column(Boolean, default=True)
    contraction_counter_notifications = Column(Boolean, default=True)
    kick_counter_notifications = Column(Boolean, default=True)
    vaccine_reminder_notifications = Column(Boolean, default=True)
    
    # Настройки частоты уведомлений (в минутах)
    sleep_notification_frequency = Column(Integer, default=30)  # каждые 30 минут
    feeding_notification_frequency = Column(Integer, default=15)  # каждые 15 минут
    contraction_notification_frequency = Column(Integer, default=10)  # каждые 10 минут
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", backref="notification_preferences")
    
    def __repr__(self):
        return f'<NotificationPreference {self.id} for User {self.user_id}>'


class NotificationLog(Base):
    """
    Модель журнала уведомлений.
    
    Эта модель хранит историю отправленных уведомлений для аудита
    и предотвращения дублирования.
    """
    __tablename__ = 'notification_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    notification_type = Column(String(50), nullable=False)  # сон, кормление, схватки, шевеления, прививки
    entity_id = Column(Integer)  # ID связанной сущности (сессии сна, кормления и т.д.)
    channel = Column(String(20), nullable=False)  # telegram, web
    content = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='sent')  # отправлено, ошибка, доставлено
    
    # Связи
    user = relationship("User", backref="notification_logs")
    
    def __repr__(self):
        return f'<NotificationLog {self.id} for User {self.user_id}>'


# Вспомогательные функции для работы с моделью NotificationPreference
def get_notification_preferences(user_id):
    """
    Получить настройки уведомлений для конкретного пользователя.
    
    Аргументы:
        user_id (int): ID пользователя
        
    Возвращает:
        NotificationPreference: Объект настроек уведомлений или None, если не найден
    """
    session = db_manager.get_session()
    try:
        preferences = session.query(NotificationPreference).filter_by(user_id=user_id).first()
        return preferences
    finally:
        db_manager.close_session(session)


def create_notification_preferences(user_id, **kwargs):
    """
    Создать настройки уведомлений для пользователя.
    
    Аргументы:
        user_id (int): ID пользователя
        **kwargs: Дополнительные настройки
        
    Возвращает:
        NotificationPreference: Созданный объект настроек уведомлений
    """
    session = db_manager.get_session()
    try:
        # Проверяем, существуют ли уже настройки
        existing = session.query(NotificationPreference).filter_by(user_id=user_id).first()
        if existing:
            return update_notification_preferences(user_id, **kwargs)
        
        preferences = NotificationPreference(
            user_id=user_id,
            **kwargs
        )
        session.add(preferences)
        session.commit()
        session.refresh(preferences)
        return preferences
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def update_notification_preferences(user_id, **kwargs):
    """
    Обновить настройки уведомлений для пользователя.
    
    Аргументы:
        user_id (int): ID пользователя
        **kwargs: Настройки для обновления
        
    Возвращает:
        NotificationPreference: Обновленный объект настроек уведомлений или None, если не найден
    """
    session = db_manager.get_session()
    try:
        preferences = session.query(NotificationPreference).filter_by(user_id=user_id).first()
        if preferences:
            for key, value in kwargs.items():
                if hasattr(preferences, key):
                    setattr(preferences, key, value)
            preferences.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(preferences)
        return preferences
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def log_notification(user_id, notification_type, entity_id, channel, content, status='sent'):
    """
    Записать уведомление в журнал.
    
    Аргументы:
        user_id (int): ID пользователя
        notification_type (str): Тип уведомления (sleep, feeding, contraction, kick, vaccine)
        entity_id (int): ID связанной сущности
        channel (str): Канал отправки (telegram, web)
        content (str): Содержимое уведомления
        status (str, optional): Статус отправки (sent, failed, delivered)
        
    Возвращает:
        NotificationLog: Созданный объект журнала уведомлений
    """
    session = db_manager.get_session()
    try:
        log = NotificationLog(
            user_id=user_id,
            notification_type=notification_type,
            entity_id=entity_id,
            channel=channel,
            content=content,
            status=status
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def get_recent_notifications(user_id, notification_type=None, limit=10):
    """
    Получить последние уведомления для пользователя.
    
    Аргументы:
        user_id (int): ID пользователя
        notification_type (str, optional): Тип уведомления для фильтрации
        limit (int, optional): Максимальное количество записей
        
    Возвращает:
        list: Список объектов NotificationLog
    """
    session = db_manager.get_session()
    try:
        query = session.query(NotificationLog).filter_by(user_id=user_id)
        
        if notification_type:
            query = query.filter_by(notification_type=notification_type)
        
        logs = query.order_by(NotificationLog.sent_at.desc()).limit(limit).all()
        return logs
    finally:
        db_manager.close_session(session)