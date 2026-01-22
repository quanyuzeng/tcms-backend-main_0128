"""User models"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.organization.models import Department, Position


class Role(models.Model):
    """角色表"""
    
    class RoleCode(models.TextChoices):
        SYSTEM_ADMIN = 'admin', _('系统管理员')
        HR_MANAGER = 'hr_manager', _('HR经理')
        TRAINING_MANAGER = 'training_manager', _('培训管理员')
        EXAM_MANAGER = 'exam_manager', _('考试管理员')
        DEPT_MANAGER = 'dept_manager', _('部门经理')
        INSTRUCTOR = 'instructor', _('讲师')
        ENGINEERING_MANAGER = 'engineering_manager', _('工程经理')
        ME_ENGINEER = 'me_engineer', _('ME工程师')
        TE_ENGINEER = 'te_engineer', _('TE工程师')
        TECHNICIAN = 'technician', _('技术员')
        PRODUCTION_OPERATOR = 'production_operator', _('生产操作员')
        EMPLOYEE = 'employee', _('普通员工')
    
    name = models.CharField(_('角色名称'), max_length=50)
    code = models.CharField(_('角色代码'), max_length=50, unique=True, choices=RoleCode.choices)
    description = models.TextField(_('角色描述'), blank=True)
    permissions = models.JSONField(_('权限列表'), default=dict, blank=True)
    status = models.CharField(_('状态'), max_length=20, choices=[
        ('enabled', _('启用')),
        ('disabled', _('禁用')),
    ], default='enabled')
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('角色')
        verbose_name_plural = _('角色')
        db_table = 'roles'
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """用户表 - 扩展Django默认用户模型"""
    
    class UserStatus(models.TextChoices):
        ACTIVE = 'active', _('激活')
        INACTIVE = 'inactive', _('禁用')
    
    # 移除不需要的字段
    first_name = None
    last_name = None
    
    # 自定义字段
    real_name = models.CharField(_('真实姓名'), max_length=50)
    employee_id = models.CharField(_('员工编号'), max_length=20, unique=True)
    email = models.EmailField(_('邮箱'), unique=True)
    phone = models.CharField(_('手机号'), max_length=20, blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('所属部门')
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('岗位')
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,   # 保护改为置空
        null=True, 
        blank=True, 
        verbose_name=_('角色')
    )
    avatar = models.ImageField(
        _('头像'),
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True
    )
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE
    )
    last_login_ip = models.GenericIPAddressField(_('最后登录IP'), null=True, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    # 指定用于登录的字段
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['real_name', 'email', 'employee_id']
    
    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        db_table = 'users'
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['department']),
            models.Index(fields=['position']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.real_name} ({self.username})"
    
    @property
    def full_name(self):
        return self.real_name
    
    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None
    
    @property
    def permissions_list(self):
        """获取用户权限列表"""
        if self.role and self.role.permissions:
            return self.role.permissions.get('permissions', [])
        return []
    
    def has_permission(self, permission_code):
        """检查用户是否有特定权限"""
        permissions = self.permissions_list
        if '*' in permissions:  # 超级权限
            return True
        return permission_code in permissions
    
    def save(self, *args, **kwargs):
        # 如果设置密码，确保哈希存储
        if self.password and not self.password.startswith('pbkdf2'):
            from django.contrib.auth.hashers import make_password
            self.password = make_password(self.password)
        super().save(*args, **kwargs)