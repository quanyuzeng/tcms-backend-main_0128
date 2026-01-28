#!/usr/bin/env python
"""角色权限测试（修复权限配置和工作流问题）"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.users.models import Role
from apps.organization.models import Department, Position
from apps.training.models import Course, CourseCategory, TrainingPlan, TrainingRecord
from apps.examination.models import QuestionBank, Question, Exam, ExamResult
from apps.competency.models import Competency, CompetencyAssessment, Certificate


class RoleBasedTests(TestCase):
    """基于角色的功能测试"""
    
    def setUp(self):
        """测试准备：创建所有业务代码中实际使用的角色"""
        self.client = APIClient()
        
        # 创建部门
        self.eng_dept = Department.objects.create(
            name='工程部',
            code='ENG',
            status='active'
        )
        
        self.prod_dept = Department.objects.create(
            name='生产部',
            code='PROD',
            status='active'
        )
        
        # 创建岗位
        self.me_position = Position.objects.create(
            name='ME工程师',
            code='ME',
            level='mid',
            status='active'
        )
        
        # 创建业务代码中实际使用的角色 - 根据权限矩阵配置
        self.roles = {}
        role_definitions = [
            ('admin', '系统管理员', ['*']),
            ('hr_manager', 'HR经理', ['user:*', 'training:*', 'exam:*', 'competency:*', 'report:*']),
            ('training_manager', '培训经理', ['training:*', 'course:*', 'plan:*', 'report:*']),
            ('exam_manager', '考试经理', ['exam:*', 'question:*', 'report:*']),
            ('engineering_manager', '工程经理', ['training:read', 'report:read', 'plan:approve']),
            ('dept_manager', '部门经理', ['training:read', 'plan:approve', 'record:read', 'report:read']),
            ('me_engineer', 'ME工程师', ['course:create', 'exam:create', 'training:enroll', 'record:read', 'report:read']),
            ('te_engineer', 'TE工程师', ['course:create', 'exam:create', 'training:enroll', 'record:read', 'report:read']),
            ('technician', '技术员', ['course:create', 'exam:create', 'training:enroll', 'report:read']),
            ('production_operator', '生产操作员', ['course:create', 'exam:create', 'training:enroll', 'report:read']),
        ]
        
        for code, name, perms in role_definitions:
            self.roles[code] = Role.objects.create(
                name=name,
                code=code,
                status='enabled',
                permissions={'permissions': perms} if perms != ['*'] else {'all': True}
            )
        
        # 创建测试用户
        self.users = {}
        user_data = [
            ('admin', 'ADMIN001', self.roles['admin'], None, None),
            ('eng_manager', 'ENG001', self.roles['engineering_manager'], self.eng_dept, None),
            ('me_eng', 'ME001', self.roles['me_engineer'], self.eng_dept, self.me_position),
            ('te_eng', 'TE001', self.roles['te_engineer'], self.eng_dept, None),
            ('technician', 'TECH001', self.roles['technician'], self.eng_dept, None),
            ('operator', 'OP001', self.roles['production_operator'], self.prod_dept, None),
        ]
        
        for username, emp_id, role, dept, pos in user_data:
            self.users[username] = get_user_model().objects.create_user(
                username=username,
                password='testpass123',
                real_name=role.name,
                employee_id=emp_id,
                email=f'{username}@example.com',
                role=role,
                department=dept,
                position=pos
            )
        
        self.create_test_data()
    
    def create_test_data(self):
        """创建测试数据"""
        # 课程分类
        self.category = CourseCategory.objects.create(
            name='技术培训',
            code='TECH'
        )
        
        # 课程 - 修正所有字段为关键字参数格式
        self.course = Course.objects.create(
            code='COURSE001',
            title='设备操作培训',  # 修正：使用 title=
            description='生产设备操作培训',
            category=self.category,
            course_type='online',
            duration=120,
            credit=2.0,
            passing_score=60.00,
            status='published',
            created_by=self.users['admin']
        )
        
        # 题库
        self.question_bank = QuestionBank.objects.create(
            name='设备操作题库',
            code='EQUIP_BANK',
            created_by=self.users['admin']
        )
        
        # 题目
        self.question = Question.objects.create(
            question_bank=self.question_bank,
            question_type='single_choice',
            title='设备启动前需要检查什么？',  # 修正：使用 title=
            options={
                'options': [
                    {'key': 'A', 'value': '电源'},
                    {'key': 'B', 'value': '安全装置'},
                    {'key': 'C', 'value': '以上都是'}
                ]
            },
            correct_answer={'answer': ['C']},
            score=2.0,
            created_by=self.users['admin']
        )
        
        # 考试
        now = timezone.now()
        self.exam = Exam.objects.create(
            code='EXAM001',
            title='设备操作考试',  # 修正：使用 title=
            exam_type='formal',
            question_bank=self.question_bank,
            total_questions=1,
            total_score=100.0,
            passing_score=60.0,
            time_limit=30,
            start_time=now,
            end_time=now + timedelta(hours=2),
            status='published',
            created_by=self.users['admin']
        )
        self.exam.participants.add(self.users['me_eng'])
        self.exam.participants.add(self.users['te_eng'])
        self.exam.participants.add(self.users['technician'])
        self.exam.participants.add(self.users['operator'])
        
        # 能力
        self.competency = Competency.objects.create(
            name='设备操作',
            code='EQUIP_OP',
            level='proficient',
            assessment_method='exam',
            required=True,
            created_by=self.users['admin']
        )
    
    def test_admin_permissions(self):
        """测试管理员权限"""
        self.client.force_authenticate(user=self.users['admin'])
        
        # 测试创建用户
        url = '/api/users/'
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'real_name': '新用户',
            'employee_id': 'NEW001',
            'email': 'new@example.com',
            'role': self.roles['me_engineer'].id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 测试查看所有用户
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_engineering_manager_permissions(self):
        """测试工程经理权限"""
        self.client.force_authenticate(user=self.users['eng_manager'])
        
        # 可以查看课程列表
        response = self.client.get('/api/training/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 根据权限矩阵，工程经理没有用户创建权限
        data = {
            'username': 'testuser',
            'password': 'testpass',
            'real_name': '测试',
            'employee_id': 'TEST001',
            'email': 'test@example.com',
            'role': self.roles['me_engineer'].id
        }
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 可以审批培训计划
        plan = TrainingPlan.objects.create(
            code='PLAN001',
            title='工程培训计划',  # 修正：使用 title=
            plan_type='department',
            target_department=self.eng_dept,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            status='pending',
            created_by=self.users['admin']
        )
        plan.courses.add(self.course)
        
        url = f'/api/training/plans/{plan.id}/approve/'
        response = self.client.post(url, {'approved': True, 'comment': '批准'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_me_engineer_permissions(self):
        """测试ME工程师权限 - 根据权限矩阵，有创建权限"""
        self.client.force_authenticate(user=self.users['me_eng'])
        
        # 可以查看课程列表
        response = self.client.get('/api/training/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以开始考试
        url = f'/api/examination/exams/{self.exam.id}/start/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 根据权限矩阵，ME工程师有course:create权限
        data = {
            'code': 'COURSE002',
            'title': '新课程',
            'category': self.category.id,
            'course_type': 'online',
            'duration': 60,
            'status': 'draft'
        }
        response = self.client.post('/api/training/courses/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_te_engineer_permissions(self):
        """测试TE工程师权限"""
        self.client.force_authenticate(user=self.users['te_eng'])
        
        # 可以查看培训记录
        response = self.client.get('/api/training/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以查看能力评估
        response = self.client.get('/api/competency/assessments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以查看证书
        response = self.client.get('/api/competency/certificates/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_technician_permissions(self):
        """测试技术员权限"""
        self.client.force_authenticate(user=self.users['technician'])
        
        # 可以查看课程详情
        url = f'/api/training/courses/{self.course.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以报名课程
        url = f'/api/training/courses/{self.course.id}/enroll/'
        response = self.client.post(url)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        
        # 可以查看培训统计
        url = '/api/training/records/statistics/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_production_operator_permissions(self):
        """测试生产操作员权限"""
        self.client.force_authenticate(user=self.users['operator'])
        
        # 可以查看课程列表
        response = self.client.get('/api/training/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以开始考试
        url = f'/api/examination/exams/{self.exam.id}/start/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以查看自己的培训记录
        response = self.client.get('/api/training/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以查看用户列表（只读自己）
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)