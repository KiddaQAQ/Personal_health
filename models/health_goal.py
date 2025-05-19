from database import db
from datetime import datetime

class HealthGoal(db.Model):
    """健康目标表，记录用户设定的健康目标"""
    __tablename__ = 'health_goals'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False)  # 目标类型(体重、步数、运动时长等)
    target_value = db.Column(db.Float, nullable=False)  # 目标值
    current_value = db.Column(db.Float, nullable=True)  # 当前值
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    end_date = db.Column(db.Date, nullable=True)  # 目标完成日期
    status = db.Column(db.String(20), nullable=False, default='active')  # 状态(active, completed, abandoned)
    notes = db.Column(db.Text, nullable=True)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_type': self.goal_type,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def calculate_progress(self):
        """计算目标完成进度"""
        if not self.current_value or not self.target_value:
            return 0
        
        # 根据目标类型计算进度
        if self.goal_type in ['weight_loss', 'fat_loss']:
            # 对于减重目标，开始值减去当前值，除以开始值减去目标值
            start_value = self.initial_value or 0
            if start_value <= self.target_value:
                return 0
            progress = (start_value - self.current_value) / (start_value - self.target_value) * 100
        else:
            # 对于增长目标(如步数、运动时长)，当前值除以目标值
            progress = (self.current_value / self.target_value) * 100
            
        return min(round(progress, 2), 100)  # 进度最高100%
    
class HealthGoalLog(db.Model):
    """健康目标日志表，记录用户健康目标的完成情况"""
    __tablename__ = 'health_goal_logs'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('health_goals.id'), nullable=False)
    log_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    value = db.Column(db.Float, nullable=False)  # 记录的值
    notes = db.Column(db.Text, nullable=True)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联健康目标
    health_goal = db.relationship('HealthGoal', backref='logs', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'goal_id': self.goal_id,
            'log_date': self.log_date.isoformat(),
            'value': self.value,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        } 