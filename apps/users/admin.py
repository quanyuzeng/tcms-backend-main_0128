# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms
from django.contrib.auth import get_user_model
from apps.users.models import Role
from apps.organization.models import Department, Position

User = get_user_model()


class CustomUserChangeForm(UserChangeForm):
    """自定义用户修改表单"""
    class Meta:
        model = User
        fields = '__all__'


class CustomUserCreationForm(UserCreationForm):
    """自定义用户创建表单"""
    class Meta:
        model = User
        fields = ('username', 'email', 'real_name', 'employee_id')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色管理"""
    list_display = ['name', 'code', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'code']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """用户管理后台"""
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    # 列表页显示字段
    list_display = [
        'username', 'real_name', 'employee_id', 'email', 
        'role', 'department', 'position', 'status', 'is_active', 
        'last_login', 'created_at'
    ]
    list_filter = [
        'status', 'role', 'department', 'is_active', 
        'last_login', 'created_at'
    ]
    search_fields = ['username', 'real_name', 'employee_id', 'email']
    ordering = ['-created_at']
    
    # 编辑页字段分组
    fieldsets = BaseUserAdmin.fieldsets + (
        ('企业信息', {
            'fields': (
                'real_name', 'employee_id', 'role', 
                'department', 'position', 'status', 'phone', 'avatar'
            )
        }),
        ('系统信息', {
            'fields': ('last_login_ip', 'created_at', 'updated_at'),
            'classes': ('collapse',)  # 可折叠
        })
    )
    
    # 创建页字段
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 
                'real_name', 'employee_id', 'email',
                'role', 'department', 'position', 'status', 'phone'
            ),
        }),
    )
    
    # 只读字段
    readonly_fields = ['last_login_ip', 'created_at', 'updated_at', 'last_login']
    
    def save_model(self, request, obj, form, change):
        """保存时处理密码和业务逻辑"""
        if not change:  # 新建用户
            # 确保密码加密
            if obj.password and not obj.password.startswith('pbkdf2_sha256'):
                obj.set_password(obj.password)
        
        # 自动记录操作IP
        if change:
            obj.last_login_ip = request.META.get('REMOTE_ADDR')
        
        super().save_model(request, obj, form, change)