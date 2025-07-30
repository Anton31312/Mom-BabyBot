"""
API эндпоинты для отслеживания показателей здоровья.

Этот модуль содержит представления API для работы с записями веса и артериального давления.
Соответствует требованиям 7.1 и 7.2 о возможности отслеживания веса и артериального давления.
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from webapp.models import WeightRecord, BloodPressureRecord

logger = logging.getLogger(__name__)


def weight_record_to_dict(weight_record):
    """Преобразует объект WeightRecord в словарь."""
    return {
        'id': weight_record.id,
        'user_id': weight_record.user.id,
        'date': weight_record.date.isoformat(),
        'weight': float(weight_record.weight),
        'notes': weight_record.notes,
        'created_at': weight_record.created_at.isoformat(),
        'updated_at': weight_record.updated_at.isoformat(),
    }


def blood_pressure_record_to_dict(bp_record):
    """Преобразует объект BloodPressureRecord в словарь."""
    return {
        'id': bp_record.id,
        'user_id': bp_record.user.id,
        'date': bp_record.date.isoformat(),
        'systolic': bp_record.systolic,
        'diastolic': bp_record.diastolic,
        'pulse': bp_record.pulse,
        'pressure_reading': bp_record.pressure_reading,
        'pressure_category': bp_record.get_pressure_category(),
        'is_normal': bp_record.is_pressure_normal(),
        'needs_medical_attention': bp_record.needs_medical_attention(),
        'systolic_status': bp_record.is_systolic_normal(),
        'diastolic_status': bp_record.is_diastolic_normal(),
        'notes': bp_record.notes,
        'created_at': bp_record.created_at.isoformat(),
        'updated_at': bp_record.updated_at.isoformat(),
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def weight_records(request, user_id):
    """
    Получение списка записей веса или создание новой записи.
    
    GET: Получить все записи веса для пользователя
    POST: Создать новую запись веса
    """
    try:
        # Преобразуем ID в целое число
        user_id = int(user_id)
        
        # Проверяем существование пользователя
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь не найден'}, status=404)
        
        if request.method == 'GET':
            # Получаем параметры фильтрации
            days = request.GET.get('days')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Базовый запрос
            queryset = WeightRecord.objects.filter(user=user)
            
            # Применяем фильтры
            if days:
                try:
                    days_int = int(days)
                    start_date_filter = timezone.now() - timedelta(days=days_int)
                    queryset = queryset.filter(date__gte=start_date_filter)
                except ValueError:
                    return JsonResponse({'error': 'Параметр days должен быть числом'}, status=400)
            
            if start_date:
                try:
                    start_date_parsed = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    queryset = queryset.filter(date__gte=start_date_parsed)
                except ValueError:
                    return JsonResponse({'error': 'Неверный формат start_date'}, status=400)
            
            if end_date:
                try:
                    end_date_parsed = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    queryset = queryset.filter(date__lte=end_date_parsed)
                except ValueError:
                    return JsonResponse({'error': 'Неверный формат end_date'}, status=400)
            
            # Получаем записи
            weight_records_list = list(queryset)
            
            # Преобразуем в словарь
            weight_records_data = [weight_record_to_dict(wr) for wr in weight_records_list]
            
            return JsonResponse({
                'weight_records': weight_records_data,
                'count': len(weight_records_data)
            })
            
        elif request.method == 'POST':
            # Разбираем данные запроса
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
            
            # Валидируем обязательные поля
            if 'weight' not in data:
                return JsonResponse({'error': 'Поле weight обязательно'}, status=400)
            
            try:
                weight = Decimal(str(data['weight']))
            except (InvalidOperation, ValueError):
                return JsonResponse({'error': 'Неверный формат веса'}, status=400)
            
            # Парсим дату
            record_date = timezone.now()
            if 'date' in data:
                try:
                    record_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
                    if timezone.is_naive(record_date):
                        record_date = timezone.make_aware(record_date)
                except ValueError:
                    return JsonResponse({'error': 'Неверный формат даты'}, status=400)
            
            # Создаем запись веса
            try:
                weight_record = WeightRecord(
                    user=user,
                    date=record_date,
                    weight=weight,
                    notes=data.get('notes', '')
                )
                weight_record.full_clean()  # Валидация модели
                weight_record.save()
                
                return JsonResponse(weight_record_to_dict(weight_record), status=201)
                
            except ValidationError as e:
                return JsonResponse({'error': f'Ошибка валидации: {e}'}, status=400)
            except Exception as e:
                logger.error(f"Error creating weight record: {e}")
                return JsonResponse({'error': 'Ошибка при создании записи веса'}, status=500)
            
    except Exception as e:
        logger.error(f"Error in weight_records: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def weight_record_detail(request, user_id, record_id):
    """
    Получение, обновление или удаление конкретной записи веса.
    
    GET: Получить детали записи веса
    PUT: Обновить запись веса
    DELETE: Удалить запись веса
    """
    try:
        # Преобразуем ID в целые числа
        user_id = int(user_id)
        record_id = int(record_id)
        
        # Проверяем существование пользователя
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь не найден'}, status=404)
        
        # Получаем запись веса
        try:
            weight_record = WeightRecord.objects.get(id=record_id, user=user)
        except WeightRecord.DoesNotExist:
            return JsonResponse({'error': 'Запись веса не найдена'}, status=404)
        
        if request.method == 'GET':
            # Возвращаем данные записи веса
            return JsonResponse(weight_record_to_dict(weight_record))
            
        elif request.method == 'PUT':
            # Разбираем данные запроса
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
            
            # Обновляем поля
            if 'weight' in data:
                try:
                    weight_record.weight = Decimal(str(data['weight']))
                except (InvalidOperation, ValueError):
                    return JsonResponse({'error': 'Неверный формат веса'}, status=400)
            
            if 'date' in data:
                try:
                    record_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
                    if timezone.is_naive(record_date):
                        record_date = timezone.make_aware(record_date)
                    weight_record.date = record_date
                except ValueError:
                    return JsonResponse({'error': 'Неверный формат даты'}, status=400)
            
            if 'notes' in data:
                weight_record.notes = data['notes']
            
            try:
                weight_record.full_clean()  # Валидация модели
                weight_record.save()
                
                return JsonResponse(weight_record_to_dict(weight_record))
                
            except ValidationError as e:
                return JsonResponse({'error': f'Ошибка валидации: {e}'}, status=400)
            
        elif request.method == 'DELETE':
            # Удаляем запись веса
            weight_record.delete()
            
            return JsonResponse({'message': 'Запись веса успешно удалена'})
            
    except Exception as e:
        logger.error(f"Error in weight_record_detail: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def blood_pressure_records(request, user_id):
    """
    Получение списка записей артериального давления или создание новой записи.
    
    GET: Получить все записи давления для пользователя
    POST: Создать новую запись давления
    """
    try:
        # Преобразуем ID в целое число
        user_id = int(user_id)
        
        # Проверяем существование пользователя
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь не найден'}, status=404)
        
        if request.method == 'GET':
            # Получаем параметры фильтрации
            days = request.GET.get('days')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Базовый запрос
            queryset = BloodPressureRecord.objects.filter(user=user)
            
            # Применяем фильтры
            if days:
                try:
                    days_int = int(days)
                    start_date_filter = timezone.now() - timedelta(days=days_int)
                    queryset = queryset.filter(date__gte=start_date_filter)
                except ValueError:
                    return JsonResponse({'error': 'Параметр days должен быть числом'}, status=400)
            
            if start_date:
                try:
                    start_date_parsed = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    queryset = queryset.filter(date__gte=start_date_parsed)
                except ValueError:
                    return JsonResponse({'error': 'Неверный формат start_date'}, status=400)
            
            if end_date:
                try:
                    end_date_parsed = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    queryset = queryset.filter(date__lte=end_date_parsed)
                except ValueError:
                    return JsonResponse({'error': 'Неверный формат end_date'}, status=400)
            
            # Получаем записи
            bp_records_list = list(queryset)
            
            # Преобразуем в словарь
            bp_records_data = [blood_pressure_record_to_dict(bp) for bp in bp_records_list]
            
            return JsonResponse({
                'blood_pressure_records': bp_records_data,
                'count': len(bp_records_data)
            })
            
        elif request.method == 'POST':
            # Разбираем данные запроса
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
            
            # Валидируем обязательные поля
            if 'systolic' not in data or 'diastolic' not in data:
                return JsonResponse({'error': 'Поля systolic и diastolic обязательны'}, status=400)
            
            try:
                systolic = int(data['systolic'])
                diastolic = int(data['diastolic'])
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Неверный формат значений давления'}, status=400)
            
            # Парсим пульс (опционально)
            pulse = None
            if 'pulse' in data and data['pulse'] is not None:
                try:
                    pulse = int(data['pulse'])
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'Неверный формат пульса'}, status=400)
            
            # Парсим дату
            record_date = timezone.now()
            if 'date' in data:
                try:
                    record_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
                    if timezone.is_naive(record_date):
                        record_date = timezone.make_aware(record_date)
                except ValueError:
                    return JsonResponse({'error': 'Неверный формат даты'}, status=400)
            
            # Создаем запись давления
            try:
                bp_record = BloodPressureRecord(
                    user=user,
                    date=record_date,
                    systolic=systolic,
                    diastolic=diastolic,
                    pulse=pulse,
                    notes=data.get('notes', '')
                )
                bp_record.full_clean()  # Валидация модели
                bp_record.save()
                
                return JsonResponse(blood_pressure_record_to_dict(bp_record), status=201)
                
            except ValidationError as e:
                return JsonResponse({'error': f'Ошибка валидации: {e}'}, status=400)
            except Exception as e:
                logger.error(f"Error creating blood pressure record: {e}")
                return JsonResponse({'error': 'Ошибка при создании записи давления'}, status=500)
            
    except Exception as e:
        logger.error(f"Error in blood_pressure_records: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def blood_pressure_record_detail(request, user_id, record_id):
    """
    Получение, обновление или удаление конкретной записи артериального давления.
    
    GET: Получить детали записи давления
    PUT: Обновить запись давления
    DELETE: Удалить запись давления
    """
    try:
        # Преобразуем ID в целые числа
        user_id = int(user_id)
        record_id = int(record_id)
        
        # Проверяем существование пользователя
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь не найден'}, status=404)
        
        # Получаем запись давления
        try:
            bp_record = BloodPressureRecord.objects.get(id=record_id, user=user)
        except BloodPressureRecord.DoesNotExist:
            return JsonResponse({'error': 'Запись давления не найдена'}, status=404)
        
        if request.method == 'GET':
            # Возвращаем данные записи давления
            return JsonResponse(blood_pressure_record_to_dict(bp_record))
            
        elif request.method == 'PUT':
            # Разбираем данные запроса
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
            
            # Обновляем поля
            if 'systolic' in data:
                try:
                    bp_record.systolic = int(data['systolic'])
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'Неверный формат систолического давления'}, status=400)
            
            if 'diastolic' in data:
                try:
                    bp_record.diastolic = int(data['diastolic'])
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'Неверный формат диастолического давления'}, status=400)
            
            if 'pulse' in data:
                if data['pulse'] is not None:
                    try:
                        bp_record.pulse = int(data['pulse'])
                    except (ValueError, TypeError):
                        return JsonResponse({'error': 'Неверный формат пульса'}, status=400)
                else:
                    bp_record.pulse = None
            
            if 'date' in data:
                try:
                    record_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
                    if timezone.is_naive(record_date):
                        record_date = timezone.make_aware(record_date)
                    bp_record.date = record_date
                except ValueError:
                    return JsonResponse({'error': 'Неверный формат даты'}, status=400)
            
            if 'notes' in data:
                bp_record.notes = data['notes']
            
            try:
                bp_record.full_clean()  # Валидация модели
                bp_record.save()
                
                return JsonResponse(blood_pressure_record_to_dict(bp_record))
                
            except ValidationError as e:
                return JsonResponse({'error': f'Ошибка валидации: {e}'}, status=400)
            
        elif request.method == 'DELETE':
            # Удаляем запись давления
            bp_record.delete()
            
            return JsonResponse({'message': 'Запись давления успешно удалена'})
            
    except Exception as e:
        logger.error(f"Error in blood_pressure_record_detail: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def health_statistics(request, user_id):
    """
    Получение статистики показателей здоровья для пользователя.
    
    GET: Получить статистику веса и давления (средние значения, тренды и т.д.)
    """
    try:
        # Преобразуем ID в целое число
        user_id = int(user_id)
        
        # Проверяем существование пользователя
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь не найден'}, status=404)
        
        # Получаем параметры
        days = int(request.GET.get('days', 30))  # По умолчанию 30 дней
        
        # Определяем временной диапазон
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Получаем записи веса
        weight_records = WeightRecord.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Получаем записи давления
        bp_records = BloodPressureRecord.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Статистика веса
        weight_stats = {
            'count': weight_records.count(),
            'latest_weight': None,
            'average_weight': None,
            'min_weight': None,
            'max_weight': None,
            'weight_change': None,
            'trend': 'stable'
        }
        
        if weight_records.exists():
            weights = [float(wr.weight) for wr in weight_records]
            weight_stats.update({
                'latest_weight': weights[-1],
                'average_weight': round(sum(weights) / len(weights), 2),
                'min_weight': min(weights),
                'max_weight': max(weights),
            })
            
            # Расчет изменения веса
            if len(weights) > 1:
                weight_stats['weight_change'] = round(weights[-1] - weights[0], 2)
                
                # Определение тренда
                if weight_stats['weight_change'] > 1:
                    weight_stats['trend'] = 'increasing'
                elif weight_stats['weight_change'] < -1:
                    weight_stats['trend'] = 'decreasing'
        
        # Статистика давления
        bp_stats = {
            'count': bp_records.count(),
            'latest_systolic': None,
            'latest_diastolic': None,
            'average_systolic': None,
            'average_diastolic': None,
            'min_systolic': None,
            'max_systolic': None,
            'min_diastolic': None,
            'max_diastolic': None,
            'normal_readings_count': 0,
            'high_readings_count': 0,
            'low_readings_count': 0,
            'critical_readings_count': 0
        }
        
        if bp_records.exists():
            systolic_values = [bp.systolic for bp in bp_records]
            diastolic_values = [bp.diastolic for bp in bp_records]
            
            bp_stats.update({
                'latest_systolic': systolic_values[-1],
                'latest_diastolic': diastolic_values[-1],
                'average_systolic': round(sum(systolic_values) / len(systolic_values), 1),
                'average_diastolic': round(sum(diastolic_values) / len(diastolic_values), 1),
                'min_systolic': min(systolic_values),
                'max_systolic': max(systolic_values),
                'min_diastolic': min(diastolic_values),
                'max_diastolic': max(diastolic_values),
            })
            
            # Подсчет категорий давления
            for bp in bp_records:
                if bp.needs_medical_attention():
                    bp_stats['critical_readings_count'] += 1
                elif bp.is_pressure_normal():
                    bp_stats['normal_readings_count'] += 1
                elif bp.is_systolic_normal() == 'high' or bp.is_diastolic_normal() == 'high':
                    bp_stats['high_readings_count'] += 1
                else:
                    bp_stats['low_readings_count'] += 1
        
        # Рекомендации
        recommendations = []
        
        # Рекомендации по весу
        if weight_stats['count'] > 0:
            if weight_stats['trend'] == 'increasing':
                recommendations.append({
                    'type': 'weight',
                    'level': 'info',
                    'message': 'Наблюдается тенденция к увеличению веса. Рекомендуется консультация с врачом.'
                })
            elif weight_stats['trend'] == 'decreasing':
                recommendations.append({
                    'type': 'weight',
                    'level': 'info',
                    'message': 'Наблюдается тенденция к снижению веса. Рекомендуется консультация с врачом.'
                })
        
        # Рекомендации по давлению
        if bp_stats['critical_readings_count'] > 0:
            recommendations.append({
                'type': 'blood_pressure',
                'level': 'critical',
                'message': f'Обнаружено {bp_stats["critical_readings_count"]} критических показаний давления. Необходима срочная консультация врача!'
            })
        elif bp_stats['high_readings_count'] > bp_stats['count'] * 0.5:
            recommendations.append({
                'type': 'blood_pressure',
                'level': 'warning',
                'message': 'Более половины измерений показывают повышенное давление. Рекомендуется консультация с врачом.'
            })
        
        return JsonResponse({
            'period_days': days,
            'weight_statistics': weight_stats,
            'blood_pressure_statistics': bp_stats,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Error in health_statistics: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def health_data_export(request, user_id):
    """
    Экспорт данных о здоровье в формате JSON.
    
    GET: Получить все данные о здоровье пользователя для экспорта
    """
    try:
        # Преобразуем ID в целое число
        user_id = int(user_id)
        
        # Проверяем существование пользователя
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь не найден'}, status=404)
        
        # Получаем все записи веса
        weight_records = WeightRecord.objects.filter(user=user).order_by('date')
        weight_data = [weight_record_to_dict(wr) for wr in weight_records]
        
        # Получаем все записи давления
        bp_records = BloodPressureRecord.objects.filter(user=user).order_by('date')
        bp_data = [blood_pressure_record_to_dict(bp) for bp in bp_records]
        
        return JsonResponse({
            'user_id': user_id,
            'export_date': timezone.now().isoformat(),
            'weight_records': weight_data,
            'blood_pressure_records': bp_data,
            'total_weight_records': len(weight_data),
            'total_bp_records': len(bp_data)
        })
        
    except Exception as e:
        logger.error(f"Error in health_data_export: {e}")
        return JsonResponse({'error': str(e)}, status=500)