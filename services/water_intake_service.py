from models.water_intake import WaterIntake
from sqlalchemy import func
from database import db
from datetime import datetime, timedelta, time
import logging

logger = logging.getLogger(__name__)

class WaterIntakeService:
    """水摄入服务，处理与水摄入记录相关的业务逻辑"""
    
    @staticmethod
    def create_water_intake(user_id, amount, record_date, intake_time=None, water_type=None, notes=None):
        """
        创建新的水摄入记录
        
        参数:
            user_id: 用户ID
            amount: 饮水量(毫升)
            record_date: 记录日期(YYYY-MM-DD)
            intake_time: 饮水时间(HH:MM:SS)，可选
            water_type: 水的类型，可选
            notes: 备注，可选
            
        返回:
            新创建的水摄入记录的字典表示
        """
        try:
            # 解析日期
            if isinstance(record_date, str):
                record_date = datetime.strptime(record_date, '%Y-%m-%d').date()
            
            # 解析时间
            datetime_obj = None
            if intake_time:
                if isinstance(intake_time, str):
                    # 尝试解析不同的时间格式
                    try:
                        time_obj = datetime.strptime(intake_time, '%H:%M:%S').time()
                    except ValueError:
                        try:
                            time_obj = datetime.strptime(intake_time, '%H:%M').time()
                        except ValueError:
                            raise ValueError(f"无法解析时间: {intake_time}")
                    
                    # 将日期和时间合并为完整的datetime对象
                    datetime_obj = datetime.combine(record_date, time_obj)
                else:
                    datetime_obj = datetime.combine(record_date, intake_time)
            else:
                # 如果未提供时间，使用当前时间
                datetime_obj = datetime.combine(record_date, datetime.now().time())
            
            # 创建水摄入记录
            water_intake = WaterIntake(
                user_id=user_id,
                amount=amount,
                record_date=record_date,
                intake_time=datetime_obj,
                water_type=water_type,
                notes=notes
            )
            
            db.session.add(water_intake)
            db.session.commit()
            
            return water_intake.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建水摄入记录失败: {str(e)}")
            raise
    
    @staticmethod
    def get_water_intake_records(user_id, start_date=None, end_date=None):
        """
        获取用户的水摄入记录
        
        参数:
            user_id: 用户ID
            start_date: 开始日期(YYYY-MM-DD)，可选
            end_date: 结束日期(YYYY-MM-DD)，可选
            
        返回:
            符合条件的水摄入记录列表
        """
        try:
            query = WaterIntake.query.filter(WaterIntake.user_id == user_id)
            
            if start_date:
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(WaterIntake.record_date >= start_date)
            
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(WaterIntake.record_date <= end_date)
            
            # 按记录日期和时间排序
            records = query.order_by(WaterIntake.record_date.desc(), WaterIntake.intake_time.desc()).all()
            
            return [record.to_dict() for record in records]
        except Exception as e:
            logger.error(f"获取水摄入记录失败: {str(e)}")
            raise
    
    @staticmethod
    def get_water_intake_record(record_id, user_id):
        """
        获取特定的水摄入记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID
            
        返回:
            找到的水摄入记录，如果不存在返回None
        """
        try:
            record = WaterIntake.query.filter(
                WaterIntake.id == record_id,
                WaterIntake.user_id == user_id
            ).first()
            
            if record:
                return record.to_dict()
            return None
        except Exception as e:
            logger.error(f"获取水摄入记录失败: {str(e)}")
            raise
    
    @staticmethod
    def update_water_intake(record_id, user_id, **kwargs):
        """
        更新水摄入记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID
            **kwargs: 要更新的字段
            
        返回:
            更新后的水摄入记录，如果不存在返回None
        """
        try:
            record = WaterIntake.query.filter(
                WaterIntake.id == record_id,
                WaterIntake.user_id == user_id
            ).first()
            
            if not record:
                return None
            
            # 更新可更改的字段
            if 'amount' in kwargs:
                record.amount = kwargs['amount']
            
            if 'record_date' in kwargs:
                if isinstance(kwargs['record_date'], str):
                    record.record_date = datetime.strptime(kwargs['record_date'], '%Y-%m-%d').date()
                else:
                    record.record_date = kwargs['record_date']
            
            if 'intake_time' in kwargs:
                # 如果提供了新的摄入时间
                time_obj = None
                if isinstance(kwargs['intake_time'], str):
                    try:
                        time_obj = datetime.strptime(kwargs['intake_time'], '%H:%M:%S').time()
                    except ValueError:
                        try:
                            time_obj = datetime.strptime(kwargs['intake_time'], '%H:%M').time()
                        except ValueError:
                            raise ValueError(f"无法解析时间: {kwargs['intake_time']}")
                else:
                    time_obj = kwargs['intake_time']
                
                # 将日期和新时间合并为完整的datetime对象
                record.intake_time = datetime.combine(record.record_date, time_obj)
            
            if 'water_type' in kwargs:
                record.water_type = kwargs['water_type']
            
            if 'notes' in kwargs:
                record.notes = kwargs['notes']
            
            record.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return record.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新水摄入记录失败: {str(e)}")
            raise
    
    @staticmethod
    def delete_water_intake(record_id, user_id):
        """
        删除水摄入记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID
            
        返回:
            成功删除返回True，否则返回False
        """
        try:
            record = WaterIntake.query.filter(
                WaterIntake.id == record_id,
                WaterIntake.user_id == user_id
            ).first()
            
            if not record:
                return False
            
            db.session.delete(record)
            db.session.commit()
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除水摄入记录失败: {str(e)}")
            raise
    
    @staticmethod
    def get_daily_summary(user_id, date):
        """
        获取某一天的水摄入摘要
        
        参数:
            user_id: 用户ID
            date: 日期(YYYY-MM-DD)
            
        返回:
            包含总水摄入量和记录列表的字典
        """
        try:
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # 获取该日期的所有水摄入记录
            records = WaterIntakeService.get_water_intake_records(
                user_id=user_id,
                start_date=date,
                end_date=date
            )
            
            # 计算总水摄入量
            total_amount = WaterIntake.get_daily_total(user_id, date)
            
            # 计算完成率（假设推荐的每日摄入量为2000毫升）
            recommended_daily_intake = 2000  # 毫升
            completion_rate = (total_amount / recommended_daily_intake) * 100 if total_amount else 0
            
            return {
                'date': date.isoformat(),
                'total_amount': total_amount,
                'records_count': len(records),
                'records': records,
                'recommended_intake': recommended_daily_intake,
                'completion_rate': min(round(completion_rate, 2), 100)
            }
        except Exception as e:
            logger.error(f"获取每日水摄入摘要失败: {str(e)}")
            raise
    
    @staticmethod
    def get_weekly_summary(user_id, start_date, end_date):
        """
        获取一段时间内的水摄入摘要
        
        参数:
            user_id: 用户ID
            start_date: 开始日期(YYYY-MM-DD)
            end_date: 结束日期(YYYY-MM-DD)
            
        返回:
            包含每日摘要的字典
        """
        try:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # 计算天数差
            days_diff = (end_date - start_date).days + 1
            
            # 获取每一天的摘要
            daily_summaries = []
            current_date = start_date
            
            for _ in range(days_diff):
                daily_summary = WaterIntakeService.get_daily_summary(
                    user_id=user_id,
                    date=current_date
                )
                daily_summaries.append(daily_summary)
                current_date += timedelta(days=1)
            
            # 计算总水摄入量
            total_amount = sum(summary['total_amount'] for summary in daily_summaries)
            
            # 计算平均每日摄入量
            average_daily_intake = total_amount / days_diff if days_diff > 0 else 0
            
            # 计算平均完成率
            average_completion_rate = sum(summary['completion_rate'] for summary in daily_summaries) / days_diff if days_diff > 0 else 0
            
            return {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days_count': days_diff,
                'total_amount': total_amount,
                'average_daily_intake': round(average_daily_intake, 2),
                'average_completion_rate': round(average_completion_rate, 2),
                'daily_summaries': daily_summaries
            }
        except Exception as e:
            logger.error(f"获取周水摄入摘要失败: {str(e)}")
            raise 