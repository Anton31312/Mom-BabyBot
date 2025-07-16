from django.urls import path
from . import views

app_name = 'webapp'

urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    path('index.html', views.index, name='index_html'),
    
    # API endpoints
    path('api/user', views.create_user, name='create_user'),
    path('webapp/data/', views.web_app_data, name='web_app_data'),
]