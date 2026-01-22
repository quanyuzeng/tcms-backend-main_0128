"""User management views"""
from rest_framework import status, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from ..models import User, Role
from ..serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer, RoleSerializer
from ..permissions import IsAdminOrHR, IsSystemAdmin


class UserViewSet(ModelViewSet):
    """用户管理视图集"""
    
    queryset = User.objects.select_related('department', 'position', 'role').all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'position', 'role', 'status']
    search_fields = ['username', 'real_name', 'employee_id', 'email', 'phone']
    ordering_fields = ['created_at', 'updated_at', 'real_name', 'employee_id']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据操作类型选择序列化器"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 系统管理员可以查看所有用户
        if user.role.code == 'admin':
            return self.queryset
        
        # HR可以查看所有用户
        if user.role.code == 'hr_manager':
            return self.queryset
        
        # 部门经理只能查看本部门用户
        if user.role.code == 'dept_manager':
            return self.queryset.filter(
                Q(department=user.department) | Q(id=user.id)
            )
        
        # 普通用户只能查看自己
        return self.queryset.filter(id=user.id)
    
    def list(self, request, *args, **kwargs):
        """获取用户列表"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': 'Success',
            'data': {
                'count': queryset.count(),
                'results': serializer.data
            }
        })
    
    def create(self, request, *args, **kwargs):
        """创建用户"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 保存用户
            user = serializer.save()
            
            # 获取临时密码（如果设置了密码）
            temp_password = request.data.get('password', '')
            
            # 发送用户创建通知邮件
            if user.email and temp_password:
                try:
                    from apps.common.email_service import EmailService
                    EmailService.send_user_created_notification(user, temp_password)
                except Exception as e:
                    # 邮件发送失败不影响主流程
                    pass
            
            return Response({
                'code': 201,
                'message': '用户创建成功',
                'data': UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'code': 400,
            'message': '用户创建失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """更新用户"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'code': 200,
                'message': '用户更新成功',
                'data': UserSerializer(user, context={'request': request}).data
            })
        
        return Response({
            'code': 400,
            'message': '用户更新失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """删除用户"""
        instance = self.get_object()
        instance.delete()
        return Response({
            'code': 204,
            'message': '用户删除成功',
            'data': {}
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """重置用户密码"""
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response({
                'code': 400,
                'message': '请提供新密码'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 8:
            return Response({
                'code': 400,
                'message': '密码长度不能少于8位'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        return Response({
            'code': 200,
            'message': '密码重置成功',
            'data': {}
        })


class RoleViewSet(ModelViewSet):
    """角色管理视图集"""
    
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsSystemAdmin]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering = ['id']


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """获取当前用户详细信息"""
    user = request.user
    serializer = UserSerializer(user, context={'request': request})
    
    return Response({
        'code': 200,
        'message': 'Success',
        'data': serializer.data
    })