from database import db
from models.user import User
from flask_jwt_extended import create_access_token
from datetime import timedelta
import re
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def register(username=None, email=None, phone=None, password=None, birth_date=None, gender=None, height=None, weight=None):
        """
        注册新用户
        支持用户名、邮箱、手机号码三种注册方式，至少需要提供一种
        可选提供生日、性别、身高、体重等个人信息
        """
        # 验证至少提供了一种身份标识
        if not any([username, email, phone]):
            return {'success': False, 'message': '请至少提供用户名、邮箱或手机号码中的一种'}, 400
        
        # 验证密码
        if not password:
            return {'success': False, 'message': '密码不能为空'}, 400
        
        # 验证用户名是否存在
        if username and User.query.filter_by(username=username).first():
            return {'success': False, 'message': '用户名已存在'}, 400
        
        # 验证邮箱是否存在
        if email and User.query.filter_by(email=email).first():
            return {'success': False, 'message': '邮箱已存在'}, 400
        
        # 验证手机号是否存在
        if phone and User.query.filter_by(phone=phone).first():
            return {'success': False, 'message': '手机号已存在'}, 400
        
        # 验证邮箱格式
        if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return {'success': False, 'message': '邮箱格式不正确'}, 400
        
        # 验证手机号格式（简单验证中国大陆手机号）
        if phone and not re.match(r'^1[3-9]\d{9}$', phone):
            return {'success': False, 'message': '手机号格式不正确'}, 400
        
        try:
            # 创建新用户
            user = User(
                username=username, 
                email=email, 
                phone=phone,
                birth_date=birth_date,
                gender=gender,
                height=height,
                weight=weight
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            return {'success': True, 'message': '注册成功', 'user': user.to_dict()}, 201
        except Exception as e:
            logger.error(f"注册用户时出错: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': f'注册失败: {str(e)}'}, 500
    
    @staticmethod
    def login(identifier, password):
        """
        用户登录
        identifier可以是用户名、邮箱或手机号
        """
        if not identifier or not password:
            return {'success': False, 'message': '用户标识和密码不能为空'}, 400
        
        try:
            # 尝试查找用户（用户名、邮箱或手机号）
            user = User.query.filter(
                (User.username == identifier) | 
                (User.email == identifier) | 
                (User.phone == identifier)
            ).first()
            
            # 验证用户和密码
            if not user:
                return {'success': False, 'message': '用户不存在'}, 401
            
            # 尝试验证密码
            password_valid = False
            try:
                password_valid = user.check_password(password)
            except Exception as e:
                logger.error(f"密码验证出错: {str(e)}")
                return {'success': False, 'message': '密码验证错误，请联系管理员'}, 500
                
            if not password_valid:
                return {'success': False, 'message': '密码错误'}, 401
            
            # 创建访问令牌
            access_token = create_access_token(
                identity=user.id,
                expires_delta=timedelta(days=1)
            )
            
            return {
                'success': True,
                'message': '登录成功',
                'access_token': access_token,
                'user': user.to_dict()
            }, 200
        except Exception as e:
            logger.error(f"登录过程中出错: {str(e)}")
            return {'success': False, 'message': f'登录失败: {str(e)}'}, 500
    
    @staticmethod
    def get_user_info(user_id):
        """
        获取用户信息
        
        参数:
            user_id: 用户ID
            
        返回:
            包含用户信息的字典和状态码
        """
        try:
            user = User.query.get(user_id)
            
            if not user:
                return {'success': False, 'message': '用户不存在'}, 404
            
            return {'success': True, 'user': user.to_dict()}, 200
        except Exception as e:
            logger.error(f"获取用户信息时出错: {str(e)}")
            return {'success': False, 'message': f'获取用户信息失败: {str(e)}'}, 500 