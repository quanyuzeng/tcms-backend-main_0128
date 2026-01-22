"""Audit URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet

app_name = 'audit'  # 添加这行

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('', include(router.urls)),
]