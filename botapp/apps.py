from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class BotappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'botapp'
    
    def ready(self):
        """
        Полностью отключена автоинициализация SQLAlchemy.
        SQLAlchemy инициализируется только вручную через management команды.
        """
        logger.info("BotappConfig ready - SQLAlchemy автоинициализация ПОЛНОСТЬЮ ОТКЛЮЧЕНА")
        # Никаких импортов или инициализации
