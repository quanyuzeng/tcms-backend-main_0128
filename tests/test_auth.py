"""Authentication tests"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.users.models import Role


class AuthTests(TestCase):
    """认证测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        
        # 创建角色
        self.admin_role = Role.objects.create(
            name='系统管理员',
            code='admin',
            permissions={'permissions': ['*']}
        )
        
        # 创建用户
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123',
            real_name='测试用户',
            employee_id='EMP001',
            email='test@example.com',
            role=self.admin_role
        )
    
    def test_login_success(self):
        """测试登录成功"""
        url = reverse('auth-login')
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'remember': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertIn('user', response.data['data'])
    
    def test_login_failure(self):
        """测试登录失败"""
        url = reverse('auth-login')
        data = {
            'username': 'testuser',
            'password': 'wrongpass',
            'remember': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_profile(self):
        """测试获取用户信息"""
        # 先登录获取token
        self.client.force_authenticate(user=self.user)
        
        url = reverse('auth-profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['real_name'], '测试用户')
    
    def test_password_change(self):
        """测试修改密码"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('auth-password-change')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证密码已更改
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
    
    def test_logout(self):
        """测试登出"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('auth-logout')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)