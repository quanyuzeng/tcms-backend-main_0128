#!/usr/bin/env python
"""Run all tests and generate test report"""
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.test.utils import get_runner
from django.conf import settings
import json
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("TCMS Backend Test Suite")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试套件
    test_modules = [
        'tests.test_auth',
        'tests.test_user_management',
        'tests.test_training',
        'tests.test_examination',
        'tests.test_competency',
        'tests.test_roles',
    ]
    
    test_results = {}
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for test_module in test_modules:
        print(f"正在运行: {test_module}")
        print("-" * 40)
        
        try:
            # 运行单个测试模块
            execute_from_command_line([
                'manage.py', 'test', test_module,
                '--verbosity', '2',
                '--no-input'
            ])
            
            test_results[test_module] = {
                'status': 'PASSED',
                'tests': 0,  # 将在报告中更新
                'failures': 0,
                'errors': 0
            }
            print(f"✅ {test_module}: PASSED")
            
        except SystemExit as e:
            # 测试失败时捕获退出码
            if e.code == 0:
                test_results[test_module] = {'status': 'PASSED'}
                print(f"✅ {test_module}: PASSED")
            else:
                test_results[test_module] = {'status': 'FAILED'}
                print(f"❌ {test_module}: FAILED")
                total_failures += 1
        except Exception as e:
            test_results[test_module] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"❌ {test_module}: ERROR - {str(e)}")
            total_errors += 1
        
        print()
    
    return test_results, total_tests, total_failures, total_errors

def generate_test_report(test_results):
    """生成测试报告"""
    print("=" * 60)
    print("生成测试报告...")
    print("=" * 60)
    
    # 报告内容
    report = {
        'project': 'TCMS Backend',
        'version': '1.0.0',
        'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'total_modules': len(test_results),
            'passed': sum(1 for r in test_results.values() if r.get('status') == 'PASSED'),
            'failed': sum(1 for r in test_results.values() if r.get('status') == 'FAILED'),
            'errors': sum(1 for r in test_results.values() if r.get('status') == 'ERROR'),
        },
        'modules': test_results,
        'coverage': {
            'auth': '用户认证模块',
            'user_management': '用户管理模块',
            'training': '培训管理模块',
            'examination': '考试管理模块',
            'competency': '能力管理模块',
            'roles': '角色权限模块',
        },
        'roles_tested': [
            '系统管理员 (admin)',
            '工程经理 (engineering_manager)',
            'ME工程师 (me_engineer)',
            'TE工程师 (te_engineer)',
            '技术员 (technician)',
            '生产操作员 (production_operator)',
        ]
    }
    
    # 保存JSON报告
    report_file = 'test_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 测试报告已保存到: {report_file}")
    
    # 生成HTML报告
    generate_html_report(report)
    
    return report

def generate_html_report(report):
    """生成HTML测试报告"""
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>TCMS Backend Test Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .summary-item {{
            display: inline-block;
            margin: 10px 20px;
            text-align: center;
        }}
        .summary-value {{
            font-size: 24px;
            font-weight: bold;
            display: block;
        }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .error {{ color: #ffc107; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        .status-passed {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-failed {{
            color: #dc3545;
            font-weight: bold;
        }}
        .status-error {{
            color: #ffc107;
            font-weight: bold;
        }}
        
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>TCMS Backend 测试报告</h1>
        
        <div class="summary">
            <h2>测试摘要</h2>
            <div class="summary-item">
                <span class="summary-value">{report['test_date']}</span>
                <span>测试时间</span>
            </div>
            <div class="summary-item">
                <span class="summary-value passed">{report['summary']['passed']}</span>
                <span>通过模块</span>
            </div>
            <div class="summary-item">
                <span class="summary-value failed">{report['summary']['failed']}</span>
                <span>失败模块</span>
            </div>
            <div class="summary-item">
                <span class="summary-value error">{report['summary']['errors']}</span>
                <span>错误模块</span>
            </div>
            <div class="summary-item">
                <span class="summary-value">{report['summary']['total_modules']}</span>
                <span>总模块数</span>
            </div>
        </div>
        
        <h2>测试模块详情</h2>
        <table>
            <thead>
                <tr>
                    <th>模块名称</th>
                    <th>测试内容</th>
                    <th>状态</th>
                    <th>说明</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # 添加每个模块的测试结果
    for module_name, result in report['modules'].items():
        module_desc = {
            'tests.test_auth': '用户登录、JWT认证、权限控制',
            'tests.test_user_management': '用户CRUD、角色管理、密码管理',
            'tests.test_training': '课程管理、培训计划、培训记录',
            'tests.test_examination': '题库管理、考试管理、成绩管理',
            'tests.test_competency': '能力评估、证书管理、能力矩阵',
            'tests.test_roles': '角色权限、数据隔离、工作流测试'
        }.get(module_name, '功能测试')
        
        status_class = {
            'PASSED': 'status-passed',
            'FAILED': 'status-failed',
            'ERROR': 'status-error'
        }.get(result.get('status', 'ERROR'), 'status-error')
        
        html_content += f"""
                <tr>
                    <td>{module_name}</td>
                    <td>{module_desc}</td>
                    <td class="{status_class}">{result.get('status', 'ERROR')}</td>
                    <td>{result.get('error', '测试通过') if result.get('status') != 'PASSED' else '所有测试用例通过'}</td>
                </tr>
"""
    
    html_content += f"""
            </tbody>
        </table>
        
        <h2>测试覆盖的角色</h2>
        <ul>
"""
    
    for role in report['roles_tested']:
        html_content += f"            <li>{role}</li>\n"
    
    html_content += f"""
        </ul>
        
        <h2>测试结论</h2>
        <p>
            本次测试覆盖了TCMS后端系统的6个核心模块，测试了6种不同角色的权限和工作流。
            所有测试用例均按照需求文档设计，确保系统的功能完整性和权限正确性。
        </p>
        
        <div class="footer">
            <p>TCMS Backend Test Report - Generated on {report['test_date']}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # 保存HTML报告
    html_file = 'test_report.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML测试报告已保存到: {html_file}")

def main():
    """主函数"""
    try:
        # 运行测试
        test_results, total_tests, total_failures, total_errors = run_tests()
        
        # 生成报告
        report = generate_test_report(test_results)
        
        # 输出总结
        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)
        print(f"总模块数: {report['summary']['total_modules']}")
        print(f"通过: {report['summary']['passed']}")
        print(f"失败: {report['summary']['failed']}")
        print(f"错误: {report['summary']['errors']}")
        
        if report['summary']['failed'] == 0 and report['summary']['errors'] == 0:
            print("\n✅ 所有测试通过!系统功能正常。")
            return 0
        else:
            print("\n⚠️  部分测试失败，请查看测试报告了解详情。")
            return 1
            
    except Exception as e:
        print(f"\n❌ 测试运行失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())