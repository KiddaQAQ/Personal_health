import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db
from models.user import User
from flask import Flask
from werkzeug.security import generate_password_hash

def create_app():
    """创建临时Flask应用，用于数据库操作"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../personalhealth.db'  # 请根据实际情况修改
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def migrate_password_hashes():
    """迁移所有用户的密码哈希，使用临时默认密码"""
    print("开始迁移用户密码哈希...")
    
    # 获取所有用户
    users = User.query.all()
    print(f"找到 {len(users)} 个用户账户需要迁移")
    
    # 临时默认密码
    temp_password = "123456"
    
    # 更新所有用户的密码
    for user in users:
        try:
            # 使用pbkdf2:sha256算法重新设置密码
            user.password_hash = generate_password_hash(temp_password, method='pbkdf2:sha256')
            print(f"用户 {user.username or user.email or user.phone} 的密码已重置为临时密码")
        except Exception as e:
            print(f"处理用户 {user.id} 时出错: {str(e)}")
    
    # 保存更改
    db.session.commit()
    print("密码哈希迁移完成！所有用户密码已重置为临时密码：123456")
    print("请通知用户登录后立即修改密码。")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        migrate_password_hashes() 