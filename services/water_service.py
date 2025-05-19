from database import db
from models.health_record import HealthRecord
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WaterService:
    """水分摄入服务类，提供饮水记录的管理功能"""
    
    @staticmethod
    def create_water_record(user_id, record_date=None, **kwargs):
        """
        创建饮水记录
        
        参数:
            user_id: 用户ID
            record_date: 记录日期
            **kwargs: 饮水记录数据
        
        返回:
            成功时返回记录ID和创建成功消息，失败时返回错误信息
        """
        try:
            if record_date is None:
                record_date = datetime.now().date()
            elif isinstance(record_date, str):
                record_date = datetime.strptime(record_date, "%Y-%m-%d").date()
            
            # 处理饮水时间
            intake_time = kwargs.get('intake_time')
            if intake_time and isinstance(intake_time, str):
                kwargs['intake_time'] = datetime.strptime(intake_time, "%H:%M").time()
            
            # 创建新记录
            record = HealthRecord(
                user_id=user_id,
                record_date=record_date,
                record_type='water'
            )
            
            # 设置饮水记录字段
            record.water_amount = kwargs.get('amount')
            record.water_type = kwargs.get('water_type')
            record.intake_time = kwargs.get('intake_time')
            record.notes = kwargs.get('notes')
            
            # 保存记录
            db.session.add(record)
            db.session.commit()
            
            logger.info(f"创建饮水记录成功，用户ID: {user_id}")
            
            return {
                "success": True,
                "message": "饮水记录创建成功",
                "record_id": record.id,
                "record": record.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建饮水记录失败: {str(e)}")
            return {
                "success": False,
                "message": f"创建记录失败: {str(e)}"
            }
    
    @staticmethod
    def get_water_records(user_id, start_date=None, end_date=None):
        """
        获取用户的饮水记录
        
        参数:
            user_id: 用户ID
            start_date: 开始日期，可选
            end_date: 结束日期，可选
            
        返回:
            饮水记录列表
        """
        try:
            query = HealthRecord.query.filter_by(user_id=user_id, record_type='water')
            
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
            logger.error(f"获取饮水记录失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取记录失败: {str(e)}",
                "records": []
            }
    
    @staticmethod
    def get_water_record(record_id, user_id):
        """
        获取指定的饮水记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID(用于验证所有权)
            
        返回:
            饮水记录详情
        """
        try:
            record = HealthRecord.query.filter_by(id=record_id, user_id=user_id, record_type='water').first()
            if record:
                return {
                    "success": True,
                    "record": record.to_dict()
                }
            else:
                return {
                    "success": False,
                    "message": "未找到记录或无权访问"
                }
        except Exception as e:
            logger.error(f"获取饮水记录 {record_id} 时出错: {str(e)}")
            return {
                "success": False,
                "message": f"获取记录失败: {str(e)}"
            } 