"""Examination URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestionBankViewSet, QuestionViewSet, ExamViewSet, ExamResultViewSet
from .views_import_export import import_questions, export_questions, download_question_import_template

app_name = 'examination'  # 添加这行

router = DefaultRouter()
router.register(r'question-banks', QuestionBankViewSet, basename='questionbank')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'results', ExamResultViewSet, basename='examresult')

urlpatterns = [
    path('', include(router.urls)),
    path('questions/import/', import_questions, name='question-import'),
    path('questions/export/', export_questions, name='question-export'),
    path('questions/import-template/', download_question_import_template, name='question-import-template'),
]