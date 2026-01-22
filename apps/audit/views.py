"""Audit views"""
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import AuditLog
from .serializers import AuditLogSerializer, AuditLogSummarySerializer
from apps.users.permissions import IsAdminOrHR


class AuditLogViewSet(ModelViewSet):
    """审计日志视图集"""
    
    queryset = AuditLog.objects.select_related('operator').all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'module', 'status', 'operator']
    search_fields = [
        'operator_name', 'operator_username', 'module',
        'object_name', 'description', 'ip_address'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 管理员可以查看所有日志
        if user.role.code in ['admin', 'hr_manager']:
            return self.queryset
        
        # 部门经理可以查看本部门日志
        if user.role.code == 'dept_manager':
            return self.queryset.filter(
                Q(operator__department=user.department) | Q(operator=user)
            )
        
        # 普通用户只能查看自己的日志
        return self.queryset.filter(operator=user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """获取审计日志汇总"""
        # 时间范围
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(created_at__gte=start_date)
        
        # 统计信息
        total_logs = queryset.count()
        success_count = queryset.filter(status='success').count()
        failed_count = queryset.filter(status='failed').count()
        
        # 按模块统计
        top_modules = list(
            queryset.values('module')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # 按操作类型统计
        top_actions = list(
            queryset.values('action')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # 最近的日志
        recent_logs = list(
            queryset.order_by('-created_at')[:10]
            .values('id', 'action', 'module', 'operator_name', 'status', 'created_at')
        )
        
        data = {
            'total_logs': total_logs,
            'success_count': success_count,
            'failed_count': failed_count,
            'top_modules': top_modules,
            'top_actions': top_actions,
            'recent_logs': recent_logs
        }
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': data
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """导出审计日志"""
        # 获取查询参数
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # 构建查询条件
        queryset = self.get_queryset()
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # 这里可以实现实际的导出逻辑
        # 暂时返回成功响应
        return Response({
            'code': 200,
            'message': '审计日志导出任务已提交',
            'data': {
                'total_count': queryset.count(),
                'download_url': '/api/audit/download/audit_logs.xlsx'
            }
        })