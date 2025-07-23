"""
API эндпоинты для календаря прививок.

Этот модуль содержит представления API для работы с вакцинами и записями о прививках.
"""

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator

from botapp.models import User
from webapp.utils.db_utils import get_db_manager
from botapp.models_child import Child, get_child
from botapp.models_vaccine import (
    Vaccine, ChildVaccine,
    get_all_vaccines, get_vaccine,
    get_child_vaccines, get_child_vaccine,
    create_child_vaccine, update_child_vaccine, delete_child_vaccine,
    mark_vaccine_completed
)

logger = logging.getLogger(__name__)


def parse_datetime(date_string):
    """Преобразует строку даты в объект datetime."""
    if not date_string:
        return None
    
    try:
        # Пробуем разные форматы дат
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # Если ни один формат не подходит
        raise ValueError(f"Невозможно разобрать дату: {date_string}")
        
    except Exception as e:
        logger.error(f"Ошибка при разборе даты '{date_string}': {e}")
        return None


def vaccine_to_dict(vaccine):
    """Преобразует объект Vaccine в словарь."""
    return {
        'id': vaccine.id,
        'name': vaccine.name,
        'description': vaccine.description,
        'recommended_age': vaccine.recommended_age,
        'is_mandatory': vaccine.is_mandatory,
        'created_at': vaccine.created_at.isoformat() if vaccine.created_at else None,
        'updated_at': vaccine.updated_at.isoformat() if vaccine.updated_at else None,
    }


def child_vaccine_to_dict(child_vaccine):
    """Преобразует объект ChildVaccine в словарь."""
    return {
        'id': child_vaccine.id,
        'child_id': child_vaccine.child_id,
        'vaccine_id': child_vaccine.vaccine_id,
        'vaccine_name': child_vaccine.vaccine.name if child_vaccine.vaccine else None,
        'date': child_vaccine.date.isoformat() if child_vaccine.date else None,
        'is_completed': child_vaccine.is_completed,
        'notes': child_vaccine.notes,
        'created_at': child_vaccine.created_at.isoformat() if child_vaccine.created_at else None,
        'updated_at': child_vaccine.updated_at.isoformat() if child_vaccine.updated_at else None,
    }


# API эндпоинты для вакцин
@method_decorator(csrf_exempt, name='dispatch')
class VaccinesListView(View):
    """
    API представление для получения списка всех вакцин.
    
    URL: /api/vaccines/
    Методы: GET
    """
    
    def get(self, request):
        """Получить список всех вакцин."""
        try:
            # Получаем все вакцины
            vaccines = get_all_vaccines()
            
            # Преобразуем в словарь
            vaccines_data = [vaccine_to_dict(vaccine) for vaccine in vaccines]
            
            return JsonResponse({'vaccines': vaccines_data})
        
        except Exception as e:
            logger.error(f"Error getting vaccines: {e}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class VaccineDetailView(View):
    """
    API представление для получения информации о конкретной вакцине.
    
    URL: /api/vaccines/{vaccine_id}/
    Методы: GET
    """
    
    def get(self, request, vaccine_id):
        """Получить информацию о конкретной вакцине."""
        try:
            # Преобразуем vaccine_id в целое число
            vaccine_id = int(vaccine_id)
            
            # Получаем вакцину
            vaccine = get_vaccine(vaccine_id)
            
            # Проверяем существование вакцины
            if not vaccine:
                return JsonResponse({'error': 'Вакцина не найдена'}, status=404)
            
            # Возвращаем данные вакцины
            return JsonResponse(vaccine_to_dict(vaccine))
        
        except Exception as e:
            logger.error(f"Error getting vaccine {vaccine_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


# API эндпоинты для прививок ребенка
@method_decorator(csrf_exempt, name='dispatch')
class ChildVaccinesListView(View):
    """
    API представление для получения списка и создания прививок для ребенка.
    
    URL: /api/users/{user_id}/children/{child_id}/vaccines/
    Методы: GET, POST
    """
    
    def get(self, request, user_id, child_id):
        """Получить все прививки для конкретного ребенка."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            child_id = int(child_id)
            
            # Получаем ребенка
            child = get_child(child_id)
            
            # Проверяем существование ребенка и принадлежность пользователю
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
            
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            # Получаем прививки ребенка
            child_vaccines = get_child_vaccines(child_id)
            
            # Преобразуем в словарь
            child_vaccines_data = [child_vaccine_to_dict(child_vaccine) for child_vaccine in child_vaccines]
            
            return JsonResponse({'child_vaccines': child_vaccines_data})
        
        except Exception as e:
            logger.error(f"Error getting vaccines for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def post(self, request, user_id, child_id):
        """Создать новую запись о прививке для ребенка."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            child_id = int(child_id)
            
            # Получаем ребенка
            child = get_child(child_id)
            
            # Проверяем существование ребенка и принадлежность пользователю
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
            
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Проверяем наличие обязательных полей
            if 'vaccine_id' not in data:
                return JsonResponse({'error': 'Не указан ID вакцины'}, status=400)
            
            # Проверяем существование вакцины
            vaccine = get_vaccine(data['vaccine_id'])
            if not vaccine:
                return JsonResponse({'error': 'Вакцина не найдена'}, status=404)
            
            # Разбираем дату, если она указана
            date = None
            if 'date' in data:
                date = parse_datetime(data['date'])
            
            # Создаем запись о прививке
            child_vaccine = create_child_vaccine(
                child_id=child_id,
                vaccine_id=data['vaccine_id'],
                date=date,
                is_completed=data.get('is_completed', False),
                notes=data.get('notes')
            )
            
            # Возвращаем созданную запись
            return JsonResponse(child_vaccine_to_dict(child_vaccine), status=201)
        
        except Exception as e:
            logger.error(f"Error creating vaccine record for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ChildVaccineDetailView(View):
    """
    API представление для получения, обновления и удаления конкретной записи о прививке.
    
    URL: /api/users/{user_id}/children/{child_id}/vaccines/{child_vaccine_id}/
    Методы: GET, PUT, DELETE
    """
    
    def get(self, request, user_id, child_id, child_vaccine_id):
        """Получить конкретную запись о прививке."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            child_id = int(child_id)
            child_vaccine_id = int(child_vaccine_id)
            
            # Получаем ребенка
            child = get_child(child_id)
            
            # Проверяем существование ребенка и принадлежность пользователю
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
            
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            # Получаем запись о прививке
            child_vaccine = get_child_vaccine(child_vaccine_id)
            
            # Проверяем существование записи и принадлежность ребенку
            if not child_vaccine:
                return JsonResponse({'error': 'Запись о прививке не найдена'}, status=404)
            
            if child_vaccine.child_id != child_id:
                return JsonResponse({'error': 'Запись о прививке не принадлежит этому ребенку'}, status=403)
            
            # Возвращаем данные записи
            return JsonResponse(child_vaccine_to_dict(child_vaccine))
        
        except Exception as e:
            logger.error(f"Error getting vaccine record {child_vaccine_id} for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def put(self, request, user_id, child_id, child_vaccine_id):
        """Обновить запись о прививке."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            child_id = int(child_id)
            child_vaccine_id = int(child_vaccine_id)
            
            # Получаем ребенка
            child = get_child(child_id)
            
            # Проверяем существование ребенка и принадлежность пользователю
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
            
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            # Получаем запись о прививке
            child_vaccine = get_child_vaccine(child_vaccine_id)
            
            # Проверяем существование записи и принадлежность ребенку
            if not child_vaccine:
                return JsonResponse({'error': 'Запись о прививке не найдена'}, status=404)
            
            if child_vaccine.child_id != child_id:
                return JsonResponse({'error': 'Запись о прививке не принадлежит этому ребенку'}, status=403)
            
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Подготавливаем данные для обновления
            update_data = {}
            
            if 'date' in data:
                update_data['date'] = parse_datetime(data['date'])
            
            if 'is_completed' in data:
                update_data['is_completed'] = data['is_completed']
            
            if 'notes' in data:
                update_data['notes'] = data['notes']
            
            # Обновляем запись о прививке
            updated_child_vaccine = update_child_vaccine(child_vaccine_id, **update_data)
            
            # Возвращаем обновленную запись
            return JsonResponse(child_vaccine_to_dict(updated_child_vaccine))
        
        except Exception as e:
            logger.error(f"Error updating vaccine record {child_vaccine_id} for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def delete(self, request, user_id, child_id, child_vaccine_id):
        """Удалить запись о прививке."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            child_id = int(child_id)
            child_vaccine_id = int(child_vaccine_id)
            
            # Получаем ребенка
            child = get_child(child_id)
            
            # Проверяем существование ребенка и принадлежность пользователю
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
            
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            # Получаем запись о прививке
            child_vaccine = get_child_vaccine(child_vaccine_id)
            
            # Проверяем существование записи и принадлежность ребенку
            if not child_vaccine:
                return JsonResponse({'error': 'Запись о прививке не найдена'}, status=404)
            
            if child_vaccine.child_id != child_id:
                return JsonResponse({'error': 'Запись о прививке не принадлежит этому ребенку'}, status=403)
            
            # Удаляем запись о прививке
            success = delete_child_vaccine(child_vaccine_id)
            
            if success:
                return JsonResponse({'message': 'Vaccine record deleted successfully'})
            else:
                return JsonResponse({'error': 'Failed to delete vaccine record'}, status=500)
        
        except Exception as e:
            logger.error(f"Error deleting vaccine record {child_vaccine_id} for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MarkVaccineCompletedView(View):
    """
    API представление для отметки прививки как выполненной.
    
    URL: /api/users/{user_id}/children/{child_id}/vaccines/{child_vaccine_id}/complete/
    Методы: POST
    """
    
    def post(self, request, user_id, child_id, child_vaccine_id):
        """Отметить прививку как выполненную."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            child_id = int(child_id)
            child_vaccine_id = int(child_vaccine_id)
            
            # Получаем ребенка
            child = get_child(child_id)
            
            # Проверяем существование ребенка и принадлежность пользователю
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
            
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            # Получаем запись о прививке
            child_vaccine = get_child_vaccine(child_vaccine_id)
            
            # Проверяем существование записи и принадлежность ребенку
            if not child_vaccine:
                return JsonResponse({'error': 'Запись о прививке не найдена'}, status=404)
            
            if child_vaccine.child_id != child_id:
                return JsonResponse({'error': 'Запись о прививке не принадлежит этому ребенку'}, status=403)
            
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Разбираем дату, если она указана
            date = None
            if 'date' in data:
                date = parse_datetime(data['date'])
            
            # Отмечаем прививку как выполненную
            updated_child_vaccine = mark_vaccine_completed(
                child_vaccine_id=child_vaccine_id,
                date=date,
                notes=data.get('notes')
            )
            
            # Возвращаем обновленную запись
            return JsonResponse(child_vaccine_to_dict(updated_child_vaccine))
        
        except Exception as e:
            logger.error(f"Error marking vaccine {child_vaccine_id} as completed for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


# Функции маршрутизации URL
def vaccines_list(request):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = VaccinesListView()
    if request.method == 'GET':
        return view.get(request)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def vaccine_detail(request, vaccine_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = VaccineDetailView()
    if request.method == 'GET':
        return view.get(request, vaccine_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def child_vaccines_list(request, user_id, child_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = ChildVaccinesListView()
    if request.method == 'GET':
        return view.get(request, user_id, child_id)
    elif request.method == 'POST':
        return view.post(request, user_id, child_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def child_vaccine_detail(request, user_id, child_id, child_vaccine_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = ChildVaccineDetailView()
    if request.method == 'GET':
        return view.get(request, user_id, child_id, child_vaccine_id)
    elif request.method == 'PUT':
        return view.put(request, user_id, child_id, child_vaccine_id)
    elif request.method == 'DELETE':
        return view.delete(request, user_id, child_id, child_vaccine_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def mark_vaccine_completed_view(request, user_id, child_id, child_vaccine_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = MarkVaccineCompletedView()
    if request.method == 'POST':
        return view.post(request, user_id, child_id, child_vaccine_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)