"""
Утилитарные функции для работы с базой данных.

Этот модуль содержит функции для работы с базой данных, транзакциями и сессиями.
"""

import logging

logger = logging.getLogger(__name__)

def get_db_manager():
    """
    Получает экземпляр db_manager с использованием отложенного импорта.
    
    Returns:
        object: Экземпляр db_manager из botapp.models.
    """
    from botapp.models_base import db_manager
    
    # Инициализируем db_manager если не инициализирован
    if db_manager.engine is None:
        import os
        database_url = os.getenv('DATABASE_URL')
        db_manager.setup_engine(database_url)
    
    return db_manager

def with_db_session(func):
    """
    Декоратор для автоматического управления сессией базы данных.
    
    Args:
        func: Функция для выполнения с сессией.
        
    Returns:
        function: Обернутая функция с автоматическим управлением сессией.
    """
    def wrapper(*args, **kwargs):
        db_manager = get_db_manager()
        session = db_manager.get_session()
        try:
            kwargs['session'] = session
            result = func(*args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при выполнении операции с базой данных: {str(e)}")
            raise
        finally:
            db_manager.close_session(session)
    return wrapper


def safe_get_object(session, model_class, object_id, error_message=None):
    """
    Безопасно получает объект из базы данных по ID.
    
    Args:
        session: Сессия базы данных.
        model_class: Класс модели.
        object_id: ID объекта.
        error_message (str, optional): Сообщение об ошибке при отсутствии объекта.
        
    Returns:
        tuple: (объект, ошибка), где объект - это найденный объект или None,
               а ошибка - это строка с сообщением об ошибке или None, если объект найден.
    """
    try:
        obj = session.query(model_class).filter_by(id=object_id).first()
        if not obj and error_message:
            return None, error_message
        return obj, None
    except Exception as e:
        logger.error(f"Ошибка при получении объекта {model_class.__name__} с ID {object_id}: {str(e)}")
        return None, f"Ошибка при получении объекта: {str(e)}"