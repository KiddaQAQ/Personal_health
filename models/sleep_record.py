from database import db
from datetime import datetime, timedelta

class SleepRecord(db.Model):
    """睡眠记录表，记录用户的睡眠情况"""
    __tablename__ = 'sleep_records'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sleep_date = db.Column(db.Date, nullable=False)  # 入睡日期
    sleep_time = db.Column(db.DateTime, nullable=False)  # 入睡时间
    wake_time = db.Column(db.DateTime, nullable=False)  # 醒来时间
    duration = db.Column(db.Integer, nullable=False)  # 睡眠时长(分钟)
    quality = db.Column(db.Integer, nullable=True)  # 睡眠质量评分(1-10)
    deep_sleep = db.Column(db.Integer, nullable=True)  # 深度睡眠时长(分钟)
    light_sleep = db.Column(db.Integer, nullable=True)  # 浅度睡眠时长(分钟)
    interruptions = db.Column(db.Integer, nullable=True, default=0)  # 睡眠中断次数
    notes = db.Column(db.Text, nullable=True)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """将记录转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sleep_date': self.sleep_date.isoformat(),
            'sleep_time': self.sleep_time.isoformat(),
            'wake_time': self.wake_time.isoformat(),
            'duration': self.duration,
            'quality': self.quality,
            'deep_sleep': self.deep_sleep,
            'light_sleep': self.light_sleep,
            'interruptions': self.interruptions,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def calculate_duration(sleep_time, wake_time):
        """计算睡眠时长(分钟)"""
        delta = wake_time - sleep_time
        return int(delta.total_seconds() / 60)
    
    @staticmethod
    def get_weekly_average(user_id, end_date=None):
        """获取指定用户一周的平均睡眠时长"""
        if not end_date:
            end_date = datetime.utcnow().date()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        start_date = end_date - timedelta(days=7)
        
        records = SleepRecord.query.filter(
            SleepRecord.user_id == user_id,
            SleepRecord.sleep_date >= start_date,
            SleepRecord.sleep_date <= end_date
        ).all()
        
        if not records:
            return 0
            
        total_duration = sum(record.duration for record in records)
        return total_duration / len(records) 