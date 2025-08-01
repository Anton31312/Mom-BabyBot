#!/usr/bin/env python
"""
Скрипт для полного отключения автоинициализации SQLAlchemy
"""
import os
import sys

def patch_apps_py():
    """Патчим apps.py чтобы полностью отключить SQLAlchemy"""
    apps_file = 'botapp/apps.py'
    
    try:
        with open(apps_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем содержимое ready() метода
        new_ready_method = '''    def ready(self):
        """
        Полностью отключена автоинициализация SQLAlchemy.
        SQLAlchemy инициализируется только вручную.
        """
        logger.info("BotappConfig ready - SQLAlchemy автоинициализация ПОЛНОСТЬЮ ОТКЛЮЧЕНА")
        # Никаких импортов моделей или инициализации SQLAlchemy'''
        
        # Находим и заменяем метод ready
        import re
        pattern = r'def ready\(self\):.*?(?=\n    def|\n\nclass|\Z)'
        
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, new_ready_method, content, flags=re.DOTALL)
            
            with open(apps_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Патч применен к {apps_file}")
            return True
        else:
            print(f"⚠️ Не найден метод ready() в {apps_file}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка патчинга {apps_file}: {e}")
        return False

def create_minimal_apps_py():
    """Создаем минимальный apps.py"""
    apps_content = '''from django.apps import AppConfig
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
'''
    
    try:
        with open('botapp/apps.py', 'w', encoding='utf-8') as f:
            f.write(apps_content)
        
        print("✅ Создан минимальный apps.py")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания apps.py: {e}")
        return False

def main():
    print("🔧 Отключение автоинициализации SQLAlchemy\n")
    
    if create_minimal_apps_py():
        print("🎉 SQLAlchemy автоинициализация полностью отключена!")
        return 0
    else:
        print("❌ Не удалось отключить автоинициализацию")
        return 1

if __name__ == "__main__":
    sys.exit(main())