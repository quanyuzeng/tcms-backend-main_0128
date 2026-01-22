"""Organization models"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """部门表"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('启用')
        INACTIVE = 'inactive', _('禁用')
    
    name = models.CharField(_('部门名称'), max_length=100)
    code = models.CharField(_('部门代码'), max_length=50, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('上级部门'),
        related_name='children'
    )
    manager = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('部门负责人'),
        related_name='managed_departments'
    )
    description = models.TextField(_('部门描述'), blank=True)
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('部门')
        verbose_name_plural = _('部门')
        db_table = 'departments'
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['manager']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def employee_count(self):
        """部门员工数量"""
        return self.users.filter(status='active').count()
    
    @property
    def level(self):
        """部门层级"""
        if not self.parent:
            return 1
        return self.parent.level + 1


class Position(models.Model):
    """岗位表"""
    
    class Level(models.TextChoices):
        JUNIOR = 'junior', _('初级')
        MID = 'mid', _('中级')
        SENIOR = 'senior', _('高级')
        EXPERT = 'expert', _('专家')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('启用')
        INACTIVE = 'inactive', _('禁用')
    
    name = models.CharField(_('岗位名称'), max_length=100)
    code = models.CharField(_('岗位代码'), max_length=50, unique=True)
    level = models.CharField(
        _('岗位级别'),
        max_length=20,
        choices=Level.choices,
        default=Level.MID
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('所属部门'),
        related_name='positions'
    )
    responsibilities = models.TextField(_('岗位职责'), blank=True)
    requirements = models.TextField(_('任职要求'), blank=True)
    required_training_hours = models.IntegerField(_('要求培训时长(小时)'), default=40)
    min_experience = models.IntegerField(_('最低工作经验(年)'), default=1)
    min_education = models.CharField(
        _('最低学历'),
        max_length=50,
        choices=[
            ('high_school', _('高中')),
            ('college', _('大专')),
            ('bachelor', _('本科')),
            ('master', _('硕士')),
            ('phd', _('博士')),
        ],
        default='bachelor'
    )
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('岗位')
        verbose_name_plural = _('岗位')
        db_table = 'positions'
        indexes = [
            models.Index(fields=['department']),
            models.Index(fields=['level']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def employee_count(self):
        """岗位员工数量"""
        return self.users.filter(status='active').count()