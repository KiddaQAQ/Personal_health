from database import db
from datetime import datetime

class MedicationType(db.Model):
    """药物类型模型"""
    __tablename__ = 'medication_types'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50))  # 药物类别：处方药、非处方药等
    description = db.Column(db.Text)  # 药物描述
    common_dosage = db.Column(db.String(100))  # 常见剂量
    side_effects = db.Column(db.Text)  # 常见副作用
    precautions = db.Column(db.Text)  # 注意事项
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    records = db.relationship('MedicationRecord', backref='medication_type', lazy=True)
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'common_dosage': self.common_dosage,
            'side_effects': self.side_effects,
            'precautions': self.precautions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MedicationRecord(db.Model):
    """药物记录模型"""
    __tablename__ = 'medication_records'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    medication_type_id = db.Column(db.Integer, db.ForeignKey('medication_types.id'), nullable=False)
    record_date = db.Column(db.Date, nullable=False)  # 服药日期
    time_taken = db.Column(db.Time, nullable=False)  # 服药时间
    dosage = db.Column(db.Float, nullable=False)  # 剂量
    dosage_unit = db.Column(db.String(20), nullable=False)  # 剂量单位（如毫克、片、毫升等）
    frequency = db.Column(db.String(50))  # 服药频率（如每日一次、每日两次等）
    duration = db.Column(db.Integer)  # 持续时间（天数）
    with_food = db.Column(db.Boolean, default=False)  # 是否与食物一起服用
    effectiveness = db.Column(db.Integer)  # 效果评分（1-5）
    side_effects_experienced = db.Column(db.Text)  # 经历的副作用
    notes = db.Column(db.Text)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 这里不再显式指定user关联，因为User类已经创建了反向引用
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'medication_type_id': self.medication_type_id,
            'medication_name': self.medication_type.name if self.medication_type else None,
            'record_date': self.record_date.isoformat() if self.record_date else None,
            'time_taken': self.time_taken.isoformat() if self.time_taken else None,
            'dosage': self.dosage,
            'dosage_unit': self.dosage_unit,
            'frequency': self.frequency,
            'duration': self.duration,
            'with_food': self.with_food,
            'effectiveness': self.effectiveness,
            'side_effects_experienced': self.side_effects_experienced,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_medication_schedule(user_id, date=None):
        """获取用户的用药计划
        
        参数:
            user_id: 用户ID
            date: 特定日期，默认为今天
            
        返回:
            用药计划列表
        """
        from sqlalchemy import func
        
        if date is None:
            date = datetime.now().date()
            
        # 查询当前正在进行的用药记录
        query = MedicationRecord.query.filter(
            MedicationRecord.user_id == user_id,
            MedicationRecord.record_date <= date,
            (MedicationRecord.record_date + func.cast(MedicationRecord.duration, db.Integer) >= date) | 
            (MedicationRecord.duration.is_(None))
        )
        
        return query.all() 