# TCMS 后端部署指南

## 环境要求

### 系统环境
- **操作系统**: Linux (推荐 Ubuntu 20.04+)
- **Python**: 3.9+
- **MySQL**: 8.0+
- **Redis**: 6.0+

### Python 依赖
```bash
pip install -r requirements.txt
```

## 部署步骤

### 1. 环境准备

#### 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip
sudo apt install mysql-server redis-server
sudo apt install libmysqlclient-dev

# 安装 Pillow 依赖
sudo apt install libjpeg-dev libpng-dev libfreetype6-dev
```

#### 创建项目目录
```bash
mkdir -p /opt/tcms-backend
cd /opt/tcms-backend
```

### 2. 代码部署

#### 上传代码
将项目代码上传到 `/opt/tcms-backend` 目录

#### 创建虚拟环境
```bash
python3.9 -m venv venv
source venv/bin/activate
```

#### 安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 数据库配置

#### 创建数据库
```sql
CREATE DATABASE tcms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tcms_user'@'localhost' IDENTIFIED BY '12345678';
GRANT ALL PRIVILEGES ON tcms_db.* TO 'tcms_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 创建超级用户
```bash
python manage.py createsuperuser
```

### 4. 配置文件

#### 创建环境变量文件
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
DEBUG=False
SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.production

# Database
DB_NAME=tcms_db
DB_USER=tcms_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_ACCESS_TOKEN_LIFETIME=30
JWT_REFRESH_TOKEN_LIFETIME=10080

# CORS
FRONTEND_URL=https://your-frontend-domain.com

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

### 5. 静态文件和媒体文件

#### 收集静态文件
```bash
python manage.py collectstatic --noinput
```

#### 创建媒体文件目录
```bash
mkdir -p media/avatars
mkdir -p media/courses
mkdir -p media/certificates
```

#### 设置权限
```bash
chown -R www-data:www-data /opt/tcms-backend
chmod -R 755 /opt/tcms-backend
```

### 6. Gunicorn 配置

#### 安装 Gunicorn
```bash
pip install gunicorn
```

#### 创建启动脚本
创建 `start.sh`:
```bash
#!/bin/bash
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production
exec gunicorn config.wsgi:application \
    --name tcms \
    --bind 0.0.0.0:8080 \
    --workers 4 \
    --timeout 300 \
    --log-level=info \
    --log-file=- \
    --access-logfile=- \
    --error-logfile=-
```

#### 创建停止脚本
创建 `stop.sh`:
```bash
#!/bin/bash
pkill -f gunicorn
```

设置执行权限：
```bash
chmod +x start.sh stop.sh
```

### 7. Nginx 配置

#### 安装 Nginx
```bash
sudo apt install nginx
```

#### 创建配置文件
创建 `/etc/nginx/sites-available/tcms`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 静态文件
    location /static/ {
        alias /opt/tcms-backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 媒体文件
    location /media/ {
        alias /opt/tcms-backend/media/;
        expires 30d;
        add_header Cache-Control "public";
    }
    
    # API 代理
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

#### 启用站点
```bash
sudo ln -s /etc/nginx/sites-available/tcms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. 系统服务配置

#### 创建 systemd 服务
创建 `/etc/systemd/system/tcms.service`:
```ini
[Unit]
Description=TCMS Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/tcms-backend
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/opt/tcms-backend/venv/bin/gunicorn config.wsgi:application --name tcms --bind 0.0.0.0:8080 --workers 4 --timeout 300 --log-level=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl start tcms
sudo systemctl enable tcms
```

### 9. Celery 配置（可选）

#### 创建 Celery 服务
创建 `/etc/systemd/system/tcms-celery.service`:
```ini
[Unit]
Description=Celery Service for TCMS
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/tcms-backend
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/opt/tcms-backend/venv/bin/celery -A config worker -l info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 启动 Celery
```bash
sudo systemctl daemon-reload
sudo systemctl start tcms-celery
sudo systemctl enable tcms-celery
```

### 10. 数据库备份

#### 创建备份脚本
创建 `backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/tcms"
mkdir -p $BACKUP_DIR

# 备份数据库
mysqldump -u tcms_user -p'your_password' tcms_db > $BACKUP_DIR/tcms_db_$DATE.sql

# 备份媒体文件
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /opt/tcms-backend/media/

# 删除7天前的备份
find $BACKUP_DIR -type f -mtime +7 -delete
```

设置定时任务：
```bash
chmod +x backup.sh
sudo crontab -e
# 添加以下内容，每天凌晨2点备份
0 2 * * * /opt/tcms-backend/backup.sh
```

## 监控与日志

### 查看日志
```bash
# 应用日志
tail -f /opt/tcms-backend/logs/django.log

# 系统日志
sudo journalctl -u tcms -f
sudo journalctl -u tcms-celery -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 健康检查
创建健康检查端点：
```bash
# 创建 health_check.py
python manage.py health_check
```

## 常见问题

### 1. 数据库连接失败
- 检查 MySQL 服务是否运行
- 检查数据库配置是否正确
- 检查防火墙设置

### 2. 静态文件无法访问
- 检查 Nginx 配置中的静态文件路径
- 确保已运行 collectstatic
- 检查文件权限

### 3. 跨域问题
- 检查 CORS_ALLOWED_ORIGINS 配置
- 确保前端域名已添加到白名单

### 4. JWT Token 失效
- 检查 JWT 配置
- 检查系统时间是否正确

## 性能优化

### 1. 数据库优化
```sql
-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_department ON users(department_id);
CREATE INDEX idx_training_records_user ON training_records(user_id);
CREATE INDEX idx_exam_results_exam ON exam_results(exam_id);
```

### 2. Redis 缓存
```bash
# 安装 Redis
sudo apt install redis-server

# 配置 Redis
sudo nano /etc/redis/redis.conf
# 设置 maxmemory 和 maxmemory-policy

# 重启 Redis
sudo systemctl restart redis
```

### 3. Gunicorn 优化
根据服务器配置调整 workers 数量：
```bash
# 一般建议：workers = CPU核心数 * 2 + 1
workers = 4  # 根据实际CPU核心数调整
```

## 安全建议

### 1. 使用 HTTPS
- 获取 SSL 证书
- 配置 Nginx 使用 HTTPS

### 2. 防火墙配置
```bash
# 只允许必要的端口
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. 定期更新
```bash
# 更新系统
sudo apt update && sudo apt upgrade

# 更新 Python 包
pip install --upgrade -r requirements.txt
```

### 4. 安全扫描
```bash
# 安装安全扫描工具
pip install safety
safety check
```

## 故障排查

### 1. 服务无法启动
```bash
# 检查日志
sudo journalctl -u tcms --no-pager

# 检查端口占用
sudo netstat -tlnp | grep 8080

# 检查配置文件
python manage.py check
```

### 2. 数据库问题
```bash
# 检查数据库连接
mysql -u tcms_user -p -h localhost tcms_db

# 检查数据表
python manage.py showmigrations
python manage.py makemigrations --check
```

### 3. 性能问题
```bash
# 查看系统资源
top
htop

# 查看数据库慢查询
# 启用 MySQL 慢查询日志
```

## 联系支持

如有问题，请联系技术支持团队。

---

**部署完成！** 现在您可以通过前端访问 TCMS 系统了。