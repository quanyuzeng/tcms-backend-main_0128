"""Examination serializers"""
from rest_framework import serializers
from .models import QuestionBank, Question, Exam, ExamResult
from apps.training.serializers import CourseSerializer
from apps.users.serializers import UserSerializer


class QuestionBankSerializer(serializers.ModelSerializer):
    """题库序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.real_name', read_only=True)
    
    class Meta:
        model = QuestionBank
        fields = [
            'id', 'name', 'code', 'category', 'description',
            'question_count', 'total_score', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class QuestionSerializer(serializers.ModelSerializer):
    """题目序列化器"""
    
    question_bank_name = serializers.CharField(source='question_bank.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.real_name', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'question_bank', 'question_bank_name', 'question_type',
            'difficulty', 'title', 'content', 'options', 'correct_answer',
            'explanation', 'score', 'sort_order', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class QuestionImportSerializer(serializers.Serializer):
    """题目导入序列化器"""
    
    question_bank_id = serializers.IntegerField(required=True)
    file = serializers.FileField(required=True)


class ExamSerializer(serializers.ModelSerializer):
    """考试序列化器"""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    question_bank_name = serializers.CharField(source='question_bank.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.real_name', read_only=True)
    participant_count = serializers.ReadOnlyField()
    result_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Exam
        fields = [
            'id', 'code', 'title', 'exam_type', 'course', 'course_title',
            'question_bank', 'question_bank_name', 'total_questions',
            'total_score', 'passing_score', 'time_limit', 'start_time',
            'end_time', 'max_attempts', 'show_result', 'show_answer',
            'random_order', 'shuffle_options', 'description', 'instructions',
            'status', 'participants', 'participant_count', 'result_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'published_at', 'created_by']
    
    def validate(self, attrs):
        """验证数据"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError('结束时间必须晚于开始时间')
        
        return attrs


class ExamDetailSerializer(ExamSerializer):
    """考试详情序列化器"""
    
    course_detail = CourseSerializer(source='course', read_only=True)
    question_bank_detail = QuestionBankSerializer(source='question_bank', read_only=True)
    participants_detail = UserSerializer(source='participants', many=True, read_only=True)
    
    class Meta(ExamSerializer.Meta):
        fields = ExamSerializer.Meta.fields + [
            'course_detail', 'question_bank_detail', 'participants_detail'
        ]


class ExamResultSerializer(serializers.ModelSerializer):
    """考试成绩序列化器"""
    
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    exam_code = serializers.CharField(source='exam.code', read_only=True)
    user_name = serializers.CharField(source='user.real_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    department_name = serializers.CharField(source='user.department.name', read_only=True)
    
    class Meta:
        model = ExamResult
        fields = [
            'id', 'exam', 'exam_title', 'exam_code', 'user', 'user_name',
            'user_username', 'department_name', 'status', 'score',
            'correct_count', 'wrong_count', 'is_passed', 'duration',
            'start_time', 'submitted_at', 'answers', 'review_comment',
            'certificate_no', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExamResultListSerializer(ExamResultSerializer):
    """考试成绩列表序列化器"""
    
    class Meta(ExamResultSerializer.Meta):
        fields = [
            'id', 'exam_title', 'user_name', 'department_name',
            'score', 'is_passed', 'duration', 'submitted_at'
        ]


class ExamSubmitSerializer(serializers.Serializer):
    """考试提交序列化器"""
    
    answers = serializers.JSONField(required=True)
    duration = serializers.IntegerField(required=True, min_value=0)
    
    def validate_answers(self, value):
        """验证答案格式"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('答案必须是字典格式')
        return value


class ParticipantManageSerializer(serializers.Serializer):
    """参与人员管理序列化器"""
    
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    action = serializers.ChoiceField(
        choices=['add', 'remove'],
        required=True
    )