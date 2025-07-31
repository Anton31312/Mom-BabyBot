from django.urls import path
from . import views
from . import api
from . import api_vaccine
from . import api_contraction
from . import api_kick
from . import api_sleep
from . import api_feeding
from . import api_notification
from . import api_performance
from . import api_health
from . import api_achievement
from . import api_progress
from . import api_pregnancy
from .utils.disclaimer_utils import acknowledge_disclaimer

app_name = 'webapp'

urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    path('index.html', views.index, name='index_html'),
    
    # Информационные разделы
    path('pregnancy/', views.pregnancy, name='pregnancy'),
    path('pregnancy/fetal-development/', views.fetal_development, name='fetal_development'),
    path('child-development/', views.child_development, name='child_development'),
    path('nutrition/', views.nutrition, name='nutrition'),
    
    # Документация
    path('documentation/', views.documentation, name='documentation'),
    path('documentation/general/', views.user_guide_general, name='user_guide_general'),
    path('documentation/pregnancy/', views.user_guide_pregnancy, name='user_guide_pregnancy'),
    path('documentation/baby/', views.user_guide_baby, name='user_guide_baby'),
    path('documentation/tools/', views.user_guide_tools, name='user_guide_tools'),
    path('documentation/sync/', views.user_guide_sync, name='user_guide_sync'),
    path('documentation/faq/', views.faq, name='faq'),
    # Техническая документация
    path('documentation/api/', views.api_documentation, name='api_documentation'),
    path('documentation/architecture/', views.architecture, name='architecture'),
    path('documentation/deployment/', views.deployment, name='deployment'),
    path('documentation/technical/', views.technical_documentation, name='technical_documentation'),
    
    # Демонстрация UI компонентов
    path('components/showcase/', views.components_showcase, name='components_showcase'),
    path('components/tooltips/', views.tooltips_example, name='tooltips_example'),
    
    # Панель производительности
    path('admin/performance/', views.performance_dashboard, name='performance_dashboard'),
    
    # Инструменты
    path('tools/contraction-counter/', views.contraction_counter, name='contraction_counter'),
    path('tools/kick-counter/', views.kick_counter, name='kick_counter'),
    path('tools/sleep-timer/', views.sleep_timer, name='sleep_timer'),
    path('tools/feeding-tracker/', views.feeding_tracker, name='feeding_tracker'),
    path('tools/child-profiles/', views.child_profiles, name='child_profiles'),
    path('tools/vaccine-calendar/', views.vaccine_calendar, name='vaccine_calendar'),
    path('tools/health-tracker/', views.health_tracker, name='health_tracker'),
    path('achievements/', views.achievements, name='achievements'),
    path('progress/', views.progress_dashboard, name='progress_dashboard'),
    
    # API эндпоинты
    path('api/user', views.create_user, name='create_user'),
    path('webapp/data/', views.web_app_data, name='web_app_data'),
    
    # API эндпоинты профилей детей
    path('api/users/<int:user_id>/children/', api.children_list, name='children_list'),
    path('api/users/<int:user_id>/children/<int:child_id>/', api.child_detail, name='child_detail'),
    
    # API эндпоинты измерений
    path('api/users/<int:user_id>/children/<int:child_id>/measurements/', api.measurements_list, name='measurements_list'),
    path('api/users/<int:user_id>/children/<int:child_id>/measurements/<int:measurement_id>/', api.measurement_detail, name='measurement_detail'),
    
    # API эндпоинты прививок
    path('api/vaccines/', api_vaccine.vaccines_list, name='vaccines_list'),
    path('api/vaccines/<int:vaccine_id>/', api_vaccine.vaccine_detail, name='vaccine_detail'),
    path('api/users/<int:user_id>/children/<int:child_id>/vaccines/', api_vaccine.child_vaccines_list, name='child_vaccines_list'),
    path('api/users/<int:user_id>/children/<int:child_id>/vaccines/<int:child_vaccine_id>/', api_vaccine.child_vaccine_detail, name='child_vaccine_detail'),
    path('api/users/<int:user_id>/children/<int:child_id>/vaccines/<int:child_vaccine_id>/complete/', api_vaccine.mark_vaccine_completed_view, name='mark_vaccine_completed'),
    
    # API эндпоинты схваток
    path('api/users/<int:user_id>/contractions/', api_contraction.contraction_sessions, name='contraction_sessions'),
    path('api/users/<int:user_id>/contractions/<int:session_id>/', api_contraction.contraction_session_detail, name='contraction_session_detail'),
    path('api/users/<int:user_id>/contractions/<int:session_id>/events/', api_contraction.contraction_events, name='contraction_events'),
    
    # API эндпоинты шевелений
    path('api/users/<int:user_id>/kicks/', api_kick.kick_sessions, name='kick_sessions'),
    path('api/users/<int:user_id>/kicks/<int:session_id>/', api_kick.kick_session_detail, name='kick_session_detail'),
    path('api/users/<int:user_id>/kicks/<int:session_id>/events/', api_kick.kick_events, name='kick_events'),
    
    # API эндпоинты сна
    path('api/users/<int:user_id>/children/<int:child_id>/sleep/', api_sleep.sleep_sessions, name='sleep_sessions'),
    path('api/users/<int:user_id>/children/<int:child_id>/sleep/<int:session_id>/', api_sleep.sleep_session_detail, name='sleep_session_detail'),
    path('api/users/<int:user_id>/children/<int:child_id>/sleep/statistics/', api_sleep.sleep_statistics, name='sleep_statistics'),
    path('api/users/<int:user_id>/children/<int:child_id>/sleep/active/', api_sleep.active_sleep_session, name='active_sleep_session'),
    
    # API эндпоинты кормления
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/', api_feeding.feeding_sessions, name='feeding_sessions'),
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/<int:session_id>/', api_feeding.feeding_session_detail, name='feeding_session_detail'),
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/statistics/', api_feeding.feeding_statistics, name='feeding_statistics'),
    
    # API эндпоинты управления таймерами кормления
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/timer/start/', api_feeding.start_feeding_timer, name='start_feeding_timer'),
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/<int:session_id>/timer/pause/', api_feeding.pause_feeding_timer, name='pause_feeding_timer'),
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/<int:session_id>/timer/stop/', api_feeding.stop_feeding_session, name='stop_feeding_session'),
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/<int:session_id>/timer/switch/', api_feeding.switch_breast, name='switch_breast'),
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/active/', api_feeding.get_active_feeding_session, name='get_active_feeding_session'),
    
    # API эндпоинты уведомлений
    path('api/users/<int:user_id>/notifications/preferences/', api_notification.notification_preferences, name='notification_preferences'),
    path('api/users/<int:user_id>/notifications/history/', api_notification.notification_history, name='notification_history'),
    path('api/users/<int:user_id>/notifications/test/', api_notification.test_notification, name='test_notification'),
    path('api/users/<int:user_id>/notifications/send/', api_notification.send_notification, name='send_notification'),
    
    # API эндпоинты производительности
    path('api/performance-metrics', api_performance.collect_metrics, name='collect_metrics'),
    path('api/performance-metrics/get', api_performance.get_metrics, name='get_metrics'),
    path('api/performance-stats', api_performance.get_performance_stats, name='get_performance_stats'),
    path('api/performance-stats/reset', api_performance.reset_stats, name='reset_stats'),
    
    # API эндпоинты здоровья
    path('api/users/<int:user_id>/health/weight/', api_health.weight_records, name='weight_records'),
    path('api/users/<int:user_id>/health/weight/<int:record_id>/', api_health.weight_record_detail, name='weight_record_detail'),
    path('api/users/<int:user_id>/health/blood-pressure/', api_health.blood_pressure_records, name='blood_pressure_records'),
    path('api/users/<int:user_id>/health/blood-pressure/<int:record_id>/', api_health.blood_pressure_record_detail, name='blood_pressure_record_detail'),
    path('api/users/<int:user_id>/health/statistics/', api_health.health_statistics, name='health_statistics'),
    path('api/users/<int:user_id>/health/export/', api_health.health_data_export, name='health_data_export'),
    
    # API эндпоинты достижений
    path('api/achievements/', api_achievement.AchievementListView.as_view(), name='achievement_list'),
    path('api/achievements/stats/', api_achievement.UserAchievementStatsView.as_view(), name='achievement_stats'),
    path('api/achievements/check/', api_achievement.CheckAchievementsView.as_view(), name='check_achievements'),
    path('api/achievements/notifications/', api_achievement.AchievementNotificationsView.as_view(), name='achievement_notifications'),
    path('api/achievements/<int:achievement_id>/', api_achievement.AchievementDetailView.as_view(), name='achievement_detail'),
    
    # API эндпоинты прогресса
    path('api/progress/statistics/', api_progress.ProgressStatisticsView.as_view(), name='progress_statistics'),
    path('api/progress/charts/', api_progress.ProgressChartsView.as_view(), name='progress_charts'),
    path('api/progress/summary/', api_progress.ProgressSummaryView.as_view(), name='progress_summary'),
    
    # API эндпоинты беременности
    path('api/pregnancy/fetal-development/', api_pregnancy.fetal_development_list, name='fetal_development_list'),
    path('api/pregnancy/fetal-development/current/', api_pregnancy.fetal_development_current, name='fetal_development_current'),
    path('api/pregnancy/fetal-development/<int:week_number>/', api_pregnancy.fetal_development_week, name='fetal_development_week'),
    
    # Эндпоинт подтверждения дисклеймера
    path('api/disclaimer/acknowledge/', acknowledge_disclaimer, name='acknowledge_disclaimer'),
]