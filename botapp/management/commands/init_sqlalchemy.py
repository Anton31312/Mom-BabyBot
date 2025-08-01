"""
Django management command для инициализации SQLAlchemy
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Инициализация SQLAlchemy базы данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительная пересоздание таблиц',
        )

    def handle(self, *args, **options):
        self.stdout.write("Инициализация SQLAlchemy...")
        
        try:
            # Показываем информацию о базе данных
            database_url = os.getenv('DATABASE_URL', 'НЕ УСТАНОВЛЕНА')
            self.stdout.write(f"DATABASE_URL: {database_url[:50]}{'...' if len(database_url) > 50 else ''}")
            
            # Импортируем модели
            self.stdout.write("Импорт моделей...")
            from botapp.models import User, Base
            from botapp.models_child import Child, Measurement
            
            # Используем ленивую инициализацию из настроек
            self.stdout.write("Инициализация SQLAlchemy engine...")
            from django.conf import settings
            
            if hasattr(settings, 'get_sqlalchemy_engine'):
                engine = settings.get_sqlalchemy_engine()
            else:
                # Fallback для старых настроек
                from sqlalchemy import create_engine
                if database_url.startswith('postgresql'):
                    engine_options = {
                        'pool_pre_ping': True,
                        'pool_recycle': 300,
                        'pool_size': 5,
                        'max_overflow': 10,
                        'echo': False
                    }
                else:
                    engine_options = {
                        'pool_pre_ping': True,
                        'pool_recycle': 300,
                        'echo': False
                    }
                engine = create_engine(database_url, **engine_options)
            
            # Проверяем подключение
            self.stdout.write("Проверка подключения...")
            from sqlalchemy import text
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            self.stdout.write(self.style.SUCCESS("Подключение работает"))
            
            # Создаем/обновляем таблицы
            if options['force']:
                self.stdout.write("Удаление существующих таблиц...")
                Base.metadata.drop_all(engine)
            
            self.stdout.write("Создание таблиц...")
            Base.metadata.create_all(engine)
            
            # Обновляем глобальные настройки
            self.stdout.write("Обновление настроек...")
            from botapp.models_base import db_manager
            db_manager.engine = engine
            from sqlalchemy.orm import sessionmaker
            db_manager.Session = sessionmaker(bind=engine)
            
            # Обновляем настройки Django
            if hasattr(settings, 'get_sqlalchemy_session_factory'):
                # Принудительно пересоздаем session factory
                settings.SQLALCHEMY_SESSION_FACTORY = None
                settings.get_sqlalchemy_session_factory()
            
            self.stdout.write(self.style.SUCCESS("SQLAlchemy успешно инициализирована!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())
            raise