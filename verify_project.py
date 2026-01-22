#!/usr/bin/env python
"""Project verification script"""
import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_directory_structure():
    """Check project directory structure"""
    print("=== Checking Directory Structure ===")
    
    required_files = [
        ("manage.py", "Django management script"),
        ("requirements.txt", "Python dependencies"),
        (".env.example", "Environment variables example"),
        ("config/settings/base.py", "Base settings"),
        ("config/settings/development.py", "Development settings"),
        ("config/settings/production.py", "Production settings"),
        ("config/urls.py", "URL configuration"),
        ("config/wsgi.py", "WSGI configuration"),
    ]
    
    apps = ["users", "organization", "training", "examination", "competency", "reporting", "audit"]
    
    app_files = [
        ("__init__.py", "App package"),
        ("apps.py", "App configuration"),
        ("models.py", "Data models"),
        ("serializers.py", "API serializers"),
        ("views.py", "API views"),
        ("urls.py", "URL routing"),
    ]
    
    all_exists = True
    
    # Check root files
    for filepath, description in required_files:
        exists = check_file_exists(filepath, description)
        all_exists = all_exists and exists
    
    # Check app files
    for app in apps:
        print(f"\n--- Checking {app} app ---")
        for filename, description in app_files:
            filepath = f"apps/{app}/{filename}"
            exists = check_file_exists(filepath, description)
            all_exists = all_exists and exists
    
    # Special check for users app
    users_special = [
        ("apps/users/permissions.py", "Permission classes"),
        ("apps/users/urls/auth.py", "Auth URLs"),
        ("apps/users/urls/user.py", "User URLs"),
        ("apps/users/views/auth.py", "Auth views"),
        ("apps/users/views/user.py", "User views"),
    ]
    
    print("\n--- Checking special files ---")
    for filepath, description in users_special:
        exists = check_file_exists(filepath, description)
        all_exists = all_exists and exists
    
    return all_exists

def check_models():
    """Check if all models are defined"""
    print("\n=== Checking Models ===")
    
    models_info = {
        "users": ["Role", "User"],
        "organization": ["Department", "Position"],
        "training": ["CourseCategory", "Course", "TrainingPlan", "TrainingRecord"],
        "examination": ["QuestionBank", "Question", "Exam", "ExamResult"],
        "competency": ["Competency", "CompetencyAssessment", "Certificate"],
        "reporting": ["ReportTemplate", "GeneratedReport"],
        "audit": ["AuditLog"],
    }
    
    total_models = sum(len(models) for models in models_info.values())
    print(f"Expected models: {total_models}")
    
    # Check models.py files exist and contain model classes
    for app, models in models_info.items():
        models_file = f"apps/{app}/models.py"
        if os.path.exists(models_file):
            with open(models_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for model in models:
                    if f"class {model}" in content:
                        print(f"✅ {app}.{model}: defined")
                    else:
                        print(f"❌ {app}.{model}: NOT FOUND")
                        return False
        else:
            print(f"❌ {app}/models.py: NOT FOUND")
            return False
    
    return True

def check_urls():
    """Check URL configurations"""
    print("\n=== Checking URLs ===")
    
    url_files = [
        "config/urls.py",
        "apps/users/urls/auth.py",
        "apps/users/urls/user.py",
        "apps/organization/urls.py",
        "apps/training/urls.py",
        "apps/examination/urls.py",
        "apps/competency/urls.py",
        "apps/reporting/urls.py",
        "apps/audit/urls.py",
    ]
    
    all_exists = True
    for filepath in url_files:
        exists = check_file_exists(filepath, "URL config")
        all_exists = all_exists and exists
    
    return all_exists

def check_documentation():
    """Check documentation files"""
    print("\n=== Checking Documentation ===")
    
    docs = [
        ("README.md", "项目说明文档"),
        ("DEPLOYMENT.md", "部署指南"),
        ("FRONTEND_INTEGRATION.md", "前端对接文档"),
        ("PROJECT_SUMMARY.md", "项目总结文档"),
    ]
    
    all_exists = True
    for filepath, description in docs:
        exists = check_file_exists(filepath, description)
        all_exists = all_exists and exists
    
    return all_exists

def check_scripts():
    """Check utility scripts"""
    print("\n=== Checking Scripts ===")
    
    scripts = [
        ("setup.sh", "项目设置脚本"),
        ("start.sh", "项目启动脚本"),
    ]
    
    all_exists = True
    for filepath, description in scripts:
        exists = check_file_exists(filepath, description)
        if exists and os.access(filepath, os.X_OK):
            print(f"✅ {filepath}: executable")
        elif exists:
            print(f"⚠️  {filepath}: not executable")
        all_exists = all_exists and exists
    
    return all_exists

def main():
    """Main verification function"""
    print("TCMS Backend Project Verification\n")
    print("=" * 50)
    
    # Check directory structure
    structure_ok = check_directory_structure()
    
    # Check models
    models_ok = check_models()
    
    # Check URLs
    urls_ok = check_urls()
    
    # Check documentation
    docs_ok = check_documentation()
    
    # Check scripts
    scripts_ok = check_scripts()
    
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    if all([structure_ok, models_ok, urls_ok, docs_ok, scripts_ok]):
        print("✅ ALL CHECKS PASSED!")
        print("\n项目结构完整，可以进行下一步操作：")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 运行设置脚本: ./setup.sh")
        print("3. 启动服务器: ./start.sh")
        print("4. 运行测试: python manage.py test")
        return 0
    else:
        print("❌ SOME CHECKS FAILED!")
        print("\n请检查上述错误信息，确保所有必需的文件都存在。")
        return 1

if __name__ == "__main__":
    sys.exit(main())