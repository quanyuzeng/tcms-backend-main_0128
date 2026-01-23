"""Authentication URLs"""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from ..views.auth import login_view, logout_view, profile_view, password_change_view, password_reset_view

app_name = 'auth'

urlpatterns = [
    path('login/', login_view, name='auth-login'),
    path('logout/', logout_view, name='auth-logout'),
    path('profile/', profile_view, name='auth-profile'),
    path('password/change/', password_change_view, name='auth-password-change'),
    path('password/reset/', password_reset_view, name='auth-password-reset'),
    # JWT Token URLs
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]