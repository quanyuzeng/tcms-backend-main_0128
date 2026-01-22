"""Competency views"""
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q

from .models import Competency, CompetencyAssessment, Certificate
from .serializers import (
    CompetencySerializer, CompetencyTreeSerializer,
    CompetencyAssessmentSerializer, CertificateSerializer,
    CertificateVerifySerializer, CertificateGenerateSerializer
)
from apps.users.permissions import IsTrainingManager, IsDeptManager


class CompetencyViewSet(ModelViewSet):
    """能力管理视图集"""
    
    queryset = Competency.objects.select_related('created_by', 'parent').prefetch_related(
        'related_positions', 'related_courses'
    )
    serializer_class = CompetencySerializer
    permission_classes = [IsAuthenticated, IsTrainingManager]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'level', 'assessment_method', 'required']
    search_fields = ['name', 'code', 'description', 'category']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取能力树"""
        top_competencies = self.queryset.filter(parent=None)
        serializer = CompetencyTreeSerializer(top_competencies, many=True)
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': serializer.data
        })


class CompetencyAssessmentViewSet(ModelViewSet):
    """能力评估管理视图集"""
    
    queryset = CompetencyAssessment.objects.select_related(
        'user', 'competency', 'assessor'
    )
    serializer_class = CompetencyAssessmentSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'competency', 'assessor']
    search_fields = ['user__real_name', 'competency__name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 管理员可以查看所有评估
        if user.role.code in ['admin', 'hr_manager', 'training_manager']:
            return self.queryset
        
        # 部门经理可以查看本部门评估
        if user.role.code == 'dept_manager':
            return self.queryset.filter(
                Q(user__department=user.department) | Q(user=user)
            )
        
        # 普通用户只能查看自己的评估
        return self.queryset.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批能力评估"""
        assessment = self.get_object()
        
        if assessment.status != 'completed':
            return Response({
                'code': 400,
                'message': '只有已完成状态的评估可以审批'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        is_approved = request.data.get('approved', True)
        
        if is_approved:
            assessment.approve()
            message = '能力评估审批通过'
        else:
            assessment.status = CompetencyAssessment.Status.REJECTED
            assessment.save()
            message = '能力评估已拒绝'
        
        return Response({
            'code': 200,
            'message': message,
            'data': CompetencyAssessmentSerializer(assessment).data
        })


class CertificateViewSet(ModelViewSet):
    """证书管理视图集"""
    
    queryset = Certificate.objects.select_related(
        'user', 'competency', 'issued_by'
    )
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'competency', 'user']
    search_fields = ['name', 'certificate_no', 'user__real_name', 'verification_code']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 管理员可以查看所有证书
        if user.role.code in ['admin', 'hr_manager', 'training_manager']:
            return self.queryset
        
        # 部门经理可以查看本部门证书
        if user.role.code == 'dept_manager':
            return self.queryset.filter(
                Q(user__department=user.department) | Q(user=user)
            )
        
        # 普通用户只能查看自己的证书
        return self.queryset.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """吊销证书"""
        certificate = self.get_object()
        
        if certificate.status == Certificate.Status.REVOKED:
            return Response({
                'code': 400,
                'message': '证书已被吊销'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        certificate.revoke()
        
        return Response({
            'code': 200,
            'message': '证书吊销成功',
            'data': CertificateSerializer(certificate).data
        })
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """验证证书"""
        serializer = CertificateVerifySerializer(data=request.data)
        
        if serializer.is_valid():
            verification_code = serializer.validated_data['verification_code']
            
            try:
                certificate = Certificate.objects.get(verification_code=verification_code)
                is_valid, message = certificate.verify()
                
                return Response({
                    'code': 200,
                    'message': message,
                    'data': {
                        'is_valid': is_valid,
                        'certificate': CertificateSerializer(certificate).data
                    }
                })
            except Certificate.DoesNotExist:
                return Response({
                    'code': 404,
                    'message': '证书不存在'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'code': 400,
            'message': '验证失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """生成证书"""
        serializer = CertificateGenerateSerializer(data=request.data)
        
        if serializer.is_valid():
            exam_result_id = serializer.validated_data.get('exam_result_id')
            assessment_id = serializer.validated_data.get('assessment_id')
            expiry_date = serializer.validated_data.get('expiry_date')
            
            # 根据考试成绩生成证书
            if exam_result_id:
                from apps.examination.models import ExamResult
                try:
                    exam_result = ExamResult.objects.get(id=exam_result_id)
                    
                    if not exam_result.is_passed:
                        return Response({
                            'code': 400,
                            'message': '考试未通过，无法生成证书'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 检查是否已存在证书
                    if hasattr(exam_result, 'certificate'):
                        return Response({
                            'code': 400,
                            'message': '证书已存在'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 创建证书
                    certificate = Certificate.objects.create(
                        name=f"{exam_result.exam.title} 证书",
                        user=exam_result.user,
                        competency=exam_result.exam.course.related_competencies.first(),
                        exam_result=exam_result,
                        issue_date=timezone.now().date(),
                        expiry_date=expiry_date,
                        issued_by=request.user
                    )
                    
                    # 发送证书颁发通知
                    try:
                        from apps.common.email_service import EmailService
                        EmailService.send_certificate_notification(exam_result.user, certificate)
                    except Exception as e:
                        # 邮件发送失败不影响主流程
                        pass
                    
                    return Response({
                        'code': 201,
                        'message': '证书生成成功',
                        'data': CertificateSerializer(certificate).data
                    }, status=status.HTTP_201_CREATED)
                
                except ExamResult.DoesNotExist:
                    return Response({
                        'code': 404,
                        'message': '考试成绩不存在'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # 根据能力评估生成证书
            elif assessment_id:
                try:
                    assessment = CompetencyAssessment.objects.get(id=assessment_id)
                    
                    if assessment.status != 'approved':
                        return Response({
                            'code': 400,
                            'message': '评估未通过审批，无法生成证书'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 检查是否已存在证书
                    if hasattr(assessment, 'certificate'):
                        return Response({
                            'code': 400,
                            'message': '证书已存在'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 创建证书
                    certificate = Certificate.objects.create(
                        name=f"{assessment.competency.name} 能力证书",
                        user=assessment.user,
                        competency=assessment.competency,
                        assessment=assessment,
                        issue_date=timezone.now().date(),
                        expiry_date=expiry_date,
                        issued_by=request.user
                    )
                    
                    return Response({
                        'code': 201,
                        'message': '证书生成成功',
                        'data': CertificateSerializer(certificate).data
                    }, status=status.HTTP_201_CREATED)
                
                except CompetencyAssessment.DoesNotExist:
                    return Response({
                        'code': 404,
                        'message': '能力评估不存在'
                    }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'code': 400,
            'message': '生成失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)