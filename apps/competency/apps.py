from django.apps import AppConfig


class CompetencyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.competency'
    label = 'competency'
    verbose_name = '能力管理'