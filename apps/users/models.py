from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    """角色表"""
    name = models.CharField(_('角色名称'), max_length=100)
    code = models.CharField(_('角色代码'), max_length=50, unique=True)
    status = models.CharField(_('状态'), max_length=20, 
                             choices=[('enabled', _('启用')), ('disabled', _('禁用'))], 
                             default='enabled')
    permissions = models.JSONField(_('权限配置'), default=dict, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """用户扩展表"""
    real_name = models.CharField(_('真实姓名'), max_length=100, blank=True)
    employee_id = models.CharField(_('员工编号'), max_length=50, unique=True, null=True, blank=True)
    
    # 修复：添加反向关系
    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('所属部门'),
        related_name='users'
    )
    position = models.ForeignKey(
        'organization.Position',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('岗位'),
        related_name='users'
    )
    
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('角色'),
        related_name='users'
    )
    
    status = models.CharField(_('状态'), max_length=20, 
                             choices=[('active', _('在职')), ('inactive', _('离职'))], 
                             default='active')
    phone = models.CharField(_('手机号'), max_length=20, blank=True)
    avatar = models.ImageField(_('头像'), upload_to='avatars/', blank=True, null=True)
    
    # 修复：添加缺失的字段
    last_login_ip = models.GenericIPAddressField(_('最后登录IP'), null=True, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    def __str__(self):
        return self.real_name or self.username