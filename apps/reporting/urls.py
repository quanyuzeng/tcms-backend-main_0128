"""Reporting URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportTemplateViewSet, GeneratedReportViewSet, ReportingViewSet

app_name = 'reporting'  # 添加这行

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet, basename='reporttemplate')
router.register(r'generated', GeneratedReportViewSet, basename='generatedreport')
router.register(r'', ReportingViewSet, basename='reporting')

urlpatterns = [
    path('', include(router.urls)),
]