"""Audit log middleware"""
import json
import time
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .models import AuditLog
from .utils import get_client_ip


class AuditLogMiddleware(MiddlewareMixin):
    """审计日志中间件"""
    
    def process_request(self, request):
        """处理请求前记录开始时间"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """处理响应后记录审计日志"""
        if not getattr(settings, 'AUDIT_LOG_ENABLED', True):
            return response
        
        # 排除不需要记录的路径
        excluded_paths = getattr(settings, 'AUDIT_LOG_EXCLUDED_PATHS', [])
        if any(request.path.startswith(path) for path in excluded_paths):
            return response
        
        # 只记录API请求
        if not request.path.startswith('/api/'):
            return response
        
        try:
            # 获取用户信息
            user = request.user if request.user.is_authenticated else None
            
            # 获取IP地址
            ip_address = get_client_ip(request)
            
            # 计算响应时间
            response_time = 0
            if hasattr(request, '_start_time'):
                response_time = int((time.time() - request._start_time) * 1000)
            
            # 获取请求参数
            request_params = {}
            if request.method == 'GET':
                request_params = dict(request.GET)
            elif request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                try:
                    if request.content_type == 'application/json':
                        request_params = json.loads(request.body.decode('utf-8'))
                    else:
                        request_params = dict(request.POST)
                except:
                    request_params = {}
            
            # 获取响应结果
            response_result = {}
            if hasattr(response, 'data'):
                response_result = response.data
            elif hasattr(response, 'content'):
                try:
                    response_result = json.loads(response.content.decode('utf-8'))
                except:
                    response_result = {}
            
            # 判断操作类型
            action = self._get_action_type(request.method, request.path)
            module = self._get_module(request.path)
            
            # 获取对象信息
            object_type, object_id, object_name = self._get_object_info(request, response)
            
            # 判断状态
            log_status = AuditLog.Status.SUCCESS if response.status_code < 400 else AuditLog.Status.FAILED

            # 获取错误信息
            error_message = ''
            if log_status == AuditLog.Status.FAILED and response_result:
                if isinstance(response_result, dict):
                    error_message = response_result.get('message', '')
                    if not error_message:
                        error_message = response_result.get('detail', '')
            
            # 创建审计日志
            AuditLog.objects.create(
                operator=user,
                operator_name=user.real_name if user else '',
                operator_username=user.username if user else '',
                action=action,
                module=module,
                object_type=object_type,
                object_id=object_id,
                object_name=object_name,
                description=self._get_description(action, module, object_name),
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                request_method=request.method,
                request_path=request.path,
                request_params=request_params,
                response_result=response_result,
                status=log_status,
                error_message=error_message,
                response_time=response_time
            )
            
        except Exception as e:
            # 记录审计日志失败不应该影响正常响应
            if settings.DEBUG:
                print(f"Audit log error: {str(e)}")
        
        return response
    
    def _get_action_type(self, method, path):
        """根据请求方法和路径判断操作类型"""
        method_map = {
            'GET': AuditLog.ActionType.EXPORT if 'export' in path else AuditLog.ActionType.LOGIN if 'login' in path else '',
            'POST': AuditLog.ActionType.CREATE if 'login' not in path and 'logout' not in path else AuditLog.ActionType.LOGIN if 'login' in path else AuditLog.ActionType.LOGOUT,
            'PUT': AuditLog.ActionType.UPDATE,
            'PATCH': AuditLog.ActionType.UPDATE,
            'DELETE': AuditLog.ActionType.DELETE,
        }
        
        # 特殊路径处理
        if 'approve' in path:
            return AuditLog.ActionType.APPROVE
        elif 'import' in path:
            return AuditLog.ActionType.IMPORT
        
        return method_map.get(method, '')
    
    def _get_module(self, path):
        """根据路径获取模块名称"""
        if '/auth/' in path:
            return 'auth'
        elif '/users/' in path:
            return 'users'
        elif '/organization/' in path:
            return 'organization'
        elif '/training/' in path:
            return 'training'
        elif '/examination/' in path:
            return 'examination'
        elif '/competency/' in path:
            return 'competency'
        elif '/reporting/' in path:
            return 'reporting'
        elif '/audit/' in path:
            return 'audit'
        else:
            return 'other'
    
    def _get_object_info(self, request, response):
        """从请求和响应中获取对象信息"""
        object_type = ''
        object_id = ''
        object_name = ''
        
        # 从路径中提取对象类型和ID
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 3:
            object_type = path_parts[1]
            if path_parts[-1].isdigit():
                object_id = path_parts[-1]
        
        # 从响应数据中获取对象名称
        if hasattr(response, 'data') and isinstance(response.data, dict):
            object_name = response.data.get('name', '') or response.data.get('title', '')
        
        return object_type, object_id, object_name
    
    def _get_description(self, action, module, object_name):
        """生成操作描述"""
        action_display = dict(AuditLog.ActionType.choices).get(action, action)
        module_display = {
            'auth': '认证',
            'users': '用户',
            'organization': '组织',
            'training': '培训',
            'examination': '考试',
            'competency': '能力',
            'reporting': '报表',
            'audit': '审计',
        }.get(module, module)
        
        obj_desc = f'"{object_name}"' if object_name else '"未知对象"'
        return f'{action_display}{module_display}{obj_desc}'