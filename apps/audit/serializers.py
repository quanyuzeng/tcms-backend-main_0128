"""Audit serializers"""
from rest_framework import serializers
from .models import AuditLog
from apps.users.serializers import UserSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    """审计日志序列化器"""
    
    operator_detail = UserSerializer(source='operator', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'operator', 'operator_detail', 'operator_name', 'operator_username',
            'action', 'action_display', 'module', 'object_type', 'object_id',
            'object_name', 'description', 'ip_address', 'user_agent',
            'request_method', 'request_path', 'request_params',
            'response_result', 'status', 'status_display', 'error_message',
            'response_time', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AuditLogSummarySerializer(serializers.Serializer):
    """审计日志汇总序列化器"""
    
    total_logs = serializers.IntegerField()
    success_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    top_modules = serializers.ListField()
    top_actions = serializers.ListField()
    recent_logs = serializers.ListField()