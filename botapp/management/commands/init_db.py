"""
Django management команда для инициализации базы данных SQLAlchemy.

Эта команда позволяет инициализировать базу данных SQLAlchemy через Django management интерфейс.
"""

import logging
from django.core.management.base import BaseCommand
from django.conf import settings
import init_db

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Инициализирует базу данных SQLAlchemy, создавая все необходимые таблицы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Создать таблицы без проверки их существования',
        )
        parser.add_argument(
            '--test-user',
            action='store_true',
            help='Создать тестового пользователя после инициализации',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Инициализация базы данных SQLAlchemy...'))
        
        # Инициализация базы данных
        success = init_db.init_database(check_first=not options['force'])
        
        if success:
            self.stdout.write(self.style.SUCCESS('База данных успешно инициализирована!'))
            
            # Создание тестового пользователя, если указан флаг
            if options['test_user'] or (settings.DEBUG and not options['force']):
                self.stdout.write(self.style.NOTICE('Создание тестового пользователя...'))
                init_db.create_test_user()
                self.stdout.write(self.style.SUCCESS('Тестовый пользователь создан!'))
        else:
            self.stdout.write(self.style.ERROR('Ошибка при инициализации базы данных!'))
            return 1
        
        return 0