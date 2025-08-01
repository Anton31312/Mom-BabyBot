from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class BotappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'botapp'
    
    def ready(self):
        """
        Initialize SQLAlchemy when Django app is ready.
        """
        try:
            import os
            from django.conf import settings
            
            # Проверяем, что мы не в процессе миграций или сборки статики
            import sys
            if any(cmd in sys.argv for cmd in ['migrate', 'collectstatic', 'makemigrations']):
                logger.info("Skipping SQLAlchemy initialization during Django management command")
                return
            
            # Импорт моделей для обеспечения их регистрации в SQLAlchemy
            from botapp.models import User
            from botapp.models_child import Child, Measurement
            
            # Инициализация SQLAlchemy только если база данных доступна
            from mom_baby_bot.sqlalchemy_utils import init_sqlalchemy
            init_sqlalchemy()
            logger.info("SQLAlchemy initialized for botapp")
        except Exception as e:
            logger.error(f"Failed to initialize SQLAlchemy for botapp: {e}")
            # Не вызываем исключение, чтобы предотвратить сбой запуска Django
            # В продакшене это нормально - SQLAlchemy инициализируется позже
