from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
import json
import logging

from .models import FetalDevelopmentInfo, PregnancyInfo

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class FetalDevelopmentView(View):
    """
    API для получения информации о развитии плода по неделям беременности.
    
    Соответствует требованию 10.3 о предоставлении информации о развитии плода
    для каждой недели беременности.
    """
    
    def get(self, request, week_number=None):
        """
        Получает информацию о развитии плода для указанной недели или текущей недели пользователя.
        
        Args:
            week_number (int, optional): Номер недели беременности
            
        Returns:
            JsonResponse: Информация о развитии плода
        """
        try:
            if week_number is not None:
                # Получаем информацию для конкретной недели
                try:
                    week_number = int(week_number)
                    if week_number < 1 or week_number > 42:
                        return JsonResponse({
                            'success': False,
                            'error': 'Номер недели должен быть от 1 до 42'
                        }, status=400)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Неверный формат номера недели'
                    }, status=400)
                
                development_info = FetalDevelopmentInfo.get_info_for_week(week_number)
                if not development_info:
                    return JsonResponse({
                        'success': False,
                        'error': f'Информация для {week_number}-й недели не найдена'
                    }, status=404)
                
                return JsonResponse({
                    'success': True,
                    'data': self._serialize_development_info(development_info)
                })
            
            else:
                # Получаем информацию для текущей недели пользователя
                try:
                    pregnancy_info = PregnancyInfo.get_active_pregnancy(request.user)
                    if not pregnancy_info:
                        return JsonResponse({
                            'success': False,
                            'error': 'Активная беременность не найдена'
                        }, status=404)
                    
                    current_week = pregnancy_info.current_week
                    development_info = FetalDevelopmentInfo.get_info_for_week(current_week)
                    
                    if not development_info:
                        return JsonResponse({
                            'success': False,
                            'error': f'Информация для {current_week}-й недели не найдена'
                        }, status=404)
                    
                    # Получаем также информацию о предыдущей и следующей неделе
                    previous_week = development_info.get_previous_week_info()
                    next_week = development_info.get_next_week_info()
                    
                    return JsonResponse({
                        'success': True,
                        'data': {
                            'current': self._serialize_development_info(development_info),
                            'previous': self._serialize_development_info(previous_week) if previous_week else None,
                            'next': self._serialize_development_info(next_week) if next_week else None,
                            'pregnancy_info': {
                                'current_week': current_week,
                                'due_date': pregnancy_info.due_date.isoformat() if pregnancy_info.due_date else None,
                                'days_until_due': pregnancy_info.days_until_due,
                                'trimester': pregnancy_info.trimester
                            }
                        }
                    })
                    
                except Exception as e:
                    logger.error(f"Ошибка при получении информации о беременности для пользователя {request.user.id}: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Ошибка при получении информации о беременности'
                    }, status=500)
        
        except Exception as e:
            logger.error(f"Ошибка в FetalDevelopmentView.get: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Внутренняя ошибка сервера'
            }, status=500)
    
    def _serialize_development_info(self, development_info):
        """
        Сериализует информацию о развитии плода для JSON ответа.
        
        Args:
            development_info (FetalDevelopmentInfo): Информация о развитии плода
            
        Returns:
            dict: Сериализованные данные
        """
        if not development_info:
            return None
        
        return {
            'week_number': development_info.week_number,
            'title': development_info.title,
            'fetal_size_description': development_info.fetal_size_description,
            'fetal_size_formatted': development_info.fetal_size_formatted,
            'fetal_length_mm': development_info.fetal_length_mm,
            'fetal_weight_g': development_info.fetal_weight_g,
            'organ_development': development_info.organ_development,
            'maternal_changes': development_info.maternal_changes,
            'common_symptoms': development_info.common_symptoms,
            'recommendations': development_info.recommendations,
            'dos_and_donts': development_info.dos_and_donts,
            'medical_checkups': development_info.medical_checkups,
            'interesting_facts': development_info.interesting_facts,
            'trimester': development_info.trimester,
            'trimester_name': development_info.trimester_name,
            'development_summary': development_info.get_development_summary(),
            'illustration_image': development_info.illustration_image.url if development_info.illustration_image else None
        }


@method_decorator(login_required, name='dispatch')
class FetalDevelopmentListView(View):
    """
    API для получения списка информации о развитии плода.
    """
    
    def get(self, request):
        """
        Получает список информации о развитии плода с возможностью фильтрации.
        
        Query parameters:
            - trimester: Номер триместра (1, 2, 3)
            - start_week: Начальная неделя для диапазона
            - end_week: Конечная неделя для диапазона
            - summary_only: Если true, возвращает только краткую информацию
            
        Returns:
            JsonResponse: Список информации о развитии плода
        """
        try:
            trimester = request.GET.get('trimester')
            start_week = request.GET.get('start_week')
            end_week = request.GET.get('end_week')
            summary_only = request.GET.get('summary_only', '').lower() == 'true'
            
            # Определяем queryset на основе параметров
            if trimester:
                try:
                    trimester = int(trimester)
                    if trimester not in [1, 2, 3]:
                        return JsonResponse({
                            'success': False,
                            'error': 'Номер триместра должен быть 1, 2 или 3'
                        }, status=400)
                    
                    queryset = FetalDevelopmentInfo.get_by_trimester(trimester)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Неверный формат номера триместра'
                    }, status=400)
            
            elif start_week and end_week:
                try:
                    start_week = int(start_week)
                    end_week = int(end_week)
                    
                    if start_week < 1 or end_week > 42 or start_week > end_week:
                        return JsonResponse({
                            'success': False,
                            'error': 'Неверный диапазон недель'
                        }, status=400)
                    
                    queryset = FetalDevelopmentInfo.get_weeks_range(start_week, end_week)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Неверный формат номеров недель'
                    }, status=400)
            
            else:
                # Возвращаем все записи
                queryset = FetalDevelopmentInfo.objects.filter(is_active=True).order_by('week_number')
            
            # Сериализуем данные
            data = []
            for development_info in queryset:
                if summary_only:
                    # Краткая информация
                    item = {
                        'week_number': development_info.week_number,
                        'title': development_info.title,
                        'fetal_size_description': development_info.fetal_size_description,
                        'development_summary': development_info.get_development_summary(),
                        'trimester': development_info.trimester,
                        'trimester_name': development_info.trimester_name
                    }
                else:
                    # Полная информация
                    item = self._serialize_development_info(development_info)
                
                data.append(item)
            
            return JsonResponse({
                'success': True,
                'data': data,
                'count': len(data)
            })
        
        except Exception as e:
            logger.error(f"Ошибка в FetalDevelopmentListView.get: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Внутренняя ошибка сервера'
            }, status=500)
    
    def _serialize_development_info(self, development_info):
        """
        Сериализует информацию о развитии плода для JSON ответа.
        
        Args:
            development_info (FetalDevelopmentInfo): Информация о развитии плода
            
        Returns:
            dict: Сериализованные данные
        """
        return {
            'week_number': development_info.week_number,
            'title': development_info.title,
            'fetal_size_description': development_info.fetal_size_description,
            'fetal_size_formatted': development_info.fetal_size_formatted,
            'fetal_length_mm': development_info.fetal_length_mm,
            'fetal_weight_g': development_info.fetal_weight_g,
            'organ_development': development_info.organ_development,
            'maternal_changes': development_info.maternal_changes,
            'common_symptoms': development_info.common_symptoms,
            'recommendations': development_info.recommendations,
            'dos_and_donts': development_info.dos_and_donts,
            'medical_checkups': development_info.medical_checkups,
            'interesting_facts': development_info.interesting_facts,
            'trimester': development_info.trimester,
            'trimester_name': development_info.trimester_name,
            'development_summary': development_info.get_development_summary(),
            'illustration_image': development_info.illustration_image.url if development_info.illustration_image else None
        }


@require_http_methods(["GET"])
@login_required
def fetal_development_week(request, week_number):
    """
    Функциональное представление для получения информации о развитии плода для конкретной недели.
    
    Args:
        request: HTTP запрос
        week_number (int): Номер недели беременности
        
    Returns:
        JsonResponse: Информация о развитии плода
    """
    view = FetalDevelopmentView()
    return view.get(request, week_number)


@require_http_methods(["GET"])
@login_required
def fetal_development_current(request):
    """
    Функциональное представление для получения информации о развитии плода для текущей недели пользователя.
    
    Args:
        request: HTTP запрос
        
    Returns:
        JsonResponse: Информация о развитии плода для текущей недели
    """
    view = FetalDevelopmentView()
    return view.get(request)


@require_http_methods(["GET"])
@login_required
def fetal_development_list(request):
    """
    Функциональное представление для получения списка информации о развитии плода.
    
    Args:
        request: HTTP запрос
        
    Returns:
        JsonResponse: Список информации о развитии плода
    """
    view = FetalDevelopmentListView()
    return view.get(request)