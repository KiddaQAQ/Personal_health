from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# 创建SQLAlchemy实例
db = SQLAlchemy()

def init_db(app):
    """初始化数据库连接"""
    db.init_app(app)
    
    # 设置SQLAlchemy模型元数据选项
    db.metadata.clear()
    
    # 确保数据库和表已创建
    with app.app_context():
        # 导入所有模型以确保它们被注册到元数据
        from models.user import User
        from models.health_record import HealthRecord
        from models.diet_record import DietRecord, Food, DietRecordItem
        from models.health_goal import HealthGoal
        from models.medication_record import MedicationType, MedicationRecord
        from models.exercise import ExerciseType, ExerciseRecord
        from models.water_intake import WaterIntake
        from models.health_report import HealthReport, Reminder
        from models.social import Share, Like, Comment
        
        # 创建所有表
        db.create_all()
        print("数据库表已创建/更新")
        
def update_password_hash_field(app):
    """修改users表的password_hash字段长度为255"""
    with app.app_context():
        try:
            db.session.execute(text("ALTER TABLE users MODIFY password_hash VARCHAR(255)"))
            db.session.commit()
            print("密码哈希字段已更新为VARCHAR(255)")
        except Exception as e:
            db.session.rollback()
            print(f"更新密码哈希字段失败: {e}") 