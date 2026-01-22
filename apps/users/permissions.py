"""Custom permissions"""
from rest_framework.permissions import BasePermission


class IsSystemAdmin(BasePermission):
    """系统管理员权限"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role.code == 'admin'


class IsAdminOrHR(BasePermission):
    """管理员或HR权限"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role.code in ['admin', 'hr_manager']


class IsTrainingManager(BasePermission):
    """培训管理员权限"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role.code in ['admin', 'hr_manager', 'training_manager']


class IsExamManager(BasePermission):
    """考试管理员权限"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role.code in ['admin', 'exam_manager']


class IsDeptManager(BasePermission):
    """部门经理权限"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role.code in ['admin', 'hr_manager', 'dept_manager']


class IsInstructor(BasePermission):
    """讲师权限"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role.code in ['admin', 'hr_manager', 'instructor']


class IsOwnerOrAdmin(BasePermission):
    """对象所有者或管理员权限"""
    
    def has_object_permission(self, request, view, obj):
        # 管理员可以访问所有对象
        if request.user.role.code in ['admin', 'hr_manager']:
            return True
        
        # 用户可以访问自己的对象
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False