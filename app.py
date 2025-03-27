from flask import Flask
from app.database import db
from app.config import Config
from app.bot import run_bot, stop_bot
import logging
import atexit
import signal
import sys

# Настройка логирования
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Создание и конфигурация Flask приложения"""
    app = Flask(__name__)
    
    # Инициализация конфигурации
    Config.init_app(app)
    
    # Инициализация базы данных
    db.init_app(app)
    
    # Создание таблиц базы данных
    with app.app_context():
        db.create_all()
    
    return app

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info(f"Получен сигнал {signum}")
    stop_bot()
    sys.exit(0)

if __name__ == '__main__':
    try:
        app = create_app()
        
        # Регистрация обработчиков сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Запуск бота в отдельном потоке
        bot_thread = run_bot(app)
        
        # Регистрация функции остановки бота при завершении приложения
        atexit.register(stop_bot)
        
        # Запуск Flask приложения
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            use_reloader=False  # Отключаем автоперезагрузку в режиме отладки
        )
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения работы")
        stop_bot()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        stop_bot()
        raise 