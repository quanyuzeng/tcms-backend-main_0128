"""Training views"""
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Avg

from .models import CourseCategory, Course, TrainingPlan, TrainingRecord
from .serializers import (
    CourseCategorySerializer, CourseSerializer, CourseDetailSerializer,
    TrainingPlanSerializer, TrainingRecordSerializer,
    TrainingRecordCreateSerializer, CourseEvaluationSerializer,
    TrainingStatisticsSerializer
)
from apps.users.permissions import IsTrainingManager, IsDeptManager


class CourseCategoryViewSet(ModelViewSet):
    """课程分类管理视图集"""
    
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated, IsTrainingManager]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering = ['sort_order', 'name']
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取分类树"""
        top_categories = self.queryset.filter(parent=None)
        serializer = self.get_serializer(top_categories, many=True)
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': serializer.data
        })


class CourseViewSet(ModelViewSet):
    """课程管理视图集"""
    
    queryset = Course.objects.select_related('category', 'created_by').prefetch_related('prerequisites')
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsTrainingManager]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'course_type', 'status', 'created_by']
    search_fields = ['title', 'code', 'description', 'instructor', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'title', 'view_count', 'enrollment_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 管理员和培训管理员可以查看所有课程
        if user.role.code in ['admin', 'hr_manager', 'training_manager']:
            return self.queryset
        
        # 其他用户只能查看已发布的课程
        return self.queryset.filter(status='published')
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布课程"""
        course = self.get_object()
        
        if course.status != 'draft':
            return Response({
                'code': 400,
                'message': '只有草稿状态的课程可以发布'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        course.publish()
        
        return Response({
            'code': 200,
            'message': '课程发布成功',
            'data': CourseSerializer(course).data
        })
    
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """报名课程"""
        course = self.get_object()
        user = request.user
        
        # 检查是否已报名
        if TrainingRecord.objects.filter(user=user, course=course).exists():
            return Response({
                'code': 400,
                'message': '您已经报名了该课程'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建培训记录
        record = TrainingRecord.objects.create(
            user=user,
            course=course,
            status=TrainingRecord.Status.NOT_STARTED
        )
        
        # 更新课程报名人数
        course.enrollment_count += 1
        course.save()
        
        # 发送报名成功邮件通知
        try:
            from apps.common.email_service import EmailService
            EmailService.send_course_enrollment_notification(user, course)
        except Exception as e:
            # 邮件发送失败不影响主流程
            pass
        
        return Response({
            'code': 201,
            'message': '报名成功',
            'data': TrainingRecordSerializer(record).data
        })


class TrainingPlanViewSet(ModelViewSet):
    """培训计划管理视图集"""
    
    queryset = TrainingPlan.objects.select_related(
        'target_department', 'target_position', 'created_by', 'approved_by'
    ).prefetch_related('courses', 'target_users')
    serializer_class = TrainingPlanSerializer
    permission_classes = [IsAuthenticated, IsTrainingManager]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['plan_type', 'status', 'target_department', 'target_position']
    search_fields = ['title', 'code', 'description']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 管理员和培训管理员可以查看所有计划
        if user.role.code in ['admin', 'hr_manager', 'training_manager']:
            return self.queryset
        
        # 部门经理可以查看本部门和公司级计划
        if user.role.code == 'dept_manager':
            return self.queryset.filter(
                Q(target_department=user.department) |
                Q(plan_type='company') |
                Q(target_users=user) |
                Q(created_by=user)
            )
        
        # 普通用户只能查看包含自己的计划
        return self.queryset.filter(
            Q(target_users=user) | Q(created_by=user)
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批培训计划"""
        plan = self.get_object()
        
        if plan.status != 'pending':
            return Response({
                'code': 400,
                'message': '只有待审批状态的计划可以审批'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        is_approved = request.data.get('approved', True)
        comment = request.data.get('comment', '')
        
        if is_approved:
            plan.approve(request.user, comment)
            message = '培训计划审批通过'
        else:
            plan.status = TrainingPlan.Status.REJECTED
            plan.approved_by = request.user
            plan.approved_at = timezone.now()
            plan.approval_comment = comment
            plan.save()
            message = '培训计划已拒绝'
        
        # 发送审批结果通知
        try:
            from apps.common.email_service import EmailService
            EmailService.send_training_plan_approval_notification(plan, is_approved, request.user, comment)
        except Exception as e:
            # 邮件发送失败不影响主流程
            pass
        
        return Response({
            'code': 200,
            'message': message,
            'data': TrainingPlanSerializer(plan).data
        })


class TrainingRecordViewSet(ModelViewSet):
    """培训记录管理视图集"""
    
    queryset = TrainingRecord.objects.select_related(
        'user', 'plan', 'course'
    )
    serializer_class = TrainingRecordSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'plan', 'course']
    search_fields = ['user__real_name', 'user__employee_id', 'course__title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'create':
            return TrainingRecordCreateSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 管理员可以查看所有记录
        if user.role.code in ['admin', 'hr_manager', 'training_manager']:
            return self.queryset
        
        # 部门经理可以查看本部门记录
        if user.role.code == 'dept_manager':
            return self.queryset.filter(
                Q(user__department=user.department) | Q(user=user)
            )
        
        # 普通用户只能查看自己的记录
        return self.queryset.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def evaluate(self, request, pk=None):
        """评价培训记录"""
        record = self.get_object()
        serializer = CourseEvaluationSerializer(data=request.data)
        
        if serializer.is_valid():
            record.evaluation = serializer.validated_data['evaluation']
            record.feedback = serializer.validated_data.get('feedback', '')
            record.save()
            
            return Response({
                'code': 200,
                'message': '评价提交成功',
                'data': TrainingRecordSerializer(record).data
            })
        
        return Response({
            'code': 400,
            'message': '评价提交失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取培训统计"""
        user = request.user
        
        # 基础统计
        if user.role.code in ['admin', 'hr_manager', 'training_manager']:
            total_courses = Course.objects.filter(status='published').count()
            total_trainees = User.objects.filter(status='active').count()
        else:
            total_courses = Course.objects.filter(
                status='published',
                training_records__user=user
            ).distinct().count()
            total_trainees = 1
        
        # 计算完成率
        if user.role.code in ['admin', 'hr_manager', 'training_manager']:
            completed_records = TrainingRecord.objects.filter(
                status='completed'
            ).count()
            total_records = TrainingRecord.objects.count()
        else:
            completed_records = TrainingRecord.objects.filter(
                user=user,
                status='completed'
            ).count()
            total_records = TrainingRecord.objects.filter(user=user).count()
        
        completion_rate = (completed_records / total_records * 100) if total_records > 0 else 0
        
        # 平均成绩
        if user.role.code in ['admin', 'hr_manager', 'training_manager']:
            avg_score = TrainingRecord.objects.filter(
                score__isnull=False
            ).aggregate(avg=Avg('score'))['avg'] or 0
        else:
            avg_score = TrainingRecord.objects.filter(
                user=user,
                score__isnull=False
            ).aggregate(avg=Avg('score'))['avg'] or 0
        
        # 部门统计
        department_stats = []
        if user.role.code in ['admin', 'hr_manager', 'training_manager']:
            from apps.organization.models import Department
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