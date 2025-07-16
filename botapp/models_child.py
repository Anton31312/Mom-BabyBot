"""
Модели для профилей детей и измерений.

Этот модуль содержит SQLAlchemy модели для профилей детей и связанных измерений
для веб-интерфейса материнского ухода.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from botapp.models import Base, db_manager

class Child(Base):
    """
    Модель профиля ребенка.
    
    Эта модель представляет профиль ребенка с основной информацией и связями
    с измерениями и другими данными, относящимися к ребенку.
    """
    __tablename__ = 'children'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(64))
    birth_date = Column(DateTime)
    gender = Column(String(10))  # 'male', 'female', or 'other'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    measurements = relationship("Measurement", back_populates="child", cascade="all, delete-orphan")
    vaccines = relationship("ChildVaccine", back_populates="child", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Child {self.id}: {self.name}>'
    
    @property
    def age_in_months(self):
        """Рассчитывает возраст ребенка в месяцах на основе даты рождения."""
        if not self.birth_date:
            return None
        
        today = datetime.utcnow()
        age_in_days = (today - self.birth_date).days
        return age_in_days // 30  # Approximate months
    
    @property
    def age_display(self):
        """Возвращает удобочитаемую строку с возрастом."""
        if not self.birth_date:
            return "Возраст не указан"
        
        today = datetime.utcnow()
        delta = today - self.birth_date
        
        years = delta.days // 365
        months = (delta.days % 365) // 30
        
        if years > 0:
            if months > 0:
                return f"{years} {'год' if years == 1 else 'года' if 1 < years < 5 else 'лет'} {months} {'месяц' if months == 1 else 'месяца' if 1 < months < 5 else 'месяцев'}"
            return f"{years} {'год' if years == 1 else 'года' if 1 < years < 5 else 'лет'}"
        else:
            return f"{months} {'месяц' if months == 1 else 'месяца' if 1 < months < 5 else 'месяцев'}"


class Measurement(Base):
    """
    Модель измерений ребенка.
    
    Эта модель хранит измерения роста ребенка, включая рост, вес
    и окружность головы.
    """
    __tablename__ = 'measurements'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    height = Column(Float)  # in centimeters
    weight = Column(Float)  # in kilograms
    head_circumference = Column(Float)  # in centimeters
    notes = Column(String(255))
    
    # Relationships
    child = relationship("Child", back_populates="measurements")
    
    def __repr__(self):
        return f'<Measurement {self.id} for Child {self.child_id}>'


# Вспомогательные функции для работы с моделью Child
def get_child(child_id):
    """
    Получить ребенка по ID.
    
    Аргументы:
        child_id (int): ID ребенка для получения
        
    Возвращает:
        Child: Объект ребенка или None, если не найден
    """
    session = db_manager.get_session()
    try:
        child = session.query(Child).filter_by(id=child_id).first()
        return child
    finally:
        db_manager.close_session(session)


def get_children_by_user(user_id):
    """
    Получить всех детей для конкретного пользователя.
    
    Аргументы:
        user_id (int): ID пользователя
        
    Возвращает:
        list: Список объектов Child
    """
    session = db_manager.get_session()
    try:
        children = session.query(Child).filter_by(user_id=user_id).all()
        return children
    finally:
        db_manager.close_session(session)


def create_child(user_id, name=None, birth_date=None, gender=None):
    """
    Создать новый профиль ребенка.
    
    Аргументы:
        user_id (int): ID родителя-пользователя
        name (str, optional): Имя ребенка
        birth_date (datetime, optional): Дата рождения ребенка
        gender (str, optional): Пол ребенка ('male', 'female', или 'other')
        
    Возвращает:
        Child: Созданный объект ребенка
    """
    session = db_manager.get_session()
    try:
        child = Child(
            user_id=user_id,
            name=name,
            birth_date=birth_date,
            gender=gender
        )
        session.add(child)
        session.commit()
        session.refresh(child)
        return child
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def update_child(child_id, **kwargs):
    """
    Обновить профиль ребенка.
    
    Аргументы:
        child_id (int): ID ребенка для обновления
        **kwargs: Поля для обновления
        
    Возвращает:
        Child: Обновленный объект ребенка или None, если не найден
    """
    session = db_manager.get_session()
    try:
        child = session.query(Child).filter_by(id=child_id).first()
        if child:
            for key, value in kwargs.items():
                if hasattr(child, key):
                    setattr(child, key, value)
            child.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(child)
        return child
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def delete_child(child_id):
    """
    Удалить профиль ребенка.
    
    Аргументы:
        child_id (int): ID ребенка для удаления
        
    Возвращает:
        bool: True если удален, False если не найден
    """
    session = db_manager.get_session()
    try:
        child = session.query(Child).filter_by(id=child_id).first()
        if child:
            session.delete(child)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


# Вспомогательные функции для работы с моделью Measurement
def get_measurements(child_id):
    """
    Получить все измерения для конкретного ребенка.
    
    Аргументы:
        child_id (int): ID ребенка
        
    Возвращает:
        list: Список объектов Measurement
    """
    session = db_manager.get_session()
    try:
        measurements = session.query(Measurement).filter_by(child_id=child_id).order_by(Measurement.date.desc()).all()
        return measurements
    finally:
        db_manager.close_session(session)


def create_measurement(child_id, height=None, weight=None, head_circumference=None, date=None, notes=None):
    """
    Создать новое измерение для ребенка.
    
    Аргументы:
        child_id (int): ID ребенка
        height (float, optional): Рост в сантиметрах
        weight (float, optional): Вес в килограммах
        head_circumference (float, optional): Окружность головы в сантиметрах
        date (datetime, optional): Дата измерения, по умолчанию текущее время
        notes (str, optional): Дополнительные заметки
        
    Возвращает:
        Measurement: Созданный объект измерения
    """
    session = db_manager.get_session()
    try:
        measurement = Measurement(
            child_id=child_id,
            height=height,
            weight=weight,
            head_circumference=head_circumference,
            date=date or datetime.utcnow(),
            notes=notes
        )
        session.add(measurement)
        session.commit()
        session.refresh(measurement)
        return measurement
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def update_measurement(measurement_id, **kwargs):
    """
    Обновить измерение.
    
    Аргументы:
        measurement_id (int): ID измерения для обновления
        **kwargs: Поля для обновления
        
    Возвращает:
        Measurement: Обновленный объект измерения или None, если не найден
    """
    session = db_manager.get_session()
    try:
        measurement = session.query(Measurement).filter_by(id=measurement_id).first()
        if measurement:
            for key, value in kwargs.items():
                if hasattr(measurement, key):
                    setattr(measurement, key, value)
            session.commit()
            session.refresh(measurement)
        return measurement
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def delete_measurement(measurement_id):
    """
    Удалить измерение.
    
    Аргументы:
        measurement_id (int): ID измерения для удаления
        
    Возвращает:
        bool: True если удалено, False если не найдено
    """
    session = db_manager.get_session()
    try:
        measurement = session.query(Measurement).filter_by(id=measurement_id).first()
        if measurement:
            session.delete(measurement)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)