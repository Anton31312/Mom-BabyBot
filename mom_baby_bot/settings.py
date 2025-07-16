"""
Настройки Django для проекта mom_baby_bot.

Сгенерировано командой 'django-admin startproject' с использованием Django 5.2.4.

Для получения дополнительной информации об этом файле см.:
https://docs.djangoproject.com/en/5.2/topics/settings/

Полный список настроек и их значений см.:
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Создание путей внутри проекта: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Настройки для быстрого старта - не подходят для продакшена
# См. https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: держите секретный ключ в секрете в продакшене!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-064iw#8r5ybqa)e(7go1o*&t)udom@cg5uy_oj2x+6qria0qlm')

# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: не запускайте с включенной отладкой в продакшене!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = []

# Конфигурация Telegram бота
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_PATH = '/webhook'
WEBAPP_URL = os.getenv('WEBAPP_URL')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

# Конфигурация сервера
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))


# Определение приложений

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'botapp',
    'webapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # SQLAlchemy middleware для управления сессиями
    'mom_baby_bot.middleware.SQLAlchemySessionMiddleware',
]

ROOT_URLCONF = 'mom_baby_bot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mom_baby_bot.wsgi.application'


# База данных
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Валидация паролей
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Интернационализация
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Статические файлы (CSS, JavaScript, изображения)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Тип первичного ключа по умолчанию
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Конфигурация SQLAlchemy
# Позволяет использовать SQLAlchemy вместе с Django
SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///mom_baby_bot.db')

# Настройки для различных типов баз данных
if SQLALCHEMY_DATABASE_URL.startswith('sqlite'):
    # Настройки для SQLite
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': DEBUG,
        'connect_args': {
            'check_same_thread': False,  # Для SQLite в многопоточной среде
            'timeout': 20,  # Таймаут подключения
        }
    }
elif SQLALCHEMY_DATABASE_URL.startswith('postgresql'):
    # Настройки для PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
        'echo': DEBUG,
    }
elif SQLALCHEMY_DATABASE_URL.startswith('mysql'):
    # Настройки для MySQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
        'echo': DEBUG,
        'connect_args': {
            'charset': 'utf8mb4',
        }
    }
else:
    # Базовые настройки для других БД
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': DEBUG,
    }

# Создание SQLAlchemy engine с настройками
SQLALCHEMY_ENGINE = create_engine(
    SQLALCHEMY_DATABASE_URL,
    **SQLALCHEMY_ENGINE_OPTIONS
)

# Создание фабрики сессий SQLAlchemy
SQLALCHEMY_SESSION_FACTORY = sessionmaker(
    bind=SQLALCHEMY_ENGINE,
    autocommit=False,
    autoflush=True,
    expire_on_commit=False  # Предотвращает истечение объектов после коммита
)

# Конфигурация сессий SQLAlchemy
SQLALCHEMY_SESSION_OPTIONS = {
    'autocommit': False,
    'autoflush': True,
    'expire_on_commit': False,
    'bind': SQLALCHEMY_ENGINE
}

# Настройки для миграций SQLAlchemy
SQLALCHEMY_MIGRATION_OPTIONS = {
    'compare_type': True,
    'compare_server_default': True,
    'render_as_batch': True,  # Для SQLite
}

# Убедиться, что директория logs существует
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Конфигурация логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

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
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'sqlalchemy.engine': {
            'handlers': ['console'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
        'bot': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}
