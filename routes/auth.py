from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from database import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 验证必要字段
    if not data or 'password' not in data:
        return jsonify({'success': False, 'message': '密码不能为空'}), 400
    
    # 验证至少提供了一种身份标识
    if not any(key in data for key in ('username', 'email', 'phone')):
        return jsonify({'success': False, 'message': '请至少提供用户名、邮箱或手机号码中的一种'}), 400
    
    # 处理注册
    result, status_code = AuthService.register(
        username=data.get('username'),
        email=data.get('email'),
        phone=data.get('phone'),
        password=data.get('password'),
        birth_date=data.get('birth_date'),
        gender=data.get('gender'),
        height=data.get('height'),
        weight=data.get('weight')
    )
    
    return jsonify(result), status_code

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    # 适配多种前端可能的字段名
    identifier = None
    password = None
    
    if not data:
        return jsonify({'success': False, 'message': '请提供登录信息'}), 400
    
    # 尝试从请求中提取识别信息和密码
    if 'identifier' in data:
        identifier = data['identifier']
    elif 'username' in data:
        identifier = data['username']
    elif 'email' in data:
        identifier = data['email']
    elif 'phone' in data:
        identifier = data['phone']
    
    if 'password' in data:
        password = data['password']
    
    # 验证是否提供了必要的信息
    if not identifier:
        return jsonify({'success': False, 'message': '请提供用户名、邮箱或手机号'}), 400
    
    if not password:
        return jsonify({'success': False, 'message': '请提供密码'}), 400
    
    # 处理登录
    result, status_code = AuthService.login(
        identifier=identifier,
        password=password
    )

    # 确保登录成功时返回完整用户信息
    if status_code == 200 and 'token' in result:
        # 打印登录成功日志
        print(f"用户 {identifier} 登录成功")
        
        # 检查返回结果是否包含用户信息
        if 'user' not in result or not result['user']:
            # 如果返回中缺少用户信息，尝试获取完整用户信息
            try:
                user = None
                # 按标识符类型查找用户
                if '@' in identifier:  # 邮箱格式
                    user = User.query.filter_by(email=identifier).first()
                elif identifier.isdigit() and len(identifier) > 5:  # 看起来像手机号码
                    user = User.query.filter_by(phone=identifier).first()
                else:  # 默认用户名
                    user = User.query.filter_by(username=identifier).first()
                    
                if user:
                    result['user'] = user.to_dict()
            except Exception as e:
                print(f"获取用户信息失败: {str(e)}")
            
        # 确保返回的响应包含必要的字段
        if 'user' not in result:
            result['user'] = {'id': result.get('user_id'), 'username': identifier}
        if 'success' not in result:
            result['success'] = True
        if 'message' not in result:
            result['message'] = '登录成功'

    # 如果有token，添加到响应头中
    response = jsonify(result)
    if 'token' in result:
        response.headers.add('Authorization', f"Bearer {result['token']}")

    return response, 200

@auth_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_profile():
    """获取用户个人信息"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}'
        }), 500

@auth_bp.route('/user', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """更新用户个人信息"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('username') or not data.get('phone') or not data.get('email'):
            return jsonify({
                'success': False,
                'message': '用户名、手机号和邮箱为必填项'
            }), 400
            
        # 检查用户名是否已被其他用户使用
        existing_user = User.query.filter(User.username == data['username'], User.id != user_id).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': '用户名已被使用'
            }), 400
            
        # 检查邮箱是否已被其他用户使用
        existing_email = User.query.filter(User.email == data['email'], User.id != user_id).first()
        if existing_email:
            return jsonify({
                'success': False,
                'message': '邮箱已被使用'
            }), 400
            
        # 检查手机号是否已被其他用户使用
        existing_phone = User.query.filter(User.phone == data['phone'], User.id != user_id).first()
        if existing_phone:
            return jsonify({
                'success': False,
                'message': '手机号已被使用'
            }), 400
            
        # 更新用户信息
        user.username = data.get('username')
        user.email = data.get('email')
        user.phone = data.get('phone')
        user.height = data.get('height')
        user.weight = data.get('weight')
        user.gender = data.get('gender')
        
        # 处理出生日期
        if data.get('birthdate'):
            try:
                user.birth_date = datetime.strptime(data['birthdate'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '出生日期格式不正确'
                }), 400
                
        # 如果提供了新密码，则更新密码
        if data.get('password'):
            user.set_password(data['password'])
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '个人信息更新成功',
            'user': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新用户信息失败: {str(e)}'
        }), 500

@auth_bp.route('/user', methods=['DELETE'])
@jwt_required()
def delete_user():
    """删除用户账号"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
        # 删除用户相关的所有记录
        # 注意：这里假设数据库设置了级联删除
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '账号已成功注销'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'注销账号失败: {str(e)}'
        }), 500

@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """验证JWT令牌是否有效"""
    user_id = get_jwt_identity()
    if user_id:
        return jsonify({
            'success': True,
            'message': '令牌有效',
            'user_id': user_id
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': '令牌无效'
        }), 401 