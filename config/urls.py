"""TCMS URL configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.urls import handler404, handler500  # 添加这行

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls.auth')),
    path('api/users/', include('apps.users.urls.user')),
    path('api/organization/', include('apps.organization.urls', namespace='organization')),
    path('api/training/', include('apps.training.urls', namespace='training')),
    path('api/examination/', include('apps.examination.urls', namespace='examination')),
    path('api/competency/', include('apps.competency.urls', namespace='competency')),
    path('api/reporting/', include('apps.reporting.urls', namespace='reporting')),
    path('api/audit/', include('apps.audit.urls', namespace='audit')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]

# 自定义错误处理（可选）
handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'

# Static and media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)