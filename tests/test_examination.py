"""Examination tests"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.users.models import Role
from apps.examination.models import QuestionBank, Question, Exam, ExamResult


class ExaminationTests(TestCase):
    """考试管理测试"""
    
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
        
        # 创建题库
        self.question_bank = QuestionBank.objects.create(
            name='技术题库',
            code='TECH_BANK',
            category='技术',
            created_by=self.admin_user
        )
        
        # 创建题目
        self.question = Question.objects.create(
            question_bank=self.question_bank,
            question_type='single_choice',
            difficulty='medium',
            title='Python中用于创建虚拟环境的是？',
            content='Python中用于创建虚拟环境的工具是？',
            options={
                'options': [
                    {'key': 'A', 'value': 'pip'},
                    {'key': 'B', 'value': 'venv'},
                    {'key': 'C', 'value': 'conda'},
                    {'key': 'D', 'value': 'virtualenv'}
                ]
            },
            correct_answer={'answer': ['B']},
            explanation='venv是Python标准库中的虚拟环境创建工具',
            score=2.0,
            created_by=self.admin_user
        )
        
        # 创建考试
        now = timezone.now()
        self.exam = Exam.objects.create(
            code='EXAM001',
            title='Python基础测试',
            exam_type='formal',
            question_bank=self.question_bank,
            total_questions=1,
            total_score=100.0,
            passing_score=60.0,
            time_limit=60,
            start_time=now,
            end_time=now + timedelta(hours=2),
            status='published',
            created_by=self.admin_user
        )
        self.exam.participants.add(self.employee_user)
    
    def test_list_exams(self):
        """查看考试列表"""
        self.client.force_authenticate(user=self.employee_user)
        
        url = reverse('exam-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['title'], 'Python基础测试')
    
    def test_create_exam(self):
        """创建考试"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('exam-list')
        now = timezone.now()
        data = {
            'code': 'EXAM002',
            'title': 'Django测试',
            'exam_type': 'formal',
            'question_bank': self.question_bank.id,
            'total_questions': 10,
            'total_score': 100.0,
            'passing_score': 60.0,
            'time_limit': 60,
            'start_time': now.isoformat(),
            'end_time': (now + timedelta(hours=2)).isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['title'], 'Django测试')
    
    def test_start_exam(self):
        """开始考试"""
        self.client.force_authenticate(user=self.employee_user)
        
        url = reverse('exam-start', kwargs={'pk': self.exam.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('questions', response.data['data'])
        self.assertEqual(len(response.data['data']['questions']), 1)
    
    def test_submit_exam(self):
        """提交考试"""
        self.client.force_authenticate(user=self.employee_user)
        
        # 创建考试结果
        result = ExamResult.objects.create(
            exam=self.exam,
            user=self.employee_user,
            status='in_progress'
        )
        
        url = reverse('exam-submit', kwargs={'pk': self.exam.id})
        data = {
            'answers': {
                str(self.question.id): ['B']
            },
            'duration': 30
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('score', response.data['data'])
    
    def test_exam_result(self):
        """查看考试成绩"""
        # 创建考试结果
        result = ExamResult.objects.create(
            exam=self.exam,
            user=self.employee_user,
            status='graded',
            score=85.00,
            correct_count=1,
            wrong_count=0,
            is_passed=True,
            duration=30,
            submitted_at=timezone.now()
        )
        
        self.client.force_authenticate(user=self.employee_user)
        
        url = reverse('examresult-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['score'], 85.00)
    
    def test_generate_certificate(self):
        """生成证书"""
        # 创建通过的考试结果
        result = ExamResult.objects.create(
            exam=self.exam,
            user=self.employee_user,
            status='graded',
            score=85.00,
            correct_count=1,
            wrong_count=0,
            is_passed=True,
            duration=30,
            submitted_at=timezone.now()
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('examresult-generate-certificate', kwargs={'pk': result.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('certificate_no', response.data['data'])