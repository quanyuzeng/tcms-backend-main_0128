"""Organization URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, PositionViewSet

app_name = 'organization'  # 添加这行

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', PositionViewSet, basename='position')

urlpatterns = [
    path('', include(router.urls)),
]