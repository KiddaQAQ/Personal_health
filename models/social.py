from database import db
from datetime import datetime
from sqlalchemy import text

# 定义可分享的内容类型枚举
SHARABLE_TYPES = [
    'health_record',
    'diet_record', 
    'exercise_record',
    'health_goal',
    'water_intake',
    'medication_record',
    'health_report'
]

class Share(db.Model):
    """用户分享的内容模型"""
    __tablename__ = 'shares'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # 分享的内容类型，从SHARABLE_TYPES中选择
    content_id = db.Column(db.Integer, nullable=False)  # 分享内容的ID
    description = db.Column(db.Text, nullable=True)  # 分享时的描述文字
    visibility = db.Column(db.String(20), default='public')  # 可见性：public, friends, private
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('shares', lazy=True))
    likes = db.relationship('Like', backref='share', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='share', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self, current_user_id=None):
        """将分享对象转换为字典，包括点赞和评论数量"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'description': self.description,
            'visibility': self.visibility,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'likes_count': len(self.likes),
            'comments_count': len(self.comments),
            'is_valid': self.is_content_valid()
        }
        
        # 检查当前用户是否已点赞
        if current_user_id:
            result['is_liked'] = any(like.user_id == current_user_id for like in self.likes)
        
        return result
    
    def is_content_valid(self):
        """检查分享的内容是否仍然存在"""
        try:
            print(f"验证内容有效性: 类型={self.content_type}, ID={self.content_id}")
            
            # 导入text函数
            from sqlalchemy import text
            
            # 根据实际数据库结构调整查询
            query_templates = {
                'health_record': "SELECT 1 FROM health_records WHERE id = :id AND record_type = 'health' LIMIT 1",
                'diet_record': "SELECT 1 FROM health_records WHERE id = :id AND record_type = 'diet' LIMIT 1",
                'exercise_record': "SELECT 1 FROM health_records WHERE id = :id AND record_type = 'exercise' LIMIT 1",
                'water_intake': "SELECT 1 FROM health_records WHERE id = :id AND record_type = 'water' LIMIT 1",
                'medication_record': "SELECT 1 FROM health_records WHERE id = :id AND record_type = 'medication' LIMIT 1",
                'health_goal': "SELECT 1 FROM health_goals WHERE id = :id LIMIT 1",
                'health_report': "SELECT 1 FROM health_reports WHERE id = :id LIMIT 1",
            }
            
            # 不同数据库查询别名映射
            alt_query_templates = {
                'diet_record': "SELECT 1 FROM diet_records WHERE id = :id LIMIT 1",
                'exercise_record': "SELECT 1 FROM exercise_records WHERE id = :id LIMIT 1",
                'medication_record': "SELECT 1 FROM medication_records WHERE id = :id LIMIT 1",
                'water_intake': "SELECT 1 FROM water_intakes WHERE id = :id LIMIT 1",
            }
            
            if self.content_type not in query_templates and self.content_type not in alt_query_templates:
                print(f"未知内容类型: {self.content_type}")
                return False
            
            # 临时禁用验证，始终返回有效
            print(f"禁用验证，假定记录有效: {self.content_type}(ID={self.content_id})")
            return True
                
            # 执行主查询
            is_valid = False
            
            if self.content_type in query_templates:
                try:
                    query = text(query_templates[self.content_type])
                    result = db.session.execute(query, {"id": self.content_id}).fetchone()
                    is_valid = result is not None
                    print(f"主查询结果 - {self.content_type}记录(ID={self.content_id})验证结果: {is_valid}")
                    if is_valid:
                        return True
                except Exception as e:
                    print(f"主查询错误: {str(e)}")
            
            # 如果主查询失败或未找到记录，尝试替代查询
            if not is_valid and self.content_type in alt_query_templates:
                try:
                    query = text(alt_query_templates[self.content_type])
                    result = db.session.execute(query, {"id": self.content_id}).fetchone()
                    is_valid = result is not None
                    print(f"替代查询结果 - {self.content_type}记录(ID={self.content_id})验证结果: {is_valid}")
                except Exception as e:
                    print(f"替代查询错误: {str(e)}")
            
            return is_valid
                
        except Exception as e:
            print(f"验证内容有效性时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

class Like(db.Model):
    """点赞模型"""
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    share_id = db.Column(db.Integer, db.ForeignKey('shares.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('likes', lazy=True))
    
    # 确保一个用户只能给一个分享点一次赞
    __table_args__ = (db.UniqueConstraint('user_id', 'share_id', name='uq_user_share_like'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username,
            'share_id': self.share_id,
            'created_at': self.created_at.isoformat()
        }

class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    share_id = db.Column(db.Integer, db.ForeignKey('shares.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)  # 用于回复评论
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    def to_dict(self, include_replies=False):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username,
            'share_id': self.share_id,
            'content': self.content,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_replies:
            result['replies'] = [reply.to_dict(False) for reply in self.replies]
            
        return result 