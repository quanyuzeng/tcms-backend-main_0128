from django.apps import AppConfig


class ExaminationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.examination'
    label = 'examination'
    verbose_name = '考试管理'