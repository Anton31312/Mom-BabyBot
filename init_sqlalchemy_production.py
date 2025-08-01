#!/usr/bin/env python
"""
Скрипт для принудительной инициализации SQLAlchemy в production
"""
import os
import sys
import django
from django.conf import settings

def main():
    """Инициализация SQLAlchemy для production"""
    
    # Настройка Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings_prod')
    django.setup()
    
    print("🔧 Инициализация SQLAlchemy для production...")
    
    try:
        # Показываем какую базу данных используем
        database_url = os.getenv('DATABASE_URL', 'НЕ УСТАНОВЛЕНА')
        print(f"📊 DATABASE_URL: {database_url[:50]}{'...' if len(database_url) > 50 else ''}")
        
        # Импортируем модели
        print("📦 Импорт моделей...")
        from botapp.models import User, Base
        from botapp.models_child import Child, Measurement
        
        # Создаем engine с правильными настройками
        print("🔗 Создание SQLAlchemy engine...")
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
        print("🔍 Проверка подключения к базе данных...")
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Подключение к базе данных работает")
        
        # Создаем таблицы
        print("🏗️ Создание таблиц...")
        Base.metadata.create_all(engine)
        print("✅ Таблицы созданы успешно")
        
        # Обновляем глобальные настройки
        print("⚙️ Обновление глобальных настроек...")
        from botapp.models_base import db_manager
        db_manager.engine = engine
        from sqlalchemy.orm import sessionmaker
        db_manager.Session = sessionmaker(bind=engine)
        
        print("🎉 SQLAlchemy успешно инициализирована для production!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации SQLAlchemy: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)