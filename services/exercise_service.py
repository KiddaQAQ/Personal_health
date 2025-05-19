from database import db
from models.exercise import ExerciseType, ExerciseRecord
from models.user import User
from datetime import datetime, timedelta
import calendar
from sqlalchemy import func, and_, cast, Date
from sqlalchemy.exc import IntegrityError
from models.health_record import HealthRecord
import logging

logger = logging.getLogger(__name__)

class ExerciseService:
    @staticmethod
    def create_exercise_type(name, category, met_value, description=None):
        """
        创建一个新的运动类型
        
        参数:
            name: 运动名称
            category: 运动类别
            met_value: 代谢当量值（即每小时消耗的卡路里）
            description: 描述信息
            
        返回:
            包含状态和数据的字典
        """
        try:
            # 检查运动类型是否已存在
            existing_type = ExerciseType.query.filter_by(name=name).first()
            if existing_type:
                return {
                    "success": False,
                    "message": f"运动类型 '{name}' 已存在",
                    "data": None
                }
            
            # 创建新的运动类型
            exercise_type = ExerciseType(
                name=name,
                category=category,
                calories_per_hour=met_value,
                description=description
            )
            
            db.session.add(exercise_type)
            db.session.commit()
            
            return {
                "success": True,
                "message": "运动类型创建成功",
                "data": exercise_type.to_dict()
            }
        except IntegrityError:
            db.session.rollback()
            return {
                "success": False,
                "message": "数据库完整性错误，可能是运动类型名称重复",
                "data": None
            }
        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"创建运动类型时发生错误: {str(e)}",
                "data": None
            }
    
    @staticmethod
    def get_exercise_types(category=None, search_term=None):
        """
        获取运动类型列表，可按类别筛选或搜索
        
        参数:
            category: 可选，按类别筛选
            search_term: 可选，搜索关键词
            
        返回:
            包含状态和数据的字典
        """
        try:
            query = ExerciseType.query
            
            # 应用筛选条件
            if category:
                query = query.filter(ExerciseType.category == category)
            
            if search_term:
                query = query.filter(ExerciseType.name.ilike(f"%{search_term}%"))
            
            # 获取结果
            exercise_types = query.order_by(ExerciseType.name).all()
            
            return {
                "success": True,
                "message": "运动类型获取成功",
                "data": [et.to_dict() for et in exercise_types]
            }
        except Exception as e:
            logger.error(f"获取运动类型时出错: {str(e)}")
            return {
                "success": False,
                "message": f"获取运动类型时发生错误: {str(e)}",
                "data": []
            }
    
    @staticmethod
    def get_exercise_type(type_id):
        """
        获取指定ID的运动类型详情
        
        参数:
            type_id: 运动类型ID
            
        返回:
            包含状态和数据的字典
        """
        try:
            exercise_type = ExerciseType.query.get(type_id)
            
            if not exercise_type:
                return {
                    "success": False,
                    "message": f"未找到ID为{type_id}的运动类型",
                    "data": None
                }
            
            return {
                "success": True,
                "message": "运动类型获取成功",
                "data": exercise_type.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取运动类型时发生错误: {str(e)}",
                "data": None
            }
    
    @staticmethod
    def create_exercise_record(user_id, record_date=None, **kwargs):
        """
        创建运动记录
        
        参数:
            user_id: 用户ID
            record_date: 记录日期
            **kwargs: 运动记录数据
        
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
                record_type='exercise'
            )
            
            # 获取运动类型
            exercise_type_id = kwargs.get('exercise_type_id')
            if exercise_type_id:
                try:
                    exercise_type = ExerciseType.query.get(exercise_type_id)
                    if exercise_type:
                        # 保存运动名称到exercise_type字段
                        record.exercise_type = exercise_type.name
                        # 如果没有提供消耗卡路里，使用运动类型的估算值
                        if not kwargs.get('calories_burned') and kwargs.get('duration'):
                            duration_hours = float(kwargs.get('duration')) / 60.0  # 将分钟转换为小时
                            record.calories_burned = round(exercise_type.calories_per_hour * duration_hours, 1)
                except Exception as e:
                    logger.warning(f"获取运动类型失败: {str(e)}")
            
            # 设置运动记录字段
            record.duration = kwargs.get('duration')
            record.intensity = kwargs.get('intensity')
            # 只有当未根据运动类型计算卡路里时，才使用传入的卡路里值
            if kwargs.get('calories_burned') and not record.calories_burned:
                record.calories_burned = kwargs.get('calories_burned')
            record.distance = kwargs.get('distance')
            record.notes = kwargs.get('notes')
            
            # 保存记录
            db.session.add(record)
            db.session.commit()
            
            logger.info(f"创建运动记录成功，用户ID: {user_id}")
            
            return {
                "success": True,
                "message": "运动记录创建成功",
                "record_id": record.id,
                "record": record.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建运动记录失败: {str(e)}")
            return {
                "success": False,
                "message": f"创建记录失败: {str(e)}"
            }
    
    @staticmethod
    def get_exercise_records(user_id, start_date=None, end_date=None):
        """
        获取用户的运动记录
        
        参数:
            user_id: 用户ID
            start_date: 开始日期，可选
            end_date: 结束日期，可选
            
        返回:
            运动记录列表
        """
        try:
            query = HealthRecord.query.filter_by(user_id=user_id, record_type='exercise')
            
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
            logger.error(f"获取运动记录失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取记录失败: {str(e)}",
                "records": []
            }
    
    @staticmethod
    def get_exercise_record(record_id, user_id):
        """
        获取指定ID的运动记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID（验证记录属于该用户）
            
        返回:
            包含状态和数据的字典
        """
        try:
            # 先尝试从新模型中查找记录
            record = HealthRecord.query.filter_by(id=record_id, user_id=user_id, record_type='exercise').first()
            
            if record:
                return {
                    "success": True,
                    "message": "运动记录获取成功",
                    "record": record.to_dict()
                }
            
            # 如果新模型中找不到，尝试旧模型
            old_record = ExerciseRecord.query.get(record_id)
            
            if old_record and old_record.user_id == user_id:
                return {
                    "success": True,
                    "message": "运动记录获取成功",
                    "record": old_record.to_dict()
                }
            
            # 两个模型都没找到则返回不存在
            return {
                "success": False,
                "message": f"未找到ID为{record_id}的运动记录或无权访问"
            }
        except Exception as e:
            logger.error(f"获取运动记录 {record_id} 时出错: {str(e)}")
            return {
                "success": False,
                "message": f"获取运动记录时发生错误: {str(e)}"
            }
    
    @staticmethod
    def update_exercise_record(record_id, user_id, exercise_type_id=None, 
                              exercise_date=None, duration=None, intensity=None,
                              calories_burned=None, distance=None, notes=None):
        """
        更新运动记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID
            其他参数: 要更新的字段
            
        返回:
            包含状态和数据的字典
        """
        try:
            record = ExerciseRecord.query.get(record_id)
            
            if not record:
                return {
                    "success": False,
                    "message": f"未找到ID为{record_id}的运动记录",
                    "data": None
                }
            
            # 验证记录是否属于该用户
            if record.user_id != user_id:
                return {
                    "success": False,
                    "message": "无权更新此运动记录",
                    "data": None
                }
            
            # 更新字段
            if exercise_type_id:
                exercise_type = ExerciseType.query.get(exercise_type_id)
                if not exercise_type:
                    return {
                        "success": False,
                        "message": f"未找到ID为{exercise_type_id}的运动类型",
                        "data": None
                    }
                record.exercise_type_id = exercise_type_id
                
            if exercise_date:
                if isinstance(exercise_date, str):
                    exercise_date = datetime.strptime(exercise_date, "%Y-%m-%d").date()
                record.exercise_date = exercise_date
                
            if duration is not None:
                record.duration = duration
                
            if intensity is not None:
                record.intensity = intensity
                
            if calories_burned is not None:
                record.calories_burned = calories_burned
                
            if distance is not None:
                record.distance = distance
                
            if notes is not None:
                record.notes = notes
            
            db.session.commit()
            
            return {
                "success": True,
                "message": "运动记录更新成功",
                "data": record.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"更新运动记录时发生错误: {str(e)}",
                "data": None
            }
    
    @staticmethod
    def delete_exercise_record(record_id, user_id):
        """
        删除运动记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID
            
        返回:
            包含状态和消息的字典
        """
        try:
            record = ExerciseRecord.query.get(record_id)
            
            if not record:
                return {
                    "success": False,
                    "message": f"未找到ID为{record_id}的运动记录"
                }
            
            # 验证记录是否属于该用户
            if record.user_id != user_id:
                return {
                    "success": False,
                    "message": "无权删除此运动记录"
                }
            
            db.session.delete(record)
            db.session.commit()
            
            return {
                "success": True,
                "message": "运动记录删除成功"
            }
        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"删除运动记录时发生错误: {str(e)}"
            }
    
    @staticmethod
    def get_exercise_summary(user_id, start_date=None, end_date=None, period=None, date=None):
        """
        获取用户运动数据汇总
        
        参数:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            period: 时间段类型 (day, week, month)
            date: 指定日期
            
        返回:
            包含状态和汇总数据的字典，以及HTTP状态码
        """
        try:
            # 处理 period 和 date 参数
            if period and date:
                # 处理日期格式
                if isinstance(date, str):
                    try:
                        specified_date = datetime.strptime(date, "%Y-%m-%d").date()
                    except ValueError:
                        # 日期格式错误，使用当前日期
                        specified_date = datetime.now().date()
                else:
                    specified_date = date if date else datetime.now().date()
                
                if period == 'day':
                    start_date = specified_date
                    end_date = specified_date
                elif period == 'week':
                    # 计算一周的开始和结束
                    start_date = specified_date - timedelta(days=specified_date.weekday())
                    end_date = start_date + timedelta(days=6)
                elif period == 'month':
                    # 计算一个月的开始和结束
                    start_date = specified_date.replace(day=1)
                    # 安全获取月份的最后一天
                    try:
                        last_day = calendar.monthrange(specified_date.year, specified_date.month)[1]
                        end_date = specified_date.replace(day=last_day)
                    except Exception:
                        # 如果计算月份最后一天出错，使用30天后作为结束日期
                        end_date = start_date + timedelta(days=30)
                else:
                    # 默认为最近30天
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=30)
            else:
                # 设置默认时间范围为过去30天
                if not end_date:
                    end_date = datetime.now().date()
                if not start_date:
                    start_date = end_date - timedelta(days=30)
                    
            # 处理日期格式
            if isinstance(start_date, str):
                try:
                    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                except ValueError:
                    # 日期格式错误，使用30天前
                    start_date = datetime.now().date() - timedelta(days=30)
                    
            if isinstance(end_date, str):
                try:
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    # 日期格式错误，使用今天
                    end_date = datetime.now().date()
            
            # 查询总卡路里、总时长和活动次数
            result = db.session.query(
                func.sum(ExerciseRecord.calories_burned).label('total_calories'),
                func.sum(ExerciseRecord.duration).label('total_duration'),
                func.count(ExerciseRecord.id).label('total_activities')
            ).filter(
                ExerciseRecord.user_id == user_id,
                ExerciseRecord.exercise_date >= start_date,
                ExerciseRecord.exercise_date <= end_date
            ).first()
            
            # 查询按日期分组的数据
            daily_data = db.session.query(
                cast(ExerciseRecord.exercise_date, Date).label('date'),
                func.sum(ExerciseRecord.calories_burned).label('calories'),
                func.sum(ExerciseRecord.duration).label('duration'),
                func.count(ExerciseRecord.id).label('count')
            ).filter(
                ExerciseRecord.user_id == user_id,
                ExerciseRecord.exercise_date >= start_date,
                ExerciseRecord.exercise_date <= end_date
            ).group_by(cast(ExerciseRecord.exercise_date, Date)
            ).order_by(cast(ExerciseRecord.exercise_date, Date)).all()
            
            # 查询按运动类型分组的数据 - 添加错误捕获
            try:
                type_data = db.session.query(
                    ExerciseType.name.label('type_name'),
                    func.sum(ExerciseRecord.calories_burned).label('calories'),
                    func.sum(ExerciseRecord.duration).label('duration'),
                    func.count(ExerciseRecord.id).label('count')
                ).join(
                    ExerciseType, ExerciseRecord.exercise_type_id == ExerciseType.id
                ).filter(
                    ExerciseRecord.user_id == user_id,
                    ExerciseRecord.exercise_date >= start_date,
                    ExerciseRecord.exercise_date <= end_date
                ).group_by(ExerciseType.name).all()
            except Exception as e:
                print(f"获取运动类型数据时出错: {str(e)}")
                type_data = []  # 在错误时使用空列表
            
            # 格式化结果 - 确保result不为None
            if result is None:
                # 如果没有数据，返回空汇总
                summary = {
                    "total_calories_burned": 0,
                    "total_duration": 0,
                    "total_activities": 0,
                    "daily_stats": [],
                    "type_stats": []
                }
            else:
                # 安全地访问结果数据
                try:
                    total_calories = result.total_calories if hasattr(result, 'total_calories') else None
                    total_duration = result.total_duration if hasattr(result, 'total_duration') else None
                    total_activities = result.total_activities if hasattr(result, 'total_activities') else None
                    
                    summary = {
                        "total_calories_burned": float(total_calories) if total_calories is not None else 0,
                        "total_duration": int(total_duration) if total_duration is not None else 0,
                        "total_activities": int(total_activities) if total_activities is not None else 0,
                        "daily_stats": [],
                        "type_stats": []
                    }
                except Exception as e:
                    print(f"处理运动汇总数据时出错: {str(e)}")
                    summary = {
                        "total_calories_burned": 0,
                        "total_duration": 0,
                        "total_activities": 0,
                        "daily_stats": [],
                        "type_stats": []
                    }
            
            # 安全处理daily_data
            if daily_data:
                try:
                    summary["daily_stats"] = [
                        {
                            "date": day.date.isoformat() if hasattr(day, 'date') else "未知日期",
                            "calories": float(day.calories) if hasattr(day, 'calories') and day.calories is not None else 0,
                            "duration": int(day.duration) if hasattr(day, 'duration') and day.duration is not None else 0,
                            "count": int(day.count) if hasattr(day, 'count') and day.count is not None else 0
                        } for day in daily_data
                    ]
                except Exception as e:
                    print(f"处理每日统计数据时出错: {str(e)}")
                    summary["daily_stats"] = []
            
            # 安全处理type_data
            if type_data:
                try:
                    summary["type_stats"] = [
                        {
                            "type": type_stat.type_name if hasattr(type_stat, 'type_name') else "未知类型",
                            "calories": float(type_stat.calories) if hasattr(type_stat, 'calories') and type_stat.calories is not None else 0,
                            "duration": int(type_stat.duration) if hasattr(type_stat, 'duration') and type_stat.duration is not None else 0,
                            "count": int(type_stat.count) if hasattr(type_stat, 'count') and type_stat.count is not None else 0
                        } for type_stat in type_data
                    ]
                except Exception as e:
                    print(f"处理类型统计数据时出错: {str(e)}")
                    summary["type_stats"] = []
            
            return {
                "success": True,
                "message": "运动数据汇总获取成功",
                "summary": summary
            }, 200
        except Exception as e:
            print(f"获取运动数据汇总错误: {str(e)}")
            return {
                "success": False,
                "message": f"获取运动数据汇总时发生错误: {str(e)}",
                "summary": {
                    "total_calories_burned": 0,
                    "total_duration": 0,
                    "total_activities": 0,
                    "daily_stats": [],
                    "type_stats": []
                }
            }, 500

    @staticmethod
    def initialize_exercise_types():
        """
        初始化常见的运动类型数据
        
        返回:
            包含状态和结果的字典
        """
        try:
            # 检查是否已经有数据
            existing_count = ExerciseType.query.count()
            if existing_count > 0:
                return {
                    "success": True,
                    "message": f"运动类型数据已存在，共有 {existing_count} 种类型",
                    "count": existing_count
                }
            
            # 预设的运动类型数据
            default_types = [
                # 有氧运动
                {"name": "跑步", "category": "有氧运动", "calories_per_hour": 600, "description": "户外或跑步机上的跑步"},
                {"name": "散步", "category": "有氧运动", "calories_per_hour": 280, "description": "轻度到中度的步行"},
                {"name": "游泳", "category": "有氧运动", "calories_per_hour": 500, "description": "各种泳姿的游泳锻炼"},
                {"name": "骑自行车", "category": "有氧运动", "calories_per_hour": 450, "description": "户外或室内自行车锻炼"},
                {"name": "椭圆机", "category": "有氧运动", "calories_per_hour": 450, "description": "在椭圆机上的锻炼"},
                {"name": "跳绳", "category": "有氧运动", "calories_per_hour": 700, "description": "使用跳绳的高强度间歇训练"},
                {"name": "爬楼梯", "category": "有氧运动", "calories_per_hour": 500, "description": "上下楼梯的有氧锻炼"},
                {"name": "划船", "category": "有氧运动", "calories_per_hour": 600, "description": "使用划船机或户外划船"},
                
                # 力量训练
                {"name": "举重", "category": "力量训练", "calories_per_hour": 350, "description": "使用自由重量进行力量训练"},
                {"name": "哑铃训练", "category": "力量训练", "calories_per_hour": 330, "description": "使用哑铃的上下肢力量训练"},
                {"name": "俯卧撑", "category": "力量训练", "calories_per_hour": 280, "description": "利用自身体重的胸部和手臂训练"},
                {"name": "引体向上", "category": "力量训练", "calories_per_hour": 300, "description": "锻炼背部和手臂肌肉的训练"},
                {"name": "深蹲", "category": "力量训练", "calories_per_hour": 350, "description": "锻炼腿部和臀部肌肉的训练"},
                {"name": "仰卧起坐", "category": "力量训练", "calories_per_hour": 250, "description": "锻炼腹部肌肉的训练"},
                {"name": "健身器械", "category": "力量训练", "calories_per_hour": 300, "description": "使用各种健身器械进行训练"},
                
                # 柔韧性训练
                {"name": "瑜伽", "category": "柔韧性训练", "calories_per_hour": 250, "description": "结合呼吸和姿势的身心锻炼"},
                {"name": "普拉提", "category": "柔韧性训练", "calories_per_hour": 270, "description": "注重核心肌群的训练系统"},
                {"name": "拉伸", "category": "柔韧性训练", "calories_per_hour": 180, "description": "伸展肌肉和关节的训练"},
                {"name": "太极", "category": "柔韧性训练", "calories_per_hour": 220, "description": "传统中国的缓慢动作练习"},
                
                # 球类运动
                {"name": "篮球", "category": "球类运动", "calories_per_hour": 550, "description": "场上五人制篮球比赛或训练"},
                {"name": "足球", "category": "球类运动", "calories_per_hour": 600, "description": "场上足球比赛或训练"},
                {"name": "网球", "category": "球类运动", "calories_per_hour": 450, "description": "网球比赛或训练"},
                {"name": "乒乓球", "category": "球类运动", "calories_per_hour": 350, "description": "乒乓球比赛或训练"},
                {"name": "羽毛球", "category": "球类运动", "calories_per_hour": 400, "description": "羽毛球比赛或训练"},
                {"name": "排球", "category": "球类运动", "calories_per_hour": 450, "description": "排球比赛或训练"},
                
                # 其他
                {"name": "舞蹈", "category": "其他", "calories_per_hour": 400, "description": "各种风格的舞蹈活动"},
                {"name": "武术", "category": "其他", "calories_per_hour": 450, "description": "中国传统武术或其他武术形式"},
                {"name": "高强度间歇训练", "category": "其他", "calories_per_hour": 700, "description": "短时高强度与休息交替的训练"},
                {"name": "户外徒步", "category": "其他", "calories_per_hour": 400, "description": "户外徒步旅行或登山"}
            ]
            
            # 批量添加运动类型
            for type_data in default_types:
                exercise_type = ExerciseType(
                    name=type_data["name"],
                    category=type_data["category"],
                    calories_per_hour=type_data["calories_per_hour"],
                    description=type_data["description"]
                )
                db.session.add(exercise_type)
            
            db.session.commit()
            
            return {
                "success": True,
                "message": f"成功初始化 {len(default_types)} 种运动类型数据",
                "count": len(default_types)
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"初始化运动类型数据时出错: {str(e)}")
            return {
                "success": False,
                "message": f"初始化运动类型数据失败: {str(e)}"
            } 