"""Audit models"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    """审计日志表"""
    
    class ActionType(models.TextChoices):
        CREATE = 'create', _('创建')
        UPDATE = 'update', _('更新')
        DELETE = 'delete', _('删除')
        LOGIN = 'login', _('登录')
        LOGOUT = 'logout', _('登出')
        EXPORT = 'export', _('导出')
        IMPORT = 'import', _('导入')
        APPROVE = 'approve', _('审批')
        REJECT = 'reject', _('拒绝')
    
    class Status(models.TextChoices):
        SUCCESS = 'success', _('成功')
        FAILED = 'failed', _('失败')
    
    operator = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('操作人'),
        related_name='audit_logs'
    )
    operator_name = models.CharField(_('操作人姓名'), max_length=100, blank=True)
    operator_username = models.CharField(_('操作人用户名'), max_length=100, blank=True)
    action = models.CharField(
        _('操作类型'),
        max_length=50,
        choices=ActionType.choices
    )
    module = models.CharField(_('模块'), max_length=50)
    object_type = models.CharField(_('对象类型'), max_length=50, blank=True)
    object_id = models.CharField(_('对象ID'), max_length=100, blank=True)
    object_name = models.CharField(_('对象名称'), max_length=200, blank=True)
    description = models.TextField(_('操作描述'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP地址'), null=True, blank=True)
    user_agent = models.TextField(_('用户代理'), blank=True)
    request_method = models.CharField(_('请求方法'), max_length=10, blank=True)
    request_path = models.CharField(_('请求路径'), max_length=500, blank=True)
    request_params = models.JSONField(_('请求参数'), default=dict, blank=True)
    response_result = models.JSONField(_('响应结果'), default=dict, blank=True)
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.SUCCESS
    )
    error_message = models.TextField(_('错误信息'), blank=True)
    response_time = models.IntegerField(_('响应时间(ms)'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('审计日志')
        verbose_name_plural = _('审计日志')
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['operator']),
            models.Index(fields=['action']),
            models.Index(fields=['module']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['object_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.operator_name} - {self.get_action_display()} - {self.module}"
    
    @property
    def is_successful(self):
        return self.status == self.Status.SUCCESS