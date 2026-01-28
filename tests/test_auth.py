#!/usr/bin/env python
"""test_auth_fixed.py - 认证测试（无需修改，原文件正常）"""
from django.test import TestCase
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
        url = '/api/auth/login/'
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'remember': False
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 检查响应数据结构
        self.assertIn('data', response.data)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
    
    def test_login_failure(self):
        """测试登录失败"""
        url = '/api/auth/login/'
        data = {
            'username': 'testuser',
            'password': 'wrongpass',
            'remember': False
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_profile(self):
        """测试获取用户信息"""
        self.client.force_authenticate(user=self.user)
        
        url = '/api/auth/profile/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['username'], 'testuser')
    
    def test_password_change(self):
        """测试修改密码"""
        self.client.force_authenticate(user=self.user)
        
        url = '/api/auth/password/change/'
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
        
        url = '/api/auth/logout/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)