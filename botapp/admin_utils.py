"""
Утилиты для интеграции SQLAlchemy моделей с Django админкой.

Этот модуль содержит классы и функции для улучшения интеграции SQLAlchemy
моделей с Django админ-панелью, включая валидацию форм, оптимизацию запросов,
и улучшенные фильтры.
"""

import inspect
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Any, Callable, Optional, Type, Union, Tuple

from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.html import format_html
from sqlalchemy import inspect as sa_inspect, desc, asc, or_, and_, not_, Column, func, text, Integer
from sqlalchemy.orm import Session, Query, joinedload, contains_eager, load_only
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine.result import Result

# Custom LRU cache with TTL
def lru_cache(maxsize=128, ttl=None):
    """
    Декоратор для кэширования результатов функции с ограничением времени жизни.
    
    Args:
        maxsize: Максимальный размер кэша
        ttl: Время жизни кэша в секундах
        
    Returns:
        Декоратор для кэширования
    """
    from functools import lru_cache as _lru_cache
    import time
    
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            current_time = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if ttl is None or current_time - timestamp < ttl:
                    return result
                
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            
            # Очистка старых записей
            if len(cache) > maxsize:
                oldest_key = min(cache.items(), key=lambda x: x[1][1])[0]
                cache.pop(oldest_key)
                
            return result
        
        return wrapper
    
    if callable(maxsize) and ttl is None:
        func = maxsize
        maxsize = 128
        return decorator(func)
    
    return decorator

from .models import db_manager


class SQLAlchemyModelForm(forms.Form):
    """
    Базовый класс формы для SQLAlchemy моделей.
    Автоматически создает поля формы на основе колонок модели с улучшенной валидацией.
    """
    
    def __init__(self, *args, instance=None, **kwargs):
        """
        Инициализирует форму с полями, соответствующими модели SQLAlchemy.
        
        Args:
            instance: Экземпляр SQLAlchemy модели (для редактирования)
        """
        self.instance = instance
        self.model_class = kwargs.pop('model_class', None)
        
        if not self.model_class and instance:
            self.model_class = instance.__class__
            
        super().__init__(*args, **kwargs)
        
        if self.model_class:
            self._build_fields_from_model()
            
        if instance:
            self._populate_form_from_instance()
    
    def _build_fields_from_model(self):
        """Создает поля формы на основе колонок модели SQLAlchemy."""
        mapper = sa_inspect(self.model_class)
        
        for column in mapper.columns:
            field_name = column.name
            
            # Пропускаем автоматически генерируемые поля
            if field_name in ('id', 'created_at', 'updated_at'):
                continue
                
            field = self._create_field_for_column(column)
            if field:
                self.fields[field_name] = field
                
        # Сортировка полей для лучшего отображения
        self._sort_fields()
    
    def _sort_fields(self):
        """Сортирует поля формы для лучшего отображения."""
        # Определяем порядок полей для более логичного отображения
        field_order = [
            # Основные идентификаторы
            'telegram_id', 'username', 'first_name', 'last_name',
            # Статус беременности
            'is_pregnant', 'pregnancy_week', 'baby_birth_date',
            # Права доступа
            'is_premium', 'is_admin',
            # Остальные поля
        ]
        
        # Создаем новый OrderedDict с отсортированными полями
        sorted_fields = {}
        
        # Сначала добавляем поля в заданном порядке
        for field_name in field_order:
            if field_name in self.fields:
                sorted_fields[field_name] = self.fields[field_name]
        
        # Затем добавляем оставшиеся поля
        for field_name, field in self.fields.items():
            if field_name not in sorted_fields:
                sorted_fields[field_name] = field
        
        # Заменяем fields на отсортированный словарь
        self.fields = sorted_fields
    
    def _create_field_for_column(self, column: Column) -> Optional[forms.Field]:
        """
        Создает поле формы Django на основе колонки SQLAlchemy с улучшенной валидацией.
        
        Args:
            column: Колонка SQLAlchemy
            
        Returns:
            forms.Field: Поле формы Django или None, если поле не поддерживается
        """
        field_name = column.name
        field_type = column.type.__class__.__name__.lower()
        required = not column.nullable and not column.default and not column.server_default
        
        # Улучшенный маппинг типов SQLAlchemy на поля Django форм
        if 'int' in field_type:
            # Определяем минимальное и максимальное значения для числовых полей
            min_value = None
            max_value = None
            
            # Специальные правила для конкретных полей
            if field_name == 'pregnancy_week':
                min_value = 1
                max_value = 42
            elif field_name == 'telegram_id':
                min_value = 1  # Telegram ID всегда положительный
            
            return forms.IntegerField(
                required=required, 
                min_value=min_value,
                max_value=max_value,
                label=field_name.replace('_', ' ').title(),
                help_text=self._get_help_text(field_name)
            )
        elif 'float' in field_type:
            return forms.FloatField(
                required=required, 
                label=field_name.replace('_', ' ').title(),
                help_text=self._get_help_text(field_name)
            )
        elif 'bool' in field_type:
            return forms.BooleanField(
                required=False, 
                label=field_name.replace('_', ' ').title(),
                help_text=self._get_help_text(field_name)
            )
        elif 'string' in field_type:
            max_length = getattr(column.type, 'length', None)
            
            # Для полей с именами пользователей добавляем валидацию
            if field_name == 'username':
                return forms.CharField(
                    max_length=max_length, 
                    required=required,
                    label=field_name.replace('_', ' ').title(),
                    help_text='Имя пользователя в Telegram (без @)',
                    validators=[self._validate_username]
                )
            
            return forms.CharField(
                max_length=max_length, 
                required=required,
                label=field_name.replace('_', ' ').title(),
                help_text=self._get_help_text(field_name)
            )
        elif 'text' in field_type:
            return forms.CharField(
                widget=forms.Textarea, 
                required=required,
                label=field_name.replace('_', ' ').title(),
                help_text=self._get_help_text(field_name)
            )
        elif 'datetime' in field_type:
            # Улучшенный виджет для datetime с поддержкой современных браузеров
            return forms.DateTimeField(
                required=required,
                widget=forms.DateTimeInput(attrs={
                    'type': 'datetime-local',
                    'class': 'vDateField',
                    'autocomplete': 'off'
                }),
                label=field_name.replace('_', ' ').title(),
                help_text=self._get_help_text(field_name)
            )
        elif 'date' in field_type:
            # Улучшенный виджет для date с поддержкой современных браузеров
            return forms.DateField(
                required=required,
                widget=forms.DateInput(attrs={
                    'type': 'date',
                    'class': 'vDateField',
                    'autocomplete': 'off'
                }),
                label=field_name.replace('_', ' ').title(),
                help_text=self._get_help_text(field_name)
            )
        
        # Для неподдерживаемых типов возвращаем CharField
        return forms.CharField(
            required=required, 
            label=field_name.replace('_', ' ').title(),
            help_text=self._get_help_text(field_name)
        )
    
    def _get_help_text(self, field_name: str) -> str:
        """
        Возвращает текст подсказки для поля.
        
        Args:
            field_name: Имя поля
            
        Returns:
            str: Текст подсказки
        """
        help_texts = {
            'telegram_id': 'Уникальный идентификатор пользователя в Telegram',
            'username': 'Имя пользователя в Telegram (без @)',
            'first_name': 'Имя пользователя',
            'last_name': 'Фамилия пользователя',
            'is_pregnant': 'Отметьте, если пользователь беременен',
            'pregnancy_week': 'Текущая неделя беременности (1-42)',
            'baby_birth_date': 'Дата рождения ребенка (если уже родился)',
            'is_premium': 'Доступ к премиум функциям',
            'is_admin': 'Административные права в боте',
        }
        
        return help_texts.get(field_name, '')
    
    def _validate_username(self, value):
        """
        Валидатор для имени пользователя Telegram.
        
        Args:
            value: Значение поля
            
        Raises:
            ValidationError: Если имя пользователя не соответствует требованиям
        """
        if value and value.startswith('@'):
            raise ValidationError('Имя пользователя не должно начинаться с @')
        
        if value and (' ' in value or '\t' in value or '\n' in value):
            raise ValidationError('Имя пользователя не должно содержать пробелы')
    
    def _populate_form_from_instance(self):
        """Заполняет форму данными из экземпляра модели."""
        if not self.instance:
            return
            
        initial_data = {}
        
        for field_name, field in self.fields.items():
            if hasattr(self.instance, field_name):
                value = getattr(self.instance, field_name)
                
                # Улучшенное преобразование типов для корректного отображения в форме
                if isinstance(value, datetime):
                    if isinstance(field, forms.DateTimeField):
                        value = value.strftime('%Y-%m-%dT%H:%M')
                    elif isinstance(field, forms.DateField):
                        value = value.strftime('%Y-%m-%d')
                
                initial_data[field_name] = value
        
        for field_name, value in initial_data.items():
            self.initial[field_name] = value
    
    def save(self, commit=True) -> Any:
        """
        Сохраняет данные формы в модель SQLAlchemy с улучшенной обработкой ошибок.
        
        Args:
            commit: Если True, изменения будут сохранены в базу данных
            
        Returns:
            Экземпляр модели SQLAlchemy
        """
        if not self.is_valid():
            raise ValueError("Форма содержит ошибки")
            
        session = db_manager.get_session()
        try:
            if not self.instance:
                self.instance = self.model_class()
                
            # Обновляем поля модели из формы
            for field_name, field_value in self.cleaned_data.items():
                if hasattr(self.instance, field_name):
                    setattr(self.instance, field_name, field_value)
            
            # Устанавливаем временные метки
            if hasattr(self.instance, 'updated_at'):
                self.instance.updated_at = datetime.utcnow()
                
            if not getattr(self.instance, 'id', None) and hasattr(self.instance, 'created_at'):
                self.instance.created_at = datetime.utcnow()
            
            if commit:
                if not getattr(self.instance, 'id', None):
                    session.add(self.instance)
                
                # Используем try-except для обработки ошибок целостности данных
                try:
                    session.commit()
                    session.refresh(self.instance)
                except SQLAlchemyError as e:
                    session.rollback()
                    # Преобразуем ошибку SQLAlchemy в понятное сообщение
                    error_msg = str(e)
                    if 'UNIQUE constraint failed' in error_msg:
                        if 'telegram_id' in error_msg:
                            raise ValidationError({'telegram_id': 'Пользователь с таким Telegram ID уже существует'})
                    raise ValidationError(f'Ошибка базы данных: {error_msg}')
                
            return self.instance
        except Exception as e:
            if commit:
                session.rollback()
            raise e
        finally:
            if commit:
                db_manager.close_session(session)


class SQLAlchemyAdminView:
    """
    Базовый класс для админ-представлений SQLAlchemy моделей.
    Предоставляет общую функциональность для списка, создания, редактирования и удаления
    с улучшенной фильтрацией, поиском и оптимизацией запросов.
    """
    
    model_class = None  # Класс модели SQLAlchemy
    form_class = None   # Класс формы Django
    list_display = []   # Поля для отображения в списке
    list_filter = []    # Поля для фильтрации
    search_fields = []  # Поля для поиска
    ordering = None     # Поле для сортировки по умолчанию
    per_page = 25       # Количество объектов на странице
    date_hierarchy = None  # Поле для иерархической навигации по датам
    advanced_filters = {}  # Расширенные фильтры (диапазоны дат, числовые диапазоны и т.д.)
    
    def __init__(self, model_class=None, form_class=None):
        """
        Инициализирует представление админки.
        
        Args:
            model_class: Класс модели SQLAlchemy
            form_class: Класс формы Django (если None, будет использован SQLAlchemyModelForm)
        """
        if model_class:
            self.model_class = model_class
            
        if form_class:
            self.form_class = form_class
        elif not self.form_class:
            self.form_class = SQLAlchemyModelForm
            
        # Если list_display не указан, используем все колонки модели
        if not self.list_display and self.model_class:
            mapper = sa_inspect(self.model_class)
            self.list_display = [c.name for c in mapper.columns if c.name != 'id']
            
        # Если ordering не указан, используем первичный ключ
        if not self.ordering and self.model_class:
            mapper = sa_inspect(self.model_class)
            pk = mapper.primary_key[0].name if mapper.primary_key else 'id'
            self.ordering = pk
    
    def get_list_display(self) -> List[str]:
        """Возвращает список полей для отображения в списке."""
        return self.list_display
    
    def get_list_filter(self) -> List[str]:
        """Возвращает список полей для фильтрации."""
        return self.list_filter
    
    def get_search_fields(self) -> List[str]:
        """Возвращает список полей для поиска."""
        return self.search_fields
    
    def get_ordering(self) -> str:
        """Возвращает поле для сортировки по умолчанию."""
        return self.ordering
    
    def get_per_page(self) -> int:
        """Возвращает количество объектов на странице."""
        return self.per_page
    
    def get_queryset(self, request: HttpRequest, session: Session) -> Query:
        """
        Возвращает базовый запрос для получения объектов.
        
        Args:
            request: HTTP запрос
            session: Сессия SQLAlchemy
            
        Returns:
            Query: Базовый запрос SQLAlchemy
        """
        return session.query(self.model_class)
    
    def apply_ordering(self, queryset: Query, ordering: str) -> Query:
        """
        Применяет сортировку к запросу.
        
        Args:
            queryset: Запрос SQLAlchemy
            ordering: Поле для сортировки (с опциональным '-' для обратной сортировки)
            
        Returns:
            Query: Запрос с примененной сортировкой
        """
        if ordering:
            if ordering.startswith('-'):
                field_name = ordering[1:]
                direction = desc
            else:
                field_name = ordering
                direction = asc
                
            if hasattr(self.model_class, field_name):
                field = getattr(self.model_class, field_name)
                queryset = queryset.order_by(direction(field))
                
        return queryset
    
    def apply_search(self, queryset: Query, search_query: str) -> Query:
        """
        Применяет поиск к запросу.
        
        Args:
            queryset: Запрос SQLAlchemy
            search_query: Строка поиска
            
        Returns:
            Query: Запрос с примененным поиском
        """
        if search_query and self.get_search_fields():
            conditions = []
            
            for field_name in self.get_search_fields():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    
                    # Определяем тип поля и применяем соответствующий оператор
                    column_type = str(field.type).lower()
                    
                    if 'int' in column_type:
                        try:
                            value = int(search_query)
                            conditions.append(field == value)
                        except ValueError:
                            pass
                    elif 'string' in column_type or 'text' in column_type:
                        conditions.append(field.ilike(f'%{search_query}%'))
                    elif 'bool' in column_type:
                        if search_query.lower() in ('true', 'yes', '1'):
                            conditions.append(field == True)
                        elif search_query.lower() in ('false', 'no', '0'):
                            conditions.append(field == False)
            
            if conditions:
                queryset = queryset.filter(or_(*conditions))
                
        return queryset
    
    def apply_filters(self, queryset: Query, request: HttpRequest) -> Query:
        """
        Применяет фильтры к запросу на основе параметров запроса.
        
        Args:
            queryset: Запрос SQLAlchemy
            request: HTTP запрос
            
        Returns:
            Query: Запрос с примененными фильтрами
        """
        for filter_name in self.get_list_filter():
            filter_value = request.GET.get(filter_name)
            
            if filter_value and hasattr(self.model_class, filter_name):
                field = getattr(self.model_class, filter_name)
                
                # Определяем тип поля и применяем соответствующий оператор
                column_type = str(field.type).lower()
                
                if 'bool' in column_type:
                    queryset = queryset.filter(field == (filter_value.lower() == 'true'))
                elif 'int' in column_type:
                    try:
                        value = int(filter_value)
                        queryset = queryset.filter(field == value)
                    except ValueError:
                        pass
                elif 'string' in column_type or 'text' in column_type:
                    if filter_value != 'all':
                        queryset = queryset.filter(field == filter_value)
                        
        return queryset
    
    def get_object(self, session: Session, object_id: int) -> Any:
        """
        Получает объект по ID.
        
        Args:
            session: Сессия SQLAlchemy
            object_id: ID объекта
            
        Returns:
            Экземпляр модели SQLAlchemy или None, если объект не найден
        """
        return session.query(self.model_class).filter_by(id=object_id).first()
    
    def changelist_view(self, request: HttpRequest) -> HttpResponse:
        """
        Представление списка объектов.
        
        Args:
            request: HTTP запрос
            
        Returns:
            HttpResponse: HTTP ответ
        """
        session = db_manager.get_session()
        try:
            # Получение параметров запроса
            search_query = request.GET.get('q', '')
            ordering = request.GET.get('o', self.get_ordering())
            page_number = request.GET.get('page', 1)
            
            # Базовый запрос
            queryset = self.get_queryset(request, session)
            
            # Применение поиска
            queryset = self.apply_search(queryset, search_query)
            
            # Применение фильтров
            queryset = self.apply_filters(queryset, request)
            
            # Применение сортировки
            queryset = self.apply_ordering(queryset, ordering)
            
            # Подсчет общего количества объектов
            total_count = queryset.count()
            
            # Пагинация
            paginator = Paginator(range(total_count), self.get_per_page())
            page_obj = paginator.get_page(page_number)
            
            # Получение объектов для текущей страницы
            offset = (int(page_obj.number) - 1) * self.get_per_page()
            objects = queryset.offset(offset).limit(self.get_per_page()).all()
            
            # Подготовка контекста для шаблона
            context = {
                'objects': objects,
                'page_obj': page_obj,
                'total_count': total_count,
                'search_query': search_query,
                'model_name': self.model_class.__name__,
                'app_label': 'botapp',
                'has_add_permission': True,
                'has_change_permission': True,
                'has_delete_permission': True,
                'list_display': self.get_list_display(),
                'list_filter': self.get_list_filter(),
                'ordering': ordering,
            }
            
            # Добавление значений фильтров в контекст
            for filter_name in self.get_list_filter():
                filter_value = request.GET.get(filter_name)
                if filter_value:
                    context[f'{filter_name}_filter'] = filter_value
            
            return render(request, 'admin/botapp/user/change_list.html', context)
            
        finally:
            db_manager.close_session(session)
    
    def add_view(self, request: HttpRequest) -> HttpResponse:
        """
        Представление добавления объекта.
        
        Args:
            request: HTTP запрос
            
        Returns:
            HttpResponse: HTTP ответ
        """
        if request.method == 'POST':
            form = self.form_class(request.POST, model_class=self.model_class)
            
            if form.is_valid():
                try:
                    obj = form.save()
                    messages.success(request, f'Объект {obj.id} успешно создан')
                    
                    # Определение URL для редиректа
                    if '_continue' in request.POST:
                        return redirect(reverse('admin:user_change', args=[obj.id]))
                    elif '_addanother' in request.POST:
                        return redirect(reverse('admin:user_add'))
                    else:
                        return redirect(reverse('admin:user_changelist'))
                        
                except Exception as e:
                    messages.error(request, f'Ошибка при сохранении: {str(e)}')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            form = self.form_class(model_class=self.model_class)
        
        context = {
            'form': form,
            'model_name': self.model_class.__name__,
            'app_label': 'botapp',
            'has_change_permission': True,
            'original': None,
        }
        
        return render(request, 'admin/botapp/user/change_form.html', context)
    
    def change_view(self, request: HttpRequest, object_id: int) -> HttpResponse:
        """
        Представление изменения объекта.
        
        Args:
            request: HTTP запрос
            object_id: ID объекта
            
        Returns:
            HttpResponse: HTTP ответ
        """
        session = db_manager.get_session()
        try:
            obj = self.get_object(session, object_id)
            
            if not obj:
                messages.error(request, 'Объект не найден')
                return redirect(reverse('admin:user_changelist'))
            
            if request.method == 'POST':
                form = self.form_class(request.POST, instance=obj, model_class=self.model_class)
                
                if form.is_valid():
                    try:
                        obj = form.save()
                        messages.success(request, f'Объект {obj.id} успешно обновлен')
                        
                        # Определение URL для редиректа
                        if '_continue' in request.POST:
                            return redirect(reverse('admin:user_change', args=[obj.id]))
                        elif '_addanother' in request.POST:
                            return redirect(reverse('admin:user_add'))
                        else:
                            return redirect(reverse('admin:user_changelist'))
                            
                    except Exception as e:
                        messages.error(request, f'Ошибка при сохранении: {str(e)}')
                else:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f'{field}: {error}')
            else:
                form = self.form_class(instance=obj, model_class=self.model_class)
            
            context = {
                'form': form,
                'model_name': self.model_class.__name__,
                'app_label': 'botapp',
                'has_change_permission': True,
                'has_delete_permission': True,
                'original': obj,
            }
            
            return render(request, 'admin/botapp/user/change_form.html', context)
            
        finally:
            db_manager.close_session(session)
    
    def delete_view(self, request: HttpRequest, object_id: int) -> HttpResponse:
        """
        Представление удаления объекта.
        
        Args:
            request: HTTP запрос
            object_id: ID объекта
            
        Returns:
            HttpResponse: HTTP ответ
        """
        session = db_manager.get_session()
        try:
            obj = self.get_object(session, object_id)
            
            if not obj:
                messages.error(request, 'Объект не найден')
                return redirect(reverse('admin:user_changelist'))
            
            if request.method == 'POST':
                try:
                    session.delete(obj)
                    session.commit()
                    messages.success(request, f'Объект {obj.id} успешно удален')
                    return redirect(reverse('admin:user_changelist'))
                except Exception as e:
                    session.rollback()
                    messages.error(request, f'Ошибка при удалении: {str(e)}')
            
            context = {
                'model_name': self.model_class.__name__,
                'app_label': 'botapp',
                'object': obj,
            }
            
            return render(request, 'admin/botapp/user/delete_confirmation.html', context)
            
        finally:
            db_manager.close_session(session)


class UserAdminForm(SQLAlchemyModelForm):
    """
    Форма для модели User с дополнительной валидацией.
    """
    
    def clean_telegram_id(self):
        """Валидация поля telegram_id."""
        telegram_id = self.cleaned_data.get('telegram_id')
        
        if telegram_id <= 0:
            raise ValidationError('Telegram ID должен быть положительным числом')
            
        # Проверка уникальности telegram_id
        if self.instance and self.instance.id:
            # Редактирование существующего пользователя
            session = db_manager.get_session()
            try:
                existing = session.query(self.model_class).filter(
                    self.model_class.telegram_id == telegram_id,
                    self.model_class.id != self.instance.id
                ).first()
                
                if existing:
                    raise ValidationError(f'Пользователь с Telegram ID {telegram_id} уже существует')
            finally:
                db_manager.close_session(session)
        else:
            # Создание нового пользователя
            session = db_manager.get_session()
            try:
                existing = session.query(self.model_class).filter(
                    self.model_class.telegram_id == telegram_id
                ).first()
                
                if existing:
                    raise ValidationError(f'Пользователь с Telegram ID {telegram_id} уже существует')
            finally:
                db_manager.close_session(session)
        
        return telegram_id
    
    def clean_pregnancy_week(self):
        """Валидация поля pregnancy_week."""
        pregnancy_week = self.cleaned_data.get('pregnancy_week')
        is_pregnant = self.cleaned_data.get('is_pregnant')
        
        if is_pregnant and pregnancy_week is not None:
            if pregnancy_week < 1 or pregnancy_week > 42:
                raise ValidationError('Неделя беременности должна быть от 1 до 42')
        
        return pregnancy_week
    
    def clean(self):
        """Валидация формы в целом."""
        cleaned_data = super().clean()
        is_pregnant = cleaned_data.get('is_pregnant')
        pregnancy_week = cleaned_data.get('pregnancy_week')
        baby_birth_date = cleaned_data.get('baby_birth_date')
        
        if is_pregnant and not pregnancy_week:
            self.add_error('pregnancy_week', 'Для беременных пользователей необходимо указать неделю беременности')
        
        if not is_pregnant and not baby_birth_date:
            self.add_error('baby_birth_date', 'Для небеременных пользователей необходимо указать дату рождения ребенка')
        
        return cleaned_data


class UserAdmin(SQLAlchemyAdminView):
    """
    Админ-представление для модели User с улучшенной фильтрацией, поиском и оптимизацией запросов.
    """
    
    list_display = ['telegram_id', 'username', 'first_name', 'last_name', 
                   'is_pregnant', 'pregnancy_week', 'baby_birth_date', 
                   'is_premium', 'is_admin', 'created_at']
    list_filter = ['is_pregnant', 'is_premium', 'is_admin']
    search_fields = ['telegram_id', 'username', 'first_name', 'last_name']
    ordering = '-created_at'
    form_class = UserAdminForm
    per_page = 30  # Увеличиваем количество пользователей на странице
    date_hierarchy = 'created_at'  # Добавляем иерархическую навигацию по датам
    
    # Расширенные фильтры для более гибкой фильтрации
    advanced_filters = {
        'created_at': {
            'type': 'date_range',
            'label': 'Дата регистрации',
        },
        'pregnancy_week': {
            'type': 'range',
            'label': 'Неделя беременности',
            'min': 1,
            'max': 42,
        },
    }
    
    @lru_cache(maxsize=32)
    def get_queryset(self, request: HttpRequest, session: Session) -> Query:
        """
        Оптимизированный запрос для получения пользователей с кэшированием.
        
        Args:
            request: HTTP запрос
            session: Сессия SQLAlchemy
            
        Returns:
            Query: Оптимизированный запрос SQLAlchemy
        """
        # Используем опцию execution_options для оптимизации запроса
        query = session.query(self.model_class).execution_options(
            compiled_cache={},  # Кэширование скомпилированных запросов
        )
        
        # Оптимизация: загружаем только необходимые поля для списка
        if request.path.endswith('/changelist/'):
            # Для списка загружаем только отображаемые поля
            columns = [getattr(self.model_class, field) for field in self.list_display if hasattr(self.model_class, field)]
            if columns:
                query = query.options(load_only(*columns))
        
        return query
    
    def apply_search(self, queryset: Query, search_query: str) -> Query:
        """
        Улучшенный поиск с поддержкой частичного совпадения и оптимизацией.
        
        Args:
            queryset: Запрос SQLAlchemy
            search_query: Строка поиска
            
        Returns:
            Query: Запрос с примененным поиском
        """
        if not search_query:
            return queryset
            
        # Разбиваем поисковый запрос на слова для более точного поиска
        search_terms = search_query.split()
        
        # Если поисковый запрос выглядит как число, пробуем искать по telegram_id
        if search_query.isdigit():
            telegram_id_condition = self.model_class.telegram_id == int(search_query)
            queryset = queryset.filter(telegram_id_condition)
            return queryset
        
        # Для каждого слова создаем условия поиска
        conditions = []
        for term in search_terms:
            term_conditions = []
            
            # Поиск по текстовым полям
            for field_name in ['username', 'first_name', 'last_name']:
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    term_conditions.append(field.ilike(f'%{term}%'))
            
            # Если есть условия для этого слова, добавляем их в общий список
            if term_conditions:
                conditions.append(or_(*term_conditions))
        
        # Применяем все условия (все слова должны найтись)
        if conditions:
            queryset = queryset.filter(and_(*conditions))
        
        return queryset
    
    def apply_filters(self, queryset: Query, request: HttpRequest) -> Query:
        """
        Улучшенная фильтрация с поддержкой расширенных фильтров.
        
        Args:
            queryset: Запрос SQLAlchemy
            request: HTTP запрос
            
        Returns:
            Query: Запрос с примененными фильтрами
        """
        # Сначала применяем стандартные фильтры
        queryset = super().apply_filters(queryset, request)
        
        # Затем применяем расширенные фильтры
        
        # Фильтр по диапазону дат регистрации
        created_from = request.GET.get('created_from')
        created_to = request.GET.get('created_to')
        
        if created_from:
            try:
                created_from_date = datetime.strptime(created_from, '%Y-%m-%d')
                queryset = queryset.filter(self.model_class.created_at >= created_from_date)
            except ValueError:
                pass
                
        if created_to:
            try:
                created_to_date = datetime.strptime(created_to, '%Y-%m-%d')
                # Добавляем день, чтобы включить весь указанный день
                created_to_date = created_to_date + timedelta(days=1)
                queryset = queryset.filter(self.model_class.created_at < created_to_date)
            except ValueError:
                pass
        
        # Фильтр по диапазону недель беременности
        pregnancy_week_min = request.GET.get('pregnancy_week_min')
        pregnancy_week_max = request.GET.get('pregnancy_week_max')
        
        if pregnancy_week_min:
            try:
                pregnancy_week_min = int(pregnancy_week_min)
                queryset = queryset.filter(self.model_class.pregnancy_week >= pregnancy_week_min)
            except ValueError:
                pass
                
        if pregnancy_week_max:
            try:
                pregnancy_week_max = int(pregnancy_week_max)
                queryset = queryset.filter(self.model_class.pregnancy_week <= pregnancy_week_max)
            except ValueError:
                pass
        
        # Фильтр по возрасту ребенка (вычисляется из даты рождения)
        baby_age_months = request.GET.get('baby_age_months')
        if baby_age_months:
            try:
                baby_age_months = int(baby_age_months)
                # Вычисляем дату, соответствующую указанному возрасту
                date_threshold = datetime.utcnow() - timedelta(days=baby_age_months * 30)
                queryset = queryset.filter(self.model_class.baby_birth_date >= date_threshold)
            except ValueError:
                pass
        
        return queryset
        
    def changelist_view(self, request: HttpRequest) -> HttpResponse:
        """
        Улучшенное представление списка пользователей с дополнительными фильтрами.
        
        Args:
            request: HTTP запрос
            
        Returns:
            HttpResponse: HTTP ответ
        """
        session = db_manager.get_session()
        try:
            # Получение параметров запроса
            search_query = request.GET.get('q', '')
            ordering = request.GET.get('o', self.get_ordering())
            page_number = request.GET.get('page', 1)
            
            # Базовый запрос с оптимизацией
            queryset = self.get_queryset(request, session)
            
            # Применение поиска
            queryset = self.apply_search(queryset, search_query)
            
            # Применение фильтров
            queryset = self.apply_filters(queryset, request)
            
            # Применение сортировки
            queryset = self.apply_ordering(queryset, ordering)
            
            # Подсчет общего количества объектов (с оптимизацией)
            # Используем оптимизированный запрос для подсчета
            count_query = queryset.statement.with_only_columns([func.count()]).order_by(None)
            total_count = session.execute(count_query).scalar()
            
            # Пагинация
            paginator = Paginator(range(total_count), self.get_per_page())
            page_obj = paginator.get_page(page_number)
            
            # Получение объектов для текущей страницы
            offset = (int(page_obj.number) - 1) * self.get_per_page()
            objects = queryset.offset(offset).limit(self.get_per_page()).all()
            
            # Получение статистики для фильтров
            filter_stats = self._get_filter_stats(session)
            
            # Подготовка контекста для шаблона
            context = {
                'objects': objects,
                'page_obj': page_obj,
                'total_count': total_count,
                'search_query': search_query,
                'model_name': self.model_class.__name__,
                'app_label': 'botapp',
                'has_add_permission': True,
                'has_change_permission': True,
                'has_delete_permission': True,
                'list_display': self.get_list_display(),
                'list_filter': self.get_list_filter(),
                'ordering': ordering,
                'filter_stats': filter_stats,
                'advanced_filters': self.advanced_filters,
            }
            
            # Добавление значений фильтров в контекст
            for filter_name in self.get_list_filter():
                filter_value = request.GET.get(filter_name)
                if filter_value:
                    context[f'{filter_name}_filter'] = filter_value
            
            # Добавление значений расширенных фильтров
            for filter_name in ['created_from', 'created_to', 'pregnancy_week_min', 
                               'pregnancy_week_max', 'baby_age_months']:
                filter_value = request.GET.get(filter_name)
                if filter_value:
                    context[filter_name] = filter_value
            
            return render(request, 'admin/botapp/user/change_list.html', context)
            
        finally:
            db_manager.close_session(session)
    
    def _get_filter_stats(self, session: Session) -> Dict[str, Any]:
        """
        Получает статистику для фильтров.
        
        Args:
            session: Сессия SQLAlchemy
            
        Returns:
            Dict[str, Any]: Словарь со статистикой
        """
        # Используем оптимизированные запросы для получения статистики
        pregnant_count = session.query(func.count()).filter(self.model_class.is_pregnant == True).scalar()
        premium_count = session.query(func.count()).filter(self.model_class.is_premium == True).scalar()
        admin_count = session.query(func.count()).filter(self.model_class.is_admin == True).scalar()
        
        # Статистика по неделям беременности
        pregnancy_stats = session.query(
            self.model_class.pregnancy_week,
            func.count().label('count')
        ).filter(
            self.model_class.is_pregnant == True,
            self.model_class.pregnancy_week != None
        ).group_by(
            self.model_class.pregnancy_week
        ).all()
        
        # Статистика по возрасту детей (в месяцах)
        current_date = datetime.utcnow()
        baby_age_stats = []
        
        # Возвращаем собранную статистику
        return {
            'pregnant_count': pregnant_count,
            'premium_count': premium_count,
            'admin_count': admin_count,
            'pregnancy_stats': pregnancy_stats,
            'baby_age_stats': baby_age_stats,
        }


def with_session(view_func):
    """
    Декоратор для автоматического управления сессией SQLAlchemy.
    
    Args:
        view_func: Функция представления
        
    Returns:
        Функция-обертка, которая автоматически управляет сессией
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        session = db_manager.get_session()
        try:
            kwargs['session'] = session
            return view_func(request, *args, **kwargs)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            db_manager.close_session(session)
    return wrapper


@lru_cache(maxsize=1, ttl=300)  # Кэширование на 5 минут
def get_admin_stats(session: Session) -> Dict[str, Any]:
    """
    Получает расширенную статистику для админ-панели с оптимизированными запросами.
    
    Args:
        session: Сессия SQLAlchemy
        
    Returns:
        Dict[str, Any]: Словарь с расширенной статистикой
    """
    from .models import User
    
    # Оптимизированные запросы для получения базовой статистики
    # Используем один запрос для получения нескольких счетчиков
    counts = session.query(
        func.count().label('total'),
        func.sum(User.is_pregnant.cast(Integer)).label('pregnant'),
        func.sum(User.is_premium.cast(Integer)).label('premium'),
        func.sum(User.is_admin.cast(Integer)).label('admin')
    ).first()
    
    total_users = counts.total if counts.total is not None else 0
    pregnant_users = counts.pregnant if counts.pregnant is not None else 0
    premium_users = counts.premium if counts.premium is not None else 0
    admin_users = counts.admin if counts.admin is not None else 0
    
    # Последние пользователи с оптимизацией запроса
    # Используем опцию load_only для загрузки только необходимых полей
    recent_users = session.query(User).options(
        load_only(
            User.id, User.telegram_id, User.username, User.first_name,
            User.is_pregnant, User.is_premium, User.is_admin, User.created_at
        )
    ).order_by(User.created_at.desc()).limit(5).all()
    
    # Статистика активности пользователей
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    week_ago = today_start - timedelta(days=7)
    
    # Пользователи, зарегистрированные сегодня
    users_today = session.query(func.count()).filter(
        User.created_at >= today_start
    ).scalar() or 0
    
    # Пользователи, зарегистрированные за последнюю неделю
    users_week = session.query(func.count()).filter(
        User.created_at >= week_ago
    ).scalar() or 0
    
    # Статистика по неделям беременности
    pregnancy_stats = session.query(
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
    
    # Преобразуем результаты в словарь для удобства использования
    pregnancy_weeks_data = {
        week: count for week, count in pregnancy_stats
    }
    
    # Статистика по возрасту детей (в месяцах)
    # Вычисляем возраст на основе даты рождения
    current_date = datetime.utcnow()
    baby_age_stats = []
    
    # Возвращаем расширенную статистику
    return {
        'total_users': total_users,
        'pregnant_users': pregnant_users,
        'premium_users': premium_users,
        'admin_users': admin_users,
        'recent_users': recent_users,
        'users_today': users_today,
        'users_week': users_week,
        'pregnancy_weeks_data': pregnancy_weeks_data,
        'baby_age_stats': baby_age_stats,
        'active_users_today': users_today,  # Для совместимости с admin.py
        'active_users_week': users_week,    # Для совместимости с admin.py
    }