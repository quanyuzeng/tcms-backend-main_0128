#!/usr/bin/env python
"""能力管理测试（修复权限和数据问题）"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.users.models import Role
from apps.competency.models import Competency, CompetencyAssessment, Certificate


class CompetencyTests(TestCase):
    """能力管理测试"""
    
    def setUp(self):
        """测试准备：创建与业务代码匹配的角色和权限"""
        self.client = APIClient()
        
        # 创建业务代码中实际使用的角色
        self.admin_role = Role.objects.create(
            name='系统管理员',
            code='admin',
            permissions={'all': True}  # 简化权限结构
        )
        
        # ME工程师角色（有创建能力权限）
        self.training_role = Role.objects.create(
            name='培训经理',
            code='training_manager',
            permissions={'training': {'create': True}}
        )
        
        # 普通员工角色（只读权限）
        self.employee_role = Role.objects.create(
            name='普通员工',
            code='me_engineer',  # 使用业务代码中的实际角色code
            permissions={'competency': {'read': True}}
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
        
        # 创建有权限的用户
        self.trainer_user = get_user_model().objects.create_user(
            username='trainer',
            password='trainer123',
            real_name='培训经理',
            employee_id='TR001',
            email='trainer@example.com',
            role=self.training_role
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
        
        # 创建能力
        self.competency = Competency.objects.create(
            name='Python编程',
            code='PYTHON',
            description='Python编程能力',
            category='技术',
            level='proficient',
            assessment_method='exam',
            required=True,
            created_by=self.admin_user
        )
    
    def test_list_competencies(self):
        """查看能力列表"""
        self.client.force_authenticate(user=self.employee_user)
        
        url = '/api/competency/competencies/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_competency(self):
        """创建能力 - 确保created_by自动赋值"""
        self.client.force_authenticate(user=self.trainer_user)
        
        url = '/api/competency/competencies/'
        data = {
            'name': 'Django开发',
            'code': 'DJANGO',
            'description': 'Django框架开发能力',
            'category': '技术',
            'level': 'proficient',
            'assessment_method': 'exam',
            'required': True
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证created_by已自动设置
        competency = Competency.objects.get(code='DJANGO')
        self.assertEqual(competency.created_by, self.trainer_user)
    
    def test_create_competency_assessment(self):
        """创建能力评估"""
        self.client.force_authenticate(user=self.trainer_user)
        
        url = '/api/competency/assessments/'
        data = {
            'user': self.employee_user.id,
            'competency': self.competency.id,
            'assessor': self.trainer_user.id,
            'level': 'proficient',
            'score': 85.00,
            'status': 'completed',
            'evidence': '完成了Python项目',
            'assessor_comment': '表现优秀'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_approve_competency_assessment(self):
        """审批能力评估"""
        # 创建能力评估
        assessment = CompetencyAssessment.objects.create(
            user=self.employee_user,
            competency=self.competency,
            assessor=self.trainer_user,
            level='proficient',
            score=85.00,
            status='completed',
            evidence='完成了Python项目',
            assessed_at=timezone.now()
        )
        
        self.client.force_authenticate(user=self.trainer_user)
        
        url = f'/api/competency/assessments/{assessment.id}/approve/'
        data = {'approved': True}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_generate_certificate(self):
        """生成证书"""
        self.client.force_authenticate(user=self.trainer_user)
        
        # 先创建评估
        assessment = CompetencyAssessment.objects.create(
            user=self.employee_user,
            competency=self.competency,
            assessor=self.trainer_user,
            level='proficient',
            score=85.00,
            status='approved',
            evidence='完成了Python项目',
            assessed_at=timezone.now()
        )
        
        url = '/api/competency/certificates/generate/'
        data = {
            'assessment_id': assessment.id,
            'expiry_date': (timezone.now() + timedelta(days=365)).date().isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_verify_certificate(self):
        """验证证书 - 修复：添加认证"""
        # 创建证书
        certificate = Certificate.objects.create(
            name='Python编程证书',
            user=self.employee_user,
            competency=self.competency,
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            issued_by=self.trainer_user,
            verification_code='TEST123456'
        )
        
        # 必须认证用户
        self.client.force_authenticate(user=self.employee_user)
        
        url = '/api/competency/certificates/verify/'
        data = {'verification_code': certificate.verification_code}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_revoke_certificate(self):
        """吊销证书"""
        # 创建证书
        certificate = Certificate.objects.create(
            name='Python编程证书',
            user=self.employee_user,
            competency=self.competency,
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            issued_by=self.trainer_user,
            verification_code='TEST789012'
        )
        
        self.client.force_authenticate(user=self.trainer_user)
        
        url = f'/api/competency/certificates/{certificate.id}/revoke/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)