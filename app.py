#!/usr/bin/env python
"""
Точка входа для запуска Django приложения с Gunicorn на Amvera
"""
import os
import sys
import django
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Настройка переменных окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
os.environ.setdefault('PORT', '80')

# Инициализация Django
django.setup()

def init_database():
    """Инициализация базы данных"""
    try:
        # Проверяем готовность
        from check_amvera_ready import main as check_ready
        if check_ready() == 0:
            print("✅ Проверка готовности прошла успешно")
        else:
            print("⚠️ Проверка готовности показала проблемы")
        
        # Инициализируем базу данных
        from init_sqlite_amvera import main as init_db
        if init_db() == 0:
            print("✅ База данных инициализирована")
        else:
            print("⚠️ Проблемы с инициализацией базы данных")
            
    except Exception as e:
        print(f"⚠️ Ошибка инициализации: {e}")

def run_gunicorn():
    """Запуск Django приложения с Gunicorn"""
    try:
        from django.core.management import execute_from_command_line
        
        # Применяем миграции
        print("📊 Применение миграций...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        
        # Собираем статические файлы
        print("📁 Сбор статических файлов...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--clear'])
        
        # Импортируем WSGI приложение
        from mom_baby_bot.wsgi import application
        
        # Настройки Gunicorn
        port = int(os.getenv('PORT', '80'))
        workers = int(os.getenv('GUNICORN_WORKERS', '2'))
        timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))
        
        print(f"🚀 Запуск Gunicorn на порту {port} с {workers} workers...")
        
        # Запускаем Gunicorn
        import gunicorn.app.base
        
        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()
            
            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key.lower(), value)
            
            def load(self):
                return self.application
        
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': workers,
            'timeout': timeout,
            'worker_class': 'sync',
            'worker_connections': 1000,
            'max_requests': 1000,
            'max_requests_jitter': 100,
            'keepalive': 5,
            'preload_app': True,
            'access_logfile': '-',
            'error_logfile': '-',
            'loglevel': 'info',
        }
        
        StandaloneApplication(application, options).run()
        
    except Exception as e:
        print(f"❌ Ошибка запуска Gunicorn: {e}")
        sys.exit(1)

def main():
    """Главная функция"""
    print("🚀 Запуск Mom&Baby Bot с Gunicorn на Amvera...")
    
    # Инициализируем базу данных
    init_database()
    
    # Запускаем Gunicorn
    run_gunicorn()

if __name__ == '__main__':
    main() 