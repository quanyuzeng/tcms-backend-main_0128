"""User serializers"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Role


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'permissions', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_code = serializers.CharField(source='role.code', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'real_name', 'employee_id', 'email', 'phone',
            'department', 'department_name', 'position', 'position_name',
            'role', 'role_name', 'role_code', 'avatar', 'avatar_url',
            'status', 'last_login', 'last_login_ip', 'created_at', 'permissions'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'avatar': {'write_only': True},
        }
    
    def get_avatar_url(self, obj):
        """获取头像URL"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def get_permissions(self, obj):
        """获取用户权限列表"""
        return obj.permissions_list if hasattr(obj, 'permissions_list') else []
    
    def create(self, validated_data):
        """创建用户"""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        """更新用户"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """创建用户序列化器"""
    
    class Meta:
        model = User
        fields = [
            'username', 'password', 'real_name', 'employee_id', 'email',
            'phone', 'department', 'position', 'role'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': True},
            'real_name': {'required': True},
            'employee_id': {'required': True},
            'email': {'required': True},
        }
    
    def create(self, validated_data):
        """创建用户"""
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """更新用户序列化器（用于部分更新，限制不可修改字段）"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_code = serializers.CharField(source='role.code', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'real_name', 'employee_id', 'email', 'phone',
            'department', 'department_name', 'position', 'position_name',
            'role', 'role_name', 'role_code', 'avatar', 'avatar_url',
            'status', 'last_login', 'last_login_ip', 'created_at'
        ]
        read_only_fields = [
            'id', 'username', 'employee_id', 'created_at', 
            'last_login', 'last_login_ip'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'avatar': {'write_only': True},
        }
    
    def get_avatar_url(self, obj):
        """获取头像URL"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def update(self, instance, validated_data):
        """更新用户（允许更新密码）"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    remember = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """验证登录信息"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.status == 'active':
                    attrs['user'] = user
                    return attrs
                else:
                    raise serializers.ValidationError('用户已被禁用')
            else:
                raise serializers.ValidationError('用户名或密码错误')
        
        raise serializers.ValidationError('必须提供用户名和密码')


class PasswordChangeSerializer(serializers.Serializer):
    """修改密码序列化器"""
    
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    
    def validate_old_password(self, value):
        """验证旧密码"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('旧密码不正确')
        return value
    
    def save(self):
        """保存新密码"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    """管理员重置用户密码序列化器"""
    
    user_id = serializers.IntegerField(required=True, label="用户ID")
    new_password = serializers.CharField(
        required=True, 
        write_only=True, 
        min_length=8,
        label="新密码"
    )
    
    def validate_user_id(self, value):
        """验证用户是否存在且有效"""
        try:
            user = User.objects.get(id=value)
            # 禁止重置自己的密码
            request = self.context.get('request')
            if request and request.user == user:
                raise serializers.ValidationError('不能重置自己的密码')
            # 禁止重置管理员密码
            if user.is_superuser:
                raise serializers.ValidationError('不能重置超级管理员密码')
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('用户不存在')
    
    def save(self):
        """重置密码"""
        user = User.objects.get(id=self.validated_data['user_id'])
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user