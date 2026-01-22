"""Audit utilities"""
import re


def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def mask_sensitive_data(data):
    """脱敏敏感数据"""
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if key.lower() in ['password', 'passwd', 'pwd']:
                masked[key] = '***'
            elif key.lower() in ['phone', 'mobile']:
                masked[key] = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', str(value))
            elif key.lower() in ['id_card', 'idcard', 'identity']:
                masked[key] = re.sub(r'(\d{4})\d{10}(\w{4})', r'\1****\2', str(value))
            else:
                masked[key] = mask_sensitive_data(value)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    else:
        return data


def get_object_changes(old_obj, new_obj):
    """获取对象变更详情"""
    changes = []
    if hasattr(old_obj, '_meta') and hasattr(new_obj, '_meta'):
        for field in old_obj._meta.fields:
            field_name = field.name
            old_value = getattr(old_obj, field_name)
            new_value = getattr(new_obj, field_name)
            if old_value != new_value:
                changes.append({
                    'field': field.verbose_name or field_name,
                    'old': str(old_value),
                    'new': str(new_value)
                })
    return changes