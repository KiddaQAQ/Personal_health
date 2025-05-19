from database import db
from datetime import datetime

class ExerciseType(db.Model):
    """运动类型模型"""
    __tablename__ = 'exercise_types'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50))  # 如：有氧运动、力量训练、伸展运动等
    calories_per_hour = db.Column(db.Float)  # 每小时消耗卡路里
    description = db.Column(db.Text)
    benefits = db.Column(db.Text)  # 运动益处
    
    # 关联关系
    records = db.relationship('ExerciseRecord', backref='exercise_type', lazy=True)
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'calories_per_hour': self.calories_per_hour,
            'description': self.description,
            'benefits': self.benefits
        }


class ExerciseRecord(db.Model):
    """运动记录模型"""
    __tablename__ = 'exercise_records'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_type_id = db.Column(db.Integer, db.ForeignKey('exercise_types.id'), nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # 运动时长（分钟）
    calories_burned = db.Column(db.Float)  # 消耗卡路里
    intensity = db.Column(db.String(20))  # 运动强度：低、中、高
    heart_rate_avg = db.Column(db.Integer)  # 平均心率
    heart_rate_max = db.Column(db.Integer)  # 最大心率
    distance = db.Column(db.Float)  # 运动距离（公里）
    steps = db.Column(db.Integer)  # 步数
    notes = db.Column(db.Text)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User关系已在User模型中通过backref定义，这里不需要重复定义
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'exercise_type_id': self.exercise_type_id,
            'exercise_type': self.exercise_type.name if self.exercise_type else None,
            'record_date': self.record_date.isoformat() if self.record_date else None,
            'duration': self.duration,
            'intensity': self.intensity,
            'calories_burned': self.calories_burned,
            'heart_rate_avg': self.heart_rate_avg,
            'heart_rate_max': self.heart_rate_max,
            'distance': self.distance,
            'steps': self.steps,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 