"""
URL configuration for mom_baby_bot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from botapp.admin import (
    admin_index_view, user_changelist_view, user_add_view, 
    user_change_view, user_delete_view
)

# Кастомные URL для SQLAlchemy админки
sqlalchemy_admin_patterns = [
    path('', admin_index_view, name='index'),
    path('botapp/user/', user_changelist_view, name='user_changelist'),
    path('botapp/user/add/', user_add_view, name='user_add'),
    path('botapp/user/<int:object_id>/change/', user_change_view, name='user_change'),
    path('botapp/user/<int:object_id>/delete/', user_delete_view, name='user_delete'),
    path('login/', admin.site.login, name='login'),
    path('logout/', admin.site.logout, name='logout'),
]

urlpatterns = [
    path('admin/', include((sqlalchemy_admin_patterns, 'admin'), namespace='admin')),
    path('django-admin/', admin.site.urls),  # Стандартная Django админка для резерва
    path('', include('webapp.urls')),
]
