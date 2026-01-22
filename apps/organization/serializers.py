"""Organization serializers"""
from rest_framework import serializers
from .models import Department, Position


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化器"""
    
    manager_name = serializers.CharField(source='manager.real_name', read_only=True)
    employee_count = serializers.ReadOnlyField()
    level = serializers.ReadOnlyField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'parent', 'manager', 'manager_name',
            'description', 'status', 'employee_count', 'level',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DepartmentTreeSerializer(serializers.ModelSerializer):
    """部门树形结构序列化器"""
    
    children = serializers.SerializerMethodField()
    manager_name = serializers.CharField(source='manager.real_name', read_only=True)
    employee_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'manager', 'manager_name',
            'description', 'status', 'employee_count', 'children'
        ]
    
    def get_children(self, obj):
        """获取子部门"""
        children = obj.children.filter(status='active')
        return DepartmentTreeSerializer(children, many=True).data


class PositionSerializer(serializers.ModelSerializer):
    """岗位序列化器"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    employee_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Position
        fields = [
            'id', 'name', 'code', 'level', 'department', 'department_name',
            'responsibilities', 'requirements', 'required_training_hours',
            'min_experience', 'min_education', 'status', 'employee_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PositionDetailSerializer(PositionSerializer):
    """岗位详情序列化器"""
    
    # 使用SerializerMethodField避免循环导入
    users = serializers.SerializerMethodField()
    
    class Meta(PositionSerializer.Meta):
        fields = PositionSerializer.Meta.fields + ['users']
    
    def get_users(self, obj):
        """获取岗位用户列表"""
        from apps.users.serializers import UserSerializer
        users = obj.users.all()[:10]  # 限制数量
        return UserSerializer(users, many=True).data