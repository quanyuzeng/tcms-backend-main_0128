# TCMS后端系统测试报告

## 测试概览

- **测试时间**: 2026-01-21 08:35:52
- **测试环境**: config.settings.development
- **总测试数**: 25
- **通过**: 11
- **失败**: 14
- **通过率**: 44.0%

## 测试详情

### 管理员登录
**结果**: ✅ 通过
**说明**: 登录成功，获取Token

### 角色列表
**结果**: ❌ 失败
**说明**: 获取失败: 404

### 创建ME工程师用户
**结果**: ❌ 失败
**说明**: 错误: {'code': 400, 'message': '用户创建失败', 'errors': {'username': [ErrorDetail(string='已存在一位使用该名字的用户。', code='unique')], 'employee_id': [ErrorDetail(string='具有 员工编号 的 用户 已存在。', code='unique')], 'email': [ErrorDetail(string='具有 邮箱 的 用户 已存在。', code='unique')]}}

### 创建课程
**结果**: ❌ 失败
**说明**: 错误: {'created_by': [ErrorDetail(string='该字段是必填项。', code='required')]}

### 创建考试
**结果**: ❌ 失败
**说明**: 错误: {'created_by': [ErrorDetail(string='该字段是必填项。', code='required')]}

### 证书生成
**结果**: ❌ 失败
**说明**: 没有考试结果

### 下载课程导入模板
**结果**: ❌ 失败
**说明**: 状态码: 404

### 导出课程
**结果**: ❌ 失败
**说明**: 状态码: 404

### 下载题目导入模板
**结果**: ❌ 失败
**说明**: 状态码: 404

### 导出题目
**结果**: ❌ 失败
**说明**: 状态码: 404

### me_eng_test course-list get
**结果**: ❌ 失败
**说明**: 期望: True, 实际: False, 状态码: 403

### me_eng_test course-list post
**结果**: ✅ 通过
**说明**: 期望: False, 实际: False, 状态码: 403

### me_eng_test exam-list get
**结果**: ❌ 失败
**说明**: 期望: True, 实际: False, 状态码: 403

### me_eng_test exam-list post
**结果**: ✅ 通过
**说明**: 期望: False, 实际: False, 状态码: 403

### eng_manager_test course-list get
**结果**: ❌ 失败
**说明**: 期望: True, 实际: False, 状态码: 403

### eng_manager_test course-list post
**结果**: ✅ 通过
**说明**: 期望: False, 实际: False, 状态码: 403

### eng_manager_test trainingplan-list get
**结果**: ❌ 失败
**说明**: 期望: True, 实际: False, 状态码: 403

### 邮件服务导入
**结果**: ✅ 通过

### 邮件方法 send_course_enrollment_notification
**结果**: ✅ 通过

### 邮件方法 send_exam_notification
**结果**: ✅ 通过

### 邮件方法 send_exam_result_notification
**结果**: ✅ 通过

### 邮件方法 send_certificate_notification
**结果**: ✅ 通过

### 邮件方法 send_training_plan_approval_notification
**结果**: ✅ 通过

### 邮件方法 send_user_created_notification
**结果**: ✅ 通过

### 证书导出
**结果**: ❌ 失败
**说明**: 没有证书数据

