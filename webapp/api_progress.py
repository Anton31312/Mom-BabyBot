"""
API для визуальной статистики прогресса пользователей.

Этот модуль содержит API-представления для сбора, анализа и отображения
статистики прогресса пользователей в различных аспектах использования приложения.

Соответствует требованию 9.4 о предоставлении визуальной статистики прогресса и достижений.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta, date
import json
import logging

from .models import (
    FeedingSession, WeightRecord, BloodPressureRecord, UserProfile,
    Achievement, UserAchievement, PersonalizedContent, UserContentView,
    DailyTip
)

logger = logging.getLogger(__name__)


@method_decorator([login_required, csrf_exempt], name='dispatch')
class ProgressStatisticsView(View):
    """
    API для получения общей статистики прогресса пользователя.
    
    GET: Возвращает комплексную статистику активности и прогресса пользователя
    """
    
    def get(self, request):
        """
        Возвращает статистику прогресса для текущего пользователя.
        
        Query параметры:
        - period: период для анализа ('week', 'month', 'quarter', 'year', 'all')
        - include_details: включать ли детальную разбивку по дням/неделям
        """
        try:
            user = request.user
            period = request.GET.get('period', 'month')
            include_details = request.GET.get('include_details', 'false').lower() == 'true'
            
            # Определяем временной период
            end_date = timezone.now()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'quarter':
                start_date = end_date - timedelta(days=90)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:  # 'all'
                start_date = None
            
            # Собираем статистику
            stats = self._collect_user_statistics(user, start_date, end_date)
            
            # Добавляем детальную разбивку если запрошена
            if include_details:
                stats['details'] = self._get_detailed_breakdown(user, start_date, end_date, period)
            
            # Добавляем информацию о тенденциях
            stats['trends'] = self._calculate_trends(user, start_date, end_date)
            
            return JsonResponse({
                'success': True,
                'period': period,
                'statistics': stats
            })
            
        except Exception as e:
            logger.error(f'Ошибка при получении статистики прогресса для пользователя {request.user.id}: {e}')
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при загрузке статистики'
            }, status=500)
    
    def _collect_user_statistics(self, user, start_date, end_date):
        """
        Собирает основную статистику активности пользователя.
        
        Args:
            user: Пользователь
            start_date: Начальная дата периода (или None для всего времени)
            end_date: Конечная дата периода
            
        Returns:
            dict: Словарь со статистикой
        """
        stats = {}
        
        # Базовый фильтр по дате
        date_filter = Q()
        if start_date:
            date_filter = Q(created_at__gte=start_date, created_at__lte=end_date)
        
        # Статистика кормления
        feeding_filter = date_filter.copy()
        feeding_filter.children = [Q(start_time__gte=start_date, start_time__lte=end_date)] if start_date else []
        
        feeding_sessions = FeedingSession.objects.filter(user=user)
        if start_date:
            feeding_sessions = feeding_sessions.filter(start_time__gte=start_date, start_time__lte=end_date)
        
        stats['feeding'] = {
            'total_sessions': feeding_sessions.count(),
            'total_duration_minutes': sum(
                session.get_total_duration_minutes() for session in feeding_sessions
            ),
            'average_session_duration': feeding_sessions.aggregate(
                avg_duration=Avg('left_breast_duration') + Avg('right_breast_duration')
            )['avg_duration'] or 0,
            'left_breast_percentage': self._calculate_breast_preference(feeding_sessions, 'left'),
            'right_breast_percentage': self._calculate_breast_preference(feeding_sessions, 'right'),
        }
        
        # Статистика здоровья
        weight_records = WeightRecord.objects.filter(user=user)
        bp_records = BloodPressureRecord.objects.filter(user=user)
        
        if start_date:
            weight_records = weight_records.filter(date__gte=start_date, date__lte=end_date)
            bp_records = bp_records.filter(date__gte=start_date, date__lte=end_date)
        
        stats['health'] = {
            'weight_records_count': weight_records.count(),
            'blood_pressure_records_count': bp_records.count(),
            'latest_weight': self._get_latest_weight(user),
            'weight_trend': self._calculate_weight_trend(user, start_date),
            'average_blood_pressure': self._calculate_average_bp(bp_records),
            'bp_normal_percentage': self._calculate_bp_normal_percentage(bp_records),
        }
        
        # Статистика достижений
        user_achievements = UserAchievement.objects.filter(user=user)
        if start_date:
            user_achievements = user_achievements.filter(earned_at__gte=start_date, earned_at__lte=end_date)
        
        stats['achievements'] = {
            'total_earned': user_achievements.count(),
            'total_points': sum(ua.achievement.points for ua in user_achievements),
            'by_type': self._group_achievements_by_type(user_achievements),
            'by_difficulty': self._group_achievements_by_difficulty(user_achievements),
            'recent_achievements': user_achievements.order_by('-earned_at')[:5],
        }
        
        # Статистика взаимодействия с контентом
        content_views = UserContentView.objects.filter(user=user)
        if start_date:
            content_views = content_views.filter(viewed_at__gte=start_date, viewed_at__lte=end_date)
        
        stats['engagement'] = {
            'content_views': content_views.count(),
            'unique_content_viewed': content_views.values('content').distinct().count(),
            'interaction_types': content_views.values('interaction_type').annotate(
                count=Count('id')
            ),
            'daily_tips_viewed': content_views.filter(
                content__content_type='tip'
            ).count(),
        }
        
        # Общая активность
        stats['activity'] = {
            'total_actions': (
                stats['feeding']['total_sessions'] +
                stats['health']['weight_records_count'] +
                stats['health']['blood_pressure_records_count'] +
                stats['engagement']['content_views']
            ),
            'days_active': self._calculate_active_days(user, start_date, end_date),
            'consistency_score': self._calculate_consistency_score(user, start_date, end_date),
        }
        
        return stats
    
    def _calculate_breast_preference(self, feeding_sessions, breast):
        """Вычисляет процент времени кормления для указанной груди."""
        total_duration = sum(session.total_duration.total_seconds() for session in feeding_sessions)
        if total_duration == 0:
            return 0
        
        breast_duration = sum(
            getattr(session, f'{breast}_breast_duration').total_seconds()
            for session in feeding_sessions
        )
        
        return round((breast_duration / total_duration) * 100, 1)
    
    def _get_latest_weight(self, user):
        """Получает последнюю запись веса пользователя."""
        latest_record = WeightRecord.objects.filter(user=user).order_by('-date').first()
        return float(latest_record.weight) if latest_record else None
    
    def _calculate_weight_trend(self, user, start_date):
        """Вычисляет тренд изменения веса."""
        records = WeightRecord.objects.filter(user=user).order_by('date')
        if start_date:
            records = records.filter(date__gte=start_date)
        
        if records.count() < 2:
            return 'insufficient_data'
        
        first_weight = float(records.first().weight)
        last_weight = float(records.last().weight)
        
        if last_weight > first_weight + 0.5:
            return 'increasing'
        elif last_weight < first_weight - 0.5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_average_bp(self, bp_records):
        """Вычисляет среднее артериальное давление."""
        if not bp_records.exists():
            return None
        
        avg_systolic = bp_records.aggregate(avg=Avg('systolic'))['avg']
        avg_diastolic = bp_records.aggregate(avg=Avg('diastolic'))['avg']
        
        return {
            'systolic': round(avg_systolic, 1) if avg_systolic else None,
            'diastolic': round(avg_diastolic, 1) if avg_diastolic else None,
        }
    
    def _calculate_bp_normal_percentage(self, bp_records):
        """Вычисляет процент нормальных показаний давления."""
        if not bp_records.exists():
            return 0
        
        normal_count = sum(1 for record in bp_records if record.is_pressure_normal())
        return round((normal_count / bp_records.count()) * 100, 1)
    
    def _group_achievements_by_type(self, user_achievements):
        """Группирует достижения по типам."""
        return user_achievements.values(
            'achievement__achievement_type'
        ).annotate(
            count=Count('id'),
            points=Sum('achievement__points')
        )
    
    def _group_achievements_by_difficulty(self, user_achievements):
        """Группирует достижения по сложности."""
        return user_achievements.values(
            'achievement__difficulty'
        ).annotate(
            count=Count('id'),
            points=Sum('achievement__points')
        )
    
    def _calculate_active_days(self, user, start_date, end_date):
        """Вычисляет количество дней активности пользователя."""
        if not start_date:
            start_date = timezone.now() - timedelta(days=365)  # Максимум год назад
        
        # Собираем даты всех активностей
        active_dates = set()
        
        # Даты кормления
        feeding_dates = FeedingSession.objects.filter(
            user=user,
            start_time__gte=start_date,
            start_time__lte=end_date
        ).values_list('start_time__date', flat=True)
        active_dates.update(feeding_dates)
        
        # Даты записей здоровья
        health_dates = list(WeightRecord.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).values_list('date__date', flat=True))
        
        health_dates.extend(BloodPressureRecord.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).values_list('date__date', flat=True))
        
        active_dates.update(health_dates)
        
        # Даты просмотра контента
        content_dates = UserContentView.objects.filter(
            user=user,
            viewed_at__gte=start_date,
            viewed_at__lte=end_date
        ).values_list('viewed_at__date', flat=True)
        active_dates.update(content_dates)
        
        return len(active_dates)
    
    def _calculate_consistency_score(self, user, start_date, end_date):
        """
        Вычисляет оценку постоянства использования приложения (0-100).
        
        Оценка основана на регулярности активности пользователя.
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        
        total_days = (end_date.date() - start_date.date()).days + 1
        active_days = self._calculate_active_days(user, start_date, end_date)
        
        if total_days == 0:
            return 0
        
        # Базовая оценка на основе процента активных дней
        base_score = (active_days / total_days) * 100
        
        # Бонус за последовательность (активность в последние дни)
        recent_activity = self._calculate_active_days(
            user,
            timezone.now() - timedelta(days=7),
            timezone.now()
        )
        consistency_bonus = min(recent_activity * 5, 20)  # Максимум 20 бонусных очков
        
        return min(round(base_score + consistency_bonus, 1), 100)
    
    def _get_detailed_breakdown(self, user, start_date, end_date, period):
        """
        Получает детальную разбивку статистики по дням/неделям.
        
        Args:
            user: Пользователь
            start_date: Начальная дата
            end_date: Конечная дата
            period: Период группировки ('week', 'month', etc.)
            
        Returns:
            dict: Детальная разбивка
        """
        if not start_date:
            return {}
        
        # Определяем интервал группировки
        if period == 'week':
            interval = timedelta(days=1)  # По дням для недели
        elif period in ['month', 'quarter']:
            interval = timedelta(days=7)  # По неделям для месяца/квартала
        else:
            interval = timedelta(days=30)  # По месяцам для года
        
        breakdown = []
        current_date = start_date
        
        while current_date < end_date:
            next_date = min(current_date + interval, end_date)
            
            # Собираем статистику для этого интервала
            interval_stats = self._collect_user_statistics(user, current_date, next_date)
            interval_stats['date'] = current_date.isoformat()
            interval_stats['period_end'] = next_date.isoformat()
            
            breakdown.append(interval_stats)
            current_date = next_date
        
        return breakdown
    
    def _calculate_trends(self, user, start_date, end_date):
        """
        Вычисляет тенденции изменения различных показателей.
        
        Returns:
            dict: Информация о трендах
        """
        if not start_date:
            return {}
        
        # Разделяем период пополам для сравнения
        mid_date = start_date + (end_date - start_date) / 2
        
        # Статистика первой половины периода
        first_half = self._collect_user_statistics(user, start_date, mid_date)
        # Статистика второй половины периода
        second_half = self._collect_user_statistics(user, mid_date, end_date)
        
        trends = {}
        
        # Тренд активности
        first_activity = first_half['activity']['total_actions']
        second_activity = second_half['activity']['total_actions']
        
        if first_activity > 0:
            activity_change = ((second_activity - first_activity) / first_activity) * 100
            trends['activity'] = {
                'direction': 'up' if activity_change > 5 else 'down' if activity_change < -5 else 'stable',
                'change_percentage': round(activity_change, 1)
            }
        else:
            trends['activity'] = {'direction': 'stable', 'change_percentage': 0}
        
        # Тренд достижений
        first_achievements = first_half['achievements']['total_earned']
        second_achievements = second_half['achievements']['total_earned']
        
        trends['achievements'] = {
            'direction': 'up' if second_achievements > first_achievements else 'stable',
            'new_achievements': second_achievements
        }
        
        # Тренд постоянства
        first_consistency = first_half['activity']['consistency_score']
        second_consistency = second_half['activity']['consistency_score']
        
        consistency_change = second_consistency - first_consistency
        trends['consistency'] = {
            'direction': 'up' if consistency_change > 5 else 'down' if consistency_change < -5 else 'stable',
            'change_points': round(consistency_change, 1)
        }
        
        return trends


@method_decorator([login_required, csrf_exempt], name='dispatch')
class ProgressChartsView(View):
    """
    API для получения данных для построения графиков прогресса.
    
    GET: Возвращает данные в формате, подходящем для построения графиков
    """
    
    def get(self, request):
        """
        Возвращает данные для графиков прогресса.
        
        Query параметры:
        - chart_type: тип графика ('weight', 'blood_pressure', 'feeding', 'activity')
        - period: период данных ('week', 'month', 'quarter', 'year')
        - format: формат данных ('chart_js', 'raw')
        """
        try:
            user = request.user
            chart_type = request.GET.get('chart_type', 'activity')
            period = request.GET.get('period', 'month')
            data_format = request.GET.get('format', 'chart_js')
            
            # Определяем временной период
            end_date = timezone.now()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'quarter':
                start_date = end_date - timedelta(days=90)
            else:  # 'year'
                start_date = end_date - timedelta(days=365)
            
            # Получаем данные в зависимости от типа графика
            if chart_type == 'weight':
                chart_data = self._get_weight_chart_data(user, start_date, end_date)
            elif chart_type == 'blood_pressure':
                chart_data = self._get_bp_chart_data(user, start_date, end_date)
            elif chart_type == 'feeding':
                chart_data = self._get_feeding_chart_data(user, start_date, end_date)
            elif chart_type == 'activity':
                chart_data = self._get_activity_chart_data(user, start_date, end_date)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Неподдерживаемый тип графика'
                }, status=400)
            
            # Форматируем данные для Chart.js если требуется
            if data_format == 'chart_js':
                chart_data = self._format_for_chartjs(chart_data, chart_type)
            
            return JsonResponse({
                'success': True,
                'chart_type': chart_type,
                'period': period,
                'data': chart_data
            })
            
        except Exception as e:
            logger.error(f'Ошибка при получении данных графика для пользователя {request.user.id}: {e}')
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при загрузке данных графика'
            }, status=500)
    
    def _get_weight_chart_data(self, user, start_date, end_date):
        """Получает данные для графика веса."""
        records = WeightRecord.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        return [
            {
                'date': record.date.isoformat(),
                'weight': float(record.weight),
                'notes': record.notes
            }
            for record in records
        ]
    
    def _get_bp_chart_data(self, user, start_date, end_date):
        """Получает данные для графика артериального давления."""
        records = BloodPressureRecord.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        return [
            {
                'date': record.date.isoformat(),
                'systolic': record.systolic,
                'diastolic': record.diastolic,
                'pulse': record.pulse,
                'category': record.get_pressure_category(),
                'is_normal': record.is_pressure_normal()
            }
            for record in records
        ]
    
    def _get_feeding_chart_data(self, user, start_date, end_date):
        """Получает данные для графика кормления."""
        sessions = FeedingSession.objects.filter(
            user=user,
            start_time__gte=start_date,
            start_time__lte=end_date
        ).order_by('start_time')
        
        return [
            {
                'date': session.start_time.isoformat(),
                'total_duration': session.get_total_duration_minutes(),
                'left_duration': session.get_breast_duration_minutes('left'),
                'right_duration': session.get_breast_duration_minutes('right'),
                'feeding_type': session.feeding_type
            }
            for session in sessions
        ]
    
    def _get_activity_chart_data(self, user, start_date, end_date):
        """Получает данные для графика общей активности."""
        # Группируем активность по дням
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        activity_data = []
        
        while current_date <= end_date_only:
            day_start = timezone.make_aware(
                timezone.datetime.combine(current_date, timezone.datetime.min.time())
            )
            day_end = day_start + timedelta(days=1)
            
            # Подсчитываем активности за день
            feeding_count = FeedingSession.objects.filter(
                user=user,
                start_time__gte=day_start,
                start_time__lt=day_end
            ).count()
            
            weight_count = WeightRecord.objects.filter(
                user=user,
                date__gte=day_start,
                date__lt=day_end
            ).count()
            
            bp_count = BloodPressureRecord.objects.filter(
                user=user,
                date__gte=day_start,
                date__lt=day_end
            ).count()
            
            content_views = UserContentView.objects.filter(
                user=user,
                viewed_at__gte=day_start,
                viewed_at__lt=day_end
            ).count()
            
            total_activity = feeding_count + weight_count + bp_count + content_views
            
            activity_data.append({
                'date': current_date.isoformat(),
                'total_activity': total_activity,
                'feeding_sessions': feeding_count,
                'health_records': weight_count + bp_count,
                'content_interactions': content_views
            })
            
            current_date += timedelta(days=1)
        
        return activity_data
    
    def _format_for_chartjs(self, data, chart_type):
        """Форматирует данные для использования с Chart.js."""
        if not data:
            return {'labels': [], 'datasets': []}
        
        labels = [item['date'] for item in data]
        
        if chart_type == 'weight':
            return {
                'labels': labels,
                'datasets': [{
                    'label': 'Вес (кг)',
                    'data': [item['weight'] for item in data],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'tension': 0.1
                }]
            }
        
        elif chart_type == 'blood_pressure':
            return {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Систолическое',
                        'data': [item['systolic'] for item in data],
                        'borderColor': 'rgb(255, 99, 132)',
                        'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                        'tension': 0.1
                    },
                    {
                        'label': 'Диастолическое',
                        'data': [item['diastolic'] for item in data],
                        'borderColor': 'rgb(54, 162, 235)',
                        'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                        'tension': 0.1
                    }
                ]
            }
        
        elif chart_type == 'feeding':
            return {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Левая грудь (мин)',
                        'data': [item['left_duration'] for item in data],
                        'borderColor': 'rgb(255, 205, 86)',
                        'backgroundColor': 'rgba(255, 205, 86, 0.2)',
                        'tension': 0.1
                    },
                    {
                        'label': 'Правая грудь (мин)',
                        'data': [item['right_duration'] for item in data],
                        'borderColor': 'rgb(75, 192, 192)',
                        'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                        'tension': 0.1
                    }
                ]
            }
        
        elif chart_type == 'activity':
            return {
                'labels': labels,
                'datasets': [{
                    'label': 'Общая активность',
                    'data': [item['total_activity'] for item in data],
                    'borderColor': 'rgb(153, 102, 255)',
                    'backgroundColor': 'rgba(153, 102, 255, 0.2)',
                    'tension': 0.1
                }]
            }
        
        return {'labels': labels, 'datasets': []}


@method_decorator([login_required, csrf_exempt], name='dispatch')
class ProgressSummaryView(View):
    """
    API для получения краткой сводки прогресса для отображения в дашборде.
    
    GET: Возвращает краткую сводку ключевых показателей прогресса
    """
    
    def get(self, request):
        """
        Возвращает краткую сводку прогресса пользователя.
        
        Эта сводка предназначена для отображения на главной странице
        или в виджетах дашборда.
        """
        try:
            user = request.user
            
            # Получаем статистику за последний месяц
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            
            # Создаем экземпляр ProgressStatisticsView для доступа к методам
            stats_view = ProgressStatisticsView()
            
            # Основные показатели
            summary = {
                'period': 'last_30_days',
                'user_level': self._calculate_user_level(user),
                'consistency_score': stats_view._calculate_consistency_score(user, start_date, end_date),
                'total_points': self._get_total_achievement_points(user),
                'active_streak': self._calculate_active_streak(user),
                'next_achievements': self._get_next_achievements(user),
                'recent_milestones': self._get_recent_milestones(user),
                'quick_stats': self._get_quick_stats(user, start_date, end_date)
            }
            
            return JsonResponse({
                'success': True,
                'summary': summary
            })
            
        except Exception as e:
            logger.error(f'Ошибка при получении сводки прогресса для пользователя {request.user.id}: {e}')
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при загрузке сводки'
            }, status=500)
    
    def _calculate_user_level(self, user):
        """Вычисляет уровень пользователя на основе очков достижений."""
        total_points = self._get_total_achievement_points(user)
        
        # Определяем уровень на основе очков
        if total_points < 100:
            level = 1
        elif total_points < 300:
            level = 2
        elif total_points < 600:
            level = 3
        elif total_points < 1000:
            level = 4
        else:
            level = 5
        
        # Вычисляем прогресс до следующего уровня
        level_thresholds = [0, 100, 300, 600, 1000, float('inf')]
        current_threshold = level_thresholds[level - 1]
        next_threshold = level_thresholds[level] if level < 5 else level_thresholds[level - 1]
        
        if level < 5:
            progress_to_next = ((total_points - current_threshold) / 
                              (next_threshold - current_threshold)) * 100
        else:
            progress_to_next = 100
        
        return {
            'current_level': level,
            'total_points': total_points,
            'progress_to_next_level': round(progress_to_next, 1),
            'points_to_next_level': max(0, next_threshold - total_points) if level < 5 else 0
        }
    
    def _get_total_achievement_points(self, user):
        """Получает общее количество очков достижений пользователя."""
        return UserAchievement.objects.filter(user=user).aggregate(
            total=Sum('achievement__points')
        )['total'] or 0
    
    def _calculate_active_streak(self, user):
        """Вычисляет текущую серию активных дней."""
        today = timezone.now().date()
        streak = 0
        current_date = today
        
        # Проверяем каждый день назад до первого неактивного дня
        while True:
            day_start = timezone.make_aware(
                timezone.datetime.combine(current_date, timezone.datetime.min.time())
            )
            day_end = day_start + timedelta(days=1)
            
            # Проверяем активность за день
            has_activity = (
                FeedingSession.objects.filter(
                    user=user, start_time__gte=day_start, start_time__lt=day_end
                ).exists() or
                WeightRecord.objects.filter(
                    user=user, date__gte=day_start, date__lt=day_end
                ).exists() or
                BloodPressureRecord.objects.filter(
                    user=user, date__gte=day_start, date__lt=day_end
                ).exists() or
                UserContentView.objects.filter(
                    user=user, viewed_at__gte=day_start, viewed_at__lt=day_end
                ).exists()
            )
            
            if has_activity:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
            
            # Ограничиваем проверку 100 днями для производительности
            if streak >= 100:
                break
        
        return streak
    
    def _get_next_achievements(self, user, limit=3):
        """Получает ближайшие к получению достижения."""
        available_achievements = Achievement.get_available_achievements_for_user(user)
        
        # Вычисляем прогресс для каждого достижения
        achievements_with_progress = []
        for achievement in available_achievements:
            progress_info = achievement.get_progress_for_user(user)
            if progress_info['progress_percentage'] > 0:
                achievements_with_progress.append({
                    'achievement': achievement,
                    'progress': progress_info
                })
        
        # Сортируем по проценту выполнения (убывание)
        achievements_with_progress.sort(
            key=lambda x: x['progress']['progress_percentage'], 
            reverse=True
        )
        
        # Форматируем для ответа
        next_achievements = []
        for item in achievements_with_progress[:limit]:
            achievement = item['achievement']
            progress = item['progress']
            
            next_achievements.append({
                'id': achievement.id,
                'title': achievement.title,
                'icon': achievement.icon,
                'points': achievement.points,
                'progress_percentage': progress['progress_percentage'],
                'current_progress': progress['current_progress'],
                'target_value': progress['target_value']
            })
        
        return next_achievements
    
    def _get_recent_milestones(self, user, days=7):
        """Получает недавние важные события (достижения, рекорды)."""
        cutoff_date = timezone.now() - timedelta(days=days)
        milestones = []
        
        # Недавние достижения
        recent_achievements = UserAchievement.objects.filter(
            user=user,
            earned_at__gte=cutoff_date
        ).select_related('achievement').order_by('-earned_at')
        
        for ua in recent_achievements:
            milestones.append({
                'type': 'achievement',
                'title': f'Получено достижение: {ua.achievement.title}',
                'icon': ua.achievement.icon,
                'date': ua.earned_at.isoformat(),
                'points': ua.achievement.points
            })
        
        # Рекорды веса (новые максимумы/минимумы)
        recent_weight = WeightRecord.objects.filter(
            user=user,
            date__gte=cutoff_date
        ).order_by('-date').first()
        
        if recent_weight:
            # Проверяем, является ли это рекордом
            all_weights = WeightRecord.objects.filter(user=user).order_by('date')
            if all_weights.count() > 1:
                previous_weights = [float(w.weight) for w in all_weights[:-1]]
                current_weight = float(recent_weight.weight)
                
                if current_weight == max(previous_weights + [current_weight]):
                    milestones.append({
                        'type': 'weight_record',
                        'title': f'Новый максимум веса: {current_weight} кг',
                        'icon': '📈',
                        'date': recent_weight.date.isoformat(),
                        'value': current_weight
                    })
                elif current_weight == min(previous_weights + [current_weight]):
                    milestones.append({
                        'type': 'weight_record',
                        'title': f'Новый минимум веса: {current_weight} кг',
                        'icon': '📉',
                        'date': recent_weight.date.isoformat(),
                        'value': current_weight
                    })
        
        # Сортируем по дате (новые сначала)
        milestones.sort(key=lambda x: x['date'], reverse=True)
        
        return milestones[:5]  # Максимум 5 недавних событий
    
    def _get_quick_stats(self, user, start_date, end_date):
        """Получает быстрые статистики для отображения в виджетах."""
        return {
            'feeding_sessions_this_month': FeedingSession.objects.filter(
                user=user,
                start_time__gte=start_date,
                start_time__lte=end_date
            ).count(),
            'health_records_this_month': (
                WeightRecord.objects.filter(
                    user=user, date__gte=start_date, date__lte=end_date
                ).count() +
                BloodPressureRecord.objects.filter(
                    user=user, date__gte=start_date, date__lte=end_date
                ).count()
            ),
            'achievements_this_month': UserAchievement.objects.filter(
                user=user,
                earned_at__gte=start_date,
                earned_at__lte=end_date
            ).count(),
            'content_interactions_this_month': UserContentView.objects.filter(
                user=user,
                viewed_at__gte=start_date,
                viewed_at__lte=end_date
            ).count()
        }


# Вспомогательные функции для интеграции с другими частями приложения

def get_user_progress_summary(user):
    """
    Вспомогательная функция для получения краткой сводки прогресса пользователя.
    
    Используется для интеграции с другими частями приложения.
    
    Args:
        user: Пользователь
        
    Returns:
        dict: Краткая сводка прогресса
    """
    try:
        view = ProgressSummaryView()
        
        # Создаем mock request объект
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        mock_request = MockRequest(user)
        
        # Получаем данные через view
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Создаем экземпляр ProgressStatisticsView для доступа к методам
        stats_view = ProgressStatisticsView()
        
        return {
            'user_level': view._calculate_user_level(user),
            'consistency_score': stats_view._calculate_consistency_score(user, start_date, end_date),
            'active_streak': view._calculate_active_streak(user),
            'total_points': view._get_total_achievement_points(user),
            'next_achievements_count': len(view._get_next_achievements(user)),
            'recent_milestones_count': len(view._get_recent_milestones(user))
        }
        
    except Exception as e:
        logger.error(f'Ошибка при получении сводки прогресса для пользователя {user.id}: {e}')
        return {
            'user_level': {'current_level': 1, 'total_points': 0},
            'consistency_score': 0,
            'active_streak': 0,
            'total_points': 0,
            'next_achievements_count': 0,
            'recent_milestones_count': 0
        }


def update_user_progress_metrics(user, action_type, context=None):
    """
    Обновляет метрики прогресса пользователя после выполнения действия.
    
    Эта функция должна вызываться из других частей приложения
    после важных действий пользователя для обновления статистики.
    
    Args:
        user: Пользователь
        action_type: Тип действия ('feeding', 'health_record', 'content_view', etc.)
        context: Дополнительный контекст действия
    """
    try:
        # Логируем действие для аналитики
        logger.info(f'Обновление метрик прогресса для пользователя {user.id}: {action_type}')
        
        # Здесь можно добавить логику для обновления кэшированных метрик
        # или запуска фоновых задач для пересчета статистики
        
        # Проверяем достижения после действия
        try:
            from .api_achievement import trigger_achievement_check
            trigger_achievement_check(user, {'action_type': action_type, 'context': context})
        except ImportError:
            # Если функция недоступна, просто логируем
            logger.warning(f'trigger_achievement_check недоступна для пользователя {user.id}')
        
    except Exception as e:
        logger.error(f'Ошибка при обновлении метрик прогресса для пользователя {user.id}: {e}')