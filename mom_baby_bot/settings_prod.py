"""
Production settings for mom_baby_bot project.
"""

import os
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allow all host headers that are configured in environment variables
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']  # Fallback для Amvera

# Security settings (адаптированы для Amvera)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# SSL настройки - включаем только если используется HTTPS
USE_HTTPS = os.getenv('USE_HTTPS', 'True').lower() == 'true'
if USE_HTTPS:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Cache settings - используем локальный кэш вместо Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'mom-baby-bot-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Cache timeout settings
CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours

# Session cache - используем базу данных для сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Database settings - используем SQLite для production
import os

# Создаем директорию для базы данных если не существует
# Используем переменную окружения если она установлена
DB_PATH = os.getenv('DATABASE_PATH', '/app/data/mom_baby_bot.db')
DB_DIR = os.path.dirname(DB_PATH)

# Создаем директорию если не существует
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR, exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DB_PATH,
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# SQLAlchemy настройки для production с SQLite
SQLALCHEMY_DATABASE_URL = f'sqlite:///{DB_PATH}'

# Настройки SQLAlchemy engine для SQLite
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'echo': False,  # Отключаем в production
    'connect_args': {
        'check_same_thread': False,  # Для SQLite в многопоточной среде
        'timeout': 20,  # Таймаут подключения
    }
}

# SQLAlchemy engine и session factory будут созданы позже
SQLALCHEMY_ENGINE = None
SQLALCHEMY_SESSION_FACTORY = None

def get_sqlalchemy_engine():
    """Ленивое создание SQLAlchemy engine для production"""
    global SQLALCHEMY_ENGINE, SQLALCHEMY_DATABASE_URL
    if SQLALCHEMY_ENGINE is None:
        from sqlalchemy import create_engine
        
        # Для SQLite создаем файл базы данных если не существует
        if SQLALCHEMY_DATABASE_URL.startswith('sqlite'):
            import os
            import sqlite3
            db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '').replace('sqlite://', '')
            db_dir = os.path.dirname(db_path)
            
            # Создаем директорию если не существует
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                print(f"Created database directory: {db_dir}")
            
            # Создаем файл базы данных если не существует
            if not os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    conn.close()
                    print(f"Created SQLite database file: {db_path}")
                except Exception as e:
                    print(f"Error creating SQLite database: {e}")
                    # Попробуем создать в текущей директории как fallback
                    fallback_path = os.path.join(os.getcwd(), 'mom_baby_bot.db')
                    print(f"Trying fallback path: {fallback_path}")
                    conn = sqlite3.connect(fallback_path)
                    conn.close()
                    # Обновляем URL для fallback
                    SQLALCHEMY_DATABASE_URL = f'sqlite:///{fallback_path}'
        
        SQLALCHEMY_ENGINE = create_engine(
            SQLALCHEMY_DATABASE_URL,
            **SQLALCHEMY_ENGINE_OPTIONS
        )
    return SQLALCHEMY_ENGINE

def get_sqlalchemy_session_factory():
    """Ленивое создание SQLAlchemy session factory для production"""
    global SQLALCHEMY_SESSION_FACTORY
    if SQLALCHEMY_SESSION_FACTORY is None:
        from sqlalchemy.orm import sessionmaker
        SQLALCHEMY_SESSION_FACTORY = sessionmaker(
            bind=get_sqlalchemy_engine(),
            autocommit=False,
            autoflush=True,
            expire_on_commit=False
        )
    return SQLALCHEMY_SESSION_FACTORY

# Logging settings for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
        'sqlalchemy.engine': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'bot': {
            'handlers': ['console', 'file'],
            'level': os.getenv('BOT_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
    },
}

# Middleware for production
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # SQLAlchemy middleware для управления сессиями
    'mom_baby_bot.middleware.SQLAlchemySessionMiddleware',
    # Middleware для кэширования
    'mom_baby_bot.cache_manager.CacheMiddleware',
]

# WhiteNoise configuration for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'