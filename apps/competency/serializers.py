"""Competency serializers"""
from rest_framework import serializers
from .models import Competency, CompetencyAssessment, Certificate
from apps.users.serializers import UserSerializer
from apps.organization.serializers import PositionSerializer


class CompetencySerializer(serializers.ModelSerializer):
    """能力序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.real_name', read_only=True)
    related_positions = PositionSerializer(many=True, read_only=True)
    related_courses = serializers.SerializerMethodField()
    
    class Meta:
        model = Competency
        fields = [
            'id', 'name', 'code', 'description', 'category', 'level',
            'assessment_method', 'required', 'passing_score', 'parent',
            'related_positions', 'related_courses', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_related_courses(self, obj):
        """获取关联课程"""
        from apps.training.serializers import CourseSerializer
        return CourseSerializer(obj.related_courses.all(), many=True).data


class CompetencyTreeSerializer(serializers.ModelSerializer):
    """能力树序列化器"""
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Competency
        fields = ['id', 'name', 'code', 'description', 'level', 'children']
    
    def get_children(self, obj):
        """获取子能力"""
        children = obj.children.all()
        return CompetencyTreeSerializer(children, many=True).data


class CompetencyAssessmentSerializer(serializers.ModelSerializer):
    """能力评估序列化器"""
    
    user_name = serializers.CharField(source='user.real_name', read_only=True)
    competency_name = serializers.CharField(source='competency.name', read_only=True)
    assessor_name = serializers.CharField(source='assessor.real_name', read_only=True)
    
    class Meta:
        model = CompetencyAssessment
        fields = [
            'id', 'user', 'user_name', 'competency', 'competency_name',
            'assessor', 'assessor_name', 'level', 'score', 'status',
            'evidence', 'assessor_comment', 'assessed_at', 'expires_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'assessor', 'assessed_at']


class CertificateSerializer(serializers.ModelSerializer):
    """证书序列化器"""
    
    user_name = serializers.CharField(source='user.real_name', read_only=True)
    competency_name = serializers.CharField(source='competency.name', read_only=True)
    issued_by_name = serializers.CharField(source='issued_by.real_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'name', 'certificate_no', 'user', 'user_name',
            'competency', 'competency_name', 'issue_date', 'expiry_date',
            'verification_code', 'status', 'status_display', 'is_expired',
            'issued_by', 'issued_by_name', 'certificate_file',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'certificate_no', 'verification_code', 'created_at', 'updated_at', 'issued_by']


class CertificateVerifySerializer(serializers.Serializer):
    """证书验证序列化器"""
    
    verification_code = serializers.CharField(required=True)


class CertificateGenerateSerializer(serializers.Serializer):
    """证书生成序列化器"""
    
    exam_result_id = serializers.IntegerField(required=False)
    assessment_id = serializers.IntegerField(required=False)
    expiry_date = serializers.DateField(required=False)
    
    def validate(self, attrs):
        """验证数据"""
        exam_result_id = attrs.get('exam_result_id')
        assessment_id = attrs.get('assessment_id')
        
        if not exam_result_id and not assessment_id:
            raise serializers.ValidationError('必须提供考试成绩ID或评估ID')
        
        return attrs