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
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'parent']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取部门树形结构"""
        # 获取顶级部门
        top_departments = self.queryset.filter(parent=None, status='active')
        serializer = DepartmentTreeSerializer(top_departments, many=True)
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': serializer.data
        })
    
    def list(self, request, *args, **kwargs):
        """获取部门列表"""
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


class PositionViewSet(ModelViewSet):
    """岗位管理视图集"""
    
    queryset = Position.objects.select_related('department').all()
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'level', 'department']
    search_fields = ['name', 'code', 'responsibilities', 'requirements']
    ordering = ['name']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'retrieve':
            return PositionDetailSerializer
        return self.serializer_class
    
    def list(self, request, *args, **kwargs):
        """获取岗位列表"""
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