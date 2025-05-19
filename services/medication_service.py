from database import db
from models.medication_record import MedicationType, MedicationRecord
from datetime import datetime, date as date_type
from sqlalchemy import func
import logging
from models.health_record import HealthRecord

logger = logging.getLogger(__name__)

class MedicationService:
    """药物服务类，提供药物类型和记录的管理功能"""
    
    @staticmethod
    def create_medication_type(name, category=None, description=None, common_dosage=None, 
                              side_effects=None, precautions=None):
        """
        创建新的药物类型
        
        参数:
            name: 药物名称
            category: 药物类别
            description: 药物描述
            common_dosage: 常见剂量
            side_effects: 副作用
            precautions: 注意事项
            
        返回:
            新创建的药物类型
        """
        try:
            # 检查药物名称是否已存在
            existing = MedicationType.query.filter_by(name=name).first()
            if existing:
                logger.warning(f"药物类型 '{name}' 已存在")
                return existing
                
            medication_type = MedicationType(
                name=name,
                category=category,
                description=description,
                common_dosage=common_dosage,
                side_effects=side_effects,
                precautions=precautions
            )
            
            db.session.add(medication_type)
            db.session.commit()
            logger.info(f"创建了新的药物类型: {name}")
            return medication_type
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建药物类型时出错: {str(e)}")
            raise
    
    @staticmethod
    def get_medication_types(category=None, search_term=None):
        """
        获取药物类型列表
        
        参数:
            category: 按类别筛选
            search_term: 搜索关键词
            
        返回:
            符合条件的药物类型列表
        """
        try:
            query = MedicationType.query
            
            if category:
                query = query.filter(MedicationType.category == category)
            
            if search_term:
                search = f"%{search_term}%"
                query = query.filter(
                    MedicationType.name.ilike(search) | 
                    MedicationType.description.ilike(search)
                )
            
            return query.order_by(MedicationType.name).all()
        except Exception as e:
            logger.error(f"获取药物类型时出错: {str(e)}")
            raise
    
    @staticmethod
    def get_medication_type(type_id):
        """
        获取指定ID的药物类型
        
        参数:
            type_id: 药物类型ID
            
        返回:
            药物类型对象
        """
        try:
            return MedicationType.query.get(type_id)
        except Exception as e:
            logger.error(f"获取药物类型 {type_id} 时出错: {str(e)}")
            raise
    
    @staticmethod
    def update_medication_type(type_id, **kwargs):
        """
        更新药物类型信息
        
        参数:
            type_id: 药物类型ID
            **kwargs: 要更新的字段
            
        返回:
            更新后的药物类型
        """
        try:
            medication_type = MedicationType.query.get(type_id)
            if not medication_type:
                logger.warning(f"药物类型 ID {type_id} 不存在")
                return None
            
            for key, value in kwargs.items():
                if hasattr(medication_type, key):
                    setattr(medication_type, key, value)
            
            medication_type.updated_at = datetime.now()
            db.session.commit()
            logger.info(f"更新了药物类型 {medication_type.name}")
            return medication_type
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新药物类型时出错: {str(e)}")
            raise
    
    @staticmethod
    def create_medication_record(user_id, record_date=None, **kwargs):
        """
        创建药物记录
        
        参数:
            user_id: 用户ID
            record_date: 记录日期
            **kwargs: 药物记录数据
        
        返回:
            成功时返回记录ID和创建成功消息，失败时返回错误信息
        """
        try:
            if record_date is None:
                record_date = datetime.now().date()
            elif isinstance(record_date, str):
                record_date = datetime.strptime(record_date, "%Y-%m-%d").date()
            
            # 处理服药时间
            time_taken = kwargs.get('time_taken')
            if time_taken and isinstance(time_taken, str):
                kwargs['time_taken'] = datetime.strptime(time_taken, "%H:%M").time()
            
            # 创建新记录
            record = HealthRecord(
                user_id=user_id,
                record_date=record_date,
                record_type='medication'
            )
            
            # 如果提供了药物类型ID，获取药物名称
            medication_type_id = kwargs.get('medication_type_id')
            if medication_type_id:
                try:
                    medication_type = MedicationType.query.get(medication_type_id)
                    if medication_type:
                        kwargs['medication_name'] = medication_type.name
                except Exception as e:
                    logger.warning(f"获取药物类型名称失败: {str(e)}")
            
            # 设置药物记录字段
            record.medication_name = kwargs.get('medication_name')
            record.dosage = kwargs.get('dosage')
            record.dosage_unit = kwargs.get('dosage_unit')
            record.frequency = kwargs.get('frequency')
            record.time_taken = kwargs.get('time_taken')
            record.with_food = kwargs.get('with_food')
            record.effectiveness = kwargs.get('effectiveness')
            record.side_effects = kwargs.get('side_effects')
            record.notes = kwargs.get('notes')
            
            # 保存记录
            db.session.add(record)
            db.session.commit()
            
            logger.info(f"创建药物记录成功，用户ID: {user_id}")
            
            return {
                "success": True,
                "message": "药物记录创建成功",
                "record_id": record.id,
                "record": record.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建药物记录失败: {str(e)}")
            return {
                "success": False,
                "message": f"创建记录失败: {str(e)}"
            }
    
    @staticmethod
    def get_medication_records(user_id, start_date=None, end_date=None):
        """获取用户的药物记录
        
        参数:
            user_id: 用户ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        返回:
            包含药物记录的字典
        """
        try:
            # 尝试从HealthRecord表中获取药物记录
            print(f"正在从HealthRecord表中获取用户{user_id}的药物记录")
            
            query = HealthRecord.query.filter(
                HealthRecord.user_id == user_id,
                HealthRecord.record_type == 'medication'
            )
            
            # 如果提供了日期范围，添加日期过滤条件
            if start_date:
                try:
                    if isinstance(start_date, str):
                        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(HealthRecord.record_date >= start_date)
                except Exception as e:
                    print(f"解析开始日期出错: {e}")
            
            if end_date:
                try:
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(HealthRecord.record_date <= end_date)
                except Exception as e:
                    print(f"解析结束日期出错: {e}")
            
            # 按日期降序排序并获取所有结果
            records = query.order_by(HealthRecord.record_date.desc()).all()
            
            # 构建返回数据
            records_data = []
            for record in records:
                try:
                    record_dict = {
                        'id': record.id,
                        'record_date': record.record_date.strftime('%Y-%m-%d') if record.record_date else None,
                        'medication_name': record.medication_name,
                        'dosage': record.dosage,
                        'dosage_unit': record.dosage_unit,
                        'with_food': record.with_food,
                        'time_taken': record.time_taken.strftime('%H:%M') if record.time_taken else None,
                        'effectiveness': record.effectiveness,
                        'side_effects': record.side_effects,
                        'notes': record.notes
                    }
                    records_data.append(record_dict)
                except Exception as e:
                    print(f"处理记录数据时出错: {e}")
            
            return {
                'success': True,
                'message': f'找到{len(records_data)}条药物记录',
                'records': records_data
            }
            
        except Exception as e:
            print(f"获取药物记录时出错: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'message': f'获取药物记录时出错: {str(e)}',
                'records': []
            }
    
    @staticmethod
    def get_medication_record(record_id, user_id):
        """
        获取指定的服药记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID(用于验证所有权)
            
        返回:
            服药记录对象或None（如果不存在）
        """
        try:
            record = HealthRecord.query.filter_by(id=record_id, user_id=user_id, record_type='medication').first()
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
            logger.error(f"获取药物记录 {record_id} 时出错: {str(e)}")
            return {
                "success": False,
                "message": f"获取记录失败: {str(e)}"
            }
    
    @staticmethod
    def update_medication_record(record_id, user_id, **kwargs):
        """
        更新服药记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID
            **kwargs: 要更新的字段
            
        返回:
            更新结果
        """
        try:
            record = HealthRecord.query.filter_by(id=record_id, user_id=user_id, record_type='medication').first()
            
            if not record:
                return {
                    "success": False,
                    "message": "记录不存在或无权访问"
                }
            
            # 处理日期和时间格式
            if 'record_date' in kwargs and isinstance(kwargs['record_date'], str):
                kwargs['record_date'] = datetime.strptime(kwargs['record_date'], '%Y-%m-%d').date()
            
            if 'time_taken' in kwargs and isinstance(kwargs['time_taken'], str):
                kwargs['time_taken'] = datetime.strptime(kwargs['time_taken'], '%H:%M').time()
            
            # 如果提供了药物类型ID，获取药物名称
            medication_type_id = kwargs.get('medication_type_id')
            if medication_type_id:
                try:
                    medication_type = MedicationType.query.get(medication_type_id)
                    if medication_type:
                        kwargs['medication_name'] = medication_type.name
                except Exception as e:
                    logger.warning(f"获取药物类型名称失败: {str(e)}")
            
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            record.updated_at = datetime.now()
            db.session.commit()
            
            return {
                "success": True,
                "message": "药物记录更新成功",
                "record": record.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新药物记录时出错: {str(e)}")
            return {
                "success": False,
                "message": f"更新记录失败: {str(e)}"
            }
    
    @staticmethod
    def delete_medication_record(record_id, user_id):
        """
        删除服药记录
        
        参数:
            record_id: 记录ID
            user_id: 用户ID
            
        返回:
            是否成功删除
        """
        try:
            record = HealthRecord.query.filter_by(id=record_id, user_id=user_id, record_type='medication').first()
            
            if not record:
                return {
                    "success": False,
                    "message": "记录不存在或无权删除"
                }
            
            db.session.delete(record)
            db.session.commit()
            
            return {
                "success": True,
                "message": "药物记录删除成功"
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除药物记录时出错: {str(e)}")
            return {
                "success": False,
                "message": f"删除记录失败: {str(e)}"
            }
    
    @staticmethod
    def get_medication_schedule(user_id, date=None):
        """
        获取用户的服药排程
        
        参数:
            user_id: 用户ID
            date: 可选，指定日期，默认为当天
            
        返回:
            排程列表和状态码
        """
        try:
            result = MedicationRecord.get_medication_schedule(user_id, date)
            
            # 确保排程存在
            if not result:
                return {
                    "success": False,
                    "message": "未找到任何服药排程"
                }, 404
            
            medication_records = []
            for record in result:
                medication_records.append(record.to_dict())
            
            return {
                "success": True,
                "message": "获取服药排程成功",
                "schedule": medication_records
            }, 200
        except Exception as e:
            logger.error(f"获取服药排程时出错: {str(e)}")
            return {
                "success": False,
                "message": f"获取服药排程时出错: {str(e)}"
            }, 500 