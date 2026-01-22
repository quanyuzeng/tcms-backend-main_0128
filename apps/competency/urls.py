"""Competency URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompetencyViewSet, CompetencyAssessmentViewSet, CertificateViewSet

app_name = 'competency'  # 添加这行

router = DefaultRouter()
router.register(r'competencies', CompetencyViewSet, basename='competency')
router.register(r'assessments', CompetencyAssessmentViewSet, basename='competencyassessment')
router.register(r'certificates', CertificateViewSet, basename='certificate')

urlpatterns = [
    path('', include(router.urls)),
]