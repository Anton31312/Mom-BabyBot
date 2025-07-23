"""
API эндпоинты для веб-интерфейса материнского ухода.

Этот модуль содержит представления API для профилей детей и измерений.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator

from botapp.models import User
from botapp.models_child import (
    Child, Measurement,
    get_child, get_children_by_user,
    create_child, update_child, delete_child,
    get_measurements, create_measurement, update_measurement, delete_measurement
)
from webapp.utils.date_utils import parse_datetime
from webapp.utils.model_utils import child_to_dict, measurement_to_dict
from webapp.utils.request_utils import parse_json_request, validate_id_param, error_response, success_response
from webapp.utils.validation_utils import validate_required_fields, validate_numeric_value, validate_date, validate_enum_value
from webapp.utils.common_utils import safe_execute
from webapp.utils.db_utils import with_db_session, safe_get_object, get_db_manager

logger = logging.getLogger(__name__)


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
            try:
                user_id = int(user_id)
            except ValueError:
                return JsonResponse({'error': 'Неверный формат ID пользователя'}, status=400)
            
            # Проверяем существование пользователя
            db_manager = get_db_manager()

            session = db_manager.get_session()
            try:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return JsonResponse({'error': 'Пользователь не найден'}, status=404)
            finally:
                db_manager.close_session(session)
            
            # Получаем детей
            try:
                children = get_children_by_user(user_id)
                
                # Преобразуем в словарь
                children_data = [child_to_dict(child) for child in children]
                
                return JsonResponse({'children': children_data})
            except Exception as e:
                logger.error(f"Ошибка при получении списка детей из базы данных: {e}")
                return JsonResponse({'error': f'Ошибка при получении списка детей: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка при получении списка детей для пользователя {user_id}: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)
    
    def post(self, request, user_id):
        """Создать новый профиль ребенка."""
        try:
            # Преобразуем user_id в целое число
            try:
                user_id = int(user_id)
            except ValueError:
                return JsonResponse({'error': 'Неверный формат ID пользователя'}, status=400)
            
            # Проверяем существование пользователя
            db_manager = get_db_manager()

            session = db_manager.get_session()
            try:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return JsonResponse({'error': 'Пользователь не найден'}, status=404)
            finally:
                db_manager.close_session(session)
            
            # Разбираем данные запроса
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Невалидный JSON в запросе'}, status=400)
            
            # Разбираем дату рождения, если она указана
            birth_date = None
            if 'birth_date' in data:
                birth_date = parse_datetime(data['birth_date'])
                if data['birth_date'] and not birth_date:
                    return JsonResponse({'error': 'Неверный формат даты рождения'}, status=400)
            
            # Проверяем наличие имени
            if 'name' not in data or not data['name']:
                return JsonResponse({'error': 'Имя ребенка обязательно для заполнения'}, status=400)
            
            # Проверяем пол ребенка, если указан
            if 'gender' in data and data['gender'] not in ['male', 'female', 'other', None, '']:
                return JsonResponse({'error': 'Неверное значение пола. Допустимые значения: male, female, other'}, status=400)
            
            # Создаем профиль ребенка
            try:
                child = create_child(
                    user_id=user_id,
                    name=data.get('name'),
                    birth_date=birth_date,
                    gender=data.get('gender')
                )
                
                # Возвращаем созданный профиль
                return JsonResponse(child_to_dict(child), status=201)
            except Exception as e:
                logger.error(f"Ошибка при создании профиля ребенка в базе данных: {e}")
                return JsonResponse({'error': f'Ошибка при создании профиля ребенка: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка при создании профиля ребенка для пользователя {user_id}: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)


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
            try:
                user_id = int(user_id)
                child_id = int(child_id)
            except ValueError:
                return JsonResponse({'error': 'Неверный формат ID пользователя или ребенка'}, status=400)
            
            # Получаем ребенка
            try:
                child = get_child(child_id)
                
                # Проверяем существование ребенка и принадлежность пользователю
                if not child:
                    return JsonResponse({'error': 'Ребенок не найден'}, status=404)
                
                if child.user_id != user_id:
                    return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
                
                # Возвращаем данные ребенка
                return JsonResponse(child_to_dict(child))
            except Exception as e:
                logger.error(f"Ошибка при получении профиля ребенка из базы данных: {e}")
                return JsonResponse({'error': f'Ошибка при получении профиля ребенка: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка при получении профиля ребенка {child_id} для пользователя {user_id}: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)
    
    def put(self, request, user_id, child_id):
        """Обновить профиль ребенка."""
        try:
            # Преобразуем ID в целые числа
            try:
                user_id = int(user_id)
                child_id = int(child_id)
            except ValueError:
                return JsonResponse({'error': 'Неверный формат ID пользователя или ребенка'}, status=400)
            
            # Получаем ребенка
            try:
                child = get_child(child_id)
                
                # Проверяем существование ребенка и принадлежность пользователю
                if not child:
                    return JsonResponse({'error': 'Ребенок не найден'}, status=404)
                
                if child.user_id != user_id:
                    return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
                
                # Разбираем данные запроса
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Невалидный JSON в запросе'}, status=400)
                
                # Подготавливаем данные для обновления
                update_data = {}
                
                if 'name' in data:
                    if not data['name']:
                        return JsonResponse({'error': 'Имя ребенка не может быть пустым'}, status=400)
                    update_data['name'] = data['name']
                
                if 'gender' in data:
                    if data['gender'] not in ['male', 'female', 'other', None, '']:
                        return JsonResponse({'error': 'Неверное значение пола. Допустимые значения: male, female, other'}, status=400)
                    update_data['gender'] = data['gender']
                
                if 'birth_date' in data:
                    birth_date = parse_datetime(data['birth_date'])
                    if data['birth_date'] and not birth_date:
                        return JsonResponse({'error': 'Неверный формат даты рождения'}, status=400)
                    update_data['birth_date'] = birth_date
                
                # Проверяем, есть ли данные для обновления
                if not update_data:
                    return JsonResponse({'error': 'Не указаны данные для обновления'}, status=400)
                
                # Обновляем профиль ребенка
                updated_child = update_child(child_id, **update_data)
                
                # Возвращаем обновленный профиль
                return JsonResponse(child_to_dict(updated_child))
            except Exception as e:
                logger.error(f"Ошибка при обновлении профиля ребенка в базе данных: {e}")
                return JsonResponse({'error': f'Ошибка при обновлении профиля ребенка: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении профиля ребенка {child_id} для пользователя {user_id}: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)
    
    def delete(self, request, user_id, child_id):
        """Удалить профиль ребенка."""
        try:
            # Преобразуем ID в целые числа
            try:
                user_id = int(user_id)
                child_id = int(child_id)
            except ValueError:
                return JsonResponse({'error': 'Неверный формат ID пользователя или ребенка'}, status=400)
            
            # Получаем ребенка
            try:
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
                logger.error(f"Ошибка при удалении профиля ребенка из базы данных: {e}")
                return JsonResponse({'error': f'Ошибка при удалении профиля ребенка: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка при удалении профиля ребенка {child_id} для пользователя {user_id}: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)


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
            try:
                user_id = int(user_id)
                child_id = int(child_id)
            except ValueError:
                return JsonResponse({'error': 'Неверный формат ID пользователя или ребенка'}, status=400)
            
            # Получаем ребенка
            try:
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
                logger.error(f"Ошибка при получении измерений из базы данных: {e}")
                return JsonResponse({'error': f'Ошибка при получении измерений: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка при получении измерений для ребенка {child_id}: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)
    
    def post(self, request, user_id, child_id):
        """Создать новое измерение для ребенка."""
        try:
            # Преобразуем ID в целые числа
            try:
                user_id = int(user_id)
                child_id = int(child_id)
            except ValueError:
                return JsonResponse({'error': 'Неверный формат ID пользователя или ребенка'}, status=400)
            
            # Получаем ребенка
            try:
                child = get_child(child_id)
                
                # Проверяем существование ребенка и принадлежность пользователю
                if not child:
                    return JsonResponse({'error': 'Ребенок не найден'}, status=404)
                
                if child.user_id != user_id:
                    return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
                
                # Разбираем данные запроса
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Невалидный JSON в запросе'}, status=400)
                
                # Проверяем наличие хотя бы одного параметра измерения
                if not any(key in data for key in ['height', 'weight', 'head_circumference']):
                    return JsonResponse({'error': 'Необходимо указать хотя бы один параметр измерения (рост, вес или окружность головы)'}, status=400)
                
                # Проверяем корректность числовых значений
                for param in ['height', 'weight', 'head_circumference']:
                    if param in data and data[param] is not None:
                        try:
                            data[param] = float(data[param])
                            if data[param] <= 0:
                                return JsonResponse({'error': f'Значение {param} должно быть положительным числом'}, status=400)
                        except (ValueError, TypeError):
                            return JsonResponse({'error': f'Неверный формат значения {param}'}, status=400)
                
                # Разбираем дату, если она указана
                date = None
                if 'date' in data:
                    date = parse_datetime(data['date'])
                    if data['date'] and not date:
                        return JsonResponse({'error': 'Неверный формат даты'}, status=400)
                
                # Создаем измерение
                try:
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
                    logger.error(f"Ошибка при создании измерения в базе данных: {e}")
                    return JsonResponse({'error': f'Ошибка при создании измерения: {str(e)}'}, status=500)
            except Exception as e:
                logger.error(f"Ошибка при проверке ребенка: {e}")
                return JsonResponse({'error': f'Ошибка при проверке данных: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка при создании измерения для ребенка {child_id}: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)


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
            try:
                user_id = int(user_id)
                child_id = int(child_id)
                measurement_id = int(measurement_id)
            except ValueError:
                return JsonResponse({'error': 'Неверный формат ID пользователя, ребенка или измерения'}, status=400)
            
            # Получаем ребенка
            try:
                child = get_child(child_id)
                
                # Проверяем существование ребенка и принадлежность пользователю
                if not child:
                    return JsonResponse({'error': 'Ребенок не найден'}, status=404)
                
                if child.user_id != user_id:
                    return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
                
                # Получаем измерение
                db_manager = get_db_manager()

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
                logger.error(f"Ошибка при получении данных из базы данных: {e}")
                return JsonResponse({'error': f'Ошибка при получении данных: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка при получении измерения {measurement_id} для ребенка {child_id}: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)
    
    def put(self, request, user_id, child_id, measurement_id):
        """Обновить измерение."""
        try:
            # Преобразуем ID в целые числа
            try:
                user_id = int(user_id)
                child_id = int(child_id)
                measurement_id = int(measurement_id)
            except ValueError:
                return JsonResponse({'error': 'Неверный формат ID пользователя, ребенка или измерения'}, status=400)
            
            # Получаем ребенка
            try:
                child = get_child(child_id)
                
                # Проверяем существование ребенка и принадлежность пользователю
                if not child:
                    return JsonResponse({'error': 'Ребенок не найден'}, status=404)
                
                if child.user_id != user_id:
                    return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
                
                # Получаем измерение
                db_manager = get_db_manager()

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
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Невалидный JSON в запросе'}, status=400)
                
                # Подготавливаем данные для обновления
                update_data = {}
                
                # Проверяем корректность числовых значений
                for param in ['height', 'weight', 'head_circumference']:
                    if param in data and data[param] is not None:
                        try:
                            data[param] = float(data[param])
                            if data[param] <= 0:
                                return JsonResponse({'error': f'Значение {param} должно быть положительным числом'}, status=400)
                            update_data[param] = data[param]
                        except (ValueError, TypeError):
                            return JsonResponse({'error': f'Неверный формат значения {param}'}, status=400)
                
                if 'notes' in data:
                    update_data['notes'] = data['notes']
                
                if 'date' in data:
                    date = parse_datetime(data['date'])
                    if data['date'] and not date:
                        return JsonResponse({'error': 'Неверный формат даты'}, status=400)
                    update_data['date'] = date
                
                # Проверяем, есть ли данные для обновления
                if not update_data:
                    return JsonResponse({'error': 'Не указаны данные для обновления'}, status=400)
                
                # Обновляем измерение
                try:
                    updated_measurement = update_measurement(measurement_id, **update_data)
                    
                    # Возвращаем обновленное измерение
                    return JsonResponse(measurement_to_dict(updated_measurement))
                except Exception as e:
                    logger.error(f"Ошибка при обновлении измерения в базе данных: {e}")
                    return JsonResponse({'error': f'Ошибка при обновлении измерения: {str(e)}'}, status=500)
            except Exception as e:
                logger.error(f"Ошибка при проверке данных: {e}")
                return JsonResponse({'error': f'Ошибка при проверке данных: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении измерения {measurement_id} для ребенка {child_id}: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)
    
    def delete(self, request, user_id, child_id, measurement_id):
        """Удалить измерение."""
        try:
            # Преобразуем ID в целые числа
            try:
                user_id = int(user_id)
                child_id = int(child_id)
                measurement_id = int(measurement_id)
            except ValueError:
                return JsonResponse({'error': 'Неверный формат ID пользователя, ребенка или измерения'}, status=400)
            
            # Получаем ребенка
            try:
                child = get_child(child_id)
                
                # Проверяем существование ребенка и принадлежность пользователю
                if not child:
                    return JsonResponse({'error': 'Ребенок не найден'}, status=404)
                
                if child.user_id != user_id:
                    return JsonResponse({'error': 'Ребенок не принадлежит этому пользователю'}, status=403)
                
                # Получаем измерение
                db_manager = get_db_manager()

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
                try:
                    success = delete_measurement(measurement_id)
                    
                    if success:
                        return JsonResponse({'message': 'Измерение успешно удалено'})
                    else:
                        return JsonResponse({'error': 'Не удалось удалить измерение'}, status=500)
                except Exception as e:
                    logger.error(f"Ошибка при удалении измерения из базы данных: {e}")
                    return JsonResponse({'error': f'Ошибка при удалении измерения: {str(e)}'}, status=500)
            except Exception as e:
                logger.error(f"Ошибка при проверке данных: {e}")
                return JsonResponse({'error': f'Ошибка при проверке данных: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка при удалении измерения {measurement_id} для ребенка {child_id}: {e}")
            return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)


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