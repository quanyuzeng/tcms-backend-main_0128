"""User management tests"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.users.models import Role


class UserManagementTests(TestCase):
    """用户管理测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        
        # 创建角色
        self.admin_role = Role.objects.create(
            name='系统管理员',
            code='admin',
            permissions={'permissions': ['*']}
        )
        
        self.employee_role = Role.objects.create(
            name='普通员工',
            code='employee',
            permissions={'permissions': ['profile:*', 'course:read', 'exam:take']}
        )
        
        # 创建管理员用户
        self.admin_user = get_user_model().objects.create_user(
            username='admin',
            password='admin123',
            real_name='管理员',
            employee_id='ADMIN001',
            email='admin@example.com',
            role=self.admin_role
        )
        
        # 创建普通用户
        self.employee_user = get_user_model().objects.create_user(
            username='employee',
            password='emp123',
            real_name='员工',
            employee_id='EMP001',
            email='emp@example.com',
            role=self.employee_role
        )
    
    def test_list_users_as_admin(self):
        """管理员查看用户列表"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 2)
    
    def test_list_users_as_employee(self):
        """普通用户查看用户列表"""
        self.client.force_authenticate(user=self.employee_user)
        
        url = reverse('user-list')
        response = self.client.get(url)
        
        # 普通用户只能查看自己
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
    
    def test_create_user(self):
        """创建用户"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'real_name': '新用户',
            'employee_id': 'EMP002',
            'email': 'new@example.com',
            'role': self.employee_role.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['username'], 'newuser')
    
    def test_update_user(self):
        """更新用户"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('user-detail', kwargs={'pk': self.employee_user.id})
        data = {
            'real_name': '更新后的员工',
            'email': 'updated@example.com'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['real_name'], '更新后的员工')
    
    def test_delete_user(self):
        """删除用户"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('user-detail', kwargs={'pk': self.employee_user.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_reset_password(self):
        """重置密码"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('user-reset-password', kwargs={'pk': self.employee_user.id})
        data = {
            'new_password': 'resetpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证密码已更改
        self.employee_user.refresh_from_db()
        self.assertTrue(self.employee_user.check_password('resetpass123'))