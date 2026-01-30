
# # # 修复 training/views.py - 移除无效的 prefetch_related
# # fixed_training_views_v2 = 
# # '''

# # with open('/mnt/kimi/output/fixed_training_views_v2.py', 'w', encoding='utf-8') as f:
# #     f.write(fixed_training_views_v2)

# # print("✅ 修复后的 training/views.py v2 已创建")
# # print("\n主要修复:")
# # print("1. 移除了 Course.queryset 中无效的 'target_departments' prefetch_related")
# # print("2. 保留了其他有效的 prefetch_related('prerequisites')")


# '''"""Training views"""
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
from apps.users.permissions import IsManager, IsManagerOrReadOnly, IsTrainingManager, IsDeptManager
from apps.users.models import User


class CourseCategoryViewSet(ModelViewSet):
    """课程分类管理视图集"""
    
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated, IsTrainingManager]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering = ['sort_order', 'name']
    
    def list(self, request, *args, **kwargs):
        """获取分类列表（统一响应格式）"""
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
        """创建分类（统一响应格式）"""
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
        """获取分类详情（统一响应格式）"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': 'Success',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """更新分类（统一响应格式）"""
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
        """删除分类（统一响应格式）"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'code': 204,
            'message': '删除成功'
        }, status=status.HTTP_204_NO_CONTENT)
    
    def perform_create(self, serializer):
        """自动设置created_by - 修复：先创建再更新"""
        instance = serializer.save()
        if hasattr(instance, 'created_by'):
            instance.created_by = self.request.user
            instance.save()
    
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
    
    # 修复：移除无效的 target_departments prefetch
    queryset = Course.objects.select_related('category', 'created_by').prefetch_related('prerequisites')
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'course_type', 'status', 'created_by']
    search_fields = ['title', 'code', 'description', 'instructor', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'title', 'view_count', 'enrollment_count']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """动态权限配置"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'publish']:
            return [IsAuthenticated(), IsTrainingManager()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 管理员、经理、工程师可以查看所有课程
        if user.role and user.role.code in [
            'admin', 'hr_manager',
            'training_manager', 'exam_manager',
            'engineering_manager', 'dept_manager',
            'me_engineer', 'te_engineer', 'technician',
            'production_operator'
        ]:
            return self.queryset
        
        # 其他用户只能查看已发布的课程
        return self.queryset.filter(status='published')
    
    def list(self, request, *args, **kwargs):
        """获取课程列表（统一响应格式）"""
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
        """创建课程（统一响应格式）"""
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
        """获取课程详情（统一响应格式）"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': 'Success',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """更新课程（统一响应格式）"""
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
        """删除课程（统一响应格式）"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'code': 204,
            'message': '删除成功'
        }, status=status.HTTP_204_NO_CONTENT)
    
    def perform_create(self, serializer):
        """自动设置created_by"""
        serializer.save(created_by=self.request.user)
    
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
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
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
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['plan_type', 'status', 'target_department', 'target_position']
    search_fields = ['title', 'code', 'description']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """动态权限配置"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsTrainingManager()]
        elif self.action == 'approve':
            return [IsAuthenticated(), IsDeptManager()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 所有经理和工程师可以查看所有计划
        if user.role and user.role.code in [
            'admin', 'hr_manager',
            'training_manager', 'exam_manager',
            'engineering_manager', 'dept_manager',
            'me_engineer', 'te_engineer', 'technician',
            'production_operator'
        ]:
            return self.queryset
        
        # 普通用户只能查看包含自己的计划
        return self.queryset.filter(
            Q(target_users=user) | Q(created_by=user)
        )
    
    def list(self, request, *args, **kwargs):
        """获取计划列表（统一响应格式）"""
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
        """创建计划（统一响应格式）"""
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
        """获取计划详情（统一响应格式）"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': 'Success',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """更新计划（统一响应格式）"""
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
        """删除计划（统一响应格式）"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'code': 204,
            'message': '删除成功'
        }, status=status.HTTP_204_NO_CONTENT)
    
    def perform_create(self, serializer):
        """自动设置created_by"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDeptManager])
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
        
        # 所有经理和工程师可以查看所有记录
        if user.role and user.role.code in [
            'admin', 'hr_manager',
            'training_manager', 'exam_manager',
            'engineering_manager', 'dept_manager',
            'me_engineer', 'te_engineer', 'technician',
            'production_operator'
        ]:
            return self.queryset
        
        # 普通用户只能查看自己的记录
        return self.queryset.filter(user=user)
    
    def list(self, request, *args, **kwargs):
        """获取记录列表（统一响应格式）"""
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
        """创建记录（统一响应格式）"""
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
        """获取记录详情（统一响应格式）"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': 'Success',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """更新记录（统一响应格式）"""
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
        """删除记录（统一响应格式）"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'code': 204,
            'message': '删除成功'
        }, status=status.HTTP_204_NO_CONTENT)
    
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
        
        # 所有经理和工程师可以查看全部统计
        if user.role and user.role.code in [
            'admin', 'hr_manager',
            'training_manager', 'exam_manager',
            'engineering_manager', 'dept_manager',
            'me_engineer', 'te_engineer', 'technician',
            'production_operator'
        ]:
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
            # 普通用户只能看自己的
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
            'completion_rate': round(completion_rate, 2),
            'avg_score': round(avg_score, 2),
            'department_stats': department_stats
        }
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': data
        })
