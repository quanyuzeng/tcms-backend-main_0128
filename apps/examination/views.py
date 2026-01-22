"""Examination views"""
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
import random

from .models import QuestionBank, Question, Exam, ExamResult
from .serializers import (
    QuestionBankSerializer, QuestionSerializer, QuestionImportSerializer,
    ExamSerializer, ExamDetailSerializer, ExamResultSerializer,
    ExamSubmitSerializer, ParticipantManageSerializer
)
from apps.users.permissions import IsExamManager, IsTrainingManager


class QuestionBankViewSet(ModelViewSet):
    """题库管理视图集"""
    
    queryset = QuestionBank.objects.select_related('created_by').all()
    serializer_class = QuestionBankSerializer
    permission_classes = [IsAuthenticated, IsExamManager]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'category', 'description']
    ordering = ['-created_at']


class QuestionViewSet(ModelViewSet):
    """题目管理视图集"""
    
    queryset = Question.objects.select_related('question_bank', 'created_by').all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, IsExamManager]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['question_bank', 'question_type', 'difficulty']
    search_fields = ['title', 'content']
    ordering = ['sort_order', 'id']
    
    @action(detail=False, methods=['post'])
    def import_questions(self, request):
        """批量导入题目"""
        serializer = QuestionImportSerializer(data=request.data)
        if serializer.is_valid():
            # 这里可以实现Excel/CSV导入逻辑
            # 暂时返回成功响应
            return Response({
                'code': 200,
                'message': '题目导入成功',
                'data': {}
            })
        
        return Response({
            'code': 400,
            'message': '导入失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ExamViewSet(ModelViewSet):
    """考试管理视图集"""
    
    queryset = Exam.objects.select_related(
        'course', 'question_bank', 'created_by'
    ).prefetch_related('participants')
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, IsExamManager]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam_type', 'status', 'course', 'question_bank']
    search_fields = ['title', 'code', 'description']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'retrieve':
            return ExamDetailSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 管理员和考试管理员可以查看所有考试
        if user.role.code in ['admin', 'hr_manager', 'exam_manager']:
            return self.queryset
        
        # 讲师可以查看自己创建的和相关的考试
        if user.role.code == 'instructor':
            return self.queryset.filter(
                Q(created_by=user) | Q(course__created_by=user)
            )
        
        # 普通用户只能查看已发布的考试
        return self.queryset.filter(
            Q(status='published') | Q(participants=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布考试"""
        exam = self.get_object()
        
        if exam.status != 'draft':
            return Response({
                'code': 400,
                'message': '只有草稿状态的考试可以发布'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        exam.publish()
        
        return Response({
            'code': 200,
            'message': '考试发布成功',
            'data': ExamSerializer(exam).data
        })
    
    @action(detail=True, methods=['post'])
    def participants(self, request, pk=None):
        """管理参与人员"""
        exam = self.get_object()
        serializer = ParticipantManageSerializer(data=request.data)
        
        if serializer.is_valid():
            user_ids = serializer.validated_data['user_ids']
            action = serializer.validated_data['action']
            
            from apps.users.models import User
            users = User.objects.filter(id__in=user_ids)
            
            if action == 'add':
                exam.participants.add(*users)
                message = '参与人员添加成功'
            else:
                exam.participants.remove(*users)
                message = '参与人员移除成功'
            
            return Response({
                'code': 200,
                'message': message,
                'data': {}
            })
        
        return Response({
            'code': 400,
            'message': '操作失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """提交考试"""
        exam = self.get_object()
        user = request.user
        
        # 检查考试是否在进行中
        if not exam.is_in_progress():
            return Response({
                'code': 400,
                'message': '考试不在进行时间段内'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取或创建考试结果
        try:
            result = ExamResult.objects.get(exam=exam, user=user)
            if result.status == 'submitted':
                return Response({
                    'code': 400,
                    'message': '您已经提交过该考试'
                }, status=status.HTTP_400_BAD_REQUEST)
        except ExamResult.DoesNotExist:
            result = ExamResult(exam=exam, user=user)
        
        # 验证提交数据
        serializer = ExamSubmitSerializer(data=request.data)
        if serializer.is_valid():
            # 保存考试结果
            result.answers = serializer.validated_data['answers']
            result.duration = serializer.validated_data['duration']
            result.start_time = result.created_at
            result.submitted_at = timezone.now()
            result.status = ExamResult.Status.SUBMITTED
            result.save()
            
            # 自动评分
            result.grade()
            
            # 发送考试成绩通知
            try:
                from apps.common.email_service import EmailService
                EmailService.send_exam_result_notification(user, result)
            except Exception as e:
                # 邮件发送失败不影响主流程
                pass
            
            return Response({
                'code': 200,
                'message': '考试提交成功',
                'data': ExamResultSerializer(result).data
            })
        
        return Response({
            'code': 400,
            'message': '提交失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def start(self, request, pk=None):
        """开始考试"""
        exam = self.get_object()
        user = request.user
        
        # 检查考试是否在进行中
        if not exam.is_in_progress():
            return Response({
                'code': 400,
                'message': '考试不在进行时间段内'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查用户是否有权限参加
        if not exam.participants.filter(id=user.id).exists():
            return Response({
                'code': 403,
                'message': '您没有权限参加该考试'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 检查尝试次数
        try:
            result = ExamResult.objects.get(exam=exam, user=user)
            if result.status == ExamResult.Status.IN_PROGRESS:
                # 继续考试
                pass
            elif exam.max_attempts and exam.max_attempts <= 1:
                return Response({
                    'code': 400,
                    'message': '您已经参加过该考试'
                }, status=status.HTTP_400_BAD_REQUEST)
        except ExamResult.DoesNotExist:
            # 创建新的考试结果
            result = ExamResult.objects.create(
                exam=exam,
                user=user,
                status=ExamResult.Status.IN_PROGRESS
            )
        
        # 生成考试题目
        questions = list(exam.question_bank.questions.all())
        
        # 随机排序题目
        if exam.random_order:
            random.shuffle(questions)
        
        # 限制题目数量
        questions = questions[:exam.total_questions]
        
        # 序列化题目（不返回正确答案）
        question_data = []
        for question in questions:
            question_info = {
                'id': question.id,
                'question_type': question.question_type,
                'difficulty': question.difficulty,
                'title': question.title,
                'content': question.content,
                'options': question.options,
                'score': question.score,
            }
            question_data.append(question_info)
        
        return Response({
            'code': 200,
            'message': 'Success',
            'data': {
                'exam_info': ExamSerializer(exam).data,
                'questions': question_data,
                'start_time': result.start_time,
                'remaining_time': exam.time_limit * 60  # 转换为秒
            }
        })


class ExamResultViewSet(ModelViewSet):
    """考试成绩管理视图集"""
    
    queryset = ExamResult.objects.select_related(
        'exam', 'user'
    )
    serializer_class = ExamResultSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam', 'user', 'status', 'is_passed']
    search_fields = ['user__real_name', 'user__employee_id', 'exam__title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据权限过滤查询集"""
        user = self.request.user
        
        # 管理员和考试管理员可以查看所有成绩
        if user.role.code in ['admin', 'hr_manager', 'exam_manager']:
            return self.queryset
        
        # 讲师可以查看相关考试成绩
        if user.role.code == 'instructor':
            return self.queryset.filter(
                Q(exam__course__created_by=user) | Q(exam__created_by=user)
            )
        
        # 部门经理可以查看本部门成绩
        if user.role.code == 'dept_manager':
            return self.queryset.filter(
                Q(user__department=user.department) | Q(user=user)
            )
        
        # 普通用户只能查看自己的成绩
        return self.queryset.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def generate_certificate(self, request, pk=None):
        """生成证书"""
        result = self.get_object()
        
        if not result.is_passed:
            return Response({
                'code': 400,
                'message': '考试未通过，无法生成证书'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 生成证书编号
        certificate_no = result.generate_certificate_no()
        
        return Response({
            'code': 200,
            'message': '证书生成成功',
            'data': {
                'certificate_no': certificate_no
            }
        })