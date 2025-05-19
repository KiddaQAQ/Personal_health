from database import db
from datetime import datetime

class HealthReport(db.Model):
    """健康报告模型"""
    __tablename__ = 'health_reports'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # 报告类型：周报、月报、年报等
    start_date = db.Column(db.Date, nullable=False)         # 报告开始日期
    end_date = db.Column(db.Date, nullable=False)           # 报告结束日期
    health_summary = db.Column(db.Text)                     # 健康状况总结
    diet_summary = db.Column(db.Text)                       # 饮食总结
    exercise_summary = db.Column(db.Text)                   # 运动总结
    medication_summary = db.Column(db.Text)                 # 用药总结
    recommendations = db.Column(db.Text)                    # 健康建议
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('health_reports', lazy=True))
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'report_type': self.report_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'health_summary': self.health_summary,
            'diet_summary': self.diet_summary,
            'exercise_summary': self.exercise_summary,
            'medication_summary': self.medication_summary,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Reminder(db.Model):
    """提醒模型（药物与预约提醒）"""
    __tablename__ = 'reminders'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)  # 提醒类型：medication（药物）, appointment（预约）
    title = db.Column(db.String(100), nullable=False)         # 提醒标题
    description = db.Column(db.Text)                         # 提醒描述
    reminder_date = db.Column(db.Date, nullable=False)       # 提醒日期
    reminder_time = db.Column(db.Time, nullable=False)       # 提醒时间
    recurrence = db.Column(db.String(20))                    # 重复类型：daily（每天）, weekly（每周）, monthly（每月）
    is_completed = db.Column(db.Boolean, default=False)      # 是否已完成
    medication_record_id = db.Column(db.Integer, db.ForeignKey('medication_records.id'))  # 关联的药物记录
    notes = db.Column(db.Text)                              # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('reminders', lazy=True))
    medication_record = db.relationship('MedicationRecord', backref=db.backref('reminders', lazy=True))
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reminder_type': self.reminder_type,
            'title': self.title,
            'description': self.description,
            'reminder_date': self.reminder_date.isoformat() if self.reminder_date else None,
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
            'recurrence': self.recurrence,
            'is_completed': self.is_completed,
            'medication_record_id': self.medication_record_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_pending_reminders(user_id, date=None):
        """获取用户待处理的提醒
        
        参数:
            user_id: 用户ID
            date: 特定日期，默认为今天
            
        返回:
            待处理的提醒列表
        """
        if date is None:
            date = datetime.now().date()
            
        # 查询当日未完成的提醒
        query = Reminder.query.filter(
            Reminder.user_id == user_id,
            Reminder.reminder_date == date,
            Reminder.is_completed == False
        ).order_by(Reminder.reminder_time)
        
        return query.all() 