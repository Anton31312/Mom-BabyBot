"""
SQLAlchemy middleware для интеграции с Django.

Этот middleware управляет сессиями SQLAlchemy на протяжении цикла запрос-ответ,
обеспечивая правильную обработку сессий и их очистку.
"""

import logging
import time
from django.conf import settings
from sqlalchemy.exc import SQLAlchemyError
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SQLAlchemySessionMiddleware:
    """
    Middleware to manage SQLAlchemy sessions for each request.
    
    This middleware:
    1. Creates a new SQLAlchemy session at the start of each request
    2. Makes the session available throughout the request
    3. Commits the session if the response is successful
    4. Rolls back the session if an exception occurs
    5. Closes the session at the end of the request
    6. Measures query performance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.session_factory = settings.SQLALCHEMY_SESSION_FACTORY
        
    def __call__(self, request):
        # Measure request start time
        request_start_time = time.time()
        
        # Create a new SQLAlchemy session for this request
        session = self.session_factory()
        
        # Store the session in the request object for access in views
        request.sqlalchemy_session = session
        
        # Store query count for this request
        request.query_count = 0
        request.query_time = 0
        
        try:
            # Process the request
            response = self.get_response(request)
            
            # If we get here without exception, commit the session
            if hasattr(session, 'dirty') and (session.dirty or session.new):
                session.commit()
                logger.debug("SQLAlchemy session committed successfully")
                
        except Exception as e:
            # If an exception occurred, rollback the session
            try:
                session.rollback()
                logger.warning(f"SQLAlchemy session rolled back due to exception: {e}")
            except SQLAlchemyError as rollback_error:
                logger.error(f"Error during session rollback: {rollback_error}")
            
            # Re-raise the original exception
            raise
            
        finally:
            # Always close the session
            try:
                session.close()
                logger.debug("SQLAlchemy session closed")
            except SQLAlchemyError as close_error:
                logger.error(f"Error closing SQLAlchemy session: {close_error}")
        
        # Calculate request processing time
        request_time = time.time() - request_start_time
        
        # Log request performance metrics
        if hasattr(request, 'query_count') and request.query_count > 0:
            logger.info(
                f"Request to {request.path} completed in {request_time:.4f}s "
                f"with {request.query_count} queries taking {request.query_time:.4f}s"
            )
            
            # Log slow requests
            if request_time > 1.0:  # More than 1 second
                logger.warning(
                    f"Slow request detected: {request.path} took {request_time:.4f}s "
                    f"with {request.query_count} queries"
                )
        
        return response


class SQLAlchemyHealthCheckMiddleware:
    """
    Middleware to check SQLAlchemy database connectivity.
    
    This middleware performs a simple database health check on each request
    to ensure the database connection is working properly.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.engine = settings.SQLALCHEMY_ENGINE
        
    def __call__(self, request):
        # Perform a simple health check
        try:
            # Test the connection with a simple query
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            logger.debug("SQLAlchemy database health check passed")
            
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy database health check failed: {e}")
            # You might want to return a 503 Service Unavailable response here
            # For now, we'll just log the error and continue
        
        response = self.get_response(request)
        return response


def get_sqlalchemy_session(request):
    """
    Utility function to get the SQLAlchemy session from the request.
    
    Args:
        request: Django request object
        
    Returns:
        SQLAlchemy session object
        
    Raises:
        AttributeError: If no session is found in the request
    """
    if not hasattr(request, 'sqlalchemy_session'):
        raise AttributeError(
            "No SQLAlchemy session found in request. "
            "Make sure SQLAlchemySessionMiddleware is enabled."
        )
    
    return request.sqlalchemy_session