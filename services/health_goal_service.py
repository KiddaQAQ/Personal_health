from database import db
from models.health_goal import HealthGoal, HealthGoalLog
from datetime import datetime

class HealthGoalService:
    @staticmethod
    def create_health_goal(user_id, goal_type, target_value, current_value=None, 
                         start_date=None, end_date=None, notes=None):
        """创建新的健康目标"""
        # 处理日期
        if start_date and isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = datetime.utcnow().date()
            
        if end_date and isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 创建健康目标
        health_goal = HealthGoal(
            user_id=user_id,
            goal_type=goal_type,
            target_value=target_value,
            current_value=current_value,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
            status='active'
        )
        
        db.session.add(health_goal)
        db.session.commit()
        
        return {'success': True, 'message': '健康目标创建成功', 'health_goal': health_goal.to_dict()}, 201
    
    @staticmethod
    def get_user_health_goals(user_id, status=None, goal_type=None):
        """获取用户的健康目标"""
        query = HealthGoal.query.filter_by(user_id=user_id)
        
        # 按状态过滤
        if status:
            query = query.filter(HealthGoal.status == status)
        
        # 按目标类型过滤
        if goal_type:
            query = query.filter(HealthGoal.goal_type == goal_type)
        
        # 按创建日期排序
        goals = query.order_by(HealthGoal.created_at.desc()).all()
        
        return {'success': True, 'goals': [goal.to_dict() for goal in goals]}, 200
    
    @staticmethod
    def get_health_goal(goal_id, user_id):
        """获取单个健康目标"""
        goal = HealthGoal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            return {'success': False, 'message': '目标不存在'}, 404
        
        # 获取目标相关的日志
        logs = HealthGoalLog.query.filter_by(goal_id=goal_id).order_by(HealthGoalLog.log_date).all()
        logs_data = [log.to_dict() for log in logs]
        
        goal_data = goal.to_dict()
        goal_data['logs'] = logs_data
        goal_data['progress'] = goal.calculate_progress()
        
        return {'success': True, 'goal': goal_data}, 200
    
    @staticmethod
    def update_health_goal(goal_id, user_id, data):
        """更新健康目标"""
        goal = HealthGoal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            return {'success': False, 'message': '目标不存在'}, 404
        
        # 更新字段
        if 'goal_type' in data:
            goal.goal_type = data['goal_type']
        
        if 'target_value' in data:
            goal.target_value = data['target_value']
        
        if 'current_value' in data:
            goal.current_value = data['current_value']
            
            # 如果当前值达到或超过目标值，自动将状态设为已完成
            if goal.goal_type in ['weight_loss', 'fat_loss']:
                # 对于减重目标，当前值低于等于目标值时表示达成
                if goal.current_value <= goal.target_value:
                    goal.status = 'completed'
                    if not goal.end_date:
                        goal.end_date = datetime.utcnow().date()
            else:
                # 对于增长目标，当前值高于等于目标值时表示达成
                if goal.current_value >= goal.target_value:
                    goal.status = 'completed'
                    if not goal.end_date:
                        goal.end_date = datetime.utcnow().date()
        
        if 'start_date' in data:
            if isinstance(data['start_date'], str):
                goal.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            else:
                goal.start_date = data['start_date']
        
        if 'end_date' in data:
            if isinstance(data['end_date'], str):
                goal.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            else:
                goal.end_date = data['end_date']
        
        if 'status' in data:
            goal.status = data['status']
            
            # 如果状态为已完成，且没有设置结束日期，则设置为当前日期
            if goal.status == 'completed' and not goal.end_date:
                goal.end_date = datetime.utcnow().date()
        
        if 'notes' in data:
            goal.notes = data['notes']
        
        db.session.commit()
        
        return {'success': True, 'message': '健康目标更新成功', 'goal': goal.to_dict()}, 200
    
    @staticmethod
    def delete_health_goal(goal_id, user_id):
        """删除健康目标"""
        goal = HealthGoal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            return {'success': False, 'message': '目标不存在'}, 404
        
        # 删除相关的日志
        HealthGoalLog.query.filter_by(goal_id=goal_id).delete()
        
        # 删除目标
        db.session.delete(goal)
        db.session.commit()
        
        return {'success': True, 'message': '健康目标删除成功'}, 200
    
    @staticmethod
    def add_goal_log(goal_id, user_id, log_date, value, notes=None):
        """添加健康目标日志"""
        # 检查目标是否存在
        goal = HealthGoal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            return {'success': False, 'message': '目标不存在'}, 404
        
        # 转换日期字符串为日期对象
        if isinstance(log_date, str):
            log_date = datetime.strptime(log_date, '%Y-%m-%d').date()
        
        # 创建日志
        goal_log = HealthGoalLog(
            goal_id=goal_id,
            log_date=log_date,
            value=value,
            notes=notes
        )
        
        db.session.add(goal_log)
        
        # 更新目标的当前值
        goal.current_value = value
        
        # 如果当前值达到或超过目标值，自动将状态设为已完成
        if goal.goal_type in ['weight_loss', 'fat_loss']:
            # 对于减重目标，当前值低于等于目标值时表示达成
            if goal.current_value <= goal.target_value:
                goal.status = 'completed'
                if not goal.end_date:
                    goal.end_date = log_date
        else:
            # 对于增长目标，当前值高于等于目标值时表示达成
            if goal.current_value >= goal.target_value:
                goal.status = 'completed'
                if not goal.end_date:
                    goal.end_date = log_date
        
        db.session.commit()
        
        return {'success': True, 'message': '目标日志添加成功', 'log': goal_log.to_dict()}, 201
    
    @staticmethod
    def get_goal_logs(goal_id, user_id):
        """获取目标的所有日志"""
        # 检查目标是否存在
        goal = HealthGoal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            return {'success': False, 'message': '目标不存在'}, 404
        
        # 获取日志
        logs = HealthGoalLog.query.filter_by(goal_id=goal_id).order_by(HealthGoalLog.log_date).all()
        
        return {'success': True, 'logs': [log.to_dict() for log in logs]}, 200 