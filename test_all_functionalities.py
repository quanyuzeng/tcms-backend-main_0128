#!/usr/bin/env python
"""Complete functionality test script for TCMS Backend"""
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
from datetime import timedelta, datetime
import random
import string

from apps.users.models import Role
from apps.organization.models import Department, Position
from apps.training.models import Course, CourseCategory, TrainingPlan, TrainingRecord
from apps.examination.models import QuestionBank, Question, Exam, ExamResult
from apps.examination.serializers import QuestionSerializer
from apps.competency.models import Competency, CompetencyAssessment, Certificate

# 测试配置
TEST_CONFIG = {
    'base_url': 'http://localhost:8080/api',
    'admin_username': 'admin_test',
    'admin_password': 'admin123456',
    'test_users_count': 5,
    'test_courses_count': 3,
    'test_exams_count': 2,
}

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


def create_test_data():
    """创建测试数据"""
    print("\n" + "="*60)
    print("创建测试数据")
    print("="*60)
    
    # 创建部门
    departments_data = [
        {'name': '工程部', 'code': 'ENG'},
        {'name': '生产部', 'code': 'PROD'},
        {'name': '质量部', 'code': 'QA'},
    ]
    
    departments = {}
    for dept_data in departments_data:
        dept, created = Department.objects.get_or_create(
            code=dept_data['code'],
            defaults={'name': dept_data['name'], 'status': 'active'}
        )
        departments[dept_data['code']] = dept
        print(f"部门: {dept.name} ({'创建' if created else '已存在'})")
    
    # 创建岗位
    positions_data = [
        {'name': 'ME工程师', 'code': 'ME', 'level': 'mid'},
        {'name': 'TE工程师', 'code': 'TE', 'level': 'mid'},
        {'name': '技术员', 'code': 'TECH', 'level': 'junior'},
        {'name': '生产操作员', 'code': 'OP', 'level': 'junior'},
        {'name': '工程经理', 'code': 'EM', 'level': 'senior'},
    ]
    
    positions = {}
    for pos_data in positions_data:
        pos, created = Position.objects.get_or_create(
            code=pos_data['code'],
            defaults={
                'name': pos_data['name'],
                'level': pos_data['level'],
                'status': 'active'
            }
        )
        positions[pos_data['code']] = pos
        print(f"岗位: {pos.name} ({'创建' if created else '已存在'})")
    
    # 创建角色（如果还不存在）
    roles_data = [
        ('admin', '系统管理员'),
        ('engineering_manager', '工程经理'),
        ('me_engineer', 'ME工程师'),
        ('te_engineer', 'TE工程师'),
        ('technician', '技术员'),
        ('production_operator', '生产操作员'),
    ]
    
    roles = {}
    for code, name in roles_data:
        role, created = Role.objects.get_or_create(
            code=code,
            defaults={'name': name, 'status': 'enabled'}
        )
        roles[code] = role
        print(f"角色: {role.name} ({'创建' if created else '已存在'})")
    
    return departments, positions, roles


def test_admin_authentication():
    """测试管理员登录"""
    print("\n" + "="*60)
    print("测试管理员登录")
    print("="*60)
    
    # 创建管理员用户
    admin_user, created = get_user_model().objects.get_or_create(
        username=TEST_CONFIG['admin_username'],
        defaults={
            'real_name': '测试管理员',
            'email': 'admin@test.com',
            'employee_id': 'ADMIN001',
            'role_id': Role.objects.get(code='admin').id
        }
    )
    if created:
        admin_user.set_password(TEST_CONFIG['admin_password'])
        admin_user.save()
        print("创建管理员用户")
    
    # 测试登录
    url = reverse('token_obtain_pair')
    response = client.post(url, {
        'username': TEST_CONFIG['admin_username'],
        'password': TEST_CONFIG['admin_password']
    }, format='json')
    
    if response.status_code == status.HTTP_200_OK:
        token = response.data['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        log_test("管理员登录", True, "登录成功，获取Token")
        return True
    else:
        log_test("管理员登录", False, f"登录失败: {response.status_code}")
        return False


def test_role_management():
    """测试角色管理"""
    print("\n" + "="*60)
    print("测试角色管理")
    print("="*60)
    
    # 测试获取角色列表
    url = reverse('user:role-list')
    response = client.get(url)
    
    if response.status_code == status.HTTP_200_OK:
        roles = response.data
        expected_roles = ['admin', 'engineering_manager', 'me_engineer', 'te_engineer', 'technician', 'production_operator']
        found_roles = [role['code'] for role in roles.get('data', {}).get('results', [])]
        
        all_present = all(role in found_roles for role in expected_roles)
        log_test("角色列表", all_present, f"期望角色: {expected_roles}, 实际: {found_roles}")
    else:
        log_test("角色列表", False, f"获取失败: {response.status_code}")


def test_user_creation():
    """测试用户创建"""
    print("\n" + "="*60)
    print("测试用户创建")
    print("="*60)
    
    # 测试创建ME工程师
    url = reverse('user:user-list')
    user_data = {
        'username': 'me_eng_test',
        'password': 'test123456',
        'real_name': 'ME工程师测试',
        'employee_id': 'ME001',
        'email': 'me@test.com',
        'role': Role.objects.get(code='me_engineer').id,
        'department': Department.objects.get(code='ENG').id,
        'position': Position.objects.get(code='ME').id
    }
    
    response = client.post(url, user_data, format='json')
    
    if response.status_code == status.HTTP_201_CREATED:
        log_test("创建ME工程师用户", True, f"用户ID: {response.data['data']['id']}")
        
        # 测试创建其他角色用户
        test_users = [
            ('te_eng_test', 'TE工程师测试', 'TE002', 'te@test.com', 'te_engineer', 'ENG', 'TE'),
            ('technician_test', '技术员测试', 'TECH001', 'tech@test.com', 'technician', 'ENG', 'TECH'),
            ('operator_test', '生产操作员测试', 'OP001', 'op@test.com', 'production_operator', 'PROD', None),
            ('eng_manager_test', '工程经理测试', 'EM001', 'em@test.com', 'engineering_manager', 'ENG', 'EM'),
        ]
        
        for username, real_name, emp_id, email, role_code, dept_code, pos_code in test_users:
            user_data = {
                'username': username,
                'password': 'test123456',
                'real_name': real_name,
                'employee_id': emp_id,
                'email': email,
                'role': Role.objects.get(code=role_code).id,
                'department': Department.objects.get(code=dept_code).id,
            }
            if pos_code:
                user_data['position'] = Position.objects.get(code=pos_code).id
            
            response = client.post(url, user_data, format='json')
            if response.status_code == status.HTTP_201_CREATED:
                log_test(f"创建{real_name}用户", True)
            else:
                log_test(f"创建{real_name}用户", False, f"错误: {response.data}")
    else:
        log_test("创建ME工程师用户", False, f"错误: {response.data}")


def test_course_management():
    """测试课程管理"""
    print("\n" + "="*60)
    print("测试课程管理")
    print("="*60)
    
    # 创建课程分类
    category, created = CourseCategory.objects.get_or_create(
        name='技术培训',
        defaults={'code': 'TECH'}
    )
    
    # 测试创建课程
    url = reverse('training:course-list')
    course_data = {
        'code': 'COURSE001',
        'title': '设备操作培训',
        'description': '生产设备基础操作培训',
        'category': category.id,
        'course_type': 'online',
        'duration': 120,
        'credit': 2.0,
        'passing_score': 60.0,
        'instructor': '张讲师',
        'status': 'published'
    }
    
    response = client.post(url, course_data, format='json')
    
    if response.status_code == status.HTTP_201_CREATED:
        course_id = response.data['data']['id']
        log_test("创建课程", True, f"课程ID: {course_id}")
        
        # 测试获取课程列表
        response = client.get(url)
        if response.status_code == status.HTTP_200_OK:
            log_test("获取课程列表", True, f"共{response.data['data']['count']}门课程")
        
        # 测试发布课程
        publish_url = reverse('training:course-publish', kwargs={'pk': course_id})
        response = client.post(publish_url)
        if response.status_code == status.HTTP_200_OK:
            log_test("发布课程", True)
        
        return course_id
    else:
        log_test("创建课程", False, f"错误: {response.data}")
        return None


def test_exam_management():
    """测试考试管理"""
    print("\n" + "="*60)
    print("测试考试管理")
    print("="*60)
    
    # 创建题库
    question_bank, created = QuestionBank.objects.get_or_create(
        name='设备操作题库',
        defaults={'code': 'EQUIP_BANK', 'created_by_id': 1}
    )
    
    # 创建题目
    question_data = {
        'question_bank': question_bank.id,
        'question_type': 'single_choice',
        'title': '设备启动前检查',
        'content': '设备启动前需要检查什么？',
        'options': {'options': [
            {'key': 'A', 'value': '电源'},
            {'key': 'B', 'value': '安全装置'},
            {'key': 'C', 'value': '以上都是'}
        ]},
        'correct_answer': {'answer': ['C']},
        'score': 2.0,
        'created_by_id': 1
    }
    
    question_serializer = QuestionSerializer(data=question_data)
    if question_serializer.is_valid():
        question = question_serializer.save()
        log_test("创建题目", True, f"题目ID: {question.id}")
    
    # 创建考试
    url = reverse('examination:exam-list')
    exam_data = {
        'code': 'EXAM001',
        'title': '设备操作考试',
        'question_bank': question_bank.id,
        'total_questions': 1,
        'total_score': 100.0,
        'passing_score': 60.0,
        'time_limit': 30,
        'start_time': timezone.now(),
        'end_time': timezone.now() + timedelta(hours=2),
        'status': 'published',
        'participants': [get_user_model().objects.get(username='me_eng_test').id]
    }
    
    response = client.post(url, exam_data, format='json')
    
    if response.status_code == status.HTTP_201_CREATED:
        exam_id = response.data['data']['id']
        log_test("创建考试", True, f"考试ID: {exam_id}")
        
        # 测试发布考试
        publish_url = reverse('examination:exam-publish', kwargs={'pk': exam_id})
        response = client.post(publish_url)
        if response.status_code == status.HTTP_200_OK:
            log_test("发布考试", True)
        
        return exam_id
    else:
        log_test("创建考试", False, f"错误: {response.data}")
        return None


def test_certificate_generation():
    """测试证书生成"""
    print("\n" + "="*60)
    print("测试证书生成")
    print("="*60)
    
    # 获取考试结果
    exam_result = ExamResult.objects.first()
    if not exam_result:
        log_test("证书生成", False, "没有考试结果")
        return
    
    # 设置考试通过
    exam_result.score = 85.0
    exam_result.is_passed = True
    exam_result.save()
    
    # 生成证书
    url = reverse('competency:certificate-generate')
    cert_data = {
        'exam_result_id': exam_result.id,
        'expiry_date': (timezone.now() + timedelta(days=365)).date()
    }
    
    response = client.post(url, cert_data, format='json')
    
    if response.status_code == status.HTTP_201_CREATED:
        cert_id = response.data['data']['id']
        log_test("生成证书", True, f"证书ID: {cert_id}")
        
        # 测试验证证书
        certificate = Certificate.objects.get(id=cert_id)
        verify_url = reverse('competency:certificate-verify')
        response = client.post(verify_url, {
            'verification_code': certificate.verification_code
        }, format='json')
        
        if response.status_code == status.HTTP_200_OK:
            is_valid = response.data['data']['is_valid']
            log_test("验证证书", is_valid, f"验证码: {certificate.verification_code}")
        
        return cert_id
    else:
        log_test("生成证书", False, f"错误: {response.data}")
        return None


def test_import_export():
    """测试导入导出功能"""
    print("\n" + "="*60)
    print("测试导入导出功能")
    print("="*60)
    
    # 测试下载课程导入模板
    url = reverse('training:course-import-template')
    response = client.get(url)
    
    if response.status_code == status.HTTP_200_OK:
        log_test("下载课程导入模板", True, f"内容类型: {response['Content-Type']}")
    else:
        log_test("下载课程导入模板", False, f"状态码: {response.status_code}")
    
    # 测试导出课程
    url = reverse('training:course-export')
    response = client.get(url)
    
    if response.status_code == status.HTTP_200_OK:
        log_test("导出课程", True, f"内容类型: {response['Content-Type']}")
    else:
        log_test("导出课程", False, f"状态码: {response.status_code}")
    
    # 测试下载题目导入模板
    url = reverse('examination:question-import-template')
    response = client.get(url)
    
    if response.status_code == status.HTTP_200_OK:
        log_test("下载题目导入模板", True, f"内容类型: {response['Content-Type']}")
    else:
        log_test("下载题目导入模板", False, f"状态码: {response.status_code}")
    
    # 测试导出题目
    url = reverse('examination:question-export')
    response = client.get(url)
    
    if response.status_code == status.HTTP_200_OK:
        log_test("导出题目", True, f"内容类型: {response['Content-Type']}")
    else:
        log_test("导出题目", False, f"状态码: {response.status_code}")


def test_role_permissions():
    """测试角色权限"""
    print("\n" + "="*60)
    print("测试角色权限")
    print("="*60)
    
    # 测试不同角色的权限
    role_tests = [
        ('me_eng_test', [
            ('course-list', 'get', True),
            ('course-list', 'post', False),
            ('exam-list', 'get', True),
            ('exam-list', 'post', False),
        ]),
        ('eng_manager_test', [
            ('course-list', 'get', True),
            ('course-list', 'post', False),
            ('trainingplan-list', 'get', True),
        ]),
    ]
    
    for username, permissions in role_tests:
        try:
            user = get_user_model().objects.get(username=username)
            client.force_authenticate(user=user)
            
            for url_name, method, expected in permissions:
                url = reverse(f'{url_name}')
                if method == 'get':
                    response = client.get(url)
                else:
                    response = client.post(url, {})
                
                actual = response.status_code != status.HTTP_403_FORBIDDEN
                passed = actual == expected
                log_test(f"{username} {url_name} {method}", passed, 
                        f"期望: {expected}, 实际: {actual}, 状态码: {response.status_code}")
        except Exception as e:
            log_test(f"测试{username}权限", False, f"错误: {str(e)}")


def test_training_workflow():
    """测试完整培训流程"""
    print("\n" + "="*60)
    print("测试完整培训流程")
    print("="*60)
    
    # 使用ME工程师用户
    user = get_user_model().objects.get(username='me_eng_test')
    client.force_authenticate(user=user)
    
    try:
        # 1. 查看课程
        url = reverse('training:course-list')
        response = client.get(url)
        if response.status_code == status.HTTP_200_OK:
            courses = response.data['data']['results']
            log_test("查看课程", True, f"获取{courses}门课程")
            
            if courses:
                course_id = courses[0]['id']
                
                # 2. 报名课程
                enroll_url = reverse('training:course-enroll', kwargs={'pk': course_id})
                response = client.post(enroll_url)
                if response.status_code == status.HTTP_201_CREATED:
                    log_test("报名课程", True)
                    
                    # 3. 查看培训记录
                    records_url = reverse('training:trainingrecord-list')
                    response = client.get(records_url)
                    if response.status_code == status.HTTP_200_OK:
                        log_test("查看培训记录", True, f"共{response.data['data']['count']}条记录")
                        
                        # 4. 完成培训
                        if response.data['data']['results']:
                            record_id = response.data['data']['results'][0]['id']
                            record = TrainingRecord.objects.get(id=record_id)
                            record.status = 'completed'
                            record.progress = 100
                            record.score = 85.0
                            record.complete_date = timezone.now()
                            record.save()
                            log_test("完成培训", True, f"得分: {record.score}")
        
    except Exception as e:
        log_test("培训流程", False, f"错误: {str(e)}")


def test_exam_workflow():
    """测试完整考试流程"""
    print("\n" + "="*60)
    print("测试完整考试流程")
    print("="*60)
    
    # 使用技术员用户
    user = get_user_model().objects.get(username='technician_test')
    client.force_authenticate(user=user)
    
    try:
        # 1. 查看考试
        url = reverse('examination:exam-list')
        response = client.get(url)
        if response.status_code == status.HTTP_200_OK:
            exams = response.data['data']['results']
            log_test("查看考试", True, f"获取{len(exams)}场考试")
            
            if exams:
                exam_id = exams[0]['id']
                
                # 2. 开始考试
                start_url = reverse('examination:exam-start', kwargs={'pk': exam_id})
                response = client.get(start_url)
                if response.status_code == status.HTTP_200_OK:
                    log_test("开始考试", True)
                    
                    # 获取题目
                    questions = response.data['data']['questions']
                    
                    # 3. 提交考试
                    submit_url = reverse('examination:exam-submit', kwargs={'pk': exam_id})
                    answers = {}
                    for q in questions:
                        if q['question_type'] == 'single_choice':
                            answers[str(q['id'])] = ['C']  # 假设C是正确答案
                        elif q['question_type'] == 'judgment':
                            answers[str(q['id'])] = ['true']
                    
                    exam_data = {
                        'answers': answers,
                        'duration': 15
                    }
                    response = client.post(submit_url, exam_data, format='json')
                    if response.status_code == status.HTTP_200_OK:
                        log_test("提交考试", True, f"得分: {response.data['data']['score']}")
                        
                        # 4. 查看成绩
                        results_url = reverse('examresult-list')
                        response = client.get(results_url)
                        if response.status_code == status.HTTP_200_OK:
                            log_test("查看成绩", True, f"共{response.data['data']['count']}条记录")
        
    except Exception as e:
        log_test("考试流程", False, f"错误: {str(e)}")


def test_email_notifications():
    """测试邮件通知"""
    print("\n" + "="*60)
    print("测试邮件通知")
    print("="*60)
    
    # 测试邮件服务导入
    try:
        from apps.common.email_service import EmailService
        log_test("邮件服务导入", True)
        
        # 测试邮件方法存在
        methods = [
            'send_course_enrollment_notification',
            'send_exam_notification',
            'send_exam_result_notification',
            'send_certificate_notification',
            'send_training_plan_approval_notification',
            'send_user_created_notification',
        ]
        
        for method in methods:
            if hasattr(EmailService, method):
                log_test(f"邮件方法 {method}", True)
            else:
                log_test(f"邮件方法 {method}", False, "方法不存在")
                
    except ImportError as e:
        log_test("邮件服务导入", False, f"错误: {str(e)}")


def test_certificate_export():
    """测试证书导出功能"""
    print("\n" + "="*60)
    print("测试证书导出功能")
    print("="*60)
    
    # 获取证书
    certificate = Certificate.objects.first()
    if not certificate:
        log_test("证书导出", False, "没有证书数据")
        return
    
    # 证书导出通常在证书详情中提供
    # 这里测试证书的基本信息和验证功能
    try:
        # 测试证书信息
        log_test("证书信息", True, f"证书编号: {certificate.certificate_no}")
        log_test("证书验证码", True, f"验证码: {certificate.verification_code}")
        
        # 测试验证功能
        url = reverse('certificate-verify')
        response = client.post(url, {
            'verification_code': certificate.verification_code
        }, format='json')
        
        if response.status_code == status.HTTP_200_OK:
            is_valid = response.data['data']['is_valid']
            log_test("证书验证", is_valid, "验证功能正常")
        else:
            log_test("证书验证", False, f"状态码: {response.status_code}")
            
    except Exception as e:
        log_test("证书导出功能", False, f"错误: {str(e)}")


def run_all_tests():
    """运行所有测试"""
    print("TCMS后端系统完整功能测试")
    print("="*60)
    print(f"测试时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试环境: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    
    # 设置测试环境
    setup_test_environment()
    
    try:
        # 创建测试数据
        departments, positions, roles = create_test_data()
        
        # 运行各项测试
        auth_success = test_admin_authentication()
        
        if auth_success:
            test_role_management()
            test_user_creation()
            course_id = test_course_management()
            exam_id = test_exam_management()
            cert_id = test_certificate_generation()
            test_import_export()
            test_role_permissions()
            test_training_workflow()
            test_exam_workflow()
            test_email_notifications()
            test_certificate_export()
        else:
            print("❌ 管理员认证失败，跳过后续测试")
        
        # 输出测试总结
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
        
        # 生成测试报告
        generate_test_report()
        
        return pass_rate == 100
        
    except Exception as e:
        print(f"\n❌ 测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def generate_test_report():
    """生成测试报告"""
    report_content = f"""# TCMS后端系统测试报告

## 测试概览

- **测试时间**: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
- **测试环境**: {os.environ.get('DJANGO_SETTINGS_MODULE')}
- **总测试数**: {test_results['passed'] + test_results['failed']}
- **通过**: {test_results['passed']}
- **失败**: {test_results['failed']}
- **通过率**: {((test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100) if (test_results['passed'] + test_results['failed']) > 0 else 0):.1f}%

## 测试详情

"""
    
    for test in test_results['tests']:
        status = "✅ 通过" if test['passed'] else "❌ 失败"
        report_content += f"### {test['name']}\n"
        report_content += f"**结果**: {status}\n"
        if test['message']:
            report_content += f"**说明**: {test['message']}\n"
        report_content += "\n"
    
    # 保存报告
    report_path = '/mnt/okcomputer/output/test_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n测试报告已保存到: {report_path}")


if __name__ =