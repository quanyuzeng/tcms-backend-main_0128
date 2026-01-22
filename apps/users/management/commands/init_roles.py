"""Initialize roles and permissions"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import Role


class Command(BaseCommand):
    help = 'Initialize roles and permissions for TCMS'
    
    def handle(self, *args, **options):
        with transaction.atomic():
            # 定义角色权限
            roles_permissions = {
                'admin': {
                    'name': '系统管理员',
                    'permissions': ['*'],
                    'description': '系统管理员，拥有所有权限'
                },
                'hr_manager': {
                    'name': 'HR经理',
                    'permissions': [
                        'user:*', 'department:*', 'position:*',
                        'training:*', 'competency:*', 'report:*'
                    ],
                    'description': 'HR经理，负责人员管理和培训管理'
                },
                'training_manager': {
                    'name': '培训管理员',
                    'permissions': [
                        'course:*', 'training:*', 'training_plan:*',
                        'training_record:*', 'report:training'
                    ],
                    'description': '培训管理员，负责培训课程和计划管理'
                },
                'exam_manager': {
                    'name': '考试管理员',
                    'permissions': [
                        'question_bank:*', 'question:*', 'exam:*',
                        'exam_result:*', 'report:exam'
                    ],
                    'description': '考试管理员，负责考试和题库管理'
                },
                'dept_manager': {
                    'name': '部门经理',
                    'permissions': [
                        'user:read', 'department:read', 'training:read',
                        'training_record:read', 'exam:read', 'exam_result:read',
                        'competency:read', 'report:read'
                    ],
                    'description': '部门经理，查看本部门数据'
                },
                'engineering_manager': {
                    'name': '工程经理',
                    'permissions': [
                        'user:read', 'department:read', 'training:read',
                        'training_record:read', 'exam:read', 'competency:read',
                        'report:read', 'training_plan:approve'
                    ],
                    'description': '工程经理，负责工程技术团队管理'
                },
                'me_engineer': {
                    'name': 'ME工程师',
                    'permissions': [
                        'course:read', 'training:read', 'training_record:*',
                        'exam:take', 'exam_result:read', 'competency:read'
                    ],
                    'description': 'ME工程师（制造工程师），参与培训考试'
                },
                'te_engineer': {
                    'name': 'TE工程师',
                    'permissions': [
                        'course:read', 'training:read', 'training_record:*',
                        'exam:take', 'exam_result:read', 'competency:read'
                    ],
                    'description': 'TE工程师（测试工程师），参与培训考试'
                },
                'technician': {
                    'name': '技术员',
                    'permissions': [
                        'course:read', 'training:read', 'training_record:*',
                        'exam:take', 'exam_result:read', 'competency:read'
                    ],
                    'description': '技术员，参与培训考试'
                },
                'production_operator': {
                    'name': '生产操作员',
                    'permissions': [
                        'course:read', 'training:read', 'training_record:*',
                        'exam:take', 'exam_result:read', 'competency:read'
                    ],
                    'description': '生产操作员，参与基础培训'
                },
                'instructor': {
                    'name': '讲师',
                    'permissions': [
                        'course:*', 'exam:read', 'exam_result:read',
                        'training_record:evaluate'
                    ],
                    'description': '讲师，负责课程开发和培训'
                },
                'employee': {
                    'name': '普通员工',
                    'permissions': [
                        'course:read', 'training:read', 'training_record:own',
                        'exam:take', 'exam_result:own', 'competency:own',
                        'profile:*', 'certificate:own'
                    ],
                    'description': '普通员工，参与培训和考试'
                }
            }
            
            created_count = 0
            updated_count = 0
            
            for code, config in roles_permissions.items():
                role, created = Role.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': config['name'],
                        'description': config['description'],
                        'permissions': {'permissions': config['permissions']}
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created role: {role.name} ({code})')
                    )
                else:
                    # 更新现有角色
                    role.name = config['name']
                    role.description = config['description']
                    role.permissions = {'permissions': config['permissions']}
                    role.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated role: {role.name} ({code})')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nRole initialization completed! '
                    f'Created: {created_count}, Updated: {updated_count}'
                )
            )
            
            # 显示所有角色
            self.stdout.write('\nAll roles:')
            for role in Role.objects.all():
                self.stdout.write(f'  - {role.name} ({role.code})')