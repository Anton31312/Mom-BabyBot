#!/usr/bin/env python
"""
Точка входа для запуска Django приложения, бота и веб-приложения на Amvera
"""
import os
import sys
import django
import multiprocessing
import time
import signal
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
    """Запуск Django веб-приложения с Gunicorn"""
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
        
        print(f"🌐 Запуск веб-приложения на порту {port} с {workers} workers...")
        
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
            'accesslog': '-',
            'errorlog': '-',
            'loglevel': 'info',
        }
        
        StandaloneApplication(application, options).run()
        
    except Exception as e:
        print(f"❌ Ошибка запуска веб-приложения: {e}")
        sys.exit(1)

def run_bot():
    """Запуск Telegram бота"""
    try:
        print("🤖 Запуск Telegram бота...")
        
        # Импортируем и запускаем бота
        from botapp.management.commands.runbot import Command
        
        # Запускаем бота через management команду
        Command.run_bot()
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        # Не выходим из процесса, так как веб-приложение может работать


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print(f"\n🛑 Получен сигнал {signum}, завершение работы...")
    sys.exit(0)

def main():
    """Главная функция с многопроцессным запуском"""
    print("🚀 Запуск Mom&Baby Bot на Amvera...")
    
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Инициализируем базу данных
    init_database()
    

    # Все компоненты (для разработки)
    print("🚀 Запуск всех компонентов...")
        
    # Создаем процессы
    processes = []
        
    # Процесс для веб-приложения
    web_process = multiprocessing.Process(target=run_gunicorn, name="WebApp")
    web_process.start()
    processes.append(web_process)
    print("✅ Веб-приложение запущено")
        
    # Небольшая задержка
    time.sleep(2)
        
    # Процесс для бота
    bot_process = multiprocessing.Process(target=run_bot, name="Bot")
    bot_process.start()
    processes.append(bot_process)
    print("✅ Бот запущен")
        
    # Ждем завершения процессов
    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал прерывания, завершение процессов...")
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
        print("✅ Все процессы завершены")

if __name__ == '__main__':
    main() 