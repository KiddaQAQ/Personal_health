from database import db
from datetime import datetime, timedelta
from sqlalchemy import func

class WaterIntake(db.Model):
    """水摄入量记录表，记录用户的饮水情况"""
    __tablename__ = 'water_intakes'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    record_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    amount = db.Column(db.Integer, nullable=False)  # 饮水量(毫升)
    intake_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # 饮水时间
    water_type = db.Column(db.String(50), nullable=True)  # 水的类型(如纯净水、矿泉水、茶等)
    notes = db.Column(db.Text, nullable=True)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """将记录转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'record_date': self.record_date.isoformat(),
            'amount': self.amount,
            'intake_time': self.intake_time.isoformat(),
            'water_type': self.water_type,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def get_daily_total(user_id, date):
        """获取指定日期的总饮水量"""
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
            
        total = db.session.query(db.func.sum(WaterIntake.amount)).filter(
            WaterIntake.user_id == user_id,
            WaterIntake.record_date == date
        ).scalar() or 0
        
        return total 