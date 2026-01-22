#!/usr/bin/env python
"""Core functionality test script for TCMS Backend"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test.utils import setup_test_environment
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


# 全局变量
client = APIClient()
test_results = {
    'passed': 0,
    'failed': 0,
    'tests': []
}


def log_test(test_name, passed, message=''):
    """记录测试结果"""
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")
    
    test_results['passed' if passed else 'failed'] += 1
    test_results['tests'].append({
        'name': test_name,
        'passed': passed,
        'message': message
    })


def run_core_tests():
    """运行核心功能测试"""
    print("TCMS后端系统核心功能测试")
    print("="*60)
    print(f"测试时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 设置测试环境
    setup_test_environment()
    
    try:
        # 1. 测试角色存在
        print("\n1. 测试角色系统")
        expected_roles = ['admin', 'engineering_manager', 'me_engineer', 'te_engineer', 'technician', 'production_operator']
        existing_roles = Role.objects.filter(code__in=expected_roles)
        found_roles = [role.code for role in existing_roles]
        
        for role_code in expected_roles:
            if role_code in found_roles:
                log_test(f"角色 {role_code}", True)
            else:
                log_test(f"角色 {role_code}", False, "角色不存在")
        
        # 2. 测试用户管理
        print("\n2. 测试用户管理")
        admin_role = Role.objects.get(code='admin')
        admin_user, created = get_user_model().objects.get_or_create(
            username='admin_test',
            defaults={
                'real_name': '测试管理员',
                'email': 'admin@test.com',
                'employee_id': 'ADMIN001',
                'role': admin_role
            }
        )
        if created:
            admin_user.set_password('admin123456')
            admin_user.save()
            log_test("创建管理员用户", True)
        else:
            log_test("管理员用户已存在", True)
        
        # 3. 测试认证
        print("\n3. 测试认证系统")
        url = reverse('token_obtain_pair')
        response = client.post(url, {
            'username': 'admin_test',
            'password': 'admin123456'
        }, format='json')
        
        if response.status_code == status.HTTP_200_OK:
            token = response.data['access']
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            log_test("用户登录认证", True, "获取JWT Token成功")
        else:
            log_test("用户登录认证", False, f"状态码: {response.status_code}")
        
        # 4. 测试课程管理
        print("\n4. 测试课程管理")
        
        # 创建课程分类
        category, created = CourseCategory.objects.get_or_create(
            name='技术培训',
            defaults={'code': 'TECH'}
        )
        
        # 测试创建课程
        url = reverse('course-list')
        course_data = {
            'code': 'TEST_COURSE_001',
            'title': '测试课程',
            'description': '测试课程描述',
            'category': category.id,
            'course_type': 'online',
            'duration': 60,
            'credit': 1.0,
            'status': 'published'
        }
        
        response = client.post(url, course_data, format='json')
        if response.status_code == status.HTTP_201_CREATED:
            course_id = response.data['data']['id']
            log_test("创建课程", True, f"课程ID: {course_id}")
            
            # 测试发布课程
            publish_url = reverse('course-publish', kwargs={'pk': course_id})
            response = client.post(publish_url)
            if response.status_code == status.HTTP_200_OK:
                log_test("发布课程", True)
            else:
                log_test("发布课程", False, f"状态码: {response.status_code}")
        else:
            log_test("创建课程", False, f"状态码: {response.status_code}")
        
        # 5. 测试考试管理
        print("\n5. 测试考试管理")
        
        # 创建题库
        question_bank, created = QuestionBank.objects.get_or_create(
            name='测试题库',
            defaults={'code': 'TEST_BANK'}
        )
        
        # 创建考试
        url = reverse('exam-list')
        exam_data = {
            'code': 'TEST_EXAM_001',
            'title': '测试考试',
            'question_bank': question_bank.id,
            'total_questions': 10,
            'total_score': 100.0,
            'passing_score': 60.0,
            'time_limit': 60,
            'start_time': timezone.now(),
            'end_time': timezone.now() + timedelta(hours=2),
            'status': 'published'
        }
        
        response = client.post(url, exam_data, format='json')
        if response.status_code == status.HTTP_201_CREATED:
            exam_id = response.data['data']['id']
            log_test("创建考试", True, f"考试ID: {exam_id}")
            
            # 测试发布考试
            publish_url = reverse('exam-publish', kwargs={'pk': exam_id})
            response = client.post(publish_url)
            if response.status_code == status.HTTP_200_OK:
                log_test("发布考试", True)
            else:
                log_test("发布考试", False, f"状态码: {response.status_code}")
        else:
            log_test("创建考试", False, f"状态码: {response.status_code}")
        
        # 6. 测试证书管理
        print("\n6. 测试证书管理")
        
        # 创建能力
        competency, created = Competency.objects.get_or_create(
            name='设备操作',
            defaults={'code': 'EQUIP_OP', 'level': 'proficient'}
        )
        
        # 创建证书
        certificate, created = Certificate.objects.get_or_create(
            name='测试证书',
            user=admin_user,
            competency=competency,
            defaults={
                'certificate_no': 'CERT001',
                'issue_date': timezone.now().date(),
                'expiry_date': timezone.now().date() + timedelta(days=365),
                'issued_by': admin_user
            }
        )
        
        if created or certificate:
            log_test("创建证书", True, f"证书编号: {certificate.certificate_no}")
            
            # 测试验证证书
            url = reverse('certificate-verify')
            response = client.post(url, {
                'verification_code': certificate.verification_code
            }, format='json')
            
            if response.status_code == status.HTTP_200_OK:
                is_valid = response.data['data']['is_valid']
                log_test("验证证书", is_valid, f"验证码: {certificate.verification_code}")
            else:
                log_test("验证证书", False, f"状态码: {response.status_code}")
        
        # 7. 测试导入导出模板
        print("\n7. 测试导入导出功能")
        
        # 测试下载课程导入模板
        url = reverse('course-import-template')
        response = client.get(url)
        if response.status_code == status.HTTP_200_OK:
            log_test("下载课程导入模板", True)
        else:
            log_test("下载课程导入模板", False, f"状态码: {response.status_code}")
        
        # 测试导出课程
        url = reverse('course-export')
        response = client.get(url)
        if response.status_code == status.HTTP_200_OK:
            log_test("导出课程", True)
        else:
            log_test("导出课程", False, f"状态码: {response.status_code}")
        
        # 8. 测试邮件服务
        print("\n8. 测试邮件服务")
        try:
            from apps.common.email_service import EmailService
            log_test("邮件服务导入", True)
            
            # 检查邮件方法
            methods = [
                'send_course_enrollment_notification',
                'send_exam_result_notification',
                'send_certificate_notification',
            ]
            
            for method in methods:
                if hasattr(EmailService, method):
                    log_test(f"邮件方法 {method}", True)
                else:
                    log_test(f"邮件方法 {method}", False, "方法不存在")
                    
        except ImportError as e:
            log_test("邮件服务导入", False, f"错误: {str(e)}")
        
        # 生成测试报告
        generate_test_summary()
        
        return test_results['failed'] == 0
        
    except Exception as e:
        print(f"\n❌ 测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def generate_test_summary():
    """生成测试总结"""
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    total_tests = test_results['passed'] + test_results['failed']
    pass_rate = (test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {test_results['passed']}")
    print(f"失败: {test_results['failed']}")
    print(f"通过率: {pass_rate:.1f}%")
    
    # 显示失败的测试
    if test_results['failed'] > 0:
        print("\n失败的测试:")
        for test in test_results['tests']:
            if not test['passed']:
                print(f"  - {test['name']}: {test['message']}")
    else:
        print("\n✅ 所有测试通过!")


if __name__ == "__main__":
    success = run_core_tests()
    sys.exit(0 if success else 1)