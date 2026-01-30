# '''

# with open('/mnt/kimi/output/run_organization_training_tests.py', 'w', encoding='utf-8') as f:
#     f.write(run_test_content)

# print("✅ 运行脚本已修复，现在会自动检测项目根目录")
# print("\n使用方法（可以在任意目录运行）:")
# print("  python run_organization_training_tests.py")
# print("  python run_organization_training_tests.py OrganizationManagementTests")
# print("  python run_organization_training_tests.py OrganizationManagementTests.test_create_department")

import os
import sys

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 如果脚本在 tests 目录，则切换到项目根目录
if os.path.basename(script_dir) == 'tests':
    project_root = os.path.dirname(script_dir)
else:
    project_root = script_dir

# 切换到项目根目录
os.chdir(project_root)

# 将项目根目录添加到 Python 路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    # 运行组织管理和课程管理测试
    test_module = 'tests.test_organization_and_training'
    
    if len(sys.argv) > 1:
        # 如果指定了特定测试类或方法
        test_module = f"{test_module}.{sys.argv[1]}"
    
    execute_from_command_line(['manage.py', 'test', test_module, '-v', '2'])
