"""Role-based functional tests for all user roles"""
from django.test import TestCase
from django.urls import reverse
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
        """测试准备：创建所有角色和用户"""
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
        
        self.te_position = Position.objects.create(
            name='TE工程师',
            code='TE',
            level='mid',
            status='active'
        )
        
        self.technician_position = Position.objects.create(
            name='技术员',
            code='TECH',
            level='junior',
            status='active'
        )
        
        # 创建角色
        self.roles = {}
        role_data = [
            ('admin', '系统管理员'),
            ('engineering_manager', '工程经理'),
            ('me_engineer', 'ME工程师'),
            ('te_engineer', 'TE工程师'),
            ('technician', '技术员'),
            ('production_operator', '生产操作员'),
        ]
        
        for code, name in role_data:
            self.roles[code] = Role.objects.create(
                name=name,
                code=code,
                status='enabled'
            )
        
        # 创建测试用户
        self.users = {}
        user_data = [
            ('admin', '管理员', 'ADMIN001', 'admin@example.com', self.roles['admin'], None, None),
            ('eng_manager', '工程经理', 'ENG001', 'eng@example.com', self.roles['engineering_manager'], self.eng_dept, None),
            ('me_eng', 'ME工程师', 'ME001', 'me@example.com', self.roles['me_engineer'], self.eng_dept, self.me_position),
            ('te_eng', 'TE工程师', 'TE001', 'te@example.com', self.roles['te_engineer'], self.eng_dept, self.te_position),
            ('technician', '技术员', 'TECH001', 'tech@example.com', self.roles['technician'], self.eng_dept, self.technician_position),
            ('operator', '生产操作员', 'OP001', 'op@example.com', self.roles['production_operator'], self.prod_dept, None),
        ]
        
        for username, real_name, emp_id, email, role, dept, pos in user_data:
            self.users[username] = get_user_model().objects.create_user(
                username=username,
                password='testpass123',
                real_name=real_name,
                employee_id=emp_id,
                email=email,
                role=role,
                department=dept,
                position=pos
            )
        
        # 创建测试数据
        self.create_test_data()
    
    def create_test_data(self):
        """创建测试数据"""
        # 课程分类
        self.category = CourseCategory.objects.create(
            name='技术培训',
            code='TECH'
        )
        
        # 课程
        self.course = Course.objects.create(
            code='COURSE001',
            title='设备操作培训',
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
            title='设备启动前需要检查什么？',
            options={'options': [{'key': 'A', 'value': '电源'}, {'key': 'B', 'value': '安全装置'}, {'key': 'C', 'value': '以上都是'}]},
            correct_answer={'answer': ['C']},
            score=2.0,
            created_by=self.users['admin']
        )
        
        # 考试
        self.exam = Exam.objects.create(
            code='EXAM001',
            title='设备操作考试',
            question_bank=self.question_bank,
            total_questions=1,
            total_score=100.0,
            passing_score=60.0,
            time_limit=30,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
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
        url = reverse('user-list')
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
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['data']['count'], 6)
    
    def test_engineering_manager_permissions(self):
        """测试工程经理权限"""
        self.client.force_authenticate(user=self.users['eng_manager'])
        
        # 可以查看用户列表
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 不能创建用户（应该失败）
        data = {
            'username': 'testuser',
            'password': 'testpass',
            'real_name': '测试',
            'employee_id': 'TEST001',
            'email': 'test@example.com',
            'role': self.roles['me_engineer'].id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 可以审批培训计划
        plan = TrainingPlan.objects.create(
            code='PLAN001',
            title='工程培训计划',
            plan_type='department',
            target_department=self.eng_dept,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            status='pending',
            created_by=self.users['admin']
        )
        plan.courses.add(self.course)
        
        url = reverse('trainingplan-approve', kwargs={'pk': plan.id})
        response = self.client.post(url, {'approved': True, 'comment': '批准'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_me_engineer_permissions(self):
        """测试ME工程师权限"""
        self.client.force_authenticate(user=self.users['me_eng'])
        
        # 可以查看课程列表
        url = reverse('course-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以报名参加考试
        url = reverse('exam-start', kwargs={'pk': self.exam.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 提交考试
        url = reverse('exam-submit', kwargs={'pk': self.exam.id})
        data = {
            'answers': {str(self.question.id): ['C']},
            'duration': 15
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 不能创建课程（应该失败）
        url = reverse('course-list')
        data = {
            'code': 'COURSE002',
            'title': '新课程',
            'category': self.category.id,
            'course_type': 'online',
            'duration': 60,
            'status': 'draft'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_te_engineer_permissions(self):
        """测试TE工程师权限"""
        self.client.force_authenticate(user=self.users['te_eng'])
        
        # 可以查看培训记录
        url = reverse('trainingrecord-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以查看能力评估
        url = reverse('competencyassessment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以查看证书
        url = reverse('certificate-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_technician_permissions(self):
        """测试技术员权限"""
        self.client.force_authenticate(user=self.users['technician'])
        
        # 可以查看课程详情
        url = reverse('course-detail', kwargs={'pk': self.course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以报名课程
        url = reverse('course-enroll', kwargs={'pk': self.course.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 可以查看培训统计
        url = reverse('trainingrecord-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_production_operator_permissions(self):
        """测试生产操作员权限"""
        self.client.force_authenticate(user=self.users['operator'])
        
        # 可以查看课程列表
        url = reverse('course-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以参加考试
        url = reverse('exam-start', kwargs={'pk': self.exam.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以查看自己的培训记录
        url = reverse('trainingrecord-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 不能查看所有用户（应该只能看到自己）
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)  # 只能看到自己
    
    def test_role_based_access_control(self):
        """测试基于角色的访问控制"""
        # 测试不同角色访问不同资源的权限
        
        roles_permissions = {
            'admin': ['user:create', 'course:create', 'exam:create'],
            'eng_manager': ['training_plan:approve', 'user:read'],
            'me_engineer': ['course:read', 'exam:take'],
            'te_engineer': ['course:read', 'exam:take'],
            'technician': ['course:read', 'exam:take'],
            'production_operator': ['course:read', 'exam:take'],
        }
        
        for username, expected_permissions in roles_permissions.items():
            user = self.users[username]
            self.client.force_authenticate(user=user)
            
            for permission in expected_permissions:
                module, action = permission.split(':')
                
                if module == 'user' and action == 'create':
                    url = reverse('user-list')
                    response = self.client.post(url, {
                        'username': f'test_{username}',
                        'password': 'testpass',
                        'real_name': '测试',
                        'employee_id': f'TEST_{username.upper()}',
                        'email': f'test_{username}@example.com',
                        'role': self.roles['employee'].id
                    }, format='json')
                    
                    if username == 'admin':
                        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                    else:
                        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                
                elif module == 'course' and action == 'create':
                    url = reverse('course-list')
                    response = self.client.post(url, {
                        'code': f'COURSE_{username}',
                        'title': f'测试课程_{username}',
                        'category': self.category.id,
                        'course_type': 'online',
                        'duration': 60
                    }, format='json')
                    
                    if username == 'admin':
                        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                    else:
                        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                
                elif module == 'exam' and action == 'take':
                    # 检查是否可以开始考试
                    url = reverse('exam-start', kwargs={'pk': self.exam.id})
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status.HTTP_200_OK)


class RoleBasedReportTests(TestCase):
    """基于角色的报表测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        
        # 创建角色
        self.roles = {}
        for code, name in [
            ('admin', '系统管理员'),
            ('engineering_manager', '工程经理'),
            ('me_engineer', 'ME工程师'),
            ('te_engineer', 'TE工程师'),
            ('technician', '技术员'),
            ('production_operator', '生产操作员'),
        ]:
            self.roles[code] = Role.objects.create(name=name, code=code)
        
        # 创建用户
        self.users = {}
        for code, role in self.roles.items():
            self.users[code] = get_user_model().objects.create_user(
                username=code,
                password='testpass123',
                real_name=role.name,
                employee_id=code.upper(),
                email=f'{code}@example.com',
                role=role
            )
    
    def test_admin_can_view_all_reports(self):
        """管理员可以查看所有报表"""
        self.client.force_authenticate(user=self.users['admin'])
        
        # 培训统计
        url = reverse('reporting-training-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 考试分析
        url = reverse('reporting-exam-analysis')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 能力矩阵
        url = reverse('reporting-competency-matrix')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 合规性报表
        url = reverse('reporting-compliance-report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_engineering_manager_can_view_reports(self):
        """工程经理可以查看报表"""
        self.client.force_authenticate(user=self.users['engineering_manager'])
        
        # 可以查看培训统计
        url = reverse('reporting-training-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 可以查看考试分析
        url = reverse('reporting-exam-analysis')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RoleWorkflowTests(TestCase):
    """角色工作流测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        
        # 创建角色
        self.roles = {}
        for code, name in [
            ('admin', '系统管理员'),
            ('engineering_manager', '工程经理'),
            ('me_engineer', 'ME工程师'),
            ('te_engineer', 'TE工程师'),
            ('technician', '技术员'),
            ('production_operator', '生产操作员'),
        ]:
            self.roles[code] = Role.objects.create(name=name, code=code)
        
        # 创建用户
        self.users = {}
        for code, role in self.roles.items():
            self.users[code] = get_user_model().objects.create_user(
                username=code,
                password='testpass123',
                real_name=role.name,
                employee_id=code.upper(),
                email=f'{code}@example.com',
                role=role
            )
    
    def test_me_engineer_workflow(self):
        """测试ME工程师完整工作流"""
        user = self.users['me_engineer']
        self.client.force_authenticate(user=user)
        
        # 1. 查看可用课程
        url = reverse('course-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. 查看课程详情
        # 先创建一个课程
        category = CourseCategory.objects.create(name='技术培训', code='TECH')
        course = Course.objects.create(
            code='ME_COURSE001',
            title='ME设备培训',
            category=category,
            course_type='online',
            duration=120,
            status='published',
            created_by=self.users['admin']
        )
        
        url = reverse('course-detail', kwargs={'pk': course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. 报名参加课程
        url = reverse('course-enroll', kwargs={'pk': course.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 4. 查看培训记录
        url = reverse('trainingrecord-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        
        # 5. 完成培训（模拟）
        record = TrainingRecord.objects.get(user=user, course=course)
        record.status = 'completed'
        record.progress = 100
        record.score = 85.00
        record.complete_date = timezone.now()
        record.save()
        
        # 6. 查看培训统计
        url = reverse('trainingrecord-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 7. 评价课程
        url = reverse('trainingrecord-evaluate', kwargs={'pk': record.id})
        response = self.client.post(url, {
            'evaluation': '课程很好',
            'feedback': '学到了很多'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_technician_workflow(self):
        """测试技术员完整工作流"""
        user = self.users['technician']
        self.client.force_authenticate(user=user)
        
        # 1. 查看考试列表
        url = reverse('exam-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. 查看考试详情
        # 先创建一个考试
        question_bank = QuestionBank.objects.create(name='技术员题库', code='TECH_BANK')
        exam = Exam.objects.create(
            code='TECH_EXAM001',
            title='技术员考试',
            question_bank=question_bank,
            total_questions=10,
            total_score=100.0,
            passing_score=60.0,
            time_limit=60,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            status='published',
            created_by=self.users['admin']
        )
        exam.participants.add(user)
        
        url = reverse('exam-detail', kwargs={'pk': exam.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. 开始考试
        url = reverse('exam-start', kwargs={'pk': exam.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 4. 提交考试
        question = Question.objects.create(
            question_bank=question_bank,
            question_type='single_choice',
            title='技术员考试题目',
            options={'options': [{'key': 'A', 'value': '选项A'}, {'key': 'B', 'value': '选项B'}]},
            correct_answer={'answer': ['A']},
            score=10.0,
            created_by=self.users['admin']
        )
        
        url = reverse('exam-submit', kwargs={'pk': exam.id})
        response = self.client.post(url, {
            'answers': {str(question.id): ['A']},
            'duration': 30
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 5. 查看考试成绩
        url = reverse('examresult-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        
        # 6. 查看能力要求
        url = reverse('competency-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_production_operator_training_flow(self):
        """测试生产操作员培训流程"""
        user = self.users['production_operator']
        self.client.force_authenticate(user=user)
        
        # 1. 查看可用培训
        url = reverse('course-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. 报名参加培训
        category = CourseCategory.objects.create(name='安全培训', code='SAFETY')
        safety_course = Course.objects.create(
            code='SAFETY001',
            title='生产安全培训',
            category=category,
            course_type='online',
            duration=60,
            status='published',
            created_by=self.users['admin']
        )
        
        url = reverse('course-enroll', kwargs={'pk': safety_course.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. 查看培训进度
        url = reverse('trainingrecord-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        
        # 4. 模拟完成培训
        record = TrainingRecord.objects.get(user=user, course=safety_course)
        record.status = 'completed'
        record.progress = 100
        record.save()
        
        # 5. 获取培训证书
        certificate = Certificate.objects.create(
            name='安全培训证书',
            user=user,
            competency=Competency.objects.create(
                name='生产安全',
                code='SAFETY_COMP',
                level='aware',
                assessment_method='training',
                required=True,
                created_by=self.users['admin']
            ),
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            issued_by=self.users['admin']
        )
        
        # 6. 验证证书
        url = reverse('certificate-verify')
        response = self.client.post(url, {
            'verification_code': certificate.verification_code
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['is_valid'])


class RolePermissionMatrixTests(TestCase):
    """角色权限矩阵测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        
        # 创建角色
        self.roles = {}
        for code, name in [
            ('admin', '系统管理员'),
            ('engineering_manager', '工程经理'),
            ('me_engineer', 'ME工程师'),
            ('te_engineer', 'TE工程师'),
            ('technician', '技术员'),
            ('production_operator', '生产操作员'),
        ]:
            self.roles[code] = Role.objects.create(name=name, code=code)
        
        # 创建用户
        self.users = {}
        for code, role in self.roles.items():
            self.users[code] = get_user_model().objects.create_user(
                username=code,
                password='testpass123',
                real_name=role.name,
                employee_id=code.upper(),
                email=f'{code}@example.com',
                role=role
            )
    
    def test_permission_matrix(self):
        """测试权限矩阵"""
        # 定义权限矩阵
        permission_matrix = {
            'admin': {
                'user:create': True,
                'user:read': True,
                'user:update': True,
                'user:delete': True,
                'course:create': True,
                'course:read': True,
                'course:update': True,
                'course:delete': True,
                'exam:create': True,
                'exam:read': True,
                'exam:update': True,
                'exam:delete': True,
                'exam:take': True,
                'report:*': True,
            },
            'engineering_manager': {
                'user:create': False,
                'user:read': True,
                'user:update': False,
                'user:delete': False,
                'course:create': False,
                'course:read': True,
                'course:update': False,
                'course:delete': False,
                'exam:create': False,
                'exam:read': True,
                'exam:update': False,
                'exam:delete': False,
                'exam:take': True,
                'report:training': True,
                'report:exam': True,
            },
            'me_engineer': {
                'user:create': False,
                'user:read': False,
                'user:update': False,
                'user:delete': False,
                'course:create': False,
                'course:read': True,
                'course:update': False,
                'course:delete': False,
                'exam:create': False,
                'exam:read': True,
                'exam:update': False,
                'exam:delete': False,
                'exam:take': True,
                'report:training': False,
                'report:exam': False,
            },
            'te_engineer': {
                'user:create': False,
                'user:read': False,
                'user:update': False,
                'user:delete': False,
                'course:create': False,
                'course:read': True,
                'course:update': False,
                'course:delete': False,
                'exam:create': False,
                'exam:read': True,
                'exam:update': False,
                'exam:delete': False,
                'exam:take': True,
                'report:training': False,
                'report:exam': False,
            },
            'technician': {
                'user:create': False,
                'user:read': False,
                'user:update': False,
                'user:delete': False,
                'course:create': False,
                'course:read': True,
                'course:update': False,
                'course:delete': False,
                'exam:create': False,
                'exam:read': True,
                'exam:update': False,
                'exam:delete': False,
                'exam:take': True,
                'report:training': False,
                'report:exam': False,
            },
            'production_operator': {
                'user:create': False,
                'user:read': False,
                'user:update': False,
                'user:delete': False,
                'course:create': False,
                'course:read': True,
                'course:update': False,
                'course:delete': False,
                'exam:create': False,
                'exam:read': True,
                'exam:update': False,
                'exam:delete': False,
                'exam:take': True,
                'report:training': False,
                'report:exam': False,
            },
        }
        
        # 测试每个角色的权限
        for role_code, expected_permissions in permission_matrix.items():
            user = self.users[role_code]
            
            for permission, expected_result in expected_permissions.items():
                actual_result = user.has_permission(permission)
                self.assertEqual(
                    actual_result, expected_result,
                    f"Role {role_code} permission {permission}: expected {expected_result}, got {actual_result}"
                )


class RoleDataIsolationTests(TestCase):
    """角色数据隔离测试"""
    
    def setUp(self):
        """测试准备"""
        self.client = APIClient()
        
        # 创建角色
        self.me_role = Role.objects.create(name='ME工程师', code='me_engineer')
        self.te_role = Role.objects.create(name='TE工程师', code='te_engineer')
        
        # 创建用户
        self.me_user = get_user_model().objects.create_user(
            username='me_eng',
            password='testpass123',
            real_name='ME工程师',
            employee_id='ME001',
            email='me@example.com',
            role=self.me_role
        )
        
        self.te_user = get_user_model().objects.create_user(
            username='te_eng',
            password='testpass123',
            real_name='TE工程师',
            employee_id='TE001',
            email='te@example.com',
            role=self.te_role
        )
        
        # 创建培训记录
        category = CourseCategory.objects.create(name='测试分类', code='TEST')
        self.course1 = Course.objects.create(
            code='COURSE1',
            title='ME课程',
            category=category,
            status='published',
            created_by=self.me_user
        )
        self.course2 = Course.objects.create(
            code='COURSE2',
            title='TE课程',
            category=category,
            status='published',
            created_by=self.te_user
        )
        
        # ME用户的培训记录
        TrainingRecord.objects.create(
            user=self.me_user,
            course=self.course1,
            status='completed',
            progress=100,
            score=85.00
        )
        
        # TE用户的培训记录
        TrainingRecord.objects.create(
            user=self.te_user,
            course=self.course2,
            status='completed',
            progress=100,
            score=90.00
        )
    
    def test_data_isolation(self):
        """测试数据隔离"""
        # ME用户只能看到自己的培训记录
        self.client.force_authenticate(user=self.me_user)
        
        url = reverse('trainingrecord-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['course'], self.course1.id)
        
        # TE用户只能看到自己的培训记录
        self.client.force_authenticate(user=self.te_user)
        
        url = reverse('trainingrecord-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['course'], self.course2.id)