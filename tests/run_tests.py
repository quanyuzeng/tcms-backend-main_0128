#!/usr/bin/env python
"""Test runner script"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# 运行测试
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    # 运行所有测试
    execute_from_command_line(['manage.py', 'test', 'tests', '-v', '2'])