"""User management URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views.user import UserViewSet, RoleViewSet, user_profile_view

app_name = 'user'

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')

urlpatterns = [
    path('profile/', user_profile_view, name='user-profile-detail'),
    path('', include(router.urls)),
]