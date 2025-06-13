# settings_api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sacco', views.SaccoSettingsViewSet, basename='sacco-settings')
router.register(r'user', views.UserSettingsViewSet, basename='user-settings')
router.register(r'admin', views.AdminSettingsViewSet, basename='admin-settings')

urlpatterns = [
    path('', include(router.urls)),
]