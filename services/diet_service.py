from database import db
from models.diet_record import Food, DietRecord, DietRecordItem
from datetime import datetime
from models.health_record import HealthRecord
import logging

logger = logging.getLogger(__name__)

class DietService:
    @staticmethod
    def create_food(name, category=None, calories=None, protein=None, fat=None, 
                   carbohydrate=None, fiber=None, sugar=None, sodium=None, 
                   serving_size=None):
        """创建新的食物"""
        food = Food(
            name=name,
            category=category,
            calories=calories,
            protein=protein,
            fat=fat,
            carbohydrate=carbohydrate,
            fiber=fiber,
            sugar=sugar,
            sodium=sodium,
            serving_size=serving_size
        )
        
        db.session.add(food)
        db.session.commit()
        
        return {'success': True, 'message': '食物创建成功', 'food': food.to_dict()}, 201
    
    @staticmethod
    def get_foods(category=None, search=None):
        """获取食物列表，可按分类或搜索关键词过滤"""
        query = Food.query
        
        if category:
            query = query.filter(Food.category == category)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(Food.name.like(search_term))
        
        foods = query.all()
        
        return {'success': True, 'foods': [food.to_dict() for food in foods]}, 200
    
    @staticmethod
    def get_food(food_id):
        """获取单个食物详情"""
        food = Food.query.get(food_id)
        
        if not food:
            return {'success': False, 'message': '食物不存在'}, 404
        
        return {'success': True, 'food': food.to_dict()}, 200
    
    @staticmethod
    def create_diet_record(user_id, record_date=None, **kwargs):
        """
        创建饮食记录
        
        参数:
            user_id: 用户ID
            record_date: 记录日期
            **kwargs: 饮食记录数据
        
        返回:
            成功时返回记录ID和创建成功消息，失败时返回错误信息
        """
        try:
            if record_date is None:
                record_date = datetime.now().date()
            elif isinstance(record_date, str):
                record_date = datetime.strptime(record_date, "%Y-%m-%d").date()
            
            # 创建新记录
            record = HealthRecord(
                user_id=user_id,
                record_date=record_date,
                record_type='diet'
            )
            
            # 设置饮食记录字段
            record.food_name = kwargs.get('food_name')
            record.meal_type = kwargs.get('meal_type')
            record.food_amount = kwargs.get('amount')
            record.notes = kwargs.get('notes')
            sugar = kwargs.get('sugar')  # 获取糖分值
            
            # 如果提供了糖分值，记录到日志
            if sugar:
                logger.info(f"收到糖分数据: {sugar}g")
            
            # 估算并设置热量值，如果前端未提供
            calories = kwargs.get('calories_burned')
            
            if not calories and record.food_amount:
                # 尝试从食物数据库获取卡路里值
                if record.food_name:
                    food = Food.query.filter(Food.name.like(f"%{record.food_name}%")).first()
                    if food and food.calories:
                        # 按比例计算卡路里
                        amount_ratio = record.food_amount / 100.0  # 假设食物营养成分是每100克计算的
                        calories = food.calories * amount_ratio
                        
                        # 如果没有提供糖分值但食物库中有，则自动估算
                        if not sugar and food.sugar:
                            sugar = food.sugar * amount_ratio
                            logger.info(f"从食物库估算糖分: {sugar}g")
            
            # 如果无法从食物库获取，使用简单估算
            if not calories and record.food_amount:
                # 简单估算：每100克食物平均提供150卡路里
                calories = record.food_amount * 1.5
                
                # 如果没有提供糖分且未从食物库获取，则根据食物类型估算
                if not sugar:
                    if any(fruit in record.food_name for fruit in ["果", "苹果", "香蕉", "橙子"]):
                        # 水果含糖较高
                        sugar = record.food_amount * 0.1  # 10% 糖分
                    elif any(sweet in record.food_name for sweet in ["糖", "巧克力", "蛋糕", "甜点"]):
                        # 甜食含糖更高
                        sugar = record.food_amount * 0.35  # 35% 糖分
                    else:
                        # 默认估算
                        sugar = record.food_amount * 0.02  # 2% 糖分
                    
                    logger.info(f"基于食物类型估算糖分: {sugar}g")
                
            record.calories_burned = calories  # 设置热量值
            record.sugar = sugar  # 设置糖分值
            
            logger.info(f"饮食记录详情 - 热量: {calories}kcal, 糖分: {sugar}g")
            
            # 保存记录
            db.session.add(record)
            db.session.commit()
            
            logger.info(f"创建饮食记录成功，用户ID: {user_id}")
            
            return {
                "success": True,
                "message": "饮食记录创建成功",
                "record_id": record.id,
                "record": record.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建饮食记录失败: {str(e)}")
            return {
                "success": False,
                "message": f"创建记录失败: {str(e)}"
            }
    
    @staticmethod
    def get_diet_records(user_id, start_date=None, end_date=None):
        """
        获取用户的饮食记录
        
        参数:
            user_id: 用户ID
            start_date: 开始日期，可选
            end_date: 结束日期，可选
            
        返回:
            饮食记录列表
        """
        try:
            query = HealthRecord.query.filter_by(user_id=user_id, record_type='diet')
            
            if start_date:
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(HealthRecord.record_date >= start_date)
                
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(HealthRecord.record_date <= end_date)
                
            # 按日期排序
            records = query.order_by(HealthRecord.record_date.desc(), 
                                     HealthRecord.created_at.desc()).all()
            
            return {
                "success": True,
                "records": [record.to_dict() for record in records],
                "count": len(records)
            }
            
        except Exception as e:
            logger.error(f"获取饮食记录失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取记录失败: {str(e)}",
                "records": []
            }
    
    @staticmethod
    def get_user_diet_records(user_id, start_date=None, end_date=None, meal_type=None):
        """获取用户的饮食记录"""
        query = DietRecord.query.filter_by(user_id=user_id)
        
        # 应用日期过滤
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(DietRecord.record_date >= start_date)
        
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(DietRecord.record_date <= end_date)
        
        # 按餐食类型过滤
        if meal_type:
            query = query.filter(DietRecord.meal_type == meal_type)
        
        # 按日期排序
        records = query.order_by(DietRecord.record_date.desc()).all()
        
        return {'success': True, 'records': [record.to_dict() for record in records]}, 200
    
    @staticmethod
    def get_diet_record(record_id, user_id):
        """
        获取单个饮食记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID
        
        返回:
            包含饮食记录详情的字典
        """
        try:
            # 先尝试从新模型中查找记录
            record = HealthRecord.query.filter_by(id=record_id, user_id=user_id, record_type='diet').first()
            
            if record:
                return {
                    "success": True,
                    "record": record.to_dict()
                }
            
            # 如果新模型中找不到，尝试旧模型
            old_record = DietRecord.query.filter_by(id=record_id, user_id=user_id).first()
            
            if old_record:
                return {
                    "success": True,
                    "record": old_record.to_dict()
                }
            
            # 两个模型都没找到则返回不存在
            return {
                "success": False,
                "message": "未找到记录或无权访问"
            }
        except Exception as e:
            logger.error(f"获取饮食记录 {record_id} 时出错: {str(e)}")
            return {
                "success": False,
                "message": f"获取记录失败: {str(e)}"
            }
    
    @staticmethod
    def update_diet_record(record_id, user_id, data):
        """更新饮食记录"""
        record = DietRecord.query.filter_by(id=record_id, user_id=user_id).first()
        
        if not record:
            return {'success': False, 'message': '记录不存在'}, 404
        
        # 更新基本信息
        if 'meal_type' in data:
            record.meal_type = data['meal_type']
        
        if 'notes' in data:
            record.notes = data['notes']
        
        if 'record_date' in data:
            if isinstance(data['record_date'], str):
                record.record_date = datetime.strptime(data['record_date'], '%Y-%m-%d').date()
            else:
                record.record_date = data['record_date']
        
        # 更新饮食项
        if 'items' in data:
            # 删除现有项
            for item in record.items:
                db.session.delete(item)
            
            # 添加新项
            total_calories = 0
            
            for item_data in data['items']:
                food_id = item_data.get('food_id')
                amount = item_data.get('amount')
                
                # 获取食物
                food = Food.query.get(food_id)
                if not food:
                    continue
                
                # 计算卡路里
                calories = None
                if food.calories and amount:
                    calories = (food.calories * amount) / 100
                    total_calories += calories
                
                # 创建记录项
                record_item = DietRecordItem(
                    diet_record=record,
                    food_id=food_id,
                    amount=amount,
                    calories=calories
                )
                
                db.session.add(record_item)
            
            # 更新总卡路里
            record.total_calories = total_calories
        
        db.session.commit()
        
        return {'success': True, 'message': '饮食记录更新成功', 'record': record.to_dict()}, 200
    
    @staticmethod
    def delete_diet_record(record_id, user_id):
        """删除饮食记录"""
        record = DietRecord.query.filter_by(id=record_id, user_id=user_id).first()
        
        if not record:
            return {'success': False, 'message': '记录不存在'}, 404
        
        db.session.delete(record)
        db.session.commit()
        
        return {'success': True, 'message': '饮食记录删除成功'}, 200
    
    @staticmethod
    def get_nutrition_summary(user_id, date=None):
        """获取用户某日或某段时间的营养摄入汇总"""
        query = DietRecord.query.filter_by(user_id=user_id)
        
        if date:
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter(DietRecord.record_date == date)
        
        records = query.all()
        
        # 初始化营养摄入汇总
        summary = {
            'total_calories': 0,
            'total_protein': 0,
            'total_fat': 0,
            'total_carbohydrate': 0,
            'total_fiber': 0,
            'total_sugar': 0,
            'total_sodium': 0,
            'meals': {}
        }
        
        for record in records:
            meal_type = record.meal_type
            
            # 确保meal_type存在于汇总中
            if meal_type not in summary['meals']:
                summary['meals'][meal_type] = {
                    'calories': 0,
                    'foods': []
                }
            
            # 添加当前记录的热量
            if record.total_calories:
                summary['total_calories'] += record.total_calories
                summary['meals'][meal_type]['calories'] += record.total_calories
            
            # 遍历记录中的每个食物项
            for item in record.items:
                food = item.food
                if food:
                    # 计算该项的营养成分，考虑食用量
                    amount_ratio = item.amount / 100 if item.amount else 0
                    
                    # 蛋白质
                    if food.protein:
                        protein = food.protein * amount_ratio
                        summary['total_protein'] += protein
                    
                    # 脂肪
                    if food.fat:
                        fat = food.fat * amount_ratio
                        summary['total_fat'] += fat
                    
                    # 碳水化合物
                    if food.carbohydrate:
                        carbohydrate = food.carbohydrate * amount_ratio
                        summary['total_carbohydrate'] += carbohydrate
                    
                    # 纤维素
                    if food.fiber:
                        fiber = food.fiber * amount_ratio
                        summary['total_fiber'] += fiber
                    
                    # 糖
                    if food.sugar:
                        sugar = food.sugar * amount_ratio
                        summary['total_sugar'] += sugar
                    
                    # 钠
                    if food.sodium:
                        sodium = food.sodium * amount_ratio
                        summary['total_sodium'] += sodium
                    
                    # 添加食物到该餐的食物列表
                    summary['meals'][meal_type]['foods'].append({
                        'name': food.name,
                        'amount': item.amount,
                        'calories': item.calories
                    })
        
        # 四舍五入所有汇总数据到2位小数
        for key in ['total_calories', 'total_protein', 'total_fat', 'total_carbohydrate', 
                   'total_fiber', 'total_sugar', 'total_sodium']:
            summary[key] = round(summary[key], 2)
        
        return {'success': True, 'summary': summary}, 200 