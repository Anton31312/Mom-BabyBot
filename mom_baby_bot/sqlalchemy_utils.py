"""
SQLAlchemy utilities for Django integration.

This module provides utility functions and classes for working with SQLAlchemy
in a Django environment.
"""

import logging
from contextlib import contextmanager
from django.conf import settings
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


@contextmanager
def get_sqlalchemy_session():
    """
    Context manager for SQLAlchemy sessions.
    
    This provides a safe way to work with SQLAlchemy sessions outside of
    the request-response cycle (e.g., in management commands, background tasks).
    
    Usage:
        with get_sqlalchemy_session() as session:
            user = session.query(User).first()
            # ... do work with session
    """
    session = settings.SQLALCHEMY_SESSION_FACTORY()
    
    try:
        yield session
        session.commit()
        logger.debug("SQLAlchemy session committed successfully")
        
    except Exception as e:
        session.rollback()
        logger.warning(f"SQLAlchemy session rolled back due to exception: {e}")
        raise
        
    finally:
        session.close()
        logger.debug("SQLAlchemy session closed")


def create_tables():
    """
    Create all SQLAlchemy tables.
    
    This function creates all tables defined in SQLAlchemy models.
    Should be called during application initialization.
    """
    try:
        # Import all models to ensure they are registered
        from botapp.models import Base
        
        # Create all tables
        Base.metadata.create_all(bind=settings.SQLALCHEMY_ENGINE)
        logger.info("SQLAlchemy tables created successfully")
        
    except Exception as e:
        logger.error(f"Error creating SQLAlchemy tables: {e}")
        raise


def drop_tables():
    """
    Drop all SQLAlchemy tables.
    
    WARNING: This will delete all data in the database!
    Use with caution, typically only in development or testing.
    """
    try:
        # Import all models to ensure they are registered
        from botapp.models import Base
        
        # Drop all tables
        Base.metadata.drop_all(bind=settings.SQLALCHEMY_ENGINE)
        logger.warning("SQLAlchemy tables dropped")
        
    except Exception as e:
        logger.error(f"Error dropping SQLAlchemy tables: {e}")
        raise


def check_database_connection():
    """
    Check if the database connection is working.
    
    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        from sqlalchemy import text
        # Используем engine из настроек Django
        with settings.SQLALCHEMY_ENGINE.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection check passed")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database connection check failed: {e}")
        return False


class SQLAlchemyMixin:
    """
    Mixin class for Django views that need SQLAlchemy access.
    
    This mixin provides convenient access to SQLAlchemy sessions
    in Django class-based views.
    """
    
    def get_sqlalchemy_session(self):
        """
        Get the SQLAlchemy session from the request.
        
        Returns:
            SQLAlchemy session object
        """
        if not hasattr(self.request, 'sqlalchemy_session'):
            raise AttributeError(
                "No SQLAlchemy session found in request. "
                "Make sure SQLAlchemySessionMiddleware is enabled."
            )
        
        return self.request.sqlalchemy_session
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to ensure SQLAlchemy session is available.
        """
        if not hasattr(request, 'sqlalchemy_session'):
            logger.warning(
                "SQLAlchemy session not found in request. "
                "Make sure SQLAlchemySessionMiddleware is enabled."
            )
        
        return super().dispatch(request, *args, **kwargs)


def init_sqlalchemy():
    """
    Initialize SQLAlchemy for the Django application.
    
    This function should be called during Django application startup
    to ensure SQLAlchemy is properly configured.
    """
    try:
        # Check database connection
        if not check_database_connection():
            raise Exception("Database connection failed")
        
        # Create tables if they don't exist
        create_tables()
        
        logger.info("SQLAlchemy initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize SQLAlchemy: {e}")
        raise