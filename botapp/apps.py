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
            from mom_baby_bot.sqlalchemy_utils import init_sqlalchemy
            init_sqlalchemy()
            logger.info("SQLAlchemy initialized for botapp")
        except Exception as e:
            logger.error(f"Failed to initialize SQLAlchemy for botapp: {e}")
            # Don't raise the exception to prevent Django from failing to start
            # In production, you might want to handle this differently
