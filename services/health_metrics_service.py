from database import db
from models.health_record import HealthRecord
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class HealthMetricsService:
    """健康指标服务类，提供基本健康指标记录的管理功能"""
    
    @staticmethod
    def create_health_metrics_record(user_id, record_date=None, **kwargs):
        """
        创建健康指标记录
        
        参数:
            user_id: 用户ID
            record_date: 记录日期
            **kwargs: 健康指标数据
        
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
                record_type='health'
            )
            
            # 设置健康指标字段
            record.weight = kwargs.get('weight')
            record.height = kwargs.get('height')
            record.bmi = kwargs.get('bmi')
            record.blood_pressure_systolic = kwargs.get('blood_pressure_systolic')
            record.blood_pressure_diastolic = kwargs.get('blood_pressure_diastolic')
            record.heart_rate = kwargs.get('heart_rate')
            record.blood_sugar = kwargs.get('blood_sugar')
            record.body_fat = kwargs.get('body_fat')
            record.sleep_hours = kwargs.get('sleep_hours')
            record.steps = kwargs.get('steps')
            record.notes = kwargs.get('notes')
            
            # 保存记录
            db.session.add(record)
            db.session.commit()
            
            logger.info(f"创建健康指标记录成功，用户ID: {user_id}")
            
            return {
                "success": True,
                "message": "健康指标记录创建成功",
                "record_id": record.id,
                "record": record.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建健康指标记录失败: {str(e)}")
            return {
                "success": False,
                "message": f"创建记录失败: {str(e)}"
            }
    
    @staticmethod
    def get_health_metrics_records(user_id, start_date=None, end_date=None):
        """
        获取用户的健康指标记录
        
        参数:
            user_id: 用户ID
            start_date: 开始日期，可选
            end_date: 结束日期，可选
            
        返回:
            健康指标记录列表
        """
        try:
            query = HealthRecord.query.filter_by(user_id=user_id, record_type='health')
            
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
            logger.error(f"获取健康指标记录失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取记录失败: {str(e)}",
                "records": []
            }
    
    @staticmethod
    def get_health_metrics_record(record_id, user_id):
        """
        获取指定的健康指标记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID(用于验证所有权)
            
        返回:
            健康指标记录详情
        """
        try:
            record = HealthRecord.query.filter_by(id=record_id, user_id=user_id, record_type='health').first()
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
            logger.error(f"获取健康指标记录 {record_id} 时出错: {str(e)}")
            return {
                "success": False,
                "message": f"获取记录失败: {str(e)}"
            } 