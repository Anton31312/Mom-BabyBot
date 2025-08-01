from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class BotappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'botapp'
    
    def ready(self):
        """
        Отключаем автоматическую инициализацию SQLAlchemy.
        SQLAlchemy будет инициализироваться вручную через management команды.
        """
        logger.info("BotappConfig ready - SQLAlchemy автоинициализация отключена")
        
        # Импортируем модели для их регистрации, но не инициализируем SQLAlchemy
        try:
            from botapp.models import User
            from botapp.models_child import Child, Measurement
            logger.info("SQLAlchemy модели импортированы")
        except Exception as e:
            logger.warning(f"Не удалось импортировать SQLAlchemy модели: {e}")
