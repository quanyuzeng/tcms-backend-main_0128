"""Competency tests"""
from django.test import TestCase
from django.urls import reverse
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
        
        url = reverse('competency-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['name'], 'Python编程')
    
    def test_create_competency(self):
        """创建能力"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('competency-list')
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
        self.assertEqual(response.data['data']['name'], 'Django开发')
    
    def test_create_competency_assessment(self):
        """创建能力评估"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('competencyassessment-list')
        data = {
            'user': self.employee_user.id,
            'competency': self.competency.id,
            'assessor': self.admin_user.id,
            'level': 'proficient',
            'score': 85.00,
            'status': 'completed',
            'evidence': '完成了Python项目',
            'assessor_comment': '表现优秀'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['score'], 85.00)
    
    def test_approve_competency_assessment(self):
        """审批能力评估"""
        # 创建能力评估
        assessment = CompetencyAssessment.objects.create(
            user=self.employee_user,
            competency=self.competency,
            assessor=self.admin_user,
            level='proficient',
            score=85.00,
            status='completed',
            evidence='完成了Python项目',
            assessed_at=timezone.now()
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('competencyassessment-approve', kwargs={'pk': assessment.id})
        data = {
            'approved': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'approved')
    
    def test_generate_certificate(self):
        """生成证书"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('certificate-generate')
        data = {
            'assessment_id': 1,
            'expiry_date': (timezone.now() + timedelta(days=365)).date().isoformat()
        }
        
        # 先创建评估
        assessment = CompetencyAssessment.objects.create(
            user=self.employee_user,
            competency=self.competency,
            assessor=self.admin_user,
            level='proficient',
            score=85.00,
            status='approved',
            evidence='完成了Python项目',
            assessed_at=timezone.now()
        )
        
        data['assessment_id'] = assessment.id
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('certificate_no', response.data['data'])
    
    def test_verify_certificate(self):
        """验证证书"""
        # 创建证书
        certificate = Certificate.objects.create(
            name='Python编程证书',
            user=self.employee_user,
            competency=self.competency,
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            issued_by=self.admin_user
        )
        
        url = reverse('certificate-verify')
        data = {
            'verification_code': certificate.verification_code
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['is_valid'])
    
    def test_revoke_certificate(self):
        """吊销证书"""
        # 创建证书
        certificate = Certificate.objects.create(
            name='Python编程证书',
            user=self.employee_user,
            competency=self.competency,
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            issued_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('certificate-revoke', kwargs={'pk': certificate.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'revoked')