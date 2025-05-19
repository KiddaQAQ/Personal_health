from database import db
from datetime import datetime

class HealthRecord(db.Model):
    __tablename__ = 'health_records'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    record_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    record_type = db.Column(db.String(20), nullable=False)  # 记录类型：health, diet, exercise, water, medication
    
    # 基本健康指标
    weight = db.Column(db.Float, nullable=True)  # 单位：kg
    height = db.Column(db.Float, nullable=True)  # 单位：cm
    bmi = db.Column(db.Float, nullable=True)
    blood_pressure_systolic = db.Column(db.Integer, nullable=True)  # 收缩压
    blood_pressure_diastolic = db.Column(db.Integer, nullable=True)  # 舒张压
    heart_rate = db.Column(db.Integer, nullable=True)  # 心率
    blood_sugar = db.Column(db.Float, nullable=True)  # 血糖
    body_fat = db.Column(db.Float, nullable=True)  # 体脂率
    sleep_hours = db.Column(db.Float, nullable=True)  # 睡眠时间
    steps = db.Column(db.Integer, nullable=True)  # 步数
    
    # 饮食记录字段
    food_name = db.Column(db.String(100), nullable=True)  # 食物名称
    meal_type = db.Column(db.String(20), nullable=True)   # 餐次：早餐、午餐、晚餐、加餐
    food_amount = db.Column(db.Float, nullable=True)      # 食物量（克）
    sugar = db.Column(db.Float, nullable=True)            # 糖分含量（克）
    
    # 运动记录字段
    exercise_type = db.Column(db.String(50), nullable=True)  # 运动类型名称
    duration = db.Column(db.Integer, nullable=True)         # 运动时长（分钟）
    intensity = db.Column(db.String(20), nullable=True)     # 运动强度：低、中、高
    calories_burned = db.Column(db.Float, nullable=True)    # 消耗卡路里
    distance = db.Column(db.Float, nullable=True)           # 运动距离（公里）
    
    # 饮水记录字段
    water_amount = db.Column(db.Integer, nullable=True)     # 饮水量（毫升）
    water_type = db.Column(db.String(20), nullable=True)    # 水的类型
    intake_time = db.Column(db.Time, nullable=True)         # 饮水时间
    
    # 服药记录字段
    medication_name = db.Column(db.String(100), nullable=True)  # 药物名称
    dosage = db.Column(db.Float, nullable=True)                # 药物剂量
    dosage_unit = db.Column(db.String(20), nullable=True)      # 剂量单位
    frequency = db.Column(db.String(50), nullable=True)        # 服用频率
    time_taken = db.Column(db.Time, nullable=True)             # 服药时间
    with_food = db.Column(db.Boolean, nullable=True)           # 是否与食物一起服用
    effectiveness = db.Column(db.Integer, nullable=True)       # 效果评分（1-5）
    side_effects = db.Column(db.Text, nullable=True)           # 副作用
    
    # 记录信息
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        basic_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'record_date': self.record_date.isoformat(),
            'record_type': self.record_type,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        # 根据记录类型添加相应字段
        if self.record_type == 'health':
            basic_dict.update({
                'weight': self.weight,
                'height': self.height,
                'bmi': self.bmi,
                'blood_pressure_systolic': self.blood_pressure_systolic,
                'blood_pressure_diastolic': self.blood_pressure_diastolic,
                'heart_rate': self.heart_rate,
                'blood_sugar': self.blood_sugar,
                'body_fat': self.body_fat,
                'sleep_hours': self.sleep_hours,
                'steps': self.steps
            })
        elif self.record_type == 'diet':
            basic_dict.update({
                'food_name': self.food_name,
                'meal_type': self.meal_type,
                'food_amount': self.food_amount,
                'sugar': self.sugar
            })
        elif self.record_type == 'exercise':
            basic_dict.update({
                'exercise_type': self.exercise_type,
                'duration': self.duration,
                'intensity': self.intensity,
                'calories_burned': self.calories_burned,
                'distance': self.distance
            })
        elif self.record_type == 'water':
            basic_dict.update({
                'water_amount': self.water_amount,
                'water_type': self.water_type,
                'intake_time': self.intake_time.isoformat() if self.intake_time else None
            })
        elif self.record_type == 'medication':
            basic_dict.update({
                'medication_name': self.medication_name,
                'dosage': self.dosage,
                'dosage_unit': self.dosage_unit,
                'frequency': self.frequency,
                'time_taken': self.time_taken.isoformat() if self.time_taken else None,
                'with_food': self.with_food,
                'effectiveness': self.effectiveness,
                'side_effects': self.side_effects
            })
            
        return basic_dict