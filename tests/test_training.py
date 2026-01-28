#!/usr/bin/env python
"""培训管理测试（修复权限和数据问题）"""
from django.test import TestCase
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
        """测试准备：创建与业务代码匹配的角色和数据"""
        self.client = APIClient()
        
        # 创建业务代码中实际使用的角色
        self.admin_role = Role.objects.create(
            name='系统管理员',
            code='admin',
            permissions={'all': True}
        )
        
        # 培训经理拥有全部权限
        self.training_role = Role.objects.create(
            name='培训经理',
            code='training_manager',
            permissions={'training': {'create': True, 'approve': True, 'read': True, 'write': True}}
        )
        
        self.employee_role = Role.objects.create(
            name='ME工程师',
            code='me_engineer',
            permissions={'training': {'read': True, 'enroll': True}}
        )
        
        # 创建部门
        self.department = Department.objects.create(
            name='技术部',
            code='TECH',
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
        
        # 创建培训管理员
        self.training_user = get_user_model().objects.create_user(
            username='training_manager',
            password='training123',
            real_name='培训经理',
            employee_id='TR001',
            email='training@example.com',
            role=self.training_role
        )
        
        # 创建普通用户
        self.employee_user = get_user_model().objects.create_user(
            username='employee',
            password='emp123',
            real_name='员工',
            employee_id='EMP001',
            email='emp@example.com',
            role=self.employee_role,
            department=self.department
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
            title='Python基础培训',  # 修正：使用 title= 而不是 'title':
            description='Python编程基础',
            category=self.category,
            course_type='online',
            duration=120,
            credit=2.0,
            passing_score=60.00,
            instructor='张老师',
            status='published',
            created_by=self.training_user
        )
    
    def test_list_courses(self):
        """查看课程列表"""
        self.client.force_authenticate(user=self.employee_user)
        
        url = '/api/training/courses/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_course(self):
        """创建课程 - 确保created_by自动赋值"""
        self.client.force_authenticate(user=self.training_user)
        
        url = '/api/training/courses/'
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
        
        # 验证created_by已自动设置
        course = Course.objects.get(code='COURSE002')
        self.assertEqual(course.created_by, self.training_user)
    
    def test_publish_course(self):
        """发布课程"""
        self.client.force_authenticate(user=self.training_user)
        
        # 创建草稿课程
        draft_course = Course.objects.create(
            code='COURSE003',
            title='草稿课程',  # 修正：使用 title=
            description='草稿课程',
            category=self.category,
            course_type='online',
            duration=60,
            credit=1.0,
            passing_score=60.00,
            status='draft',
            created_by=self.training_user
        )
        
        url = f'/api/training/courses/{draft_course.id}/publish/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证状态已更新
        draft_course.refresh_from_db()
        self.assertEqual(draft_course.status, 'published')
    
    def test_enroll_course(self):
        """报名课程"""
        self.client.force_authenticate(user=self.employee_user)
        
        url = f'/api/training/courses/{self.course.id}/enroll/'
        response = self.client.post(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        
        # 验证已创建记录
        self.assertTrue(TrainingRecord.objects.filter(user=self.employee_user, course=self.course).exists())
    
    def test_create_training_plan(self):
        """创建培训计划 - 确保created_by自动赋值"""
        self.client.force_authenticate(user=self.training_user)
        
        url = '/api/training/plans/'
        data = {
            'code': 'PLAN001',
            'title': '新员工培训计划',
            'description': '新员工入职培训',
            'plan_type': 'department',
            'target_department': self.department.id,
            'start_date': timezone.now().date().isoformat(),
            'end_date': (timezone.now().date() + timedelta(days=30)).isoformat(),
            'status': 'draft'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证created_by已自动设置
        plan = TrainingPlan.objects.get(code='PLAN001')
        self.assertEqual(plan.created_by, self.training_user)
    
    def test_approve_training_plan(self):
        """审批培训计划 - 培训经理有审批权限"""
        self.client.force_authenticate(user=self.training_user)
        
        # 创建待审批的培训计划
        plan = TrainingPlan.objects.create(
            code='PLAN002',
            title='待审批计划',  # 修正：使用 title=
            description='待审批计划',
            plan_type='department',
            target_department=self.department,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            status='pending',
            created_by=self.training_user
        )
        plan.courses.add(self.course)
        
        url = f'/api/training/plans/{plan.id}/approve/'
        data = {
            'approved': True,
            'comment': '审批通过'
        }
        
        response = self.client.post(url, data, format='json')
        # 培训经理有审批权限，应返回200
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证状态已更新
        plan.refresh_from_db()
        self.assertEqual(plan.status, 'approved')
    
    def test_training_statistics(self):
        """培训统计"""
        self.client.force_authenticate(user=self.training_user)
        
        # 创建培训记录
        TrainingRecord.objects.create(
            user=self.employee_user,
            course=self.course,
            status='completed',
            progress=100,
            score=85.00,
            complete_date=timezone.now()
        )
        
        url = '/api/training/records/statistics/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证数据结构
        self.assertIn('total_courses', response.data['data'])
        self.assertIn('completion_rate', response.data['data'])