import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

class Config:
    """Конфигурация приложения"""
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Webhook
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    WEBHOOK_PATH = '/webhook'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL')
    
    # URL веб-приложения
    WEBAPP_URL = os.getenv('WEBAPP_URL')
    
    # Список администраторов (ID пользователей Telegram)
    ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
    
    @classmethod
    def init_app(cls, app):
        """Инициализация приложения с конфигурацией"""
        app.config.from_object(cls) 