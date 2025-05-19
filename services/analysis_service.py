from models.diet_record import DietRecord, Food
from models.exercise import ExerciseType, ExerciseRecord
from models.user import User
from models.health_record import HealthRecord
from database import db
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Date
import calendar

class AnalysisService:
    """营养成分分析与运动建议服务"""
    
    @staticmethod
    def get_nutrition_analysis(user_id, start_date=None, end_date=None):
        """
        获取用户在指定时间段内的营养摄入分析
        
        参数:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        返回:
            包含营养分析结果的字典
        """
        try:
            print(f"开始营养分析 - 用户ID: {user_id}, 开始日期: {start_date}, 结束日期: {end_date}")
            
            # 设置默认时间范围为过去7天
            if not end_date:
                end_date = datetime.now().date()
            if not start_date:
                start_date = end_date - timedelta(days=6)  # 包括今天在内共7天
                
            # 处理日期格式
            if isinstance(start_date, str):
                try:
                    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                except ValueError:
                    # 如果日期格式无效，使用默认日期
                    start_date = datetime.now().date() - timedelta(days=6)
            
            if isinstance(end_date, str):
                try:
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    # 如果日期格式无效，使用默认日期
                    end_date = datetime.now().date()
            
            print(f"处理后的日期范围: {start_date} 至 {end_date}")
            
            # 获取用户基本信息，用于计算推荐摄入量
            user = User.query.get(user_id)
            if not user:
                print(f"未找到用户: {user_id}")
                return {
                    "success": False, 
                    "message": "未找到用户信息"
                }
            
            # 获取该时间段内的所有饮食记录
            diet_records = DietRecord.query.filter(
                DietRecord.user_id == user_id,
                DietRecord.record_date >= start_date,
                DietRecord.record_date <= end_date
            ).all()
            
            print(f"找到 {len(diet_records)} 条饮食记录")
            
            # 同时获取HealthRecord表中的饮食记录
            health_diet_records = HealthRecord.query.filter(
                HealthRecord.user_id == user_id,
                HealthRecord.record_type == 'diet',
                HealthRecord.record_date >= start_date,
                HealthRecord.record_date <= end_date
            ).all()
            
            print(f"从HealthRecord表中找到 {len(health_diet_records)} 条饮食记录")
            
            # 初始化每日营养数据存储
            days_count = (end_date - start_date).days + 1
            daily_nutrition = {}
            
            current_date = start_date
            while current_date <= end_date:
                daily_nutrition[current_date.isoformat()] = {
                    "date": current_date.isoformat(),
                    "calories": 0,
                    "protein": 0,
                    "fat": 0,
                    "carbohydrate": 0,
                    "fiber": 0,
                    "sugar": 0,
                    "sodium": 0,
                    "meals": {}
                }
                current_date += timedelta(days=1)
            
            # 累计每日营养摄入
            for record in diet_records:
                day_key = record.record_date.isoformat()
                meal_type = record.meal_type if record.meal_type else "未分类"
                
                print(f"处理记录: 日期 {day_key}, 餐次 {meal_type}, ID {record.id}")
                
                # 确保meal_type存在于当日汇总中
                if meal_type not in daily_nutrition[day_key]["meals"]:
                    daily_nutrition[day_key]["meals"][meal_type] = {
                        "calories": 0,
                        "items": []
                    }
                
                # 累加当前餐次的热量
                if hasattr(record, 'total_calories') and record.total_calories:
                    print(f"  添加总热量: {record.total_calories}")
                    daily_nutrition[day_key]["calories"] += record.total_calories
                    daily_nutrition[day_key]["meals"][meal_type]["calories"] += record.total_calories
                
                # 遍历该餐次的每个食物项
                if hasattr(record, 'items') and record.items:
                    print(f"  该记录有 {len(record.items)} 个食物项")
                    for item in record.items:
                        if not item:
                            continue
                        
                        print(f"    处理食物项: {item}")
                        
                        # 直接从item获取营养素信息
                        amount = item.amount if hasattr(item, 'amount') and item.amount else 0
                        calories = item.calories if hasattr(item, 'calories') and item.calories else 0
                        
                        # 尝试从关联的food对象获取营养素
                        protein = 0
                        fat = 0
                        carbs = 0
                        fiber = 0
                        sugar = 0
                        sodium = 0
                        food_name = "未知食物"
                        
                        # 直接从item获取营养素
                        if hasattr(item, 'protein') and item.protein is not None:
                            protein = item.protein
                        if hasattr(item, 'fat') and item.fat is not None:
                            fat = item.fat
                        if hasattr(item, 'carbohydrate') and item.carbohydrate is not None:
                            carbs = item.carbohydrate
                        if hasattr(item, 'fiber') and item.fiber is not None:
                            fiber = item.fiber
                        if hasattr(item, 'sugar') and item.sugar is not None:
                            sugar = item.sugar
                        if hasattr(item, 'sodium') and item.sodium is not None:
                            sodium = item.sodium
                        
                        # 如果item上没有营养素数据，尝试从food对象获取
                        if (hasattr(item, 'food') and item.food and 
                            (protein == 0 and fat == 0 and carbs == 0)):
                            
                            food = item.food
                            print(f"    从食物对象获取营养素: {food.name if hasattr(food, 'name') else 'Unknown'}")
                            
                            # 计算该项的营养成分，考虑食用量
                            amount_ratio = amount / 100.0  # 假设营养素数据是按照100克计算的
                            
                            if hasattr(food, 'protein') and food.protein:
                                protein = food.protein * amount_ratio
                            if hasattr(food, 'fat') and food.fat:
                                fat = food.fat * amount_ratio
                            if hasattr(food, 'carbohydrate') and food.carbohydrate:
                                carbs = food.carbohydrate * amount_ratio
                            if hasattr(food, 'fiber') and food.fiber:
                                fiber = food.fiber * amount_ratio
                            if hasattr(food, 'sugar') and food.sugar:
                                sugar = food.sugar * amount_ratio
                            if hasattr(food, 'sodium') and food.sodium:
                                sodium = food.sodium * amount_ratio
                            
                            if hasattr(food, 'name') and food.name:
                                food_name = food.name
                        
                        # 获取食物名称（优先使用food_name属性）
                        if hasattr(item, 'food_name') and item.food_name:
                            food_name = item.food_name
                        
                        print(f"    营养素数据: 蛋白质 {protein}g, 脂肪 {fat}g, 碳水 {carbs}g, 纤维 {fiber}g, 糖 {sugar}g, 钠 {sodium}mg")
                        
                        # 累加各营养素
                        daily_nutrition[day_key]["protein"] += protein
                        daily_nutrition[day_key]["fat"] += fat
                        daily_nutrition[day_key]["carbohydrate"] += carbs
                        daily_nutrition[day_key]["fiber"] += fiber
                        daily_nutrition[day_key]["sugar"] += sugar
                        daily_nutrition[day_key]["sodium"] += sodium
                            
                        # 添加食物到该餐的食物列表
                        daily_nutrition[day_key]["meals"][meal_type]["items"].append({
                            "name": food_name,
                            "amount": amount,
                            "calories": calories
                        })
            
            # 处理从HealthRecord获取的饮食记录
            for record in health_diet_records:
                day_key = record.record_date.isoformat()
                meal_type = record.meal_type if record.meal_type else "未分类"
                
                print(f"处理HealthRecord记录: 日期 {day_key}, 餐次 {meal_type}, ID {record.id}")
                
                # 确保每个日期和餐次都有对应的数据结构
                if day_key not in daily_nutrition:
                    print(f"  警告: 日期 {day_key} 不在统计中，创建新的日期条目")
                    daily_nutrition[day_key] = {
                        "date": day_key,
                        "calories": 0,
                        "protein": 0,
                        "fat": 0,
                        "carbohydrate": 0,
                        "fiber": 0,
                        "sugar": 0,
                        "sodium": 0,
                        "meals": {}
                    }
                
                if meal_type not in daily_nutrition[day_key]["meals"]:
                    daily_nutrition[day_key]["meals"][meal_type] = {
                        "calories": 0,
                        "items": []
                    }
                
                # 提取食物名称、数量和热量
                food_name = record.food_name or "未知食物"
                amount = record.food_amount or 0
                
                # 获取热量数据，如果有的话
                calories = record.calories_burned or 0
                
                # 添加到菜品列表并更新总卡路里
                item_details = {
                    "food_name": food_name,
                    "amount": amount,
                    "calories": calories
                }
                
                # 添加食物项到餐次中
                daily_nutrition[day_key]["meals"][meal_type]["items"].append(item_details)
                
                # 如果有热量数据，则添加到当天统计
                if calories > 0:
                    print(f"  添加热量: {calories}")
                    daily_nutrition[day_key]["calories"] += calories
                    daily_nutrition[day_key]["meals"][meal_type]["calories"] += calories
                
                # 根据食物名称估算营养素
                protein_estimate = 0
                fat_estimate = 0
                carbs_estimate = 0
                fiber_estimate = 0
                sugar_estimate = 0
                sodium_estimate = 0
                
                # 尝试从Food表中查找匹配的食物来获取准确的营养信息
                food = Food.query.filter(Food.name.like(f"%{food_name}%")).first()
                
                if food and food.calories:
                    print(f"  从食物数据库匹配到: {food.name}")
                    # 如果找到食物，使用其营养数据（按照摄入量比例计算）
                    amount_ratio = amount / 100.0  # 假设营养素数据是按照100克计算的
                    
                    # 使用卡路里估算营养素
                    calories = food.calories * amount_ratio if food.calories else calories
                    protein_estimate = food.protein * amount_ratio if food.protein else 0
                    fat_estimate = food.fat * amount_ratio if food.fat else 0
                    carbs_estimate = food.carbohydrate * amount_ratio if food.carbohydrate else 0
                    fiber_estimate = food.fiber * amount_ratio if food.fiber else 0
                    sugar_estimate = food.sugar * amount_ratio if food.sugar else 0
                    sodium_estimate = food.sodium * amount_ratio if food.sodium else 0
                    
                    # 在日志中特别输出糖分和纤维素数据，方便调试
                    print(f"  食物营养成分明细 - 纤维素: {fiber_estimate}g, 糖分: {sugar_estimate}g")
                else:
                    # 如果找不到食物，使用估算方法
                    if "鸡蛋" in food_name or "蛋" in food_name:
                        protein_estimate = amount * 0.13  # 13% 蛋白质
                        fat_estimate = amount * 0.10      # 10% 脂肪
                        carbs_estimate = amount * 0.01    # 1% 碳水
                        fiber_estimate = amount * 0.001   # 0.1% 纤维
                        sodium_estimate = amount * 1.4    # 140mg/100g 钠
                        sugar_estimate = amount * 0.005   # 0.5% 糖分
                    # 水果类食物
                    elif any(fruit in food_name for fruit in ["果", "苹果", "香蕉", "橙子", "橘子", "梨"]):
                        protein_estimate = amount * 0.01  # 1% 蛋白质
                        fat_estimate = amount * 0.001     # 0.1% 脂肪
                        carbs_estimate = amount * 0.15    # 15% 碳水
                        fiber_estimate = amount * 0.02    # 2% 纤维
                        sodium_estimate = amount * 0.01   # 1mg/100g 钠
                        sugar_estimate = amount * 0.1     # 10% 糖分(水果含糖较高)
                        print(f"  水果类食物估算 - 纤维素: {fiber_estimate}g, 糖分: {sugar_estimate}g")
                    # 甜食类
                    elif any(sweet in food_name for sweet in ["糖", "巧克力", "蛋糕", "甜点", "冰淇淋", "饼干"]):
                        protein_estimate = amount * 0.05  # 5% 蛋白质
                        fat_estimate = amount * 0.15      # 15% 脂肪
                        carbs_estimate = amount * 0.60    # 60% 碳水
                        fiber_estimate = amount * 0.01    # 1% 纤维
                        sodium_estimate = amount * 0.2    # 20mg/100g 钠
                        sugar_estimate = amount * 0.35    # 35% 糖分(甜食含糖高)
                        print(f"  甜食类食物估算 - 纤维素: {fiber_estimate}g, 糖分: {sugar_estimate}g")
                    # 肉类食物
                    elif any(meat in food_name for meat in ["肉", "牛肉", "猪肉", "鸡肉", "鱼", "虾"]):
                        protein_estimate = amount * 0.22  # 22% 蛋白质
                        fat_estimate = amount * 0.10      # 10% 脂肪
                        carbs_estimate = 0                # 几乎没有碳水
                        fiber_estimate = 0                # 几乎没有纤维
                        sodium_estimate = amount * 0.7    # 70mg/100g 钠
                        sugar_estimate = 0                # 几乎没有糖
                    # 米饭、面条等主食
                    elif any(carb in food_name for carb in ["米饭", "面", "米", "饭", "馒头", "面包"]):
                        protein_estimate = amount * 0.07  # 7% 蛋白质
                        fat_estimate = amount * 0.01      # 1% 脂肪
                        carbs_estimate = amount * 0.28    # 28% 碳水
                        fiber_estimate = amount * 0.01    # 1% 纤维
                        sodium_estimate = amount * 0.02   # 2mg/100g 钠
                        sugar_estimate = amount * 0.01    # 1% 糖分
                    # 蔬菜
                    elif any(veg in food_name for veg in ["菜", "青菜", "蔬菜", "西红柿", "番茄", "黄瓜"]):
                        protein_estimate = amount * 0.02  # 2% 蛋白质
                        fat_estimate = 0                  # 几乎没有脂肪
                        carbs_estimate = amount * 0.05    # 5% 碳水
                        fiber_estimate = amount * 0.03    # 3% 纤维
                        sodium_estimate = amount * 0.1    # 10mg/100g 钠
                        sugar_estimate = amount * 0.02    # 2% 糖分
                    # 如果有热量数据但没有匹配到食物类型，则按比例估算营养素
                    elif calories > 0:
                        protein_estimate = calories * 0.2 / 4  # 假设20%热量来自蛋白质
                        fat_estimate = calories * 0.3 / 9      # 假设30%热量来自脂肪
                        carbs_estimate = calories * 0.5 / 4    # 假设50%热量来自碳水
                        fiber_estimate = amount * 0.03         # 假设每100g食物含3g纤维
                        sodium_estimate = amount * 0.05        # 假设每100g食物含50mg钠
                        sugar_estimate = calories * 0.1 / 4    # 假设10%热量来自糖
                
                print(f"  估算营养素 - 蛋白质: {protein_estimate}g, 脂肪: {fat_estimate}g, 碳水: {carbs_estimate}g, 纤维: {fiber_estimate}g, 糖分: {sugar_estimate}g")
                
                # 累加各营养素到日统计
                daily_nutrition[day_key]["protein"] += protein_estimate
                daily_nutrition[day_key]["fat"] += fat_estimate
                daily_nutrition[day_key]["carbohydrate"] += carbs_estimate
                daily_nutrition[day_key]["fiber"] += fiber_estimate
                daily_nutrition[day_key]["sugar"] += sugar_estimate
                daily_nutrition[day_key]["sodium"] += sodium_estimate
                
                # 如果没有热量数据，从营养素计算热量
                if calories <= 0:
                    calculated_calories = (protein_estimate * 4) + (fat_estimate * 9) + (carbs_estimate * 4)
                    if calculated_calories > 0:
                        print(f"  根据营养素计算热量: {calculated_calories}卡路里")
                        daily_nutrition[day_key]["calories"] += calculated_calories
                        daily_nutrition[day_key]["meals"][meal_type]["calories"] += calculated_calories
            
            # 打印每日数据汇总
            for day, data in daily_nutrition.items():
                print(f"日期 {day} 汇总: 热量 {data['calories']}kcal, 蛋白质 {data['protein']}g, 脂肪 {data['fat']}g, 碳水 {data['carbohydrate']}g")
            
            # 计算营养素平均值
            avg_nutrition = {
                "calories": 0,
                "protein": 0,
                "fat": 0,
                "carbohydrate": 0,
                "fiber": 0,
                "sugar": 0,
                "sodium": 0
            }
            
            for day_data in daily_nutrition.values():
                for key in avg_nutrition:
                    if key in day_data:
                        avg_nutrition[key] += day_data[key]
            
            # 计算每项平均值
            for key in avg_nutrition:
                avg_nutrition[key] = round(avg_nutrition[key] / days_count, 2) if days_count > 0 else 0
            
            print(f"平均营养素: {avg_nutrition}")
            
            # 计算总卡路里推荐值
            recommended_calories = 2200  # 通用推荐值
            
            # 如果有可用的计算TDEE函数，尝试使用
            if hasattr(user, 'calculate_tdee') and callable(getattr(user, 'calculate_tdee')):
                try:
                    calculated_tdee = user.calculate_tdee()
                    if calculated_tdee and calculated_tdee > 0:
                        recommended_calories = calculated_tdee
                except:
                    pass
            
            # 如果无法计算TDEE，使用基础估算
            if hasattr(user, 'gender') and user.gender:
                user_gender = user.gender.lower() if isinstance(user.gender, str) else ""
                if user_gender == 'male':
                    recommended_calories = 2500  # 男性平均推荐值
                elif user_gender == 'female':
                    recommended_calories = 2000  # 女性平均推荐值
            
            # 计算各营养素推荐值
            recommended_nutrition = {
                "calories": recommended_calories,
                "protein": round(recommended_calories * 0.15 / 4, 2),  # 15%卡路里来自蛋白质，1克蛋白质=4卡路里
                "fat": round(recommended_calories * 0.3 / 9, 2),  # 30%卡路里来自脂肪，1克脂肪=9卡路里
                "carbohydrate": round(recommended_calories * 0.55 / 4, 2),  # 55%卡路里来自碳水，1克碳水=4卡路里
                "fiber": 25,  # 每天25克膳食纤维推荐值
                "sugar": 25,  # 每天25克糖推荐值 (WHO建议)
                "sodium": 2300  # 每天2300毫克钠推荐值
            }
            
            # 计算各项营养素每日平均摄入占推荐值的百分比
            percentage = {}
            for key in avg_nutrition:
                if key in recommended_nutrition and recommended_nutrition[key] > 0:
                    percentage[key] = round((avg_nutrition[key] / recommended_nutrition[key]) * 100, 2)
                else:
                    percentage[key] = 0
            
            # 生成营养分析报告
            analysis = []
            
            # 热量分析
            if percentage.get("calories", 0) > 110:
                analysis.append({
                    "nutrient": "calories",
                    "status": "过高",
                    "message": "您的每日平均热量摄入超过推荐值的10%以上，可能导致体重增加。建议减少高热量食物的摄入，如甜点、油炸食品等。"
                })
            elif percentage.get("calories", 0) < 90:
                analysis.append({
                    "nutrient": "calories",
                    "status": "过低",
                    "message": "您的每日平均热量摄入低于推荐值的10%以上，可能导致营养不足。建议适当增加食物摄入量，确保均衡营养。"
                })
            else:
                analysis.append({
                    "nutrient": "calories",
                    "status": "正常",
                    "message": "您的每日平均热量摄入在推荐范围内，保持得很好。"
                })
            
            # 蛋白质分析
            if percentage.get("protein", 0) < 80:
                analysis.append({
                    "nutrient": "protein",
                    "status": "不足",
                    "message": "您的蛋白质摄入不足，蛋白质是维持肌肉健康的重要营养素。建议增加瘦肉、鱼、蛋、豆类等富含优质蛋白的食物。"
                })
            elif percentage.get("protein", 0) > 150:
                analysis.append({
                    "nutrient": "protein",
                    "status": "过多",
                    "message": "您的蛋白质摄入较多，长期过量摄入蛋白质可能增加肾脏负担。建议适当减少，保持均衡。"
                })
            else:
                analysis.append({
                    "nutrient": "protein",
                    "status": "适量",
                    "message": "您的蛋白质摄入适量，有助于维持肌肉健康和代谢功能。"
                })
            
            # 脂肪分析
            if percentage.get("fat", 0) > 120:
                analysis.append({
                    "nutrient": "fat",
                    "status": "过多",
                    "message": "您的脂肪摄入过多，可能增加心血管疾病风险。建议减少油炸食品、高脂肪肉类和全脂乳制品的摄入。"
                })
            elif percentage.get("fat", 0) < 70:
                analysis.append({
                    "nutrient": "fat",
                    "status": "不足",
                    "message": "您的脂肪摄入不足，适量的健康脂肪对吸收脂溶性维生素很重要。建议适当增加坚果、橄榄油、鱼类等健康脂肪来源。"
                })
            else:
                analysis.append({
                    "nutrient": "fat",
                    "status": "适量",
                    "message": "您的脂肪摄入适量，有助于维持激素平衡和细胞功能。"
                })
            
            # 碳水化合物分析
            if percentage.get("carbohydrate", 0) > 120:
                analysis.append({
                    "nutrient": "carbohydrate",
                    "status": "过多",
                    "message": "您的碳水化合物摄入过多，可能导致血糖波动和体重增加。建议减少精制碳水的摄入，如白面包、蛋糕、糖果等。"
                })
            elif percentage.get("carbohydrate", 0) < 70:
                analysis.append({
                    "nutrient": "carbohydrate",
                    "status": "不足",
                    "message": "您的碳水化合物摄入不足，可能影响能量供应和大脑功能。建议适当增加全谷物、水果等优质碳水来源。"
                })
            else:
                analysis.append({
                    "nutrient": "carbohydrate",
                    "status": "适量",
                    "message": "您的碳水化合物摄入适量，为身体提供了充足的能量。"
                })
            
            # 膳食纤维分析
            if percentage.get("fiber", 0) < 80:
                analysis.append({
                    "nutrient": "fiber",
                    "status": "不足",
                    "message": "您的膳食纤维摄入不足，可能影响肠道健康。建议增加全谷物、蔬菜、水果和豆类的摄入。"
                })
            else:
                analysis.append({
                    "nutrient": "fiber",
                    "status": "适量",
                    "message": "您的膳食纤维摄入适量，有助于维持肠道健康和控制血糖。"
                })
            
            # 糖分析
            if percentage.get("sugar", 0) > 120:
                analysis.append({
                    "nutrient": "sugar",
                    "status": "过多",
                    "message": "您的糖摄入过多，可能增加肥胖和糖尿病风险。建议减少甜饮料、甜点、糖果等添加糖的摄入。"
                })
            else:
                analysis.append({
                    "nutrient": "sugar",
                    "status": "适量",
                    "message": "您的糖摄入在合理范围内，继续保持控制添加糖的摄入。"
                })
            
            # 钠分析
            if percentage.get("sodium", 0) > 120:
                analysis.append({
                    "nutrient": "sodium",
                    "status": "过多",
                    "message": "您的钠摄入过多，可能增加高血压风险。建议减少加工食品、咸味零食和过度调味的食物摄入。"
                })
            else:
                analysis.append({
                    "nutrient": "sodium",
                    "status": "适量",
                    "message": "您的钠摄入在合理范围内，有助于维持正常的血压水平。"
                })
            
            # 返回完整的分析结果
            # 确保每日数据正确格式化
            daily_nutrition_list = list(daily_nutrition.values())
            print(f"返回 {len(daily_nutrition_list)} 条每日营养数据")

            # 返回分析结果
            result = {
                "success": True,
                "data": {
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "days": days_count
                    },
                    "daily_nutrition": daily_nutrition_list,
                    "average": avg_nutrition,
                    "recommended": recommended_nutrition,
                    "percentage": percentage,
                    "analysis": analysis
                }
            }

            # 打印结果中的daily_nutrition长度以确认
            print(f"最终返回结果: success={result['success']}, 每日数据数量={len(result['data']['daily_nutrition'])}")
            for day in result['data']['daily_nutrition'][:3]:  # 只打印前3天作为示例
                print(f"示例日期数据: {day['date']}, 热量={day['calories']}, 蛋白质={day['protein']}")

            return result
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            print(f"营养分析错误: {str(e)}\n{traceback_str}")
            return {
                "success": False,
                "message": f"获取营养分析失败: {str(e)}",
                "error_details": traceback_str
            }
    
    @staticmethod
    def get_exercise_recommendations(user_id, based_on_diet=True, days=7):
        """
        根据用户的饮食和活动情况，生成运动建议
        
        参数:
            user_id: 用户ID
            based_on_diet: 是否基于饮食数据生成建议
            days: 分析最近几天的数据
            
        返回:
            包含运动建议的字典
        """
        try:
            # 确保days是有效的正整数
            try:
                days = int(days)
                if days <= 0:
                    days = 7
            except (ValueError, TypeError):
                days = 7
            
            # 获取用户信息
            user = User.query.get(user_id)
            if not user:
                return {
                    "success": False,
                    "message": "未找到用户信息"
                }
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            # 获取用户最近的运动记录
            try:
                exercise_records = ExerciseRecord.query.filter(
                    ExerciseRecord.user_id == user_id,
                    ExerciseRecord.record_date >= start_date,
                    ExerciseRecord.record_date <= end_date
                ).all()
            except Exception as e:
                # 如果查询出错，使用空列表
                exercise_records = []
                print(f"获取运动记录时出错: {str(e)}")
            
            # 初始化默认值
            avg_daily_duration = 0
            has_cardio = False
            has_strength = False
            has_flexibility = False
            exercise_types_used = {}
            
            # 如果没有找到运动记录，尝试从健康记录中获取基本数据
            if not exercise_records:
                # 查询健康记录
                try:
                    health_records = HealthRecord.query.filter(
                        HealthRecord.user_id == user_id,
                        HealthRecord.record_date >= start_date,
                        HealthRecord.record_date <= end_date
                    ).all()
                except Exception as e:
                    # 如果查询出错，使用空列表
                    health_records = []
                    print(f"获取健康记录时出错: {str(e)}")
                
                # 如果存在健康记录，基于步数创建一些基本运动数据
                if health_records:
                    # 获取或创建一个"步行"运动类型
                    try:
                        walking_type = ExerciseType.query.filter_by(name="步行").first()
                        if not walking_type:
                            # 创建一个默认的步行类型
                            walking_type = ExerciseType(
                                name="步行",
                                category="有氧运动",
                                calories_per_hour=300,
                                description="步行是一种低强度有氧运动",
                                benefits="有助于心血管健康，改善血液循环，消耗热量"
                            )
                            db.session.add(walking_type)
                            db.session.commit()
                    except Exception as e:
                        # 如果无法获取或创建步行类型，跳过
                        print(f"获取或创建步行运动类型时出错: {str(e)}")
                    
                    # 计算每天的步数(如果有)转化为运动时长
                    avg_daily_duration = 30  # 默认每天30分钟
                    has_cardio = True        # 步行属于有氧运动
                    has_strength = False     # 没有力量训练
                    has_flexibility = False  # 没有柔韧性训练
                    exercise_types_used = {
                        "步行": {
                            "count": len(health_records),
                            "duration": avg_daily_duration * len(health_records),
                            "category": "有氧运动"
                        }
                    }
                else:
                    # 如果连健康记录都没有，设置默认值
                    avg_daily_duration = 0
                    has_cardio = False
                    has_strength = False
                    has_flexibility = False
                    exercise_types_used = {}
            else:
                # 计算每日平均运动时长
                total_duration = 0
                for record in exercise_records:
                    if hasattr(record, 'duration') and record.duration is not None:
                        try:
                            total_duration += float(record.duration)
                        except (ValueError, TypeError):
                            # 如果转换失败，忽略这条记录
                            pass
                
                avg_daily_duration = total_duration / days if days > 0 else 0
                
                # 获取用户活动的运动类型
                exercise_types_used = {}
                for record in exercise_records:
                    if hasattr(record, 'exercise_type') and record.exercise_type:
                        type_name = record.exercise_type.name if hasattr(record.exercise_type, 'name') else "未知运动"
                        category = record.exercise_type.category if hasattr(record.exercise_type, 'category') else "其他"
                        
                        if type_name not in exercise_types_used:
                            exercise_types_used[type_name] = {
                                "count": 0,
                                "duration": 0,
                                "category": category
                            }
                        
                        exercise_types_used[type_name]["count"] += 1
                        
                        if hasattr(record, 'duration') and record.duration is not None:
                            try:
                                duration = float(record.duration)
                                exercise_types_used[type_name]["duration"] += duration
                            except (ValueError, TypeError):
                                # 如果转换失败，使用0
                                pass
                
                # 检查是否有心肺运动和力量训练
                has_cardio = any(data.get("category") == "有氧运动" for data in exercise_types_used.values())
                has_strength = any(data.get("category") == "力量训练" for data in exercise_types_used.values())
                has_flexibility = any(data.get("category") == "柔韧性训练" for data in exercise_types_used.values())
            
            # 分析用户的饮食摄入
            calorie_surplus = 0
            if based_on_diet:
                try:
                    # 获取用户最近的饮食记录
                    diet_records = DietRecord.query.filter(
                        DietRecord.user_id == user_id,
                        DietRecord.record_date >= start_date,
                        DietRecord.record_date <= end_date
                    ).all()
                    
                    # 计算每日平均卡路里摄入
                    total_calories = 0
                    for record in diet_records:
                        if hasattr(record, 'total_calories') and record.total_calories is not None:
                            try:
                                total_calories += float(record.total_calories)
                            except (ValueError, TypeError):
                                # 如果转换失败，忽略这条记录
                                pass
                    
                    avg_daily_calories = total_calories / days if days > 0 else 0
                    
                    # 估算用户的每日能量需求
                    daily_calorie_need = 0
                    if hasattr(user, 'calculate_tdee') and callable(getattr(user, 'calculate_tdee')):
                        try:
                            calculated_tdee = user.calculate_tdee()
                            if calculated_tdee:
                                daily_calorie_need = calculated_tdee
                            else:
                                daily_calorie_need = 2000
                        except Exception:
                            daily_calorie_need = 2000
                    else:
                        daily_calorie_need = 2000
                    
                    # 计算卡路里盈余/赤字
                    calorie_surplus = avg_daily_calories - daily_calorie_need
                except Exception as e:
                    # 如果分析饮食摄入出错，使用默认值
                    calorie_surplus = 0
                    print(f"分析饮食摄入时出错: {str(e)}")
            
            # 获取所有可用的运动类型
            available_types = {
                "有氧运动": [],
                "力量训练": [],
                "柔韧性训练": [],
                "其他": []
            }
            
            try:
                all_exercise_types = ExerciseType.query.all()
                
                for ex_type in all_exercise_types:
                    if not hasattr(ex_type, 'category'):
                        continue
                        
                    category = ex_type.category if ex_type.category else "其他"
                    
                    # 创建一个运动类型的基本信息
                    type_info = {
                        "id": getattr(ex_type, 'id', 0),
                        "name": getattr(ex_type, 'name', "未知运动"),
                        "calories_per_hour": getattr(ex_type, 'calories_per_hour', 0)
                    }
                    
                    # 将运动类型添加到相应的类别中
                    if category in available_types:
                        available_types[category].append(type_info)
                    else:
                        available_types["其他"].append(type_info)
            except Exception as e:
                # 如果获取运动类型失败，使用空数据
                print(f"获取运动类型时出错: {str(e)}")
            
            # 生成运动建议
            recommendations = []
            
            # 基于运动时长的建议
            if avg_daily_duration < 30:
                recommendations.append({
                    "type": "duration",
                    "severity": "high",
                    "message": "您的每日平均运动时间不足30分钟，低于世界卫生组织推荐的每日至少30分钟中等强度活动。建议逐步增加运动时间，达到每天至少30-60分钟。"
                })
            elif avg_daily_duration < 60:
                recommendations.append({
                    "type": "duration",
                    "severity": "medium",
                    "message": "您的每日平均运动时间为{:.0f}分钟，已达到基本健康标准，但对于体重管理或提高健康水平，建议增加到每天60分钟。".format(avg_daily_duration)
                })
            else:
                recommendations.append({
                    "type": "duration",
                    "severity": "low",
                    "message": "您的每日平均运动时间为{:.0f}分钟，达到了良好的活动水平，有助于维持健康和预防慢性疾病。".format(avg_daily_duration)
                })
            
            # 基于运动多样性的建议
            if not has_cardio:
                cardio_suggestions = available_types.get("有氧运动", [])[:3]
                recommendations.append({
                    "type": "variety",
                    "category": "有氧运动",
                    "severity": "high",
                    "message": "您的运动计划中缺少有氧运动，这类运动有助于提高心肺功能和燃烧卡路里。建议每周进行至少150分钟中等强度有氧运动。",
                    "suggestions": cardio_suggestions
                })
            
            if not has_strength:
                strength_suggestions = available_types.get("力量训练", [])[:3]
                recommendations.append({
                    "type": "variety",
                    "category": "力量训练",
                    "severity": "medium",
                    "message": "您的运动计划中缺少力量训练，这类运动有助于增强肌肉力量、提高代谢率和改善体态。建议每周进行2-3次力量训练。",
                    "suggestions": strength_suggestions
                })
            
            if not has_flexibility:
                flexibility_suggestions = available_types.get("柔韧性训练", [])[:3]
                recommendations.append({
                    "type": "variety",
                    "category": "柔韧性训练",
                    "severity": "low",
                    "message": "您的运动计划中缺少柔韧性训练，这类运动有助于提高关节活动范围、预防伤害和减轻肌肉紧张。建议每周进行2-3次柔韧性训练，如瑜伽或拉伸。",
                    "suggestions": flexibility_suggestions
                })
            
            # 基于卡路里平衡的建议
            if based_on_diet and calorie_surplus > 300:
                high_intensity_suggestions = [
                    type_data for type_data in available_types.get("有氧运动", []) 
                    if type_data.get("calories_per_hour") and type_data.get("calories_per_hour") > 400
                ][:3]
                
                recommendations.append({
                    "type": "calorie_balance",
                    "severity": "high",
                    "message": "您的每日平均卡路里摄入超出消耗约{:.0f}卡路里，可能导致体重增加。建议增加高强度有氧运动，如HIIT训练、跑步或游泳，帮助燃烧额外卡路里。".format(calorie_surplus),
                    "suggestions": high_intensity_suggestions
                })
            elif based_on_diet and calorie_surplus < -300:
                recommendations.append({
                    "type": "calorie_balance",
                    "severity": "medium",
                    "message": "您的每日平均卡路里摄入低于消耗约{:.0f}卡路里，可能导致能量不足。如果您的目标是减重，请确保赤字不要过大；如果不是，建议适当增加食物摄入，尤其是在运动前后。".format(abs(calorie_surplus))
                })
            
            # 创建每周运动计划建议
            weekly_plan = []
            
            # 确定推荐总时长
            if avg_daily_duration < 30:
                recommended_weekly_duration = 210  # 每周210分钟，平均每天30分钟
            elif avg_daily_duration < 60:
                recommended_weekly_duration = 300  # 每周300分钟，平均每天约43分钟
            else:
                recommended_weekly_duration = 420  # 每周420分钟，平均每天60分钟
            
            # 分配运动类型时间
            cardio_percentage = 0.5  # 50%时间用于有氧
            strength_percentage = 0.3  # 30%时间用于力量
            flexibility_percentage = 0.2  # 20%时间用于柔韧性
            
            cardio_minutes = int(recommended_weekly_duration * cardio_percentage)
            strength_minutes = int(recommended_weekly_duration * strength_percentage)
            flexibility_minutes = int(recommended_weekly_duration * flexibility_percentage)
            
            # 创建每周运动计划
            days_of_week = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            
            # 有氧运动: 周一、周三、周五、周日
            cardio_days = [0, 2, 4, 6]
            cardio_per_day = cardio_minutes // len(cardio_days) if len(cardio_days) > 0 else 0
            
            # 力量训练: 周二、周四、周六
            strength_days = [1, 3, 5]
            strength_per_day = strength_minutes // len(strength_days) if len(strength_days) > 0 else 0
            
            # 柔韧性训练: 每天都可以做一些
            flexibility_per_day = flexibility_minutes // 7 if len(days_of_week) > 0 else 0
            
            for i, day in enumerate(days_of_week):
                day_plan = {
                    "day": day,
                    "activities": []
                }
                
                # 添加有氧运动
                if i in cardio_days and available_types.get("有氧运动"):
                    day_plan["activities"].append({
                        "category": "有氧运动",
                        "duration": cardio_per_day,
                        "suggestions": available_types.get("有氧运动", [])[:2]
                    })
                
                # 添加力量训练
                if i in strength_days and available_types.get("力量训练"):
                    day_plan["activities"].append({
                        "category": "力量训练",
                        "duration": strength_per_day,
                        "suggestions": available_types.get("力量训练", [])[:2]
                    })
                
                # 添加柔韧性训练
                if available_types.get("柔韧性训练"):
                    day_plan["activities"].append({
                        "category": "柔韧性训练",
                        "duration": flexibility_per_day,
                        "suggestions": available_types.get("柔韧性训练", [])[:1]
                    })
                
                weekly_plan.append(day_plan)
            
            # 返回完整的建议
            return {
                "success": True,
                "data": {
                    "current_status": {
                        "average_daily_duration": round(avg_daily_duration, 1),
                        "exercise_types_used": exercise_types_used,
                        "has_cardio": has_cardio,
                        "has_strength": has_strength,
                        "has_flexibility": has_flexibility,
                        "calorie_surplus": round(calorie_surplus, 1) if based_on_diet else None
                    },
                    "recommendations": recommendations,
                    "weekly_plan": weekly_plan,
                    "available_exercise_types": available_types
                }
            }
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            return {
                "success": False,
                "message": f"获取运动建议失败: {str(e)}",
                "error_details": traceback_str
            }
    
    @staticmethod
    def get_diet_recommendations(user_id, days=7):
        """
        根据用户的健康状况和活动水平，生成饮食建议
        
        参数:
            user_id: 用户ID
            days: 分析最近几天的数据
            
        返回:
            包含饮食建议的字典
        """
        try:
            # 获取用户信息
            user = User.query.get(user_id)
            if not user:
                return {
                    "success": False,
                    "message": "未找到用户信息"
                }
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            # 获取用户最近的饮食记录
            diet_records = DietRecord.query.filter(
                DietRecord.user_id == user_id,
                DietRecord.record_date >= start_date,
                DietRecord.record_date <= end_date
            ).all()
            
            # 如果没有找到饮食记录，尝试从健康记录中获取基本数据
            if not diet_records:
                # 查询健康记录
                health_records = HealthRecord.query.filter(
                    HealthRecord.user_id == user_id,
                    HealthRecord.record_date >= start_date,
                    HealthRecord.record_date <= end_date
                ).all()
                
                # 如果存在健康记录，使用其中的数据
                if health_records:
                    # 创建一些基本分析数据
                    avg_calories = 0
                    avg_carbs = 0
                    avg_protein = 0
                    avg_fat = 0
                    food_groups = {}
                    water_intake = 0
                    meal_times = {}
                    
                    for record in health_records:
                        # 如果健康记录中有能够使用的饮食数据，提取出来
                        if hasattr(record, 'calorie_intake') and record.calorie_intake:
                            avg_calories += record.calorie_intake
                        if hasattr(record, 'water_intake') and record.water_intake:
                            water_intake += record.water_intake
                    
                    # 计算平均值
                    if health_records:
                        avg_calories = avg_calories / len(health_records) if avg_calories > 0 else 2000  # 默认2000卡路里
                        water_intake = water_intake / len(health_records) if water_intake > 0 else 1500  # 默认1.5升水
                else:
                    # 如果连健康记录都没有，设置一些默认值
                    avg_calories = 2000
                    avg_carbs = 250
                    avg_protein = 70
                    avg_fat = 65
                    food_groups = {}
                    water_intake = 1500
                    meal_times = {}
            else:
                # 计算平均热量和营养素摄入
                total_calories = sum(record.total_calories for record in diet_records if record.total_calories)
                total_carbs = sum(record.total_carbs for record in diet_records if record.total_carbs)
                total_protein = sum(record.total_protein for record in diet_records if record.total_protein)
                total_fat = sum(record.total_fat for record in diet_records if record.total_fat)
                total_water = sum(record.water_intake for record in diet_records if record.water_intake)
                
                avg_calories = total_calories / days
                avg_carbs = total_carbs / days
                avg_protein = total_protein / days
                avg_fat = total_fat / days
                water_intake = total_water / days
                
                # 饮食多样性分析 - 收集不同食物组
                food_groups = {}
                meal_times = {}
                
                for record in diet_records:
                    for item in record.diet_items:
                        food = item.food
                        if food and food.food_group:
                            if food.food_group not in food_groups:
                                food_groups[food.food_group] = 0
                            food_groups[food.food_group] += 1
                        
                        # 统计进餐时间
                        if item.meal_time:
                            hour = item.meal_time.hour
                            if hour not in meal_times:
                                meal_times[hour] = 0
                            meal_times[hour] += 1
            
            # 返回饮食建议
            return {
                "success": True,
                "data": {
                    "avg_calories": avg_calories,
                    "avg_carbs": avg_carbs,
                    "avg_protein": avg_protein,
                    "avg_fat": avg_fat,
                    "water_intake": water_intake,
                    "food_groups": food_groups,
                    "meal_times": meal_times
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取饮食建议失败: {str(e)}"
            }
    
    @staticmethod
    def get_comprehensive_health_analysis(user_id, days=30):
        """
        提供用户全面的健康分析，结合健康记录、运动记录和饮食记录的数据
        
        参数:
            user_id: 用户ID
            days: 分析最近几天的数据
            
        返回:
            包含综合健康分析和建议的字典
        """
        try:
            # 获取用户信息
            user = User.query.get(user_id)
            if not user:
                return {
                    "success": False,
                    "message": "未找到用户信息"
                }
            
            # 获取各种健康数据的分析结果
            health_stats = AnalysisService.get_health_statistics(user_id, days)
            exercise_recommendations = AnalysisService.get_exercise_recommendations(user_id, days)
            diet_recommendations = AnalysisService.get_diet_recommendations(user_id, days)
            
            # 检查各种数据是否成功获取
            if not health_stats.get("success") or not exercise_recommendations.get("success") or not diet_recommendations.get("success"):
                return {
                    "success": False,
                    "message": "无法获取完整的健康数据分析"
                }
            
            # 获取数据
            health_data = health_stats.get("data", {})
            exercise_data = exercise_recommendations.get("data", {})
            diet_data = diet_recommendations.get("data", {})
            
            # 综合健康状况评估
            health_score = 70  # 基础分数
            health_insights = []
            health_recommendations = []
            
            # 根据体重变化进行评估
            weight_change = health_data.get("weight_trend", 0)
            if abs(weight_change) > 5:
                health_score -= 10
                if weight_change > 0:
                    health_insights.append("体重增长速度较快")
                    health_recommendations.append("建议控制饮食摄入，增加运动量")
                else:
                    health_insights.append("体重下降速度较快")
                    health_recommendations.append("建议保持均衡饮食，确保营养摄入")
            
            # 根据血压评估
            avg_systolic = health_data.get("avg_blood_pressure", {}).get("systolic", 120)
            avg_diastolic = health_data.get("avg_blood_pressure", {}).get("diastolic", 80)
            
            if avg_systolic > 140 or avg_diastolic > 90:
                health_score -= 15
                health_insights.append("血压偏高")
                health_recommendations.append("建议定期监测血压，减少盐分摄入，进行适度有氧运动")
            elif avg_systolic < 90 or avg_diastolic < 60:
                health_score -= 10
                health_insights.append("血压偏低")
                health_recommendations.append("建议多补充水分，适当增加盐分摄入，避免突然站立")
            
            # 根据心率评估
            avg_heart_rate = health_data.get("avg_heart_rate", 75)
            if avg_heart_rate > 100:
                health_score -= 10
                health_insights.append("静息心率偏高")
                health_recommendations.append("建议进行心率监测，增加有氧运动，减少咖啡因摄入")
            elif avg_heart_rate < 50 and not exercise_data.get("is_athlete", False):
                health_score -= 5
                health_insights.append("静息心率偏低")
                health_recommendations.append("建议咨询医生，排除心脏问题")
            
            # 根据运动情况评估
            avg_exercise_duration = exercise_data.get("avg_daily_duration", 0)
            if avg_exercise_duration < 30:
                health_score -= 10
                health_insights.append("运动量不足")
                health_recommendations.append("建议每天进行至少30分钟的中等强度运动")
            elif avg_exercise_duration > 120:
                health_score += 5
                health_insights.append("运动量充足")
                health_recommendations.append("保持良好的运动习惯，注意劳逸结合")
            
            # 根据饮食情况评估
            avg_calories = diet_data.get("avg_calories", 2000)
            water_intake = diet_data.get("water_intake", 1500)
            
            if water_intake < 1500:
                health_score -= 5
                health_insights.append("水分摄入不足")
                health_recommendations.append("建议每天饮水至少1.5升")
            
            if user.gender == "男":
                if avg_calories < 1800:
                    health_score -= 5
                    health_insights.append("热量摄入可能不足")
                    health_recommendations.append("建议适当增加健康食物的摄入")
                elif avg_calories > 2800:
                    health_score -= 5
                    health_insights.append("热量摄入可能过多")
                    health_recommendations.append("建议控制饮食摄入，增加蛋白质的比例")
            else:
                if avg_calories < 1500:
                    health_score -= 5
                    health_insights.append("热量摄入可能不足")
                    health_recommendations.append("建议适当增加健康食物的摄入")
                elif avg_calories > 2300:
                    health_score -= 5
                    health_insights.append("热量摄入可能过多")
                    health_recommendations.append("建议控制饮食摄入，增加蛋白质的比例")
            
            # 调整健康评分以确保在合理范围内
            health_score = max(0, min(100, health_score))
            
            # 设置健康状况级别
            if health_score >= 90:
                health_status = "优秀"
            elif health_score >= 75:
                health_status = "良好"
            elif health_score >= 60:
                health_status = "一般"
            else:
                health_status = "需要改善"
            
            # 返回综合分析结果
            return {
                "success": True,
                "data": {
                    "health_score": health_score,
                    "health_status": health_status,
                    "health_insights": health_insights,
                    "health_recommendations": health_recommendations,
                    "health_statistics": health_data,
                    "exercise_data": exercise_data,
                    "diet_data": diet_data
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取综合健康分析失败: {str(e)}"
            } 