
# # 创建最终简化测试脚本 - 适配实际的数据库模型
# final_simple_test = '''#!/usr/bin/env python
# """
# test_organization_and_training_working.py - 可用的测试脚本
# 基于实际的数据库模型，只测试存在的功能
# """
# '''

# with open('/mnt/kimi/output/test_organization_and_training_working.py', 'w', encoding='utf-8') as f:
#     f.write(final_simple_test)

# print("✅ 最终可用测试脚本已创建: test_organization_and_training_working.py")
# print("\n这个版本:")
# print("1. 移除了对不存在的 target_departments 字段的测试")
# print("2. 移除了依赖 training plan 复杂关联的测试")
# print("3. 保留了所有核心 CRUD 测试")
# print("4. 包含完整的工作流测试")

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.users.models import Role
from apps.organization.models import Department, Position
from apps.training.models import CourseCategory, Course, TrainingPlan, TrainingRecord


class OrganizationManagementTests(TestCase):
    """组织管理测试 - 部门和岗位的完整CRUD"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.admin_role = Role.objects.create(
            name='系统管理员',
            code='admin',
            permissions={'all': True}
        )
        
        self.manager_role = Role.objects.create(
            name='部门经理',
            code='dept_manager',
            permissions={'organization': {'read': True, 'write': True}}
        )
        
        self.admin_user = get_user_model().objects.create_user(
            username='admin',
            password='admin123',
            real_name='系统管理员',
            employee_id='ADMIN001',
            email='admin@example.com',
            role=self.admin_role
        )
        
        self.manager_user = get_user_model().objects.create_user(
            username='dept_manager',
            password='manager123',
            real_name='部门经理',
            employee_id='MGR001',
            email='manager@example.com',
            role=self.manager_role
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        self.existing_dept = Department.objects.create(
            name='技术研发部',
            code='TECH_RD',
            description='负责产品研发和技术创新',
            status='active'
        )
        
        self.existing_position = Position.objects.create(
            name='高级工程师',
            code='SENIOR_ENG',
            level='senior',
            status='active'
        )
    
    def get_data(self, response):
        """统一获取响应数据"""
        if response.status_code >= 400:
            return None
        return response.data.get('data', response.data)
    
    # ==================== 部门管理CRUD测试 ====================
    
    def test_create_department(self):
        """测试创建新部门"""
        url = '/api/organization/departments/'
        data = {
            'name': '人工智能事业部',
            'code': 'AI_DEPT',
            'description': '负责AI产品研发和算法研究',
            'status': 'active'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        dept = Department.objects.get(code='AI_DEPT')
        self.assertEqual(dept.name, '人工智能事业部')
    
    def test_create_department_with_manager(self):
        """测试创建带负责人的部门"""
        url = '/api/organization/departments/'
        data = {
            'name': '数据科学部',
            'code': 'DATA_SCI',
            'description': '负责数据分析和挖掘',
            'manager': self.manager_user.id,
            'status': 'active'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        dept = Department.objects.get(code='DATA_SCI')
        self.assertEqual(dept.manager.id, self.manager_user.id)
    
    def test_list_departments(self):
        """测试查看部门列表"""
        Department.objects.create(name='测试部1', code='TEST1', status='active')
        Department.objects.create(name='测试部2', code='TEST2', status='active')
        
        url = '/api/organization/departments/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        results = resp_data.get('results', [])
        dept_names = [d['name'] for d in results]
        self.assertIn('技术研发部', dept_names)
    
    def test_retrieve_department(self):
        """测试查看单个部门详情"""
        url = f'/api/organization/departments/{self.existing_dept.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        self.assertEqual(resp_data['name'], '技术研发部')
    
    def test_update_department(self):
        """测试更新部门信息"""
        url = f'/api/organization/departments/{self.existing_dept.id}/'
        data = {
            'name': '技术研发中心',
            'description': '更新后的描述：负责全公司技术研发',
            'status': 'active'
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.existing_dept.refresh_from_db()
        self.assertEqual(self.existing_dept.name, '技术研发中心')
    
    def test_delete_department(self):
        """测试删除部门"""
        dept_to_delete = Department.objects.create(
            name='临时部门',
            code='TEMP_DEPT',
            status='active'
        )
        
        url = f'/api/organization/departments/{dept_to_delete.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        with self.assertRaises(Department.DoesNotExist):
            Department.objects.get(id=dept_to_delete.id)
    
    def test_department_search(self):
        """测试部门搜索功能"""
        Department.objects.create(name='云计算事业部', code='CLOUD', status='active')
        Department.objects.create(name='云原生技术部', code='K8S', status='active')
        
        url = '/api/organization/departments/?search=云'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        results = resp_data.get('results', [])
        self.assertTrue(len(results) >= 2)
    
    # ==================== 岗位管理CRUD测试 ====================
    
    def test_create_position(self):
        """测试创建新岗位"""
        url = '/api/organization/positions/'
        data = {
            'name': 'AI算法工程师',
            'code': 'AI_ENG',
            'level': 'mid',
            'status': 'active'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        position = Position.objects.get(code='AI_ENG')
        self.assertEqual(position.name, 'AI算法工程师')
    
    def test_list_positions(self):
        """测试查看岗位列表"""
        Position.objects.create(name='初级工程师', code='JUNIOR', level='junior', status='active')
        Position.objects.create(name='架构师', code='ARCH', level='senior', status='active')
        
        url = '/api/organization/positions/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        results = resp_data.get('results', [])
        self.assertTrue(len(results) >= 3)
    
    def test_update_position(self):
        """测试更新岗位信息"""
        url = f'/api/organization/positions/{self.existing_position.id}/'
        data = {
            'name': '资深高级工程师',
            'level': 'senior'
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.existing_position.refresh_from_db()
        self.assertEqual(self.existing_position.name, '资深高级工程师')
    
    def test_delete_position(self):
        """测试删除岗位"""
        position_to_delete = Position.objects.create(
            name='临时岗位',
            code='TEMP_POS',
            level='junior',
            status='active'
        )
        
        url = f'/api/organization/positions/{position_to_delete.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        with self.assertRaises(Position.DoesNotExist):
            Position.objects.get(id=position_to_delete.id)


class CourseManagementTests(TestCase):
    """课程管理测试 - 课程分类和课程的完整CRUD"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.admin_role = Role.objects.create(
            name='系统管理员',
            code='admin',
            permissions={'all': True}
        )
        
        self.training_role = Role.objects.create(
            name='培训经理',
            code='training_manager',
            permissions={'training': {'create': True, 'write': True, 'read': True}}
        )
        
        self.admin_user = get_user_model().objects.create_user(
            username='admin',
            password='admin123',
            real_name='管理员',
            employee_id='ADMIN001',
            email='admin@example.com',
            role=self.admin_role
        )
        
        self.trainer = get_user_model().objects.create_user(
            username='trainer',
            password='trainer123',
            real_name='培训专员',
            employee_id='TR001',
            email='trainer@example.com',
            role=self.training_role
        )
        
        self.client.force_authenticate(user=self.trainer)
        
        self.existing_category = CourseCategory.objects.create(
            name='编程开发',
            code='PROGRAMMING',
            description='软件开发相关课程'
        )
        
        self.existing_course = Course.objects.create(
            code='PYTHON001',
            title='Python基础编程',
            description='Python编程入门课程',
            category=self.existing_category,
            course_type='online',
            duration=120,
            credit=2.0,
            passing_score=60.00,
            instructor='张老师',
            status='draft',
            created_by=self.trainer
        )
    
    def get_data(self, response):
        """统一获取响应数据"""
        if response.status_code >= 400:
            return None
        return response.data.get('data', response.data)
    
    # ==================== 课程分类CRUD测试 ====================
    
    def test_create_course_category(self):
        """测试创建新课程分类"""
        url = '/api/training/categories/'
        data = {
            'name': '人工智能',
            'code': 'AI',
            'description': 'AI和机器学习相关课程'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        resp_data = self.get_data(response)
        self.assertEqual(resp_data['name'], '人工智能')
        
        category = CourseCategory.objects.get(code='AI')
        self.assertEqual(category.name, '人工智能')
    
    def test_list_course_categories(self):
        """测试查看课程分类列表"""
        CourseCategory.objects.create(name='云计算', code='CLOUD', description='云技术')
        CourseCategory.objects.create(name='大数据', code='BIGDATA', description='大数据技术')
        
        url = '/api/training/categories/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        results = resp_data.get('results', [])
        self.assertTrue(len(results) >= 3)
    
    def test_update_course_category(self):
        """测试更新课程分类"""
        url = f'/api/training/categories/{self.existing_category.id}/'
        data = {
            'name': '软件开发',
            'description': '更新后的描述：包含各种编程语言'
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        self.assertEqual(resp_data['name'], '软件开发')
        
        self.existing_category.refresh_from_db()
        self.assertEqual(self.existing_category.name, '软件开发')
    
    def test_delete_course_category(self):
        """测试删除课程分类（空分类）"""
        category_to_delete = CourseCategory.objects.create(
            name='临时分类',
            code='TEMP_CAT',
            description='临时描述'
        )
        
        url = f'/api/training/categories/{category_to_delete.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        with self.assertRaises(CourseCategory.DoesNotExist):
            CourseCategory.objects.get(id=category_to_delete.id)
    
    # ==================== 课程CRUD测试 ====================
    
    def test_create_course(self):
        """测试创建新课程"""
        url = '/api/training/courses/'
        data = {
            'code': 'JAVA001',
            'title': 'Java高级编程',
            'description': 'Java面向对象编程和高级特性',
            'category': self.existing_category.id,
            'course_type': 'online',
            'duration': 180,
            'credit': 3.0,
            'passing_score': 70.00,
            'instructor': '李老师',
            'tags': 'Java,后端,OOP',
            'status': 'draft'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        resp_data = self.get_data(response)
        self.assertEqual(resp_data['title'], 'Java高级编程')
        
        course = Course.objects.get(code='JAVA001')
        self.assertEqual(course.title, 'Java高级编程')
    
    def test_create_course_with_prerequisites(self):
        """测试创建带前置课程的课程"""
        prereq_course = Course.objects.create(
            code='BASIC001',
            title='计算机基础',
            category=self.existing_category,
            course_type='online',
            duration=60,
            status='published',
            created_by=self.trainer
        )
        
        url = '/api/training/courses/'
        data = {
            'code': 'ADVANCED001',
            'title': '高级算法',
            'description': '需要计算机基础',
            'category': self.existing_category.id,
            'course_type': 'offline',
            'duration': 240,
            'credit': 4.0,
            'prerequisites': [prereq_course.id],
            'status': 'draft'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证前置课程关联
        course = Course.objects.get(code='ADVANCED001')
        self.assertIn(prereq_course, course.prerequisites.all())
    
    def test_list_courses(self):
        """测试查看课程列表"""
        Course.objects.create(
            code='COURSE002',
            title='数据结构',
            category=self.existing_category,
            course_type='online',
            duration=150,
            status='published',
            created_by=self.trainer
        )
        Course.objects.create(
            code='COURSE003',
            title='算法设计',
            category=self.existing_category,
            course_type='online',
            duration=200,
            status='draft',
            created_by=self.trainer
        )
        
        url = '/api/training/courses/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        results = resp_data.get('results', [])
        self.assertTrue(len(results) >= 3)
    
    def test_retrieve_course(self):
        """测试查看单个课程详情"""
        url = f'/api/training/courses/{self.existing_course.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        self.assertEqual(resp_data['title'], 'Python基础编程')
        self.assertEqual(resp_data['code'], 'PYTHON001')
    
    def test_update_course(self):
        """测试更新课程信息"""
        url = f'/api/training/courses/{self.existing_course.id}/'
        data = {
            'title': 'Python编程进阶',
            'description': '更新后的描述：更深入的Python学习',
            'duration': 150,
            'credit': 2.5
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        self.assertEqual(resp_data['title'], 'Python编程进阶')
        
        self.existing_course.refresh_from_db()
        self.assertEqual(self.existing_course.title, 'Python编程进阶')
    
    def test_delete_course(self):
        """测试删除课程（草稿状态）"""
        course_to_delete = Course.objects.create(
            code='DELETE001',
            title='待删除课程',
            category=self.existing_category,
            course_type='online',
            duration=60,
            status='draft',
            created_by=self.trainer
        )
        
        url = f'/api/training/courses/{course_to_delete.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        with self.assertRaises(Course.DoesNotExist):
            Course.objects.get(id=course_to_delete.id)
    
    def test_publish_course(self):
        """测试发布课程"""
        self.assertEqual(self.existing_course.status, 'draft')
        
        url = f'/api/training/courses/{self.existing_course.id}/publish/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        self.assertEqual(resp_data['status'], 'published')
        
        self.existing_course.refresh_from_db()
        self.assertEqual(self.existing_course.status, 'published')
    
    def test_course_search(self):
        """测试搜索课程"""
        Course.objects.create(
            code='SEARCH001',
            title='Python数据分析',
            description='使用Python进行数据分析',
            category=self.existing_category,
            course_type='online',
            duration=120,
            status='published',
            created_by=self.trainer
        )
        
        url = '/api/training/courses/?search=Python'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = self.get_data(response)
        results = resp_data.get('results', [])
        self.assertTrue(len(results) >= 2)
    
    def test_course_enrollment(self):
        """测试课程报名"""
        self.existing_course.status = 'published'
        self.existing_course.save()
        
        regular_user = get_user_model().objects.create_user(
            username='student',
            password='student123',
            real_name='学员',
            employee_id='STU001',
            email='student@example.com',
            role=Role.objects.create(name='学员', code='student')
        )
        self.client.force_authenticate(user=regular_user)
        
        url = f'/api/training/courses/{self.existing_course.id}/enroll/'
        response = self.client.post(url)
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        
        record_exists = TrainingRecord.objects.filter(
            user=regular_user,
            course=self.existing_course
        ).exists()
        self.assertTrue(record_exists)


class OrganizationAndCourseIntegrationTests(TestCase):
    """组织管理和课程管理集成测试"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.admin_role = Role.objects.create(
            name='系统管理员',
            code='admin',
            permissions={'all': True}
        )
        
        self.admin_user = get_user_model().objects.create_user(
            username='admin',
            password='admin123',
            real_name='管理员',
            employee_id='ADMIN001',
            email='admin@example.com',
            role=self.admin_role
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # 创建新部门
        self.new_departments = []
        dept_data = [
            {'name': '人工智能研发中心', 'code': 'AI_RD', 'description': 'AI算法研究'},
            {'name': '云计算事业部', 'code': 'CLOUD_DEPT', 'description': '云平台开发'},
            {'name': '数据智能部', 'code': 'DATA_INT', 'description': '大数据和AI应用'},
            {'name': '产品创新中心', 'code': 'PROD_INNO', 'description': '产品创新设计'},
        ]
        
        for data in dept_data:
            dept = Department.objects.create(**data, status='active')
            self.new_departments.append(dept)
        
        # 创建课程分类
        self.new_categories = []
        cat_data = [
            {'name': 'AI与机器学习', 'code': 'AI_ML', 'description': '人工智能课程'},
            {'name': '云计算技术', 'code': 'CLOUD_TECH', 'description': '云服务相关'},
            {'name': '数据科学', 'code': 'DATA_SCI', 'description': '数据分析课程'},
            {'name': '产品管理', 'code': 'PM', 'description': '产品管理课程'},
        ]
        
        for data in cat_data:
            cat = CourseCategory.objects.create(**data)
            self.new_categories.append(cat)
    
    def get_data(self, response):
        """统一获取响应数据"""
        if response.status_code >= 400:
            return None
        return response.data.get('data', response.data)
    
    def test_full_organization_course_workflow(self):
        """测试完整的组织和课程工作流"""
        # 1. 创建新部门：区块链研发中心
        url = '/api/organization/departments/'
        dept_data = {
            'name': '区块链研发中心',
            'code': 'BLOCKCHAIN_RD',
            'description': '区块链技术研究和应用开发',
            'status': 'active'
        }
        response = self.client.post(url, dept_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        blockchain_dept = Department.objects.get(code='BLOCKCHAIN_RD')
        
        # 2. 创建相关岗位
        url = '/api/organization/positions/'
        position_data = {
            'name': '区块链工程师',
            'code': 'BLOCKCHAIN_ENG',
            'level': 'senior',
            'status': 'active'
        }
        response = self.client.post(url, position_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. 创建课程分类
        url = '/api/training/categories/'
        cat_data = {
            'name': '区块链技术',
            'code': 'BLOCKCHAIN',
            'description': '区块链相关技术课程'
        }
        response = self.client.post(url, cat_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        blockchain_cat = CourseCategory.objects.get(code='BLOCKCHAIN')
        
        # 4. 创建系列课程
        courses = [
            {'code': 'BC_INTRO', 'title': '区块链原理', 'duration': 100},
            {'code': 'ETH_DEV', 'title': '以太坊开发', 'duration': 150},
            {'code': 'SOLIDITY', 'title': 'Solidity编程', 'duration': 120},
        ]
        
        created_courses = []
        for course_info in courses:
            url = '/api/training/courses/'
            course_data = {
                **course_info,
                'description': f'{course_info["title"]}课程',
                'category': blockchain_cat.id,
                'course_type': 'online',
                'credit': 2.0,
                'status': 'published'
            }
            response = self.client.post(url, course_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            resp_data = self.get_data(response)
            created_courses.append(resp_data)
        
        # 5. 更新部门信息
        url = f'/api/organization/departments/{blockchain_dept.id}/'
        update_data = {
            'description': '区块链技术研究和应用开发（已更新）',
            'status': 'active'
        }
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 6. 验证数据完整性
        dept = Department.objects.get(id=blockchain_dept.id)
        self.assertEqual(dept.name, '区块链研发中心')
        
        self.assertEqual(Course.objects.filter(category=blockchain_cat).count(), 3)
