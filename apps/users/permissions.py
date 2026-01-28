"""Custom permissions"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSystemAdmin(BasePermission):
    """系统管理员权限"""

    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                hasattr(request.user, 'role') and
                request.user.role and
                request.user.role.code == 'admin')


class IsAdminOrHR(BasePermission):
    """管理员或HR权限"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (hasattr(request.user, 'role') and
                request.user.role and
                request.user.role.code in ['admin', 'hr_manager'])


class IsManager(BasePermission):
    """
    所有经理级别权限（与HR经理同级）
    admin, hr_manager, training_manager, exam_manager, 
    engineering_manager, dept_manager
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (hasattr(request.user, 'role') and
                request.user.role and
                request.user.role.code in [
                    'admin', 'hr_manager', 
                    'training_manager', 'exam_manager',
                    'engineering_manager', 'dept_manager'
                ])


class IsManagerOrReadOnly(BasePermission):
    """
    所有经理拥有写权限，所有认证用户有读权限
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 安全方法（GET, HEAD, OPTIONS）允许所有认证用户
        if request.method in SAFE_METHODS:
            return True
        
        # 非安全方法需要经理权限
        return (hasattr(request.user, 'role') and
                request.user.role and
                request.user.role.code in [
                    'admin', 'hr_manager',
                    'training_manager', 'exam_manager',
                    'engineering_manager', 'dept_manager'
                ])


class IsEngineer(BasePermission):
    """
    所有工程师权限（ME工程师、TE工程师、技术员）
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (hasattr(request.user, 'role') and
                request.user.role and
                request.user.role.code in [
                    'me_engineer', 'te_engineer', 'technician',
                    'production_operator'  # 生产操作员也视为工程师级别
                ])


class IsEngineerOrManager(BasePermission):
    """
    工程师或经理权限（创建权限）
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (hasattr(request.user, 'role') and
                request.user.role and
                request.user.role.code in [
                    # 经理
                    'admin', 'hr_manager',
                    'training_manager', 'exam_manager',
                    'engineering_manager', 'dept_manager',
                    # 工程师
                    'me_engineer', 'te_engineer', 'technician',
                    'production_operator'
                ])


class IsTrainingManager(BasePermission):
    """培训管理员权限（包含所有经理）"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (hasattr(request.user, 'role') and
                request.user.role and
                request.user.role.code in [
                    'admin', 'hr_manager',
                    'training_manager', 'exam_manager',
                    'engineering_manager', 'dept_manager',
                    'me_engineer', 'te_engineer', 'technician',
                    'production_operator'
                ])


class IsExamManager(BasePermission):
    """考试管理员权限（包含所有经理和工程师）"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (hasattr(request.user, 'role') and
                request.user.role and
                request.user.role.code in [
                    'admin', 'hr_manager',
                    'training_manager', 'exam_manager',
                    'engineering_manager', 'dept_manager',
                    'me_engineer', 'te_engineer', 'technician',
                    'production_operator'
                ])


class IsDeptManager(BasePermission):
    """部门经理权限（包含所有经理）"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (hasattr(request.user, 'role') and
                request.user.role and
                request.user.role.code in [
                    'admin', 'hr_manager',
                    'training_manager', 'exam_manager',
                    'engineering_manager', 'dept_manager'
                ])


class IsInstructor(BasePermission):
    """讲师权限（包含所有经理和工程师）"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (hasattr(request.user, 'role') and
                request.user.role and
                request.user.role.code in [
                    'admin', 'hr_manager',
                    'training_manager', 'exam_manager',
                    'engineering_manager', 'dept_manager',
                    'instructor',
                    'me_engineer', 'te_engineer', 'technician',
                    'production_operator'
                ])


class IsOwnerOrAdmin(BasePermission):
    """对象所有者或管理员权限"""

    def has_permission(self, request, view):
        """检查视图级别权限"""
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 管理员和经理可以访问所有对象
        if (hasattr(request.user, 'role') and
            request.user.role and
            request.user.role.code in [
                'admin', 'hr_manager',
                'training_manager', 'exam_manager',
                'engineering_manager', 'dept_manager'
            ]):
            return True

        # 用户可以访问自己的对象
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user

        return False