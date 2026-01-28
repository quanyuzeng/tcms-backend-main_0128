#!/usr/bin/env python
"""Simple test script for TCMS Backend"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test.utils import setup_test_environment
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.users.models import Role
from apps.organization.models import Department, Position
from apps.training.models import Course, CourseCategory

# 设置测试环境
setup_test_environment()
client = APIClient()

def test_basic_functionality():
    """测试基本功能"""
    print("TCMS后端系统基本功能测试")
    print("="*60)
    
    passed = 0
    failed = 0
    
    try:
        # 1. 测试角色存在
        print("\n1. 测试角色系统")
        expected_roles = ['admin', 'engineering_manager', 'me_engineer', 'te_engineer', 'technician', 'production_operator']
        existing_roles = Role.objects.filter(code__in=expected_roles)
        found_roles = [role.code for role in existing_roles]
        
        for role_code in expected_roles:
            if role_code in found_roles:
                print(f"✅ 角色 {role_code} 存在")
                passed += 1
            else:
                print(f"❌ 角色 {role_code} 不存在")
                failed += 1
        
        # 2. 创建测试用户
        print("\n2. 创建测试用户")
        admin_role = Role.objects.get(code='admin')
        admin_user, created = get_user_model().objects.get_or_create(
            username='test_admin',
            defaults={
                'real_name': '测试管理员',
                'email': 'test_admin@test.com',
                'employee_id': 'TEST001',
                'role': admin_role
            }
        )
        if created:
            admin_user.set_password('test123456')
            admin_user.save()
            print("✅ 创建测试管理员用户")
            passed += 1
        else:
            print("✅ 测试管理员用户已存在")
            passed += 1
        
        # 3. 测试认证
        print("\n3. 测试认证系统")
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(admin_user)
        access_token = str(refresh.access_token)
        print(f"✅ 生成JWT Token成功: {access_token[:20]}...")
        passed += 1
        
        # 设置认证
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 4. 测试课程分类
        print("\n4. 测试课程管理")
        category, created = CourseCategory.objects.get_or_create(
            name='技术培训',
            defaults={'code': 'TECH'}
        )
        
        # 测试创建课程 - 直接创建对象，避免reverse
        course_data = {
            'code': 'TEST_COURSE_001',
            'title': '测试课程',
            'description': '测试课程描述',
            'category': category,
            'course_type': 'online',
            'duration': 60,
            'credit': 1.0,
            'status': 'published'
        }
        
        try:
            # 直接创建课程对象
            course = Course.objects.create(
                code=course_data['code'],
                title=course_data['title'],
                description=course_data['description'],
                category=category,
                course_type=course_data['course_type'],
                duration=course_data['duration'],
                credit=course_data['credit'],
                created_by=admin_user
            )
            print(f"✅ 创建课程成功: {course.title}")
            passed += 1
        except Exception as e:
            print(f"❌ 创建课程失败: {str(e)}")
            failed += 1
        
        # 5. 测试邮件服务
        print("\n5. 测试邮件服务")
        try:
            from apps.common.email_service import EmailService
            print("✅ 邮件服务导入成功")
            
            # 检查邮件方法
            methods = [
                'send_course_enrollment_notification',
                'send_exam_result_notification',
                'send_certificate_notification',
            ]
            
            for method in methods:
                if hasattr(EmailService, method):
                    print(f"✅ 邮件方法 {method} 存在")
                    passed += 1
                else:
                    print(f"❌ 邮件方法 {method} 不存在")
                    failed += 1
                    
        except ImportError as e:
            print(f"❌ 邮件服务导入失败: {str(e)}")
            failed += 1
        
        # 6. 测试证书生成
        print("\n6. 测试证书功能")
        try:
            from apps.competency.models import Certificate, Competency
            
            # 创建能力
            competency, created = Competency.objects.get_or_create(
                name='设备操作',
                defaults={
                    'code': 'EQUIP_OP',
                    'level': 'proficient',
                    'created_by': admin_user
                }
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
            
            print(f"✅ 证书生成成功: {certificate.certificate_no}")
            print(f"✅ 证书验证码: {certificate.verification_code}")
            passed += 2
            
        except Exception as e:
            print(f"❌ 证书生成失败: {str(e)}")
            failed += 2
        
        # 测试总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        total = passed + failed
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {(passed/total*100) if total > 0 else 0:.1f}%")
        
        if failed == 0:
            print("\n✅ 所有测试通过!")
            return True
        else:
            print(f"\n⚠️ 有 {failed} 个测试失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)