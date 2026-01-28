"""Reporting views"""
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.utils import timezone

from .models import ReportTemplate, GeneratedReport
from .serializers import ReportTemplateSerializer, GeneratedReportSerializer
from apps.users.permissions import IsSystemAdmin
from apps.users.models import User


class ReportTemplateViewSet(ModelViewSet):
    """报表模板管理视图集"""
    
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    # 只有系统管理员可以管理模板
    permission_classes = [IsAuthenticated, IsSystemAdmin]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """自动设置created_by"""
        serializer.save(created_by=self.request.user)


class GeneratedReportViewSet(ModelViewSet):
    """已生成报表管理视图集"""
    
    queryset = GeneratedReport.objects.select_related('template', 'generated_by')
    serializer_class = GeneratedReportSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template', 'status']
    search_fields = ['template__name']
    ordering = ['-generated_at']
    
    def get_queryset(self):
        """根据权限过滤"""
        user = self.request.user
        
        # 所有经理和工程师可以查看所有报表
        if user.role and user.role.code in [
            'admin', 'hr_manager',
            'training_manager', 'exam_manager',
            'engineering_manager', 'dept_manager',
            'me_engineer', 'te_engineer', 'technician',
            'production_operator'
        ]:
            return self.queryset
        
        return self.queryset.filter(generated_by=user)
    
    def perform_create(self, serializer):
        """自动设置created_by"""
        serializer.save(generated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """下载报表"""
        report = self.get_object()
        
        if not report.file_path or not report.file_path.storage.exists(report.file_path.name):
            return Response({
                'code': 404,
                'message': '报表文件不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 返回文件下载响应
        from django.http import FileResponse
        return FileResponse(report.file_path.open('rb'), as_attachment=True)


class ReportingViewSet(ModelViewSet):
    """报表视图集"""
    
    permission_classes = [IsAuthenticated]
    
    # 允许查看报表的角色列表（所有经理和工程师）
    REPORT_VIEWER_ROLES = [
        'admin', 'hr_manager',
        'training_manager', 'exam_manager',
        'engineering_manager', 'dept_manager',
        'me_engineer', 'te_engineer', 'technician',
        'production_operator'
    ]
    
    # 允许查看所有数据的角色（经理级别）
    FULL_ACCESS_ROLES = [
        'admin', 'hr_manager',
        'training_manager', 'exam_manager',
        'engineering_manager', 'dept_manager'
    ]
    
    @action(detail=False, methods=['get'])
    def training_statistics(self, request):
        """培训统计报表"""
        user = request.user
        
        # 检查权限
        if user.role and user.role.code not in self.REPORT_VIEWER_ROLES:
            return Response({
                'code': 403,
                'message': '无权访问此报表'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from apps.training.models import Course, TrainingRecord
        
        # 统计数据
        if user.role and user.role.code in self.FULL_ACCESS_ROLES:
            total_courses = Course.objects.filter(status='published').count()
            total_trainees = User.objects.filter(status='active').count()
            total_records = TrainingRecord.objects.count()
            completed_records = TrainingRecord.objects.filter(status='completed').count()
            avg_score = TrainingRecord.objects.filter(
                score__isnull=False
            ).aggregate(avg=Avg('score'))['avg'] or 0
            
            # 部门统计
            from apps.organization.models import Department
            department_stats = []
            departments = Department.objects.filter(status='active')
            for dept in departments:
                dept_records = TrainingRecord.objects.filter(
                    user__department=dept
                )
                dept_completed = dept_records.filter(status='completed').count()
                dept_total = dept_records.count()
                dept_completion_rate = (dept_completed / dept_total * 100) if dept_total > 0 else 0
                
                department_stats.append({
                    'department_name': dept.name,
                    'course_count': Course.objects.filter(
                        training_records__user__department=dept
                    ).distinct().count(),
                    'trainee_count': dept.employee_count,
                    'completion_rate': round(dept_completion_rate, 2)
                })
        else:
            # 工程师只能看自己的数据
            total_courses = Course.objects.filter(
                status='published',
                training_records__user=user
            ).distinct().count()
            total_trainees = 1
            total_records = TrainingRecord.objects.filter(user=user).count()
            completed_records = TrainingRecord.objects.filter(
                user=user,
                status='completed'
            ).count()
            avg_score = TrainingRecord.objects.filter(
                user=user,
                score__isnull=False
            ).aggregate(avg=Avg('score'))['avg'] or 0
            department_stats = []
        
        completion_rate = (completed_records / total_records * 100) if total_records > 0 else 0
        
        data = {
            'total_courses': total_courses,
            'total_trainees': total_trainees,
            'total_records': total_records,
            'completed_records': completed_records,
            'completion_rate': round(completion_rate, 2),
            'avg_score': round(avg_score, 2),
            'department_stats': department_stats
        }
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': data
        })
    
    @action(detail=False, methods=['get'])
    def competency_statistics(self, request):
        """能力统计报表"""
        user = request.user
        
        # 检查权限
        if user.role and user.role.code not in self.REPORT_VIEWER_ROLES:
            return Response({
                'code': 403,
                'message': '无权访问此报表'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from apps.competency.models import CompetencyAssessment, Certificate
        
        # 统计数据
        if user.role and user.role.code in self.FULL_ACCESS_ROLES:
            total_assessments = CompetencyAssessment.objects.count()
            approved_assessments = CompetencyAssessment.objects.filter(status='approved').count()
            total_certificates = Certificate.objects.filter(status='valid').count()
            expired_certificates = Certificate.objects.filter(status='expired').count()
            
            # 部门统计
            from apps.organization.models import Department
            department_stats = []
            departments = Department.objects.filter(status='active')
            for dept in departments:
                dept_assessments = CompetencyAssessment.objects.filter(user__department=dept).count()
                dept_approved = CompetencyAssessment.objects.filter(
                    user__department=dept,
                    status='approved'
                ).count()
                dept_certificates = Certificate.objects.filter(
                    user__department=dept,
                    status='valid'
                ).count()
                
                department_stats.append({
                    'department_name': dept.name,
                    'total_assessments': dept_assessments,
                    'approved_assessments': dept_approved,
                    'approval_rate': round(dept_approved / dept_assessments * 100, 2) if dept_assessments > 0 else 0,
                    'valid_certificates': dept_certificates
                })
        else:
            # 工程师只能看自己的数据
            total_assessments = CompetencyAssessment.objects.filter(user=user).count()
            approved_assessments = CompetencyAssessment.objects.filter(
                user=user,
                status='approved'
            ).count()
            total_certificates = Certificate.objects.filter(
                user=user,
                status='valid'
            ).count()
            expired_certificates = Certificate.objects.filter(
                user=user,
                status='expired'
            ).count()
            department_stats = []
        
        data = {
            'total_assessments': total_assessments,
            'approved_assessments': approved_assessments,
            'approval_rate': round(approved_assessments / total_assessments * 100, 2) if total_assessments > 0 else 0,
            'total_certificates': total_certificates,
            'expired_certificates': expired_certificates,
            'department_stats': department_stats
        }
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': data
        })