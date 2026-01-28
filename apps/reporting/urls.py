"""Reporting URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportTemplateViewSet, GeneratedReportViewSet, ReportingViewSet

app_name = 'reporting'

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet, basename='reporttemplate')
router.register(r'generated', GeneratedReportViewSet, basename='generatedreport')
router.register(r'', ReportingViewSet, basename='reporting')

# 修复：添加明确的路由路径
urlpatterns = [
    path('', include(router.urls)),
    # 添加测试期望的路由
    path('reports/training_statistics/', ReportingViewSet.as_view({'get': 'training_statistics'}), name='training_statistics'),
    path('reports/competency_statistics/', ReportingViewSet.as_view({'get': 'competency_statistics'}), name='competency_statistics'),
]