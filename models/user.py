from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 用户个人信息
    height = db.Column(db.Float, nullable=True)  # 身高(cm)
    weight = db.Column(db.Float, nullable=True)  # 体重(kg)
    birth_date = db.Column(db.Date, nullable=True)  # 出生日期
    gender = db.Column(db.String(10), nullable=True)  # 性别
    activity_level = db.Column(db.String(20), nullable=True)  # 活动水平(久坐、轻度活动、中度活动、重度活动)
    
    # 用户健康数据关联 - 使用字符串而不是直接引用类以避免循环引用
    health_records = db.relationship('HealthRecord', backref='user', lazy=True)
    diet_records = db.relationship('DietRecord', backref='user', lazy=True)
    health_goals = db.relationship('HealthGoal', backref='user', lazy=True)
    medication_records = db.relationship('MedicationRecord', backref='user', lazy=True)
    exercise_records = db.relationship('ExerciseRecord', backref='user', lazy=True)
    water_intake_records = db.relationship('WaterIntake', backref='user', lazy=True)
    
    def set_password(self, password):
        # 使用pbkdf2:sha256代替scrypt，兼容性更好
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError as e:
            # 如果发生哈希类型不支持的错误，记录错误
            print(f"密码验证错误: {str(e)}")
            # 返回验证失败
            return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'height': self.height,
            'weight': self.weight,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'gender': self.gender,
            'activity_level': self.activity_level,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def calculate_bmr(self):
        """计算基础代谢率(BMR) - 使用修订版Harris-Benedict公式"""
        if not self.weight or not self.height or not self.birth_date or not self.gender:
            return None
            
        # 计算年龄
        today = datetime.now().date()
        age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        
        if self.gender.lower() == 'male':
            # 男性BMR = 88.362 + (13.397 × 体重kg) + (4.799 × 身高cm) - (5.677 × 年龄)
            bmr = 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * age)
        else:
            # 女性BMR = 447.593 + (9.247 × 体重kg) + (3.098 × 身高cm) - (4.330 × 年龄)
            bmr = 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * age)
            
        return round(bmr, 2)
    
    def calculate_tdee(self):
        """计算每日总能量消耗(TDEE)"""
        bmr = self.calculate_bmr()
        if not bmr:
            return None
            
        # 根据活动水平计算TDEE
        activity_multipliers = {
            'sedentary': 1.2,  # 久坐不动
            'lightly_active': 1.375,  # 轻度活动(每周轻度运动1-3天)
            'moderately_active': 1.55,  # 中度活动(每周中度运动3-5天)
            'very_active': 1.725,  # 重度活动(每周剧烈运动6-7天)
            'extra_active': 1.9  # 极度活动(体力劳动或每天训练2次)
        }
        
        multiplier = activity_multipliers.get(self.activity_level.lower(), 1.2)
        return round(bmr * multiplier, 2) 