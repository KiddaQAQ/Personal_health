from database import db
from datetime import datetime

class Food(db.Model):
    """食物数据表，存储各种食物的营养成分信息"""
    __tablename__ = 'foods'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)  # 食物分类
    calories = db.Column(db.Float, nullable=True)  # 卡路里(每100克)
    protein = db.Column(db.Float, nullable=True)  # 蛋白质(克)
    fat = db.Column(db.Float, nullable=True)  # 脂肪(克)
    carbohydrate = db.Column(db.Float, nullable=True)  # 碳水化合物(克)
    fiber = db.Column(db.Float, nullable=True)  # 纤维素(克)
    sugar = db.Column(db.Float, nullable=True)  # 糖(克)
    sodium = db.Column(db.Float, nullable=True)  # 钠(毫克)
    serving_size = db.Column(db.Float, nullable=True)  # 标准份量(克)
    
    # 关联饮食记录项
    diet_items = db.relationship('DietRecordItem', backref='food', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'calories': self.calories,
            'protein': self.protein,
            'fat': self.fat,
            'carbohydrate': self.carbohydrate,
            'fiber': self.fiber,
            'sugar': self.sugar,
            'sodium': self.sodium,
            'serving_size': self.serving_size
        }

class DietRecord(db.Model):
    """饮食记录表，记录用户每天的饮食情况"""
    __tablename__ = 'diet_records'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    record_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    meal_type = db.Column(db.String(20), nullable=False)  # 早餐、午餐、晚餐、加餐
    total_calories = db.Column(db.Float, nullable=True)  # 总卡路里
    notes = db.Column(db.Text, nullable=True)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联饮食记录项
    items = db.relationship('DietRecordItem', backref='diet_record', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'record_date': self.record_date.isoformat(),
            'meal_type': self.meal_type,
            'total_calories': self.total_calories,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class DietRecordItem(db.Model):
    """饮食记录项，记录每次饮食中具体的食物及其数量"""
    __tablename__ = 'diet_record_items'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    diet_record_id = db.Column(db.Integer, db.ForeignKey('diet_records.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # 食用量(克)
    calories = db.Column(db.Float, nullable=True)  # 该项的卡路里
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'diet_record_id': self.diet_record_id,
            'food_id': self.food_id,
            'food_name': self.food.name if self.food else None,
            'amount': self.amount,
            'calories': self.calories,
            'created_at': self.created_at.isoformat()
        } 