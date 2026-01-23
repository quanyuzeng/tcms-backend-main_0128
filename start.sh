#!/bin/bash
# TCMS Backend Start Script

# 激活虚拟环境
source venv/bin/activate

# 设置环境变量
export DJANGO_SETTINGS_MODULE=config.settings.development

# 启动 Django 开发服务器
echo "Starting TCMS Backend..."
python manage.py runserver 127.0.0.1:8080