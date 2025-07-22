from django.urls import path
from . import views
from . import api
from . import api_vaccine
from . import api_contraction
from . import api_kick
from . import api_sleep
from . import api_feeding
from . import api_notification

app_name = 'webapp'

urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    path('index.html', views.index, name='index_html'),
    
    # Информационные разделы
    path('pregnancy/', views.pregnancy, name='pregnancy'),
    path('child-development/', views.child_development, name='child_development'),
    path('nutrition/', views.nutrition, name='nutrition'),
    
    # UI Components Showcase
    path('components/showcase/', views.components_showcase, name='components_showcase'),
    
    # Инструменты
    path('tools/contraction-counter/', views.contraction_counter, name='contraction_counter'),
    path('tools/kick-counter/', views.kick_counter, name='kick_counter'),
    path('tools/sleep-timer/', views.sleep_timer, name='sleep_timer'),
    path('tools/feeding-tracker/', views.feeding_tracker, name='feeding_tracker'),
    path('tools/child-profiles/', views.child_profiles, name='child_profiles'),
    path('tools/vaccine-calendar/', views.vaccine_calendar, name='vaccine_calendar'),
    
    # API endpoints
    path('api/user', views.create_user, name='create_user'),
    path('webapp/data/', views.web_app_data, name='web_app_data'),
    
    # Child Profile API endpoints
    path('api/users/<int:user_id>/children/', api.children_list, name='children_list'),
    path('api/users/<int:user_id>/children/<int:child_id>/', api.child_detail, name='child_detail'),
    
    # Measurement API endpoints
    path('api/users/<int:user_id>/children/<int:child_id>/measurements/', api.measurements_list, name='measurements_list'),
    path('api/users/<int:user_id>/children/<int:child_id>/measurements/<int:measurement_id>/', api.measurement_detail, name='measurement_detail'),
    
    # Vaccine API endpoints
    path('api/vaccines/', api_vaccine.vaccines_list, name='vaccines_list'),
    path('api/vaccines/<int:vaccine_id>/', api_vaccine.vaccine_detail, name='vaccine_detail'),
    path('api/users/<int:user_id>/children/<int:child_id>/vaccines/', api_vaccine.child_vaccines_list, name='child_vaccines_list'),
    path('api/users/<int:user_id>/children/<int:child_id>/vaccines/<int:child_vaccine_id>/', api_vaccine.child_vaccine_detail, name='child_vaccine_detail'),
    path('api/users/<int:user_id>/children/<int:child_id>/vaccines/<int:child_vaccine_id>/complete/', api_vaccine.mark_vaccine_completed_view, name='mark_vaccine_completed'),
    
    # Contraction API endpoints
    path('api/users/<int:user_id>/contractions/', api_contraction.contraction_sessions, name='contraction_sessions'),
    path('api/users/<int:user_id>/contractions/<int:session_id>/', api_contraction.contraction_session_detail, name='contraction_session_detail'),
    path('api/users/<int:user_id>/contractions/<int:session_id>/events/', api_contraction.contraction_events, name='contraction_events'),
    
    # Kick API endpoints
    path('api/users/<int:user_id>/kicks/', api_kick.kick_sessions, name='kick_sessions'),
    path('api/users/<int:user_id>/kicks/<int:session_id>/', api_kick.kick_session_detail, name='kick_session_detail'),
    path('api/users/<int:user_id>/kicks/<int:session_id>/events/', api_kick.kick_events, name='kick_events'),
    
    # Sleep API endpoints
    path('api/users/<int:user_id>/children/<int:child_id>/sleep/', api_sleep.sleep_sessions, name='sleep_sessions'),
    path('api/users/<int:user_id>/children/<int:child_id>/sleep/<int:session_id>/', api_sleep.sleep_session_detail, name='sleep_session_detail'),
    path('api/users/<int:user_id>/children/<int:child_id>/sleep/statistics/', api_sleep.sleep_statistics, name='sleep_statistics'),
    path('api/users/<int:user_id>/children/<int:child_id>/sleep/active/', api_sleep.active_sleep_session, name='active_sleep_session'),
    
    # Feeding API endpoints
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/', api_feeding.feeding_sessions, name='feeding_sessions'),
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/<int:session_id>/', api_feeding.feeding_session_detail, name='feeding_session_detail'),
    path('api/users/<int:user_id>/children/<int:child_id>/feeding/statistics/', api_feeding.feeding_statistics, name='feeding_statistics'),
    
    # Notification API endpoints
    path('api/users/<int:user_id>/notifications/preferences/', api_notification.notification_preferences, name='notification_preferences'),
    path('api/users/<int:user_id>/notifications/history/', api_notification.notification_history, name='notification_history'),
    path('api/users/<int:user_id>/notifications/test/', api_notification.test_notification, name='test_notification'),
    path('api/users/<int:user_id>/notifications/send/', api_notification.send_notification, name='send_notification'),
]