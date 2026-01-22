"""Training tests"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.users.models import Role
from apps.organization.models import Department, Position
from apps.training.models import CourseCategory, Course, TrainingPlan, TrainingRecord


class TrainingTests(TestCase):
    """培训管理测试"""
    
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
        
        # 创建部门
        self.department = Department.objects.create(
            name='技术部',
            code='TECH',
            status='active'
        )
        
        # 创建岗位
        self.position = Position.objects.create(
            name='软件工程师',
            code='SE',
            level='mid',
            status='active'
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
            role=self.employee_role,
            department=self.department,
            position=self.position
        )
        
        # 创建课程分类
        self.category = CourseCategory.objects.create(
            name='技术培训',
            code='TECH',
            description='技术相关培训'
        )
        
        # 创建课程
        self.course = Course.objects.create(
            code='COURSE001',
            title='Python基础培训',
            description='Python编程基础',
            category=self.category,
            course_type='online',
            duration=120,
            credit=2.0,
            passing_score=60.00,
            instructor='张老师',
            status='published',
            created_by=self.admin_user
        )
    
    def test_list_courses(self):
        """查看课程列表"""
        self.client.force_authenticate(user=self.employee_user)
        
        url = reverse('course-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['title'], 'Python基础培训')
    
    def test_create_course(self):
        """创建课程"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('course-list')
        data = {
            'code': 'COURSE002',
            'title': 'Django培训',
            'description': 'Django框架培训',
            'category': self.category.id,
            'course_type': 'online',
            'duration': 180,
            'credit': 3.0,
            'passing_score': 60.00,
            'instructor': '李老师',
            'status': 'draft'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['title'], 'Django培训')
    
    def test_publish_course(self):
        """发布课程"""
        self.client.force_authenticate(user=self.admin_user)
        
        # 创建草稿课程
        draft_course = Course.objects.create(
            code='COURSE003',
            title='草稿课程',
            description='草稿课程',
            category=self.category,
            course_type='online',
            duration=60,
            credit=1.0,
            passing_score=60.00,
            status='draft',
            created_by=self.admin_user
        )
        
        url = reverse('course-publish', kwargs={'pk': draft_course.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'published')
    
    def test_enroll_course(self):
        """报名课程"""
        self.client.force_authenticate(user=self.employee_user)
        
        url = reverse('course-enroll', kwargs={'pk': self.course.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['user'], self.employee_user.id)
        self.assertEqual(response.data['data']['course'], self.course.id)
    
    def test_create_training_plan(self):
        """创建培训计划"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('trainingplan-list')
        data = {
            'code': 'PLAN001',
            'title': '新员工培训计划',
            'description': '新员工入职培训',
            'plan_type': 'department',
            'target_department': self.department.id,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=30),
            'course_ids': [self.course.id],
            'status': 'draft'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['title'], '新员工培训计划')
    
    def test_approve_training_plan(self):
        """审批培训计划"""
        self.client.force_authenticate(user=self.admin_user)
        
        # 创建待审批的培训计划
        plan = TrainingPlan.objects.create(
            code='PLAN002',
            title='待审批计划',
            description='待审批计划',
            plan_type='department',
            target_department=self.department,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            status='pending',
            created_by=self.admin_user
        )
        plan.courses.add(self.course)
        
        url = reverse('trainingplan-approve', kwargs={'pk': plan.id})
        data = {
            'approved': True,
            'comment': '审批通过'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'approved')
    
    def test_training_statistics(self):
        """培训统计"""
        self.client.force_authenticate(user=self.admin_user)
        
        # 创建培训记录
        TrainingRecord.objects.create(
            user=self.employee_user,
            course=self.course,
            status='completed',
            progress=100,
            score=85.00,
            complete_date=timezone.now()
        )
        
        url = reverse('trainingrecord-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['total_courses'], 1)
        self.assertEqual(response.data['data']['completion_rate'], 100)