"""Reporting views"""
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from .models import ReportTemplate, GeneratedReport
from .serializers import (
    ReportTemplateSerializer, GeneratedReportSerializer,
    ReportExportSerializer, TrainingStatisticsSerializer,
    ExamAnalysisSerializer, CompetencyMatrixSerializer,
    ComplianceReportSerializer
)
from apps.users.permissions import IsAdminOrHR, IsTrainingManager


class ReportTemplateViewSet(ModelViewSet):
    """报表模板管理视图集"""
    
    queryset = ReportTemplate.objects.select_related('created_by').all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering = ['-created_at']


class GeneratedReportViewSet(ModelViewSet):
    """生成的报表管理视图集"""
    
    queryset = GeneratedReport.objects.select_related('template', 'generated_by').all()
    serializer_class = GeneratedReportSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template', 'status', 'file_format']
    search_fields = ['title', 'template__name']
    ordering = ['-generated_at']
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 管理员可以查看所有报表
        if user.role.code in ['admin', 'hr_manager']:
            return self.queryset
        
        # 普通用户只能查看自己生成的报表
        return self.queryset.filter(generated_by=user)


class ReportingViewSet(ModelViewSet):
    """报表视图集"""
    
    permission_classes = [IsAuthenticated, IsTrainingManager]
    
    @action(detail=False, methods=['get'])
    def training_statistics(self, request):
        """培训统计报表"""
        # 获取查询参数
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        department_id = request.query_params.get('department_id')
        
        # 构建查询条件
        filters = Q()
        if start_date:
            filters &= Q(created_at__gte=start_date)
        if end_date:
            filters &= Q(created_at__lte=end_date)
        if department_id:
            filters &= Q(user__department_id=department_id)
        
        # 统计数据
        from apps.training.models import TrainingRecord, Course
        
        # 总课程数
        total_courses = Course.objects.filter(status='published').count()
        
        # 总培训人数
        total_trainees = TrainingRecord.objects.filter(filters).values('user').distinct().count()
        
        # 完成率
        completed_count = TrainingRecord.objects.filter(filters, status='completed').count()
        total_records = TrainingRecord.objects.filter(filters).count()
        completion_rate = (completed_count / total_records * 100) if total_records > 0 else 0
        
        # 平均成绩
        avg_score = TrainingRecord.objects.filter(
            filters, score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        # 部门统计
        department_stats = []
        from apps.organization.models import Department
        departments = Department.objects.filter(status='active')
        
        for dept in departments:
            dept_filters = filters & Q(user__department=dept)
            dept_records = TrainingRecord.objects.filter(dept_filters)
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
        
        data = {
            'total_courses': total_courses,
            'total_trainees': total_trainees,
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
    def exam_analysis(self, request):
        """考试分析报表"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # 构建查询条件
        filters = Q()
        if start_date:
            filters &= Q(created_at__gte=start_date)
        if end_date:
            filters &= Q(created_at__lte=end_date)
        
        from apps.examination.models import Exam, ExamResult
        
        # 总考试数
        total_exams = Exam.objects.filter(filters).count()
        
        # 总参与人数
        total_participants = ExamResult.objects.filter(
            filters, submitted_at__isnull=False
        ).values('user').distinct().count()
        
        # 平均成绩
        avg_score = ExamResult.objects.filter(
            filters, score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        # 通过率
        passed_count = ExamResult.objects.filter(filters, is_passed=True).count()
        total_results = ExamResult.objects.filter(filters).count()
        pass_rate = (passed_count / total_results * 100) if total_results > 0 else 0
        
        # 考试统计
        exam_stats = []
        exams = Exam.objects.filter(filters)
        for exam in exams:
            exam_results = ExamResult.objects.filter(exam=exam)
            exam_avg = exam_results.filter(score__isnull=False).aggregate(avg=Avg('score'))['avg'] or 0
            exam_pass_rate = (exam_results.filter(is_passed=True).count() / exam_results.count() * 100) if exam_results.count() > 0 else 0
            
            exam_stats.append({
                'exam_title': exam.title,
                'participant_count': exam_results.count(),
                'avg_score': round(exam_avg, 2),
                'pass_rate': round(exam_pass_rate, 2)
            })
        
        data = {
            'total_exams': total_exams,
            'total_participants': total_participants,
            'avg_score': round(avg_score, 2),
            'pass_rate': round(pass_rate, 2),
            'exam_stats': exam_stats
        }
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': data
        })
    
    @action(detail=False, methods=['get'])
    def competency_matrix(self, request):
        """能力矩阵报表"""
        department_id = request.query_params.get('department_id')
        position_id = request.query_params.get('position_id')
        
        # 构建查询条件
        filters = Q()
        if department_id:
            filters &= Q(department_id=department_id)
        if position_id:
            filters &= Q(position_id=position_id)
        
        from apps.users.models import User
        from apps.competency.models import Competency, CompetencyAssessment
        
        # 获取用户列表
        users = User.objects.filter(filters, status='active')
        
        # 获取能力列表
        competencies = Competency.objects.filter(required=True)
        
        # 构建矩阵数据
        matrix = []
        for user in users:
            user_data = {
                'user_id': user.id,
                'user_name': user.real_name,
                'department': user.department.name if user.department else '',
                'position': user.position.name if user.position else '',
                'competencies': []
            }
            
            for competency in competencies:
                try:
                    assessment = CompetencyAssessment.objects.get(
                        user=user, competency=competency
                    )
                    competency_data = {
                        'competency_id': competency.id,
                        'competency_name': competency.name,
                        'status': assessment.status,
                        'level': assessment.level,
                        'score': assessment.score,
                        'is_expired': assessment.is_expired
                    }
                except CompetencyAssessment.DoesNotExist:
                    competency_data = {
                        'competency_id': competency.id,
                        'competency_name': competency.name,
                        'status': 'not_assessed',
                        'level': None,
                        'score': None,
                        'is_expired': False
                    }
                
                user_data['competencies'].append(competency_data)
            
            matrix.append(user_data)
        
        data = {
            'users': list(users.values('id', 'real_name', 'department__name', 'position__name')),
            'competencies': list(competencies.values('id', 'name', 'level')),
            'matrix': matrix
        }
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': data
        })
    
    @action(detail=False, methods=['get'])
    def compliance_report(self, request):
        """合规性报表"""
        department_id = request.query_params.get('department_id')
        
        # 构建查询条件
        filters = Q(status='active')
        if department_id:
            filters &= Q(department_id=department_id)
        
        from apps.users.models import User
        from apps.competency.models import Certificate
        from apps.training.models import TrainingRecord
        
        # 总员工数
        total_employees = User.objects.filter(filters).count()
        
        # 合规员工数（所有必需培训和证书都完成）
        # 这里简化处理，实际应该根据岗位要求判断
        compliant_employees = User.objects.filter(
            filters,
            training_records__status='completed'
        ).distinct().count()
        
        compliance_rate = (compliant_employees / total_employees * 100) if total_employees > 0 else 0
        
        # 不合规员工
        non_compliant_users = User.objects.filter(
            filters
        ).exclude(
            id__in=User.objects.filter(
                training_records__status='completed'
            ).values('id')
        ).values('id', 'real_name', 'employee_id', 'department__name')
        
        # 过期证书
        expired_certificates = Certificate.objects.filter(
            Q(user__department_id=department_id) if department_id else Q(),
            expiry_date__lt=timezone.now().date(),
            status='valid'
        ).values(
            'id', 'name', 'certificate_no', 'user__real_name',
            'expiry_date', 'competency__name'
        )
        
        data = {
            'total_employees': total_employees,
            'compliant_employees': compliant_employees,
            'compliance_rate': round(compliance_rate, 2),
            'non_compliant_users': list(non_compliant_users),
            'expired_certificates': list(expired_certificates)
        }
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': data
        })
    
    @action(detail=False, methods=['post'])
    def export(self, request):
        """导出报表"""
        serializer = ReportExportSerializer(data=request.data)
        
        if serializer.is_valid():
            report_type = serializer.validated_data['report_type']
            file_format = serializer.validated_data['format']
            filters = serializer.validated_data.get('filters', {})
            
            # 这里可以实现实际的导出逻辑
            # 暂时返回成功响应
            return Response({
                'code': 200,
                'message': '报表导出任务已提交',
                'data': {
                    'report_type': report_type,
                    'format': file_format,
                    'filters': filters,
                    'download_url': f'/api/reporting/download/{report_type}.{file_format}'
                }
            })
        
        return Response({
            'code': 400,
            'message': '导出失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)