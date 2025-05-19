import functools
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, JWTManager
import logging

logger = logging.getLogger(__name__)

def token_required(f):
    """验证用户身份的装饰器"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        try:
            # 验证JWT令牌
            verify_jwt_in_request()
            # 获取用户ID
            user_id = get_jwt_identity()
            
            # 创建用户对象
            current_user = {'id': user_id}
            
            # 将当前用户传递给被装饰的函数
            return f(current_user, *args, **kwargs)
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': '未授权访问，请先登录'
            }), 401
    return decorated 