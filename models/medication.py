from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Time, Boolean, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from datetime import datetime, date, time

from models.db import Base
from models.user import User

class MedicationType(Base):
    """药物类型模型"""
    __tablename__ = 'medication_types'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True, comment='药物名称')
    category = Column(String(50), nullable=True, comment='药物类别')
    description = Column(Text, nullable=True, comment='药物描述')
    common_dosage = Column(String(100), nullable=True, comment='常用剂量')
    side_effects = Column(Text, nullable=True, comment='可能的副作用')
    precautions = Column(Text, nullable=True, comment='使用注意事项')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联到药物记录
    records = relationship('MedicationRecord', back_populates='medication_type')
    
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


class MedicationRecord(Base):
    """药物记录模型"""
    __tablename__ = 'medication_records'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    medication_type_id = Column(Integer, ForeignKey('medication_types.id'), nullable=False, comment='药物类型ID')
    record_date = Column(Date, nullable=False, comment='服药日期')
    time_taken = Column(Time, nullable=False, comment='服药时间')
    dosage = Column(Float, nullable=False, comment='剂量')
    dosage_unit = Column(String(20), nullable=False, comment='剂量单位')
    frequency = Column(String(50), nullable=True, comment='服药频率')
    duration = Column(String(50), nullable=True, comment='持续时间')
    with_food = Column(Boolean, default=False, comment='是否与食物一起服用')
    effectiveness = Column(String(50), nullable=True, comment='有效性评价')
    side_effects_experienced = Column(Text, nullable=True, comment='经历的副作用')
    notes = Column(Text, nullable=True, comment='备注')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    user = relationship('User', back_populates='medication_records')
    medication_type = relationship('MedicationType', back_populates='records')
    
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