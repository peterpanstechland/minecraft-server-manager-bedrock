"""认证相关功能"""
from functools import wraps
from flask import jsonify, session, request
from flask_login import current_user

def login_required_api(f):
    """API路由的登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': '未授权访问，请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

def validate_request_data(required_fields):
    """验证请求数据装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json and not request.form:
                return jsonify({'error': '无效的请求格式'}), 400
            
            data = request.get_json(silent=True) or request.form
            missing = [field for field in required_fields if field not in data]
            
            if missing:
                return jsonify({
                    'error': f'缺少必需字段: {", ".join(missing)}'
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
