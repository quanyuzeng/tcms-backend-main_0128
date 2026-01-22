"""Training URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseCategoryViewSet, CourseViewSet,
    TrainingPlanViewSet, TrainingRecordViewSet
)
from .views_import_export import import_courses, export_courses, download_course_import_template

app_name = 'training'  # 添加这行

router = DefaultRouter()
router.register(r'categories', CourseCategoryViewSet, basename='coursecategory')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'plans', TrainingPlanViewSet, basename='trainingplan')
router.register(r'records', TrainingRecordViewSet, basename='trainingrecord')

urlpatterns = [
    path('', include(router.urls)),
    path('courses/import/', import_courses, name='course-import'),
    path('courses/export/', export_courses, name='course-export'),
    path('courses/import-template/', download_course_import_template, name='course-import-template'),
]