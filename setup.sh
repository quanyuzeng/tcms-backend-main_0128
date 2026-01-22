#!/bin/bash
# TCMS Backend Setup Script

echo "=== TCMS Backend Setup ==="

# 1. 创建虚拟环境
echo "Creating virtual environment..."
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 升级 pip
echo "Upgrading pip..."
pip install --upgrade pip

# 4. 安装依赖
echo "Installing dependencies..."
pip install -r requirements.txt

# 5. 创建 .env 文件
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# 6. 创建日志目录
mkdir -p logs

# 7. 运行数据库迁移
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

# 8. 创建超级用户
echo "Creating superuser..."
python manage.py createsuperuser

echo "=== Setup Complete ==="
echo "To start the server, run: ./start.sh"