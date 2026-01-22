"""Reporting models"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class ReportTemplate(models.Model):
    """报表模板表"""
    
    class ReportType(models.TextChoices):
        TRAINING_STATISTICS = 'training_statistics', _('培训统计报表')
        EXAM_ANALYSIS = 'exam_analysis', _('考试分析报表')
        COMPETENCY_MATRIX = 'competency_matrix', _('能力矩阵报表')
        COMPLIANCE_REPORT = 'compliance_report', _('合规性报表')
        USER_ACTIVITY = 'user_activity', _('用户活动报表')
    
    name = models.CharField(_('模板名称'), max_length=100)
    code = models.CharField(_('模板代码'), max_length=50, unique=True)
    report_type = models.CharField(
        _('报表类型'),
        max_length=50,
        choices=ReportType.choices
    )
    description = models.TextField(_('模板描述'), blank=True)
    config = models.JSONField(_('模板配置'), default=dict)
    is_active = models.BooleanField(_('是否激活'), default=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('创建人'),
        related_name='created_report_templates'
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('报表模板')
        verbose_name_plural = _('报表模板')
        db_table = 'report_templates'
    
    def __str__(self):
        return self.name


class GeneratedReport(models.Model):
    """生成的报表表"""
    
    class Format(models.TextChoices):
        EXCEL = 'excel', _('Excel')
        PDF = 'pdf', _('PDF')
        CSV = 'csv', _('CSV')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('生成中')
        COMPLETED = 'completed', _('已完成')
        FAILED = 'failed', _('生成失败')
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        verbose_name=_('报表模板'),
        related_name='generated_reports'
    )
    title = models.CharField(_('报表标题'), max_length=200)
    file_format = models.CharField(
        _('文件格式'),
        max_length=20,
        choices=Format.choices,
        default=Format.EXCEL
    )
    file_path = models.CharField(_('文件路径'), max_length=500, blank=True)
    file_size = models.IntegerField(_('文件大小'), default=0)
    parameters = models.JSONField(_('报表参数'), default=dict)
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    error_message = models.TextField(_('错误信息'), blank=True)
    generated_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('生成人'),
        related_name='generated_reports'
    )
    generated_at = models.DateTimeField(_('生成时间'), auto_now_add=True)
    completed_at = models.DateTimeField(_('完成时间'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('生成的报表')
        verbose_name_plural = _('生成的报表')
        db_table = 'generated_reports'
        indexes = [
            models.Index(fields=['template']),
            models.Index(fields=['status']),
            models.Index(fields=['generated_by']),
            models.Index(fields=['generated_at']),
        ]
    
    def __str__(self):
        return self.title