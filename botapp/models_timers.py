"""
Модели для счетчиков и таймеров.

Этот модуль содержит SQLAlchemy модели для счетчиков схваток, шевелений,
таймеров сна и отслеживания кормления для веб-интерфейса материнского ухода.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from botapp.models_base import Base, db_manager


class Contraction(Base):
    """
    Модель сессии схваток.
    
    Эта модель представляет сессию отслеживания схваток с временем начала и окончания,
    а также связью с отдельными событиями схваток.
    """
    __tablename__ = 'contractions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime)
    notes = Column(String(255))
    
    # Связи
    user = relationship("User", backref="contractions")
    contraction_events = relationship("ContractionEvent", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Contraction Session {self.id} for User {self.user_id}>'
    
    @property
    def duration(self):
        """Рассчитывает общую продолжительность сессии схваток в минутах."""
        if not self.end_time:
            return None
        
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60
    
    @property
    def count(self):
        """Возвращает количество схваток в сессии."""
        return len(self.contraction_events)
    
    @property
    def average_interval(self):
        """Рассчитывает средний интервал между схватками в минутах."""
        if len(self.contraction_events) < 2:
            return None
        
        # Сортируем события по времени
        sorted_events = sorted(self.contraction_events, key=lambda e: e.timestamp)
        
        # Рассчитываем интервалы между последовательными схватками
        intervals = []
        for i in range(1, len(sorted_events)):
            delta = sorted_events[i].timestamp - sorted_events[i-1].timestamp
            intervals.append(delta.total_seconds() / 60)
        
        # Возвращаем среднее значение
        return sum(intervals) / len(intervals)


class ContractionEvent(Base):
    """
    Модель отдельной схватки.
    
    Эта модель представляет отдельное событие схватки с временной меткой
    и продолжительностью.
    """
    __tablename__ = 'contraction_events'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('contractions.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    duration = Column(Integer)  # продолжительность в секундах
    intensity = Column(Integer)  # шкала интенсивности от 1 до 10
    
    # Связи
    session = relationship("Contraction", back_populates="contraction_events")
    
    def __repr__(self):
        return f'<Contraction Event {self.id} at {self.timestamp}>'


class Kick(Base):
    """
    Модель сессии шевелений.
    
    Эта модель представляет сессию отслеживания шевелений ребенка с временем начала
    и окончания, а также связью с отдельными событиями шевелений.
    """
    __tablename__ = 'kicks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime)
    notes = Column(String(255))
    
    # Связи
    user = relationship("User", backref="kicks")
    kick_events = relationship("KickEvent", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Kick Session {self.id} for User {self.user_id}>'
    
    @property
    def duration(self):
        """Рассчитывает общую продолжительность сессии шевелений в минутах."""
        if not self.end_time:
            return None
        
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60
    
    @property
    def count(self):
        """Возвращает количество шевелений в сессии."""
        return len(self.kick_events)


class KickEvent(Base):
    """
    Модель отдельного шевеления.
    
    Эта модель представляет отдельное событие шевеления с временной меткой
    и опциональной интенсивностью.
    """
    __tablename__ = 'kick_events'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('kicks.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    intensity = Column(Integer)  # шкала интенсивности от 1 до 10
    
    # Связи
    session = relationship("Kick", back_populates="kick_events")
    
    def __repr__(self):
        return f'<Kick Event {self.id} at {self.timestamp}>'


class SleepSession(Base):
    """
    Модель сессии сна.
    
    Эта модель представляет сессию сна ребенка с временем начала и окончания,
    а также типом сна (дневной или ночной).
    """
    __tablename__ = 'sleep_sessions'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime)
    type = Column(String(10))  # 'day' или 'night'
    quality = Column(Integer)  # шкала качества от 1 до 5
    notes = Column(String(255))
    
    # Связи
    child = relationship("Child", backref="sleep_sessions")
    
    def __repr__(self):
        return f'<Sleep Session {self.id} for Child {self.child_id}>'
    
    @property
    def duration(self):
        """Рассчитывает продолжительность сна в минутах."""
        if not self.end_time:
            return None
        
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60


class FeedingSession(Base):
    """
    Модель сессии кормления с поддержкой двух таймеров.
    
    Эта модель представляет сессию кормления ребенка с информацией о типе кормления
    (грудное или из бутылочки), количестве, продолжительности и поддержкой
    отдельных таймеров для каждой груди.
    """
    __tablename__ = 'feeding_sessions'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime)  # время окончания сессии
    type = Column(String(10), nullable=False)  # 'breast' или 'bottle'
    amount = Column(Float)  # в мл, только для бутылочки
    duration = Column(Integer)  # в минутах, только для груди (устаревшее поле)
    breast = Column(String(5))  # 'left', 'right' или 'both', только для груди (устаревшее поле)
    food_type = Column(String(50))  # тип пищи/смеси
    milk_type = Column(String(50))  # тип молока/смеси (альтернативное название)
    notes = Column(String(255))
    
    # Новые поля для поддержки двух таймеров
    left_breast_duration = Column(Integer, default=0)  # продолжительность кормления левой грудью в секундах
    right_breast_duration = Column(Integer, default=0)  # продолжительность кормления правой грудью в секундах
    left_timer_start = Column(DateTime)  # время начала таймера левой груди
    right_timer_start = Column(DateTime)  # время начала таймера правой груди
    left_timer_active = Column(Boolean, default=False)  # активен ли таймер левой груди
    right_timer_active = Column(Boolean, default=False)  # активен ли таймер правой груди
    last_active_breast = Column(String(5))  # последняя активная грудь ('left' или 'right')
    
    # Связи
    child = relationship("Child", backref="feeding_sessions")
    
    def __repr__(self):
        return f'<Feeding Session {self.id} for Child {self.child_id}>'
    
    @property
    def total_duration_seconds(self):
        """Общая продолжительность кормления в секундах."""
        return (self.left_breast_duration or 0) + (self.right_breast_duration or 0)
    
    @property
    def total_duration_minutes(self):
        """Общая продолжительность кормления в минутах."""
        return self.total_duration_seconds / 60
    
    @property
    def is_active(self):
        """Проверяет, активна ли сессия кормления."""
        return self.left_timer_active or self.right_timer_active
    
    def get_breast_duration_minutes(self, breast):
        """
        Возвращает продолжительность кормления для указанной груди в минутах.
        
        Args:
            breast (str): 'left' или 'right'
            
        Returns:
            float: Продолжительность в минутах
        """
        if breast == 'left':
            return (self.left_breast_duration or 0) / 60
        elif breast == 'right':
            return (self.right_breast_duration or 0) / 60
        return 0
    
    def get_breast_percentage(self, breast):
        """
        Возвращает процент времени кормления для указанной груди.
        
        Args:
            breast (str): 'left' или 'right'
            
        Returns:
            float: Процент времени (0-100)
        """
        total_seconds = self.total_duration_seconds
        if total_seconds == 0:
            return 0
        
        if breast == 'left':
            breast_seconds = self.left_breast_duration or 0
        elif breast == 'right':
            breast_seconds = self.right_breast_duration or 0
        else:
            return 0
        
        return (breast_seconds / total_seconds) * 100


# Вспомогательные функции для работы с моделью Contraction
def get_contraction_sessions(user_id):
    """
    Получить все сессии схваток для конкретного пользователя.
    
    Аргументы:
        user_id (int): ID пользователя
        
    Возвращает:
        list: Список объектов Contraction
    """
    session = db_manager.get_session()
    try:
        contractions = session.query(Contraction).filter_by(user_id=user_id).order_by(Contraction.start_time.desc()).all()
        return contractions
    finally:
        db_manager.close_session(session)


def create_contraction_session(user_id, notes=None):
    """
    Создать новую сессию схваток.
    
    Аргументы:
        user_id (int): ID пользователя
        notes (str, optional): Заметки к сессии
        
    Возвращает:
        Contraction: Созданный объект сессии схваток
    """
    session = db_manager.get_session()
    try:
        contraction = Contraction(
            user_id=user_id,
            start_time=datetime.utcnow(),
            notes=notes
        )
        session.add(contraction)
        session.commit()
        session.refresh(contraction)
        return contraction
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def end_contraction_session(session_id):
    """
    Завершить сессию схваток.
    
    Аргументы:
        session_id (int): ID сессии схваток
        
    Возвращает:
        Contraction: Обновленный объект сессии схваток или None, если не найден
    """
    session = db_manager.get_session()
    try:
        contraction = session.query(Contraction).filter_by(id=session_id).first()
        if contraction:
            contraction.end_time = datetime.utcnow()
            session.commit()
            session.refresh(contraction)
        return contraction
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def add_contraction_event(session_id, duration=None, intensity=None):
    """
    Добавить событие схватки к сессии.
    
    Аргументы:
        session_id (int): ID сессии схваток
        duration (int, optional): Продолжительность схватки в секундах
        intensity (int, optional): Интенсивность схватки (1-10)
        
    Возвращает:
        ContractionEvent: Созданный объект события схватки
    """
    session = db_manager.get_session()
    try:
        event = ContractionEvent(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            duration=duration,
            intensity=intensity
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


# Вспомогательные функции для работы с моделью Kick
def get_kick_sessions(user_id):
    """
    Получить все сессии шевелений для конкретного пользователя.
    
    Аргументы:
        user_id (int): ID пользователя
        
    Возвращает:
        list: Список объектов Kick
    """
    session = db_manager.get_session()
    try:
        kicks = session.query(Kick).filter_by(user_id=user_id).order_by(Kick.start_time.desc()).all()
        return kicks
    finally:
        db_manager.close_session(session)


def create_kick_session(user_id, notes=None):
    """
    Создать новую сессию шевелений.
    
    Аргументы:
        user_id (int): ID пользователя
        notes (str, optional): Заметки к сессии
        
    Возвращает:
        Kick: Созданный объект сессии шевелений
    """
    session = db_manager.get_session()
    try:
        kick = Kick(
            user_id=user_id,
            start_time=datetime.utcnow(),
            notes=notes
        )
        session.add(kick)
        session.commit()
        session.refresh(kick)
        return kick
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def end_kick_session(session_id):
    """
    Завершить сессию шевелений.
    
    Аргументы:
        session_id (int): ID сессии шевелений
        
    Возвращает:
        Kick: Обновленный объект сессии шевелений или None, если не найден
    """
    session = db_manager.get_session()
    try:
        kick = session.query(Kick).filter_by(id=session_id).first()
        if kick:
            kick.end_time = datetime.utcnow()
            session.commit()
            session.refresh(kick)
        return kick
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def add_kick_event(session_id, intensity=None):
    """
    Добавить событие шевеления к сессии.
    
    Аргументы:
        session_id (int): ID сессии шевелений
        intensity (int, optional): Интенсивность шевеления (1-10)
        
    Возвращает:
        KickEvent: Созданный объект события шевеления
    """
    session = db_manager.get_session()
    try:
        event = KickEvent(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            intensity=intensity
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


# Вспомогательные функции для работы с моделью SleepSession
def get_sleep_sessions(child_id):
    """
    Получить все сессии сна для конкретного ребенка.
    
    Аргументы:
        child_id (int): ID ребенка
        
    Возвращает:
        list: Список объектов SleepSession
    """
    session = db_manager.get_session()
    try:
        sleep_sessions = session.query(SleepSession).filter_by(child_id=child_id).order_by(SleepSession.start_time.desc()).all()
        return sleep_sessions
    finally:
        db_manager.close_session(session)


def create_sleep_session(child_id, type='day', quality=None, notes=None):
    """
    Создать новую сессию сна.
    
    Аргументы:
        child_id (int): ID ребенка
        type (str, optional): Тип сна ('day' или 'night')
        quality (int, optional): Качество сна (1-5)
        notes (str, optional): Заметки к сессии
        
    Возвращает:
        SleepSession: Созданный объект сессии сна
    """
    session = db_manager.get_session()
    try:
        sleep_session = SleepSession(
            child_id=child_id,
            start_time=datetime.utcnow(),
            type=type,
            quality=quality,
            notes=notes
        )
        session.add(sleep_session)
        session.commit()
        session.refresh(sleep_session)
        return sleep_session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def end_sleep_session(session_id, quality=None):
    """
    Завершить сессию сна.
    
    Аргументы:
        session_id (int): ID сессии сна
        quality (int, optional): Качество сна (1-5)
        
    Возвращает:
        SleepSession: Обновленный объект сессии сна или None, если не найден
    """
    session = db_manager.get_session()
    try:
        sleep_session = session.query(SleepSession).filter_by(id=session_id).first()
        if sleep_session:
            sleep_session.end_time = datetime.utcnow()
            if quality is not None:
                sleep_session.quality = quality
            session.commit()
            session.refresh(sleep_session)
        return sleep_session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


# Вспомогательные функции для работы с моделью FeedingSession
def get_feeding_sessions(child_id):
    """
    Получить все сессии кормления для конкретного ребенка.
    
    Аргументы:
        child_id (int): ID ребенка
        
    Возвращает:
        list: Список объектов FeedingSession
    """
    session = db_manager.get_session()
    try:
        feeding_sessions = session.query(FeedingSession).filter_by(child_id=child_id).order_by(FeedingSession.timestamp.desc()).all()
        return feeding_sessions
    finally:
        db_manager.close_session(session)


def create_feeding_session(child_id, type, amount=None, duration=None, breast=None, food_type=None, notes=None):
    """
    Создать новую сессию кормления.
    
    Аргументы:
        child_id (int): ID ребенка
        type (str): Тип кормления ('breast' или 'bottle')
        amount (float, optional): Количество в мл (для бутылочки)
        duration (int, optional): Продолжительность в минутах (для груди)
        breast (str, optional): Используемая грудь ('left', 'right', 'both')
        food_type (str, optional): Тип пищи/смеси
        notes (str, optional): Заметки к сессии
        
    Возвращает:
        FeedingSession: Созданный объект сессии кормления
    """
    session = db_manager.get_session()
    try:
        feeding_session = FeedingSession(
            child_id=child_id,
            timestamp=datetime.utcnow(),
            type=type,
            amount=amount,
            duration=duration,
            breast=breast,
            food_type=food_type,
            notes=notes
        )
        session.add(feeding_session)
        session.commit()
        session.refresh(feeding_session)
        return feeding_session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def update_feeding_session(session_id, **kwargs):
    """
    Обновить сессию кормления.
    
    Аргументы:
        session_id (int): ID сессии кормления
        **kwargs: Поля для обновления
        
    Возвращает:
        FeedingSession: Обновленный объект сессии кормления или None, если не найден
    """
    session = db_manager.get_session()
    try:
        feeding_session = session.query(FeedingSession).filter_by(id=session_id).first()
        if feeding_session:
            for key, value in kwargs.items():
                if hasattr(feeding_session, key):
                    setattr(feeding_session, key, value)
            session.commit()
            session.refresh(feeding_session)
        return feeding_session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)