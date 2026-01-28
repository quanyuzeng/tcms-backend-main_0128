"""Training serializers"""
from rest_framework import serializers
from .models import CourseCategory, Course, TrainingPlan, TrainingRecord
from apps.organization.serializers import DepartmentSerializer, PositionSerializer
from apps.users.serializers import UserSerializer


class CourseCategorySerializer(serializers.ModelSerializer):
    """课程分类序列化器"""
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'code', 'parent', 'description', 'sort_order', 'children']
        read_only_fields = ['id']
    
    def get_children(self, obj):
        """获取子分类"""
        children = obj.children.all()
        return CourseCategorySerializer(children, many=True).data


class CourseSerializer(serializers.ModelSerializer):
    """课程序列化器"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.real_name', read_only=True)
    completion_rate = serializers.ReadOnlyField()
    prerequisites = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'code', 'title', 'description', 'category', 'category_name',
            'course_type', 'duration', 'credit', 'passing_score', 'instructor',
            'thumbnail', 'content_url', 'prerequisites', 'tags', 'status',
            'view_count', 'enrollment_count', 'completion_count', 'completion_rate',
            'created_by', 'created_by_name', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'published_at', 'created_by']


class CourseDetailSerializer(CourseSerializer):
    """课程详情序列化器"""
    
    prerequisites_detail = CourseSerializer(source='prerequisites', many=True, read_only=True)
    
    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ['prerequisites_detail']


class TrainingPlanSerializer(serializers.ModelSerializer):
    """培训计划序列化器"""
    
    target_department_name = serializers.CharField(source='target_department.name', read_only=True)
    target_position_name = serializers.CharField(source='target_position.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.real_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.real_name', read_only=True)
    courses = CourseSerializer(many=True, read_only=True)
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = TrainingPlan
        fields = [
            'id', 'code', 'title', 'description', 'plan_type',
            'target_department', 'target_department_name',
            'target_position', 'target_position_name',
            'target_users', 'courses', 'course_ids',
            'start_date', 'end_date', 'total_hours', 'total_courses',
            'status', 'approved_by', 'approved_by_name', 'approved_at',
            'approval_comment', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'approved_by', 'approved_at']
    
    def create(self, validated_data):
        """创建培训计划"""
        course_ids = validated_data.pop('course_ids', [])
        target_users = validated_data.pop('target_users', [])
        
        # created_by 由视图的 perform_create 设置，这里不处理
        plan = TrainingPlan.objects.create(**validated_data)
        
        # 关联课程
        if course_ids:
            from apps.training.models import Course
            courses = Course.objects.filter(id__in=course_ids)
            plan.courses.set(courses)
            plan.total_hours = sum(course.duration for course in courses)
            plan.total_courses = len(courses)
            plan.save()
        
        # 关联用户
        if target_users:
            plan.target_users.set(target_users)
        
        return plan
    
    def update(self, instance, validated_data):
        """更新培训计划"""
        course_ids = validated_data.pop('course_ids', None)
        target_users = validated_data.pop('target_users', None)
        
        # 更新基本字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 更新课程关联
        if course_ids is not None:
            from apps.training.models import Course
            courses = Course.objects.filter(id__in=course_ids)
            instance.courses.set(courses)
            instance.total_hours = sum(course.duration for course in courses)
            instance.total_courses = len(courses)
            instance.save()
        
        # 更新用户关联
        if target_users is not None:
            instance.target_users.set(target_users)
        
        return instance


class TrainingRecordSerializer(serializers.ModelSerializer):
    """培训记录序列化器"""
    
    user_name = serializers.CharField(source='user.real_name', read_only=True)
    plan_title = serializers.CharField(source='plan.title', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    
    class Meta:
        model = TrainingRecord
        fields = [
            'id', 'user', 'user_name', 'plan', 'plan_title',
            'course', 'course_title', 'course_code', 'status',
            'progress', 'study_duration', 'complete_date', 'score',
            'feedback', 'evaluation', 'certificate_no',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TrainingRecordCreateSerializer(serializers.ModelSerializer):
    """创建培训记录序列化器"""
    
    class Meta:
        model = TrainingRecord
        fields = ['user', 'plan', 'course', 'status', 'progress', 'study_duration']


class TrainingStatisticsSerializer(serializers.Serializer):
    """培训统计序列化器"""
    
    total_courses = serializers.IntegerField()
    total_trainees = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_score = serializers.FloatField()
    department_stats = serializers.ListField()


class CourseEvaluationSerializer(serializers.Serializer):
    """课程评价序列化器"""
    
    record_id = serializers.IntegerField(required=True)
    evaluation = serializers.CharField(required=True)
    feedback = serializers.CharField(required=False, allow_blank=True)