from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.social import Share, Like, Comment, SHARABLE_TYPES
from database import db
import json
from sqlalchemy import and_, desc
from datetime import datetime
from werkzeug.exceptions import NotFound, BadRequest, Forbidden

# 创建蓝图
social_bp = Blueprint('social', __name__)

# 辅助函数：获取当前登录用户ID
def get_current_user_id():
    return get_jwt_identity()

# 辅助函数：授权检查
def authorize_user(obj, user_id):
    if obj.user_id != user_id:
        raise Forbidden("无权进行此操作")

#------------------分享功能------------------#

@social_bp.route('/share', methods=['POST'])
@jwt_required()
def create_share():
    """创建一个新的分享"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        print(f"创建分享API请求数据: {data}")
        
        # 验证必需字段
        if not all(k in data for k in ['content_type', 'content_id']):
            return jsonify({'error': '缺少必要字段'}), 400
        
        # 验证内容类型
        if data['content_type'] not in SHARABLE_TYPES:
            return jsonify({'error': f'无效的内容类型: {data["content_type"]}，有效类型: {SHARABLE_TYPES}'}), 400
        
        # 确保content_id是整数
        try:
            content_id = int(data['content_id'])
        except (ValueError, TypeError):
            return jsonify({'error': f'内容ID必须是整数，当前值: {data["content_id"]}'}), 400
        
        # 创建新分享
        new_share = Share(
            user_id=user_id,
            content_type=data['content_type'],
            content_id=content_id,
            description=data.get('description', ''),
            visibility=data.get('visibility', 'public')
        )
        
        print(f"检查分享内容是否有效: {data['content_type']}, ID: {content_id}")
        
        # 检查分享内容是否有效
        if not new_share.is_content_valid():
            return jsonify({'error': f'分享的内容不存在或已被删除: {data["content_type"]}, ID: {content_id}'}), 400
        
        db.session.add(new_share)
        db.session.commit()
        
        return jsonify({'message': '分享成功', 'share': new_share.to_dict()}), 201
    except Exception as e:
        print(f"创建分享时出错: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'创建分享时发生错误: {str(e)}'}), 500

@social_bp.route('/share/<int:share_id>', methods=['GET'])
@jwt_required()
def get_share(share_id):
    """获取单个分享的详细信息"""
    share = Share.query.get_or_404(share_id)
    
    # 检查可见性权限
    user_id = get_current_user_id()
    if share.visibility != 'public' and share.user_id != user_id:
        if share.visibility == 'private':
            return jsonify({'error': '无权查看此分享'}), 403
        # TODO: 如果有朋友关系功能，这里可以检查朋友关系
    
    return jsonify(share.to_dict(current_user_id=user_id)), 200

@social_bp.route('/shares', methods=['GET'])
@jwt_required()
def get_shares():
    """获取分享列表，支持分页和过滤"""
    user_id = get_current_user_id()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    content_type = request.args.get('content_type')
    user_filter = request.args.get('user_id', type=int)
    
    # 构建查询
    query = Share.query
    
    # 过滤条件
    if content_type:
        query = query.filter_by(content_type=content_type)
    
    if user_filter:
        query = query.filter_by(user_id=user_filter)
    else:
        # 未指定用户时，只显示公开的分享或自己的分享
        query = query.filter(
            (Share.visibility == 'public') | 
            (Share.user_id == user_id)
        )
    
    # 按时间降序排序
    query = query.order_by(desc(Share.created_at))
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 构建响应，传入当前用户ID以确定点赞状态
    shares = [share.to_dict(current_user_id=user_id) for share in pagination.items]
    
    return jsonify({
        'shares': shares,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@social_bp.route('/share/<int:share_id>', methods=['PUT'])
@jwt_required()
def update_share(share_id):
    """更新分享信息"""
    user_id = get_current_user_id()
    share = Share.query.get_or_404(share_id)
    
    # 授权检查
    authorize_user(share, user_id)
    
    data = request.get_json()
    
    # 可更新的字段
    if 'description' in data:
        share.description = data['description']
    
    if 'visibility' in data:
        if data['visibility'] in ['public', 'friends', 'private']:
            share.visibility = data['visibility']
        else:
            return jsonify({'error': '无效的可见性设置'}), 400
    
    db.session.commit()
    return jsonify({'message': '分享已更新', 'share': share.to_dict()}), 200

@social_bp.route('/share/<int:share_id>', methods=['DELETE'])
@jwt_required()
def delete_share(share_id):
    """删除分享"""
    user_id = get_current_user_id()
    share = Share.query.get_or_404(share_id)
    
    # 授权检查
    authorize_user(share, user_id)
    
    db.session.delete(share)
    db.session.commit()
    
    return jsonify({'message': '分享已删除'}), 200

#------------------点赞功能------------------#

@social_bp.route('/share/<int:share_id>/like', methods=['POST'])
@jwt_required()
def like_share(share_id):
    """给分享点赞"""
    user_id = get_current_user_id()
    share = Share.query.get_or_404(share_id)
    
    # 检查是否已点赞
    existing_like = Like.query.filter_by(user_id=user_id, share_id=share_id).first()
    if existing_like:
        return jsonify({'message': '已经点过赞了', 'like': existing_like.to_dict()}), 200
    
    # 创建新的点赞
    new_like = Like(user_id=user_id, share_id=share_id)
    db.session.add(new_like)
    db.session.commit()
    
    return jsonify({'message': '点赞成功', 'like': new_like.to_dict()}), 201

@social_bp.route('/share/<int:share_id>/like', methods=['DELETE'])
@jwt_required()
def unlike_share(share_id):
    """取消点赞"""
    user_id = get_current_user_id()
    like = Like.query.filter_by(user_id=user_id, share_id=share_id).first()
    
    if not like:
        return jsonify({'message': '未找到点赞记录'}), 404
    
    db.session.delete(like)
    db.session.commit()
    
    return jsonify({'message': '已取消点赞'}), 200

@social_bp.route('/share/<int:share_id>/likes', methods=['GET'])
@jwt_required()
def get_likes(share_id):
    """获取分享的点赞列表"""
    # 验证分享存在
    share = Share.query.get_or_404(share_id)
    
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 查询点赞
    pagination = Like.query.filter_by(share_id=share_id).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    likes = [like.to_dict() for like in pagination.items]
    
    return jsonify({
        'likes': likes,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

#------------------评论功能------------------#

@social_bp.route('/share/<int:share_id>/comment', methods=['POST'])
@jwt_required()
def add_comment(share_id):
    """添加评论"""
    user_id = get_current_user_id()
    share = Share.query.get_or_404(share_id)
    
    data = request.get_json()
    
    # 验证必需字段
    if 'content' not in data or not data['content'].strip():
        return jsonify({'error': '评论内容不能为空'}), 400
    
    # 创建新评论
    new_comment = Comment(
        user_id=user_id,
        share_id=share_id,
        content=data['content'],
        parent_id=data.get('parent_id')  # 如果是回复其他评论
    )
    
    # 如果是回复，验证父评论存在
    if new_comment.parent_id:
        parent = Comment.query.get(new_comment.parent_id)
        if not parent or parent.share_id != share_id:
            return jsonify({'error': '回复的评论不存在或不属于此分享'}), 400
    
    db.session.add(new_comment)
    db.session.commit()
    
    return jsonify({'message': '评论成功', 'comment': new_comment.to_dict()}), 201

@social_bp.route('/comment/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """更新评论"""
    user_id = get_current_user_id()
    comment = Comment.query.get_or_404(comment_id)
    
    # 授权检查
    authorize_user(comment, user_id)
    
    data = request.get_json()
    
    # 验证必需字段
    if 'content' not in data or not data['content'].strip():
        return jsonify({'error': '评论内容不能为空'}), 400
    
    comment.content = data['content']
    db.session.commit()
    
    return jsonify({'message': '评论已更新', 'comment': comment.to_dict()}), 200

@social_bp.route('/comment/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """删除评论"""
    user_id = get_current_user_id()
    comment = Comment.query.get_or_404(comment_id)
    
    # 授权检查 - 允许评论作者或分享作者删除评论
    share = Share.query.get(comment.share_id)
    if comment.user_id != user_id and share.user_id != user_id:
        return jsonify({'error': '无权删除此评论'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': '评论已删除'}), 200

@social_bp.route('/share/<int:share_id>/comments', methods=['GET'])
@jwt_required()
def get_comments(share_id):
    """获取分享的评论列表"""
    # 验证分享存在
    share = Share.query.get_or_404(share_id)
    
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 只获取顶级评论（非回复）
    query = Comment.query.filter_by(share_id=share_id, parent_id=None)
    
    # 按时间排序
    query = query.order_by(Comment.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 构建响应，包含评论的回复
    comments = [comment.to_dict(include_replies=True) for comment in pagination.items]
    
    return jsonify({
        'comments': comments,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200 