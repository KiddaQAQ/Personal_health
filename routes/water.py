from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.water_service import WaterService
from datetime import datetime
from database import db
from models.health_record import HealthRecord
import logging

logger = logging.getLogger(__name__)

# 创建水分摄入蓝图
water_bp = Blueprint('water', __name__, url_prefix='/api/water-intake')

@water_bp.route('/records', methods=['POST'])
@jwt_required()
def create_water_record():
    """创建新的饮水记录"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '数据不能为空'}), 400
    
    # 检查必要字段
    required_fields = ['amount']
    if not all(field in data for field in required_fields):
        missing_fields = [field for field in required_fields if field not in data]
        return jsonify({
            'success': False, 
            'message': f'缺少必要字段: {", ".join(missing_fields)}'
        }), 400
    
    # 创建记录
    result = WaterService.create_water_record(
        user_id=user_id,
        record_date=data.get('record_date'),
        amount=data.get('amount'),
        water_type=data.get('water_type'),
        intake_time=data.get('intake_time'),
        notes=data.get('notes')
    )
    
    status_code = 201 if result.get('success') else 400
    return jsonify(result), status_code

@water_bp.route('/records', methods=['GET'])
@jwt_required()
def get_water_records():
    """获取饮水记录列表"""
    user_id = get_jwt_identity()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    result = WaterService.get_water_records(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify(result), 200 if result.get('success') else 400 

@water_bp.route('/records/<int:record_id>', methods=['GET'])
@jwt_required()
def get_water_record(record_id):
    """获取单个饮水记录"""
    user_id = get_jwt_identity()
    
    try:
        result = WaterService.get_water_record(record_id, user_id)
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"获取饮水记录 {record_id} 时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500 

@water_bp.route('/records/<int:record_id>', methods=['PUT'])
@jwt_required()
def update_water_record(record_id):
    """更新饮水记录"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '数据不能为空'}), 400
    
    try:
        # 先获取记录
        record = HealthRecord.query.filter_by(id=record_id, user_id=user_id, record_type='water').first()
        
        if not record:
            return jsonify({'success': False, 'message': '记录不存在或无权修改'}), 404
        
        # 更新字段
        if 'amount' in data:
            record.water_amount = data['amount']
        
        if 'water_type' in data:
            record.water_type = data['water_type']
            
        if 'intake_time' in data and data['intake_time']:
            try:
                record.intake_time = datetime.strptime(data['intake_time'], "%H:%M").time()
            except ValueError:
                pass
        
        if 'notes' in data:
            record.notes = data['notes']
            
        if 'record_date' in data and data['record_date']:
            try:
                record.record_date = datetime.strptime(data['record_date'], "%Y-%m-%d").date()
            except ValueError:
                pass
        
        # 保存更改
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '饮水记录更新成功',
            'record': record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新饮水记录 {record_id} 时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@water_bp.route('/records/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_water_record(record_id):
    """删除饮水记录"""
    user_id = get_jwt_identity()
    
    try:
        # 查找记录
        record = HealthRecord.query.filter_by(id=record_id, user_id=user_id, record_type='water').first()
        
        if not record:
            return jsonify({'success': False, 'message': '记录不存在或无权删除'}), 404
        
        # 删除记录
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '饮水记录删除成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除饮水记录 {record_id} 时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500 