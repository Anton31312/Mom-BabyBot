from django.contrib import admin
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.shortcuts import render
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.html import format_html
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, not_
from .models import User, db_manager
from .admin_utils import (
    SQLAlchemyModelForm, SQLAlchemyAdminView, UserAdmin, UserAdminForm,
    get_admin_stats, with_session
)


# Инициализация админ-представлений с улучшенными настройками
user_admin = UserAdmin(User, UserAdminForm)

# Функции представлений для админки SQLAlchemy моделей с улучшенной интеграцией
def user_changelist_view(request):
    """Представление списка пользователей с улучшенной фильтрацией и поиском"""
    return user_admin.changelist_view(request)


def user_add_view(request):
    """Представление добавления пользователя с расширенной валидацией форм"""
    return user_admin.add_view(request)


def user_change_view(request, object_id):
    """Представление изменения пользователя с расширенной валидацией форм"""
    return user_admin.change_view(request, object_id)


def user_delete_view(request, object_id):
    """Представление удаления пользователя с подтверждением"""
    return user_admin.delete_view(request, object_id)


@with_session
def admin_index_view(request, session=None):
    """Главная страница админки с оптимизированной статистикой и графиками"""
    # Получение статистики с оптимизированными запросами
    stats = get_admin_stats(session)
    
    # Получение дополнительной статистики для графиков
    # Регистрации по дням за последний месяц
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    registrations_by_day = session.query(
        func.date(User.created_at).label('date'),
        func.count().label('count')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by(
        func.date(User.created_at)
    ).all()
    
    # Преобразуем результаты в формат для графика
    registration_dates = [str(r[0]) for r in registrations_by_day]
    registration_counts = [r[1] for r in registrations_by_day]
    
    # Распределение пользователей по неделям беременности
    pregnancy_weeks = session.query(
        User.pregnancy_week,
        func.count().label('count')
    ).filter(
        User.is_pregnant == True,
        User.pregnancy_week != None
    ).group_by(
        User.pregnancy_week
    ).order_by(
        User.pregnancy_week
    ).all()
    
    # Преобразуем результаты в формат для графика
    pregnancy_week_labels = [f"Неделя {r[0]}" for r in pregnancy_weeks]
    pregnancy_week_counts = [r[1] for r in pregnancy_weeks]
    
    context = {
        'title': 'Администрирование сайта',
        'site_title': 'Mom&Baby Bot Admin',
        'site_header': 'Mom&Baby Bot Админ-панель',
        'total_users': stats['total_users'],
        'pregnant_users': stats['pregnant_users'],
        'premium_users': stats['premium_users'],
        'admin_users': stats['admin_users'],
        'recent_users': stats['recent_users'],
        'sqlalchemy_models': [
            {
                'name': 'Пользователи',
                'url': reverse('admin:user_changelist'),
                'count': stats['total_users'],
            }
        ],
        # Данные для графиков
        'registration_dates': registration_dates,
        'registration_counts': registration_counts,
        'pregnancy_week_labels': pregnancy_week_labels,
        'pregnancy_week_counts': pregnancy_week_counts,
        # Дополнительная статистика
        'active_users_today': stats.get('active_users_today', 0),
        'active_users_week': stats.get('active_users_week', 0),
    }
    
    return render(request, 'admin/index.html', context)


# API для получения данных для графиков и диаграмм
@with_session
def admin_api_stats(request, session=None):
    """API для получения статистики в формате JSON для интерактивных графиков"""
    stats_type = request.GET.get('type', 'registrations')
    
    if stats_type == 'registrations':
        # Регистрации по дням за последний месяц
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        registrations_by_day = session.query(
            func.date(User.created_at).label('date'),
            func.count().label('count')
        ).filter(
            User.created_at >= thirty_days_ago
        ).group_by(
            func.date(User.created_at)
        ).all()
        
        data = {
            'labels': [str(r[0]) for r in registrations_by_day],
            'data': [r[1] for r in registrations_by_day],
            'title': 'Регистрации пользователей за последние 30 дней'
        }
    elif stats_type == 'pregnancy_weeks':
        # Распределение пользователей по неделям беременности
        pregnancy_weeks = session.query(
            User.pregnancy_week,
            func.count().label('count')
        ).filter(
            User.is_pregnant == True,
            User.pregnancy_week != None
        ).group_by(
            User.pregnancy_week
        ).order_by(
            User.pregnancy_week
        ).all()
        
        data = {
            'labels': [f"Неделя {r[0]}" for r in pregnancy_weeks],
            'data': [r[1] for r in pregnancy_weeks],
            'title': 'Распределение пользователей по неделям беременности'
        }
    else:
        data = {'error': 'Неизвестный тип статистики'}
    
    return JsonResponse(data)


# Настройка стандартной Django админки с улучшенным интерфейсом
admin.site.site_header = 'Mom&Baby Bot Админ-панель'
admin.site.site_title = 'Mom&Baby Bot Admin'
admin.site.index_title = 'Управление ботом'

# Регистрация URL для SQLAlchemy моделей в админке
admin_urls = [
    path('', admin_index_view, name='index'),
    path('botapp/user/', user_changelist_view, name='user_changelist'),
    path('botapp/user/add/', user_add_view, name='user_add'),
    path('botapp/user/<int:object_id>/', user_change_view, name='user_change'),
    path('botapp/user/<int:object_id>/delete/', user_delete_view, name='user_delete'),
    path('api/stats/', admin_api_stats, name='admin_api_stats'),
]

# Добавление URL в urlpatterns Django админки
admin.site.get_urls = lambda: admin.site.get_urls() + admin_urls
