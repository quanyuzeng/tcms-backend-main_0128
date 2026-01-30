"""Organization views"""
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from .models import Department, Position
from .serializers import (
    DepartmentSerializer, DepartmentTreeSerializer,
    PositionSerializer, PositionDetailSerializer
)
from apps.users.permissions import IsAdminOrHR


class DepartmentViewSet(ModelViewSet):
    """部门管理视图集"""
    
    queryset = Department.objects.select_related('manager').all()
    serializer_class = DepartmentSerializer
    # 修复认证问题：必须显式声明，即使settings中有全局配置
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # 修复筛选问题：添加 'id' 精确匹配 + 'status', 'parent'
    filterset_fields = ['id', 'status', 'parent']
    search_fields = ['name', 'code', 'description']
    # 使用DRF默认search参数名（前端需同步改为search）
    ordering = ['name']
    
    def list(self, request, *args, **kwargs):
        """获取部门列表（支持过滤/搜索/分页）"""
        queryset = self.filter_queryset(self.get_queryset())
        
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
        """创建部门（统一响应格式）"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({
            'code': 201,
            'message': '创建成功',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)
    
    def retrieve(self, request, *args, **kwargs):
        """获取部门详情（统一响应格式）"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': 'Success',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """更新部门（统一响应格式）"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'code': 200,
            'message': '更新成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """删除部门（统一响应格式）"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'code': 204,
            'message': '删除成功'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取部门树形结构（仅顶级部门）"""
        top_departments = self.queryset.filter(parent=None, status='active')
        serializer = DepartmentTreeSerializer(top_departments, many=True)
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': serializer.data
        })


class PositionViewSet(ModelViewSet):
    """岗位管理视图集"""
    
    queryset = Position.objects.select_related('department').all()
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'status', 'level', 'department']
    search_fields = ['name', 'code', 'responsibilities', 'requirements']
    ordering = ['name']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'retrieve':
            return PositionDetailSerializer
        return self.serializer_class
    
    def list(self, request, *args, **kwargs):
        """获取岗位列表（支持过滤/搜索/分页）"""
        queryset = self.filter_queryset(self.get_queryset())
        
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
        """创建岗位（统一响应格式）"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({
            'code': 201,
            'message': '创建成功',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)
    
    def retrieve(self, request, *args, **kwargs):
        """获取岗位详情（统一响应格式）"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': 'Success',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """更新岗位（统一响应格式）"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'code': 200,
            'message': '更新成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """删除岗位（统一响应格式）"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'code': 204,
            'message': '删除成功'
        }, status=status.HTTP_204_NO_CONTENT)