"""Reporting serializers"""
from rest_framework import serializers
from .models import ReportTemplate, GeneratedReport


class ReportTemplateSerializer(serializers.ModelSerializer):
    """报表模板序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.real_name', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'code', 'report_type', 'report_type_display',
            'description', 'config', 'is_active', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GeneratedReportSerializer(serializers.ModelSerializer):
    """生成的报表序列化器"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.real_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_format_display = serializers.CharField(source='get_file_format_display', read_only=True)
    
    class Meta:
        model = GeneratedReport
        fields = [
            'id', 'template', 'template_name', 'title', 'file_format',
            'file_format_display', 'file_path', 'file_size', 'parameters',
            'status', 'status_display', 'error_message', 'generated_by',
            'generated_by_name', 'generated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'generated_at', 'completed_at']


class ReportExportSerializer(serializers.Serializer):
    """报表导出序列化器"""
    
    report_type = serializers.ChoiceField(
        choices=[
            ('training_statistics', '培训统计'),
            ('exam_analysis', '考试分析'),
            ('competency_matrix', '能力矩阵'),
            ('compliance_report', '合规性报表'),
        ],
        required=True
    )
    format = serializers.ChoiceField(
        choices=['excel', 'pdf', 'csv'],
        default='excel'
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    department_id = serializers.IntegerField(required=False)
    user_id = serializers.IntegerField(required=False)
    
    def validate(self, attrs):
        """验证数据"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError('开始日期不能晚于结束日期')
        
        return attrs


class TrainingStatisticsSerializer(serializers.Serializer):
    """培训统计序列化器"""
    
    total_courses = serializers.IntegerField()
    total_trainees = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_score = serializers.FloatField()
    department_stats = serializers.ListField()
    
    # 额外统计
    total_training_hours = serializers.IntegerField()
    total_certificates = serializers.IntegerField()
    top_courses = serializers.ListField()
    monthly_stats = serializers.ListField()


class ExamAnalysisSerializer(serializers.Serializer):
    """考试分析序列化器"""
    
    total_exams = serializers.IntegerField()
    total_participants = serializers.IntegerField()
    avg_score = serializers.FloatField()
    pass_rate = serializers.FloatField()
    exam_stats = serializers.ListField()
    score_distribution = serializers.ListField()


class CompetencyMatrixSerializer(serializers.Serializer):
    """能力矩阵序列化器"""
    
    users = serializers.ListField()
    competencies = serializers.ListField()
    matrix = serializers.ListField()


class ComplianceReportSerializer(serializers.Serializer):
    """合规性报表序列化器"""
    
    total_employees = serializers.IntegerField()
    compliant_employees = serializers.IntegerField()
    compliance_rate = serializers.FloatField()
    non_compliant_users = serializers.ListField()
    expired_certificates = serializers.ListField()