#!/usr/bin/env python
"""Test script for new roles functionality"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test.utils import setup_test_environment
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.users.models import Role
from apps.organization.models import Department, Position
from apps.training.models import Course, CourseCategory, TrainingRecord
from apps.examination.models import QuestionBank, Question, Exam, ExamResult
from apps.competency.models import Competency, Certificate


def test_all_roles():
    """测试所有新角色的功能"""
    print("=" * 60)
    print("测试所有角色功能")
    print("=" * 60)
    
    client = APIClient()
    
    # 创建部门
    eng_dept = Department.objects.create(name='工程部', code='ENG', status='active')
    prod_dept = Department.objects.create(name='生产部', code='PROD', status='active')
    
    # 创建岗位
    me_position = Position.objects.create(name='ME工程师', code='ME', level='mid', status='active')
    te_position = Position.objects.create(name='TE工程师', code='TE', level='mid', status='active')
    technician_position = Position.objects.create(name='技术员', code='TECH', level='junior', status='active')
    
    # 创建角色
    roles_data = [
        ('engineering_manager', '工程经理'),
        ('me_engineer', 'ME工程师'),
        ('te_engineer', 'TE工程师'),
        ('technician', '技术员'),
        ('production_operator', '生产操作员'),
        ('admin', '系统管理员'),
    ]
    
    roles = {}
    for code, name in roles_data:
        roles[code] = Role.objects.get_or_create(code=code, defaults={
            'name': name,
            'status': 'enabled'
        })[0]
    
    # 创建用户
    users_data = [
        ('admin', '管理员', 'ADMIN001', None, None, 'admin'),
        ('eng_manager', '工程经理', 'ENG001', eng_dept, None, 'engineering_manager'),
        ('me_eng', 'ME工程师', 'ME001', eng_dept, me_position, 'me_engineer'),
        ('te_eng', 'TE工程师', 'TE001', eng_dept, te_position, 'te_engineer'),
        ('technician', '技术员', 'TECH001', eng_dept, technician_position, 'technician'),
        ('operator', '生产操作员', 'OP001', prod_dept, None, 'production_operator'),
    ]
    
    users = {}
    for username, real_name, emp_id, dept, pos, role_code in users_data:
        users[username] = get_user_model().objects.get_or_create(
            username=username,
            defaults={
                'password': 'testpass123',
                'real_name': real_name,
                'employee_id': emp_id,
                'email': f'{username}@example.com',
                'role': roles[role_code],
                'department': dept,
                'position': pos
            }
        )[0]
    
    # 创建测试数据
    category = CourseCategory.objects.get_or_create(name='技术培训', code='TECH')[0]
    course = Course.objects.get_or_create(
        code='COURSE001',
        defaults={
            'title': '设备操作培训',
            'category': category,
            'course_type': 'online',
            'duration': 120,
            'status': 'published',
            'created_by': users['admin']
        }
    )[0]
    
    question_bank = QuestionBank.objects.get_or_create(
        name='设备操作题库',
        defaults={'code': 'EQUIP_BANK', 'created_by': users['admin']}
    )[0]
    
    question = Question.objects.get_or_create(
        title='设备启动前需要检查什么？',
        defaults={
            'question_bank': question_bank,
            'question_type': 'single_choice',
            'options': {'options': [{'key': 'A', 'value': '电源'}, {'key': 'B', 'value': '安全装置'}, {'key': 'C', 'value': '以上都是'}]},
            'correct_answer': {'answer': ['C']},
            'score': 2.0,
            'created_by': users['admin']
        }
    )[0]
    
    exam = Exam.objects.get_or_create(
        code='EXAM001',
        defaults={
            'title': '设备操作考试',
            'question_bank': question_bank,
            'total_questions': 1,
            'total_score': 100.0,
            'passing_score': 60.0,
            'time_limit': 30,
            'start_time': timezone.now(),
            'end_time': timezone.now() + timedelta(hours=2),
            'status': 'published',
            'created_by': users['admin']
        }
    )[0]
    exam.participants.add(users['me_eng'], users['te_eng'], users['technician'], users['operator'])
    
    competency = Competency.objects.get_or_create(
        name='设备操作',
        defaults={
            'code': 'EQUIP_OP',
            'level': 'proficient',
            'assessment_method': 'exam',
            'required': True,
            'created_by': users['admin']
        }
    )[0]
    
    test_results = {}
    
    # 测试每个角色
    for username, user in users.items():
        if username == 'admin':
            continue  # 跳过管理员，单独测试
            
        print(f"\n测试角色: {user.real_name} ({username})")
        print("-" * 40)
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        role_tests = {
            'login_access': True,  # 所有角色都可以登录
            'view_courses': False,
            'enroll_courses': False,
            'view_exams': False,
            'take_exams': False,
            'view_training_records': False,
            'view_certificates': False,
            'view_reports': False,
            'create_courses': False,
            'create_exams': False,
            'manage_users': False,
        }
        
        # 根据角色设置预期结果
        if username == 'eng_manager':
            role_tests.update({
                'view_courses': True,
                'view_exams': True,
                'view_training_records': True,
                'view_reports': True,
            })
        elif username in ['me_eng', 'te_eng', 'technician', 'operator']:
            role_tests.update({
                'view_courses': True,
                'enroll_courses': True,
                'view_exams': True,
                'take_exams': True,
                'view_training_records': True,
                'view_certificates': True,
            })
        
        # 执行测试
        passed_tests = 0
        total_tests = len(role_tests)
        
        # 测试查看课程
        url = reverse('course-list')
        response = client.get(url)
        actual = response.status_code == status.HTTP_200_OK
        expected = role_tests['view_courses']
        if actual == expected:
            print(f"✅ 查看课程: {'成功' if actual else '失败(预期)'}")
            passed_tests += 1
        else:
            print(f"❌ 查看课程: 预期{expected}, 实际{actual}")
        
        # 测试报名课程
        url = reverse('course-enroll', kwargs={'pk': course.id})
        response = client.post(url)
        actual = response.status_code == status.HTTP_201_CREATED
        expected = role_tests['enroll_courses']
        if actual == expected:
            print(f"✅ 报名课程: {'成功' if actual else '失败(预期)'}")
            if actual:
                passed_tests += 1
        else:
            print(f"❌ 报名课程: 预期{expected}, 实际{actual}")
        
        # 测试查看考试
        url = reverse('exam-list')
        response = client.get(url)
        actual = response.status_code == status.HTTP_200_OK
        expected = role_tests['view_exams']
        if actual == expected:
            print(f"✅ 查看考试: {'成功' if actual else '失败(预期)'}")
            passed_tests += 1
        else:
            print(f"❌ 查看考试: 预期{expected}, 实际{actual}")
        
        # 测试开始考试
        url = reverse('exam-start', kwargs={'pk': exam.id})
        response = client.get(url)
        actual = response.status_code == status.HTTP_200_OK
        expected = role_tests['take_exams']
        if actual == expected:
            print(f"✅ 开始考试: {'成功' if actual else '失败(预期)'}")
            if actual:
                passed_tests += 1
        else:
            print(f"❌ 开始考试: 预期{expected}, 实际{actual}")
        
        # 测试查看培训记录
        url = reverse('trainingrecord-list')
        response = client.get(url)
        actual = response.status_code == status.HTTP_200_OK
        expected = role_tests['view_training_records']
        if actual == expected:
            print(f"✅ 查看培训记录: {'成功' if actual else '失败(预期)'}")
            passed_tests += 1
        else:
            print(f"❌ 查看培训记录: 预期{expected}, 实际{actual}")
        
        # 测试创建课程（应该失败）
        url = reverse('course-list')
        data = {
            'code': f'TEST_{username}',
            'title': f'测试课程_{username}',
            'category': category.id,
            'course_type': 'online',
            'duration': 60
        }
        response = client.post(url, data, format='json')
        actual = response.status_code == status.HTTP_403_FORBIDDEN
        expected = not role_tests['create_courses']
        if actual == expected:
            print(f"✅ 创建课程权限: {'正确限制' if actual else '错误'}")
            passed_tests += 1
        else:
            print(f"❌ 创建课程权限: 预期{expected}, 实际{actual}")
        
        # 测试创建用户（应该失败）
        url = reverse('user-list')
        data = {
            'username': f'test_{username}',
            'password': 'testpass',
            'real_name': '测试',
            'employee_id': f'TEST_{username.upper()}',
            'email': f'test_{username}@example.com',
            'role': roles['me_engineer'].id
        }
        response = client.post(url, data, format='json')
        actual = response.status_code == status.HTTP_403_FORBIDDEN
        expected = not role_tests['manage_users']
        if actual == expected:
            print(f"✅ 创建用户权限: {'正确限制' if actual else '错误'}")
            passed_tests += 1
        else:
            print(f"❌ 创建用户权限: 预期{expected}, 实际{actual}")
        
        test_results[username] = {
            'role': user.real_name,
            'passed': passed_tests,
            'total': total_tests,
            'rate': f"{(passed_tests/total_tests)*100:.1f}%"
        }
        
        print(f"测试结果: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
    
    # 测试管理员
    print(f"\n测试角色: 系统管理员")
    print("-" * 40)
    
    admin = users['admin']
    client = APIClient()
    client.force_authenticate(user=admin)
    
    # 管理员应该可以创建用户
    url = reverse('user-list')
    data = {
        'username': 'new_admin_test',
        'password': 'testpass123',
        'real_name': '新管理员测试',
        'employee_id': 'ADMIN_TEST',
        'email': 'admin_test@example.com',
        'role': roles['admin'].id
    }
    response = client.post(url, data, format='json')
    
    if response.status_code == status.HTTP_201_CREATED:
        print("✅ 管理员创建用户: 成功")
        test_results['admin'] = {'role': '系统管理员', 'passed': 1, 'total': 1, 'rate': '100.0%'}
    else:
        print(f"❌ 管理员创建用户: 失败 ({response.status_code})")
        test_results['admin'] = {'role': '系统管理员', 'passed': 0, 'total': 1, 'rate': '0.0%'}
    
    # 输出测试汇总
    print("\n" + "=" * 60)
    print("角色功能测试汇总")
    print("=" * 60)
    
    total_passed = 0
    total_tests = 0
    
    for username, result in test_results.items():
        status = "✅ 通过" if result['passed'] == result['total'] else "❌ 部分失败"
        print(f"{result['role']:20s} ({username:15s}): {result['passed']:2d}/{result['total']:2d} ({result['rate']:>6s}) - {status}")
        total_passed += result['passed']
        total_tests += result['total']
    
    print("-" * 60)
    print(f"总计: {total_passed}/{total_tests} ({(total_passed/total_tests)*100:.1f}%)")
    
    if total_passed == total_tests:
        print("\n✅ 所有角色测试通过!")
        return True
    else:
        print(f"\n⚠️  {total_tests - total_passed} 个测试失败，请查看详情")
        return False


if __name__ == "__main__":
    try:
        setup_test_environment()
        success = test_all_roles()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)