# TCMS Backend

Training & Competency Management System - 培训与岗位能力管理系统后端

## 项目概述

TCMS 是一个完整的培训与岗位能力管理系统，采用现代化的技术栈开发，提供完整的培训生命周期管理、能力评估、考试认证和合规审计功能。

## 技术栈

- **后端框架**: Django 4.2+
- **API框架**: Django REST Framework 3.14+
- **认证**: JWT (djangorestframework-simplejwt)
- **数据库**: MySQL 8.0+
- **缓存**: Redis 6.0+
- **任务队列**: Celery + Redis
- **文件存储**: MinIO / AWS S3

## 项目结构

```
tcms-backend/
├── apps/                     # Django 应用
│   ├── users/               # 用户管理
│   ├── organization/        # 组织管理
│   ├── training/            # 培训管理
│   ├── examination/         # 考试管理
│   ├── competency/          # 能力管理
│   ├── reporting/           # 报表管理
│   └── audit/               # 审计日志
├── config/                  # 项目配置
│   ├── settings/           # 环境配置
│   ├── urls.py             # URL 配置
│   └── wsgi.py             # WSGI 配置
├── tests/                   # 测试文件
├── requirements.txt         # Python 依赖
├── manage.py               # Django 管理脚本
└── README.md               # 项目说明
```

## 功能模块

### 1. 认证与权限模块
- JWT 登录认证
- 基于角色的访问控制 (RBAC)
- 密码管理
- 用户权限控制

### 2. 用户管理模块
- 用户信息管理
- 角色管理
- 部门与岗位关联
- 用户状态管理

### 3. 组织管理模块
- 部门管理（树形结构）
- 岗位管理
- 组织架构管理

### 4. 培训管理模块
- 课程管理
- 培训计划
- 培训记录
- 学习进度跟踪

### 5. 考试管理模块
- 题库管理
- 考试管理
- 在线考试
- 成绩管理

### 6. 能力管理模块
- 能力库管理
- 能力评估
- 证书管理
- 证书验证

### 7. 报表管理模块
- 培训统计报表
- 考试分析报表
- 能力矩阵报表
- 合规性报表

### 8. 审计日志模块
- 操作日志记录
- 安全审计
- 日志查询与导出

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd tcms-backend
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库等信息
```

### 5. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. 创建超级用户

```bash
python manage.py createsuperuser
```

### 7. 启动开发服务器

```bash
python manage.py runserver
```

服务器将在 http://127.0.0.1:8080 启动

## API 文档

### 认证相关
- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/logout/` - 用户登出
- `GET /api/auth/profile/` - 获取用户信息
- `POST /api/auth/password/change/` - 修改密码
- `POST /api/auth/password/reset/` - 重置密码

### 用户管理
- `GET /api/users/` - 获取用户列表
- `POST /api/users/` - 创建用户
- `GET /api/users/{id}/` - 获取用户详情
- `PUT /api/users/{id}/` - 更新用户
- `DELETE /api/users/{id}/` - 删除用户
- `POST /api/users/{id}/reset-password/` - 重置密码

### 组织管理
- `GET /api/organization/departments/` - 获取部门列表
- `POST /api/organization/departments/` - 创建部门
- `GET /api/organization/positions/` - 获取岗位列表
- `POST /api/organization/positions/` - 创建岗位

### 培训管理
- `GET /api/training/courses/` - 获取课程列表
- `POST /api/training/courses/` - 创建课程
- `GET /api/training/courses/{id}/` - 获取课程详情
- `POST /api/training/courses/{id}/publish/` - 发布课程
- `POST /api/training/courses/{id}/enroll/` - 报名课程
- `GET /api/training/plans/` - 获取培训计划列表
- `POST /api/training/plans/` - 创建培训计划
- `POST /api/training/plans/{id}/approve/` - 审批培训计划
- `GET /api/training/records/` - 获取培训记录
- `POST /api/training/records/{id}/evaluate/` - 评价培训

### 考试管理
- `GET /api/examination/question-banks/` - 获取题库列表
- `POST /api/examination/question-banks/` - 创建题库
- `GET /api/examination/questions/` - 获取题目列表
- `POST /api/examination/questions/import/` - 导入题目
- `GET /api/examination/exams/` - 获取考试列表
- `POST /api/examination/exams/` - 创建考试
- `POST /api/examination/exams/{id}/publish/` - 发布考试
- `POST /api/examination/exams/{id}/submit/` - 提交考试
- `GET /api/examination/exams/{id}/start/` - 开始考试
- `GET /api/examination/results/` - 获取考试成绩
- `POST /api/examination/results/{id}/generate-certificate/` - 生成证书

### 能力管理
- `GET /api/competency/competencies/` - 获取能力列表
- `POST /api/competency/competencies/` - 创建能力
- `GET /api/competency/competencies/tree/` - 获取能力树
- `GET /api/competency/assessments/` - 获取能力评估列表
- `POST /api/competency/assessments/` - 创建能力评估
- `POST /api/competency/assessments/{id}/approve/` - 审批评估
- `GET /api/competency/certificates/` - 获取证书列表
- `POST /api/competency/certificates/generate/` - 生成证书
- `POST /api/competency/certificates/verify/` - 验证证书
- `POST /api/competency/certificates/{id}/revoke/` - 吊销证书

### 报表管理
- `GET /api/reporting/training-statistics/` - 培训统计
- `GET /api/reporting/exam-analysis/` - 考试分析
- `GET /api/reporting/competency-matrix/` - 能力矩阵
- `GET /api/reporting/compliance-report/` - 合规性报表
- `POST /api/reporting/export/` - 导出报表

### 审计日志
- `GET /api/audit/logs/` - 获取审计日志
- `GET /api/audit/logs/summary/` - 获取日志汇总
- `GET /api/audit/logs/export/` - 导出日志

## 测试

### 运行测试

```bash
# 运行所有测试
python manage.py test

# 运行特定测试
python manage.py test tests.test_auth

# 运行测试并显示详细信息
python manage.py test -v 2

# 生成测试覆盖率报告
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### 测试文件

- `tests/test_auth.py` - 认证测试
- `tests/test_user_management.py` - 用户管理测试
- `tests/test_training.py` - 培训管理测试
- `tests/test_examination.py` - 考试管理测试
- `tests/test_competency.py` - 能力管理测试

## 部署

### 开发环境

```bash
# 使用内置开发服务器
python manage.py runserver

# 或使用脚本
./start.sh
```

### 生产环境

详细部署步骤请参考 [DEPLOYMENT.md](DEPLOYMENT.md)

## 前端对接

详细的前端对接说明请参考 [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)

## 数据库设计

### 核心数据表

- `users` - 用户表
- `roles` - 角色表
- `departments` - 部门表
- `positions` - 岗位表
- `courses` - 课程表
- `training_plans` - 培训计划表
- `training_records` - 培训记录表
- `exams` - 考试表
- `exam_results` - 考试成绩表
- `competencies` - 能力表
- `certificates` - 证书表
- `audit_logs` - 审计日志表

详细的数据库设计请参考需求文档。

## 权限控制

### 角色定义

- **系统管理员 (admin)**: 所有权限
- **HR经理 (hr_manager)**: 用户管理、部门管理、培训管理
- **培训管理员 (training_manager)**: 培训管理、课程管理
- **考试管理员 (exam_manager)**: 考试管理、题库管理
- **部门经理 (dept_manager)**: 本部门数据查看、培训参与
- **讲师 (instructor)**: 课程管理、考试查看
- **普通员工 (employee)**: 个人数据查看、培训考试参与

### 权限说明

权限采用细粒度设计，格式为：`模块:操作`

- `*` - 所有权限
- `user:*` - 用户管理所有权限
- `user:read` - 用户查看权限
- `user:write` - 用户写入权限
- `course:read` - 课程查看权限
- `exam:take` - 考试参与权限

## 安全特性

- JWT Token 认证
- 密码哈希存储 (bcrypt)
- 跨域请求控制 (CORS)
- 请求频率限制
- 审计日志记录
- 敏感信息脱敏
- SQL 注入防护
- XSS 防护

## 性能优化

- 数据库查询优化
- Redis 缓存
- 分页查询
- 索引优化
- 静态文件压缩
- CDN 支持

## 国际化

- 支持中英文切换
- 基于 Django 国际化框架
- 前端支持 vue-i18n

## 日志记录

- 应用日志: `logs/django.log`
- 审计日志: 数据库 `audit_logs` 表
- 登录日志: 记录 IP、时间、结果

## 配置说明

### 环境变量

- `DEBUG`: 调试模式
- `SECRET_KEY`: Django 密钥
- `DB_*`: 数据库配置
- `REDIS_URL`: Redis 连接地址
- `FRONTEND_URL`: 前端域名（CORS）

### 配置文件

- `config/settings/base.py` - 基础配置
- `config/settings/development.py` - 开发环境配置
- `config/settings/production.py` - 生产环境配置

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 版本历史

- **v1.0.0** - 初始版本
  - 用户认证与权限管理
  - 组织管理
  - 培训管理
  - 考试管理
  - 能力管理
  - 报表管理
  - 审计日志

## 许可证

MIT License

## 联系方式

如有问题，请联系开发团队。

---

**欢迎使用 TCMS 培训与岗位能力管理系统！**