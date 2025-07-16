"""
Модели для календаря прививок.

Этот модуль содержит SQLAlchemy модели для календаря прививок, включая
модели Vaccine и ChildVaccine для веб-интерфейса материнского ухода.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from botapp.models import Base, db_manager


class Vaccine(Base):
    """
    Модель вакцины.

    Эта модель представляет информацию о вакцине, включая название, описание,
    рекомендуемый возраст и обязательность.
    """
    __tablename__ = 'vaccines'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    recommended_age = Column(String(64))  # например, "2 месяца", "1 год"
    is_mandatory = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    child_vaccines = relationship(
        "ChildVaccine", back_populates="vaccine", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Vaccine {self.id}: {self.name}>'


class ChildVaccine(Base):
    """
    Модель связи ребенка и вакцины.

    Эта модель представляет информацию о сделанной или запланированной прививке
    для конкретного ребенка.
    """
    __tablename__ = 'child_vaccines'

    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    vaccine_id = Column(Integer, ForeignKey('vaccines.id'), nullable=False)
    date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    notes = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    child = relationship("Child", back_populates="vaccines")
    vaccine = relationship("Vaccine", back_populates="child_vaccines")

    def __repr__(self):
        status = "Выполнена" if self.is_completed else "Запланирована"
        return f'<ChildVaccine {self.id}: {status} для ребенка {self.child_id}>'


# Вспомогательные функции для работы с моделью Vaccine
def get_all_vaccines():
    """
    Получить список всех вакцин.

    Возвращает:
        list: Список объектов Vaccine
    """
    session = db_manager.get_session()
    try:
        vaccines = session.query(Vaccine).all()
        return vaccines
    finally:
        db_manager.close_session(session)


def get_vaccine(vaccine_id):
    """
    Получить вакцину по ID.

    Аргументы:
        vaccine_id (int): ID вакцины

    Возвращает:
        Vaccine: Объект вакцины или None, если не найден
    """
    session = db_manager.get_session()
    try:
        vaccine = session.query(Vaccine).filter_by(id=vaccine_id).first()
        return vaccine
    finally:
        db_manager.close_session(session)


def create_vaccine(name, description=None, recommended_age=None, is_mandatory=False):
    """
    Создать новую вакцину.

    Аргументы:
        name (str): Название вакцины
        description (str, optional): Описание вакцины
        recommended_age (str, optional): Рекомендуемый возраст
        is_mandatory (bool, optional): Является ли вакцина обязательной

    Возвращает:
        Vaccine: Созданный объект вакцины
    """
    session = db_manager.get_session()
    try:
        vaccine = Vaccine(
            name=name,
            description=description,
            recommended_age=recommended_age,
            is_mandatory=is_mandatory
        )
        session.add(vaccine)
        session.commit()
        session.refresh(vaccine)
        return vaccine
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def update_vaccine(vaccine_id, **kwargs):
    """
    Обновить информацию о вакцине.

    Аргументы:
        vaccine_id (int): ID вакцины для обновления
        **kwargs: Поля для обновления

    Возвращает:
        Vaccine: Обновленный объект вакцины или None, если не найден
    """
    session = db_manager.get_session()
    try:
        vaccine = session.query(Vaccine).filter_by(id=vaccine_id).first()
        if vaccine:
            for key, value in kwargs.items():
                if hasattr(vaccine, key):
                    setattr(vaccine, key, value)
            vaccine.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(vaccine)
        return vaccine
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def delete_vaccine(vaccine_id):
    """
    Удалить вакцину.

    Аргументы:
        vaccine_id (int): ID вакцины для удаления

    Возвращает:
        bool: True если удалена, False если не найдена
    """
    session = db_manager.get_session()
    try:
        vaccine = session.query(Vaccine).filter_by(id=vaccine_id).first()
        if vaccine:
            session.delete(vaccine)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


# Вспомогательные функции для работы с моделью ChildVaccine
def get_child_vaccines(child_id):
    """
    Получить все прививки для конкретного ребенка.

    Аргументы:
        child_id (int): ID ребенка

    Возвращает:
        list: Список объектов ChildVaccine
    """
    session = db_manager.get_session()
    try:
        child_vaccines = session.query(
            ChildVaccine).filter_by(child_id=child_id).all()
        return child_vaccines
    finally:
        db_manager.close_session(session)


def get_child_vaccine(child_vaccine_id):
    """
    Получить запись о прививке по ID.

    Аргументы:
        child_vaccine_id (int): ID записи о прививке

    Возвращает:
        ChildVaccine: Объект записи о прививке или None, если не найден
    """
    session = db_manager.get_session()
    try:
        child_vaccine = session.query(ChildVaccine).filter_by(
            id=child_vaccine_id).first()
        return child_vaccine
    finally:
        db_manager.close_session(session)


def create_child_vaccine(child_id, vaccine_id, date=None, is_completed=False, notes=None):
    """
    Создать новую запись о прививке для ребенка.

    Аргументы:
        child_id (int): ID ребенка
        vaccine_id (int): ID вакцины
        date (datetime, optional): Дата прививки
        is_completed (bool, optional): Выполнена ли прививка
        notes (str, optional): Дополнительные заметки

    Возвращает:
        ChildVaccine: Созданный объект записи о прививке
    """
    session = db_manager.get_session()
    try:
        child_vaccine = ChildVaccine(
            child_id=child_id,
            vaccine_id=vaccine_id,
            date=date,
            is_completed=is_completed,
            notes=notes
        )
        session.add(child_vaccine)
        session.commit()
        session.refresh(child_vaccine)
        return child_vaccine
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def update_child_vaccine(child_vaccine_id, **kwargs):
    """
    Обновить запись о прививке.

    Аргументы:
        child_vaccine_id (int): ID записи о прививке для обновления
        **kwargs: Поля для обновления

    Возвращает:
        ChildVaccine: Обновленный объект записи о прививке или None, если не найден
    """
    session = db_manager.get_session()
    try:
        child_vaccine = session.query(ChildVaccine).filter_by(
            id=child_vaccine_id).first()
        if child_vaccine:
            for key, value in kwargs.items():
                if hasattr(child_vaccine, key):
                    setattr(child_vaccine, key, value)
            child_vaccine.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(child_vaccine)
        return child_vaccine
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def delete_child_vaccine(child_vaccine_id):
    """
    Удалить запись о прививке.

    Аргументы:
        child_vaccine_id (int): ID записи о прививке для удаления

    Возвращает:
        bool: True если удалена, False если не найдена
    """
    session = db_manager.get_session()
    try:
        child_vaccine = session.query(ChildVaccine).filter_by(
            id=child_vaccine_id).first()
        if child_vaccine:
            session.delete(child_vaccine)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def mark_vaccine_completed(child_vaccine_id, date=None, notes=None):
    """
    Отметить прививку как выполненную.

    Аргументы:
        child_vaccine_id (int): ID записи о прививке
        date (datetime, optional): Дата выполнения прививки
        notes (str, optional): Дополнительные заметки

    Возвращает:
        ChildVaccine: Обновленный объект записи о прививке или None, если не найден
    """
    session = db_manager.get_session()
    try:
        child_vaccine = session.query(ChildVaccine).filter_by(
            id=child_vaccine_id).first()
        if child_vaccine:
            child_vaccine.is_completed = True
            if date:
                child_vaccine.date = date
            else:
                child_vaccine.date = datetime.utcnow()
            if notes:
                child_vaccine.notes = notes
            child_vaccine.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(child_vaccine)
        return child_vaccine
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


def get_upcoming_vaccines(child_id):
    """
    Получить список предстоящих прививок для ребенка.

    Аргументы:
        child_id (int): ID ребенка

    Возвращает:
        list: Список объектов ChildVaccine, которые не отмечены как выполненные
    """
    session = db_manager.get_session()
    try:
        upcoming_vaccines = session.query(ChildVaccine).filter_by(
            child_id=child_id, is_completed=False
        ).all()
        return upcoming_vaccines
    finally:
        db_manager.close_session(session)


def get_completed_vaccines(child_id):
    """
    Получить список выполненных прививок для ребенка.

    Аргументы:
        child_id (int): ID ребенка

    Возвращает:
        list: Список объектов ChildVaccine, которые отмечены как выполненные
    """
    session = db_manager.get_session()
    try:
        completed_vaccines = session.query(ChildVaccine).filter_by(
            child_id=child_id, is_completed=True
        ).all()
        return completed_vaccines
    finally:
        db_manager.close_session(session)
