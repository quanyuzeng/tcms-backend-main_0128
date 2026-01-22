"""Authentication views"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.utils import timezone

from ..models import User
from ..serializers import (
    LoginSerializer, PasswordChangeSerializer, 
    PasswordResetSerializer, UserSerializer
)
from ..permissions import IsAdminOrHR


@api_view(['POST'])
@permission_classes([])
def login_view(request):
    """用户登录"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # 更新最后登录信息
        user.last_login = timezone.now()
        user.last_login_ip = request.META.get('REMOTE_ADDR')
        user.save()
        
        # 生成JWT token
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'code': 200,
            'message': '登录成功',
            'data': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user, context={'request': request}).data
            }
        })
    
    return Response({
        'code': 400,
        'message': '登录失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """用户登出"""
    try:
        # 将refresh token加入黑名单
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except:
        pass
    
    logout(request)
    
    return Response({
        'code': 200,
        'message': '登出成功',
        'data': {}
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """获取当前用户信息"""
    user = request.user
    serializer = UserSerializer(user, context={'request': request})
    
    return Response({
        'code': 200,
        'message': 'Success',
        'data': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def password_change_view(request):
    """修改密码"""
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({
            'code': 200,
            'message': '密码修改成功',
            'data': {}
        })
    
    return Response({
        'code': 400,
        'message': '密码修改失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminOrHR])
def password_reset_view(request):
    """重置用户密码（管理员）"""
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'code': 200,
            'message': '密码重置成功',
            'data': {}
        })
    
    return Response({
        'code': 400,
        'message': '密码重置失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)