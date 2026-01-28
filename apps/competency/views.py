"""Competency views"""
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q

from .models import Competency, CompetencyAssessment, Certificate
from .serializers import (
    CompetencySerializer, CompetencyAssessmentSerializer, CertificateSerializer,
    CertificateVerifySerializer, CertificateGenerateSerializer
)
from apps.users.permissions import IsManager, IsManagerOrReadOnly


class IsCompetencyManager(BasePermission):
    """
    能力管理权限（所有经理和工程师）
    """
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


class CompetencyViewSet(ModelViewSet):
    """能力管理视图集"""
    
    queryset = Competency.objects.select_related('created_by').prefetch_related(
        'related_positions', 'related_courses'
    )
    serializer_class = CompetencySerializer
    # 所有经理和工程师都可以创建
    permission_classes = [IsAuthenticated, IsCompetencyManager]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """自动设置created_by"""
        serializer.save(created_by=self.request.user)


class CompetencyAssessmentViewSet(ModelViewSet):
    """能力评估管理视图集"""
    
    queryset = CompetencyAssessment.objects.select_related(
        'user', 'competency', 'assessor'
    )
    serializer_class = CompetencyAssessmentSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'competency', 'status', 'level']
    search_fields = ['user__real_name', 'user__employee_id', 'competency__name']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        自定义权限：
        - list/retrieve: 所有认证用户
        - create/update/destroy/approve: 需要经理或工程师权限
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsCompetencyManager]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """根据权限过滤"""
        user = self.request.user
        
        # 所有经理和工程师可以查看所有评估
        if user.role and user.role.code in [
            'admin', 'hr_manager',
            'training_manager', 'exam_manager',
            'engineering_manager', 'dept_manager',
            'me_engineer', 'te_engineer', 'technician',
            'production_operator'
        ]:
            return self.queryset
        
        return self.queryset.filter(user=user)
    
    def perform_create(self, serializer):
        """自动设置assessor为当前用户"""
        serializer.save(assessor=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批评估"""
        assessment = self.get_object()
        
        if assessment.status != 'completed':
            return Response({
                'code': 400,
                'message': '只有已完成的评估才能审批'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        is_approved = request.data.get('approved', True)
        comment = request.data.get('comment', '')
        
        if is_approved:
            assessment.status = CompetencyAssessment.Status.APPROVED
            assessment.assessor_comment = comment
            assessment.assessed_at = timezone.now()
            assessment.save()
            
            # 生成证书
            try:
                certificate = assessment.generate_certificate(issued_by=request.user)
            except Exception as e:
                return Response({
                    'code': 500,
                    'message': f'证书生成失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            message = '评估审批通过'
        else:
            assessment.status = CompetencyAssessment.Status.REJECTED
            assessment.assessor_comment = comment
            assessment.assessed_at = timezone.now()
            assessment.save()
            message = '评估已拒绝'
        
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
    filterset_fields = ['user', 'competency', 'status']
    search_fields = ['user__real_name', 'certificate_no', 'competency__name']
    ordering = ['-issue_date']
    
    def get_permissions(self):
        """
        自定义权限：
        - list/retrieve/verify: 所有认证用户
        - create/update/destroy/generate/revoke: 需要经理或工程师权限
        """
        if self.action in ['list', 'retrieve', 'verify']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsCompetencyManager]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """根据权限过滤"""
        user = self.request.user
        
        # 所有经理和工程师可以查看所有证书
        if user.role and user.role.code in [
            'admin', 'hr_manager',
            'training_manager', 'exam_manager',
            'engineering_manager', 'dept_manager',
            'me_engineer', 'te_engineer', 'technician',
            'production_operator'
        ]:
            return self.queryset
        
        return self.queryset.filter(user=user)
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """验证证书"""
        serializer = CertificateVerifySerializer(data=request.data)
        
        if serializer.is_valid():
            verification_code = serializer.validated_data['verification_code']
            
            try:
                certificate = Certificate.objects.get(verification_code=verification_code)
                return Response({
                    'code': 200,
                    'message': '证书验证成功',
                    'data': CertificateSerializer(certificate).data
                })
            except Certificate.DoesNotExist:
                return Response({
                    'code': 404,
                    'message': '证书不存在或无效'
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
            
            from apps.examination.models import ExamResult
            
            if exam_result_id:
                try:
                    exam_result = ExamResult.objects.get(id=exam_result_id)
                    if not exam_result.is_passed:
                        return Response({
                            'code': 400,
                            'message': '考试未通过，无法生成证书'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 创建证书
                    certificate = Certificate.objects.create(
                        name=f"{exam_result.exam.title}证书",
                        user=exam_result.user,
                        competency=None,  # 考试证书不关联能力
                        exam_result=exam_result,
                        issued_by=request.user,
                        issue_date=timezone.now().date(),
                        expiry_date=expiry_date
                    )
                    
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
            
            if assessment_id:
                try:
                    assessment = CompetencyAssessment.objects.get(id=assessment_id)
                    certificate = assessment.generate_certificate(issued_by=request.user)
                    if expiry_date:
                        certificate.expiry_date = expiry_date
                        certificate.save()
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
                except ValueError as e:
                    return Response({
                        'code': 400,
                        'message': str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'code': 400,
            'message': '生成失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """吊销证书"""
        certificate = self.get_object()
        certificate.revoke()
        
        return Response({
            'code': 200,
            'message': '证书已吊销',
            'data': CertificateSerializer(certificate).data
        })