"""
API эндпоинты для веб-интерфейса материнского ухода.

Этот модуль содержит представления API для профилей детей и измерений.
"""

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator

from botapp.models import User, db_manager
from botapp.models_child import (
    Child, Measurement,
    get_child, get_children_by_user,
    create_child, update_child, delete_child,
    get_measurements, create_measurement, update_measurement, delete_measurement
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


def child_to_dict(child):
    """Преобразует объект Child в словарь."""
    return {
        'id': child.id,
        'user_id': child.user_id,
        'name': child.name,
        'birth_date': child.birth_date.isoformat() if child.birth_date else None,
        'gender': child.gender,
        'age_in_months': child.age_in_months,
        'age_display': child.age_display,
        'created_at': child.created_at.isoformat() if child.created_at else None,
        'updated_at': child.updated_at.isoformat() if child.updated_at else None,
    }


def measurement_to_dict(measurement):
    """Преобразует объект Measurement в словарь."""
    return {
        'id': measurement.id,
        'child_id': measurement.child_id,
        'date': measurement.date.isoformat() if measurement.date else None,
        'height': measurement.height,
        'weight': measurement.weight,
        'head_circumference': measurement.head_circumference,
        'notes': measurement.notes,
    }


# API эндпоинты для профилей детей
@method_decorator(csrf_exempt, name='dispatch')
class ChildrenListView(View):
    """
    API представление для получения списка и создания профилей детей.
    
    URL: /api/users/{user_id}/children/
    Методы: GET, POST
    """
    
    def get(self, request, user_id):
        """Получить всех детей для конкретного пользователя."""
        try:
            # Преобразуем user_id в целое число
            user_id = int(user_id)
            
            # Проверяем существование пользователя
            session = db_manager.get_session()
            try:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return JsonResponse({'error': 'Пользователь не найден'}, status=404)
            finally:
                db_manager.close_session(session)
            
            # Получаем детей
            children = get_children_by_user(user_id)
            
            # Преобразуем в словарь
            children_data = [child_to_dict(child) for child in children]
            
            return JsonResponse({'children': children_data})
        
        except Exception as e:
            logger.error(f"Error getting children for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def post(self, request, user_id):
        """Создать новый профиль ребенка."""
        try:
            # Преобразуем user_id в целое число
            user_id = int(user_id)
            
            # Проверяем существование пользователя
            session = db_manager.get_session()
            try:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return JsonResponse({'error': 'Пользователь не найден'}, status=404)
            finally:
                db_manager.close_session(session)
            
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Разбираем дату рождения, если она указана
            birth_date = None
            if 'birth_date' in data:
                birth_date = parse_datetime(data['birth_date'])
            
            # Создаем профиль ребенка
            child = create_child(
                user_id=user_id,
                name=data.get('name'),
                birth_date=birth_date,
                gender=data.get('gender')
            )
            
            # Возвращаем созданный профиль
            return JsonResponse(child_to_dict(child), status=201)
        
        except Exception as e:
            logger.error(f"Error creating child profile for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ChildDetailView(View):
    """
    API представление для получения, обновления и удаления конкретного профиля ребенка.
    
    URL: /api/users/{user_id}/children/{child_id}/
    Методы: GET, PUT, DELETE
    """
    
    def get(self, request, user_id, child_id):
        """Получить конкретный профиль ребенка."""
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
            
            # Возвращаем данные ребенка
            return JsonResponse(child_to_dict(child))
        
        except Exception as e:
            logger.error(f"Error getting child profile {child_id} for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def put(self, request, user_id, child_id):
        """Обновить профиль ребенка."""
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
            
            # Подготавливаем данные для обновления
            update_data = {}
            
            if 'name' in data:
                update_data['name'] = data['name']
            
            if 'gender' in data:
                update_data['gender'] = data['gender']
            
            if 'birth_date' in data:
                update_data['birth_date'] = parse_datetime(data['birth_date'])
            
            # Обновляем профиль ребенка
            updated_child = update_child(child_id, **update_data)
            
            # Возвращаем обновленный профиль
            return JsonResponse(child_to_dict(updated_child))
        
        except Exception as e:
            logger.error(f"Error updating child profile {child_id} for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def delete(self, request, user_id, child_id):
        """Удалить профиль ребенка."""
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
            
            # Удаляем профиль ребенка
            success = delete_child(child_id)
            
            if success:
                return JsonResponse({'message': 'Профиль ребенка успешно удален'})
            else:
                return JsonResponse({'error': 'Не удалось удалить профиль ребенка'}, status=500)
        
        except Exception as e:
            logger.error(f"Error deleting child profile {child_id} for user {user_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


# API эндпоинты для измерений
@method_decorator(csrf_exempt, name='dispatch')
class MeasurementsListView(View):
    """
    API представление для получения списка и создания измерений для ребенка.
    
    URL: /api/users/{user_id}/children/{child_id}/measurements/
    Методы: GET, POST
    """
    
    def get(self, request, user_id, child_id):
        """Получить все измерения для конкретного ребенка."""
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
            
            # Получаем измерения
            measurements = get_measurements(child_id)
            
            # Преобразуем в словарь
            measurements_data = [measurement_to_dict(measurement) for measurement in measurements]
            
            return JsonResponse({'measurements': measurements_data})
        
        except Exception as e:
            logger.error(f"Error getting measurements for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def post(self, request, user_id, child_id):
        """Создать новое измерение для ребенка."""
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
            
            # Разбираем дату, если она указана
            date = None
            if 'date' in data:
                date = parse_datetime(data['date'])
            
            # Создаем измерение
            measurement = create_measurement(
                child_id=child_id,
                height=data.get('height'),
                weight=data.get('weight'),
                head_circumference=data.get('head_circumference'),
                date=date,
                notes=data.get('notes')
            )
            
            # Возвращаем созданное измерение
            return JsonResponse(measurement_to_dict(measurement), status=201)
        
        except Exception as e:
            logger.error(f"Error creating measurement for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MeasurementDetailView(View):
    """
    API представление для получения, обновления и удаления конкретного измерения.
    
    URL: /api/users/{user_id}/children/{child_id}/measurements/{measurement_id}/
    Методы: GET, PUT, DELETE
    """
    
    def get(self, request, user_id, child_id, measurement_id):
        """Получить конкретное измерение."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            child_id = int(child_id)
            measurement_id = int(measurement_id)
            
            # Получаем ребенка
            child = get_child(child_id)
            
            # Проверяем существование ребенка и принадлежность пользователю
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
            
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            # Получаем измерение
            session = db_manager.get_session()
            try:
                measurement = session.query(Measurement).filter_by(id=measurement_id).first()
                
                # Проверяем существование измерения и принадлежность ребенку
                if not measurement:
                    return JsonResponse({'error': 'Измерение не найдено'}, status=404)
                
                if measurement.child_id != child_id:
                    return JsonResponse({'error': 'Измерение не принадлежит этому ребенку'}, status=403)
                
                # Возвращаем данные измерения
                return JsonResponse(measurement_to_dict(measurement))
            finally:
                db_manager.close_session(session)
        
        except Exception as e:
            logger.error(f"Error getting measurement {measurement_id} for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def put(self, request, user_id, child_id, measurement_id):
        """Обновить измерение."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            child_id = int(child_id)
            measurement_id = int(measurement_id)
            
            # Получаем ребенка
            child = get_child(child_id)
            
            # Проверяем существование ребенка и принадлежность пользователю
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
            
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            # Получаем измерение
            session = db_manager.get_session()
            try:
                measurement = session.query(Measurement).filter_by(id=measurement_id).first()
                
                # Проверяем существование измерения и принадлежность ребенку
                if not measurement:
                    return JsonResponse({'error': 'Измерение не найдено'}, status=404)
                
                if measurement.child_id != child_id:
                    return JsonResponse({'error': 'Измерение не принадлежит этому ребенку'}, status=403)
            finally:
                db_manager.close_session(session)
            
            # Разбираем данные запроса
            data = json.loads(request.body)
            
            # Подготавливаем данные для обновления
            update_data = {}
            
            if 'height' in data:
                update_data['height'] = data['height']
            
            if 'weight' in data:
                update_data['weight'] = data['weight']
            
            if 'head_circumference' in data:
                update_data['head_circumference'] = data['head_circumference']
            
            if 'notes' in data:
                update_data['notes'] = data['notes']
            
            if 'date' in data:
                update_data['date'] = parse_datetime(data['date'])
            
            # Обновляем измерение
            updated_measurement = update_measurement(measurement_id, **update_data)
            
            # Возвращаем обновленное измерение
            return JsonResponse(measurement_to_dict(updated_measurement))
        
        except Exception as e:
            logger.error(f"Error updating measurement {measurement_id} for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def delete(self, request, user_id, child_id, measurement_id):
        """Удалить измерение."""
        try:
            # Преобразуем ID в целые числа
            user_id = int(user_id)
            child_id = int(child_id)
            measurement_id = int(measurement_id)
            
            # Получаем ребенка
            child = get_child(child_id)
            
            # Проверяем существование ребенка и принадлежность пользователю
            if not child:
                return JsonResponse({'error': 'Ребенок не найден'}, status=404)
            
            if child.user_id != user_id:
                return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
            
            # Получаем измерение
            session = db_manager.get_session()
            try:
                measurement = session.query(Measurement).filter_by(id=measurement_id).first()
                
                # Проверяем существование измерения и принадлежность ребенку
                if not measurement:
                    return JsonResponse({'error': 'Измерение не найдено'}, status=404)
                
                if measurement.child_id != child_id:
                    return JsonResponse({'error': 'Измерение не принадлежит этому ребенку'}, status=403)
            finally:
                db_manager.close_session(session)
            
            # Удаляем измерение
            success = delete_measurement(measurement_id)
            
            if success:
                return JsonResponse({'message': 'Измерение успешно удалено'})
            else:
                return JsonResponse({'error': 'Не удалось удалить измерение'}, status=500)
        
        except Exception as e:
            logger.error(f"Error deleting measurement {measurement_id} for child {child_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)


# Функции маршрутизации URL
def children_list(request, user_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = ChildrenListView()
    if request.method == 'GET':
        return view.get(request, user_id)
    elif request.method == 'POST':
        return view.post(request, user_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def child_detail(request, user_id, child_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = ChildDetailView()
    if request.method == 'GET':
        return view.get(request, user_id, child_id)
    elif request.method == 'PUT':
        return view.put(request, user_id, child_id)
    elif request.method == 'DELETE':
        return view.delete(request, user_id, child_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def measurements_list(request, user_id, child_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = MeasurementsListView()
    if request.method == 'GET':
        return view.get(request, user_id, child_id)
    elif request.method == 'POST':
        return view.post(request, user_id, child_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def measurement_detail(request, user_id, child_id, measurement_id):
    """Маршрутизация к соответствующему методу на основе HTTP-метода."""
    view = MeasurementDetailView()
    if request.method == 'GET':
        return view.get(request, user_id, child_id, measurement_id)
    elif request.method == 'PUT':
        return view.put(request, user_id, child_id, measurement_id)
    elif request.method == 'DELETE':
        return view.delete(request, user_id, child_id, measurement_id)
    return JsonResponse({'error': 'Method not allowed'}, status=405)