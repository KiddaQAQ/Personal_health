from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.water_intake_service import WaterIntakeService
from utils.validation import validate_request_json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

water_intake_bp = Blueprint('water_intake', __name__)

@water_intake_bp.route('/records', methods=['POST'])
@jwt_required()
def create_water_intake_record():
    """创建新的水摄入记录"""
    current_user_id = get_jwt_identity()
    schema = {
        "type": "object",
        "required": ["amount", "record_date"],
        "properties": {
            "amount": {"type": "number", "minimum": 0},
            "record_date": {"type": "string", "format": "date"},
            "intake_time": {"type": "string", "format": "time"},
            "water_type": {"type": "string"},
            "notes": {"type": "string"}
        }
    }
    
    data = request.get_json()
    validation_result = validate_request_json(data, schema)
    
    if validation_result:
        return jsonify({"error": validation_result}), 422
    
    try:
        # 如果没有提供intake_time，使用当前时间
        if 'intake_time' not in data or not data['intake_time']:
            data['intake_time'] = datetime.now().strftime('%H:%M:%S')
            
        record = WaterIntakeService.create_water_intake(
            user_id=current_user_id,
            amount=data['amount'],
            record_date=data['record_date'],
            intake_time=data['intake_time'],
            water_type=data.get('water_type'),
            notes=data.get('notes')
        )
        
        return jsonify({
            "message": "水摄入记录已创建",
            "record": record
        }), 201
    except Exception as e:
        logger.error(f"创建水摄入记录时出错: {str(e)}")
        return jsonify({"error": f"创建水摄入记录失败: {str(e)}"}), 500

@water_intake_bp.route('/records', methods=['GET'])
@jwt_required()
def get_water_intake_records():
    """获取用户的水摄入记录"""
    current_user_id = get_jwt_identity()
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        records = WaterIntakeService.get_water_intake_records(
            user_id=current_user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            "records": records,
            "count": len(records)
        }), 200
    except Exception as e:
        logger.error(f"获取水摄入记录时出错: {str(e)}")
        return jsonify({"error": f"获取水摄入记录失败: {str(e)}"}), 500

@water_intake_bp.route('/records/<int:record_id>', methods=['GET'])
@jwt_required()
def get_water_intake_record(record_id):
    """获取特定的水摄入记录"""
    current_user_id = get_jwt_identity()
    
    try:
        record = WaterIntakeService.get_water_intake_record(
            record_id=record_id,
            user_id=current_user_id
        )
        
        if not record:
            return jsonify({"error": "记录不存在或无权访问"}), 404
            
        return jsonify(record), 200
    except Exception as e:
        logger.error(f"获取水摄入记录 {record_id} 时出错: {str(e)}")
        return jsonify({"error": f"获取水摄入记录失败: {str(e)}"}), 500

@water_intake_bp.route('/records/<int:record_id>', methods=['PUT'])
@jwt_required()
def update_water_intake_record(record_id):
    """更新水摄入记录"""
    current_user_id = get_jwt_identity()
    
    schema = {
        "type": "object",
        "properties": {
            "amount": {"type": "number", "minimum": 0},
            "record_date": {"type": "string", "format": "date"},
            "intake_time": {"type": "string", "format": "time"},
            "water_type": {"type": "string"},
            "notes": {"type": "string"}
        }
    }
    
    data = request.get_json()
    validation_result = validate_request_json(data, schema)
    
    if validation_result:
        return jsonify({"error": validation_result}), 422
        
    if not data:
        return jsonify({"error": "请提供至少一个要更新的字段"}), 422
    
    try:
        updated_record = WaterIntakeService.update_water_intake(
            record_id=record_id,
            user_id=current_user_id,
            **data
        )
        
        if not updated_record:
            return jsonify({"error": "记录不存在或无权更新"}), 404
            
        return jsonify({
            "message": "水摄入记录已更新",
            "record": updated_record
        }), 200
    except Exception as e:
        logger.error(f"更新水摄入记录 {record_id} 时出错: {str(e)}")
        return jsonify({"error": f"更新水摄入记录失败: {str(e)}"}), 500

@water_intake_bp.route('/records/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_water_intake_record(record_id):
    """删除水摄入记录"""
    current_user_id = get_jwt_identity()
    
    try:
        success = WaterIntakeService.delete_water_intake(
            record_id=record_id,
            user_id=current_user_id
        )
        
        if not success:
            return jsonify({"error": "记录不存在或无权删除"}), 404
            
        return jsonify({"message": "水摄入记录已删除"}), 200
    except Exception as e:
        logger.error(f"删除水摄入记录 {record_id} 时出错: {str(e)}")
        return jsonify({"error": f"删除水摄入记录失败: {str(e)}"}), 500

@water_intake_bp.route('/summary/daily', methods=['GET'])
@jwt_required()
def get_daily_water_summary():
    """获取每日水摄入摘要"""
    current_user_id = get_jwt_identity()
    
    date_str = request.args.get('date')
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        summary = WaterIntakeService.get_daily_summary(
            user_id=current_user_id,
            date=date_str
        )
        
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"获取每日水摄入摘要时出错: {str(e)}")
        return jsonify({"error": f"获取每日水摄入摘要失败: {str(e)}"}), 500

@water_intake_bp.route('/summary/weekly', methods=['GET'])
@jwt_required()
def get_weekly_water_summary():
    """获取每周水摄入摘要"""
    current_user_id = get_jwt_identity()
    
    end_date_str = request.args.get('end_date')
    if not end_date_str:
        end_date_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # 默认获取截至指定日期的前7天数据
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        start_date = end_date - timedelta(days=6)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        summary = WaterIntakeService.get_weekly_summary(
            user_id=current_user_id,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"获取每周水摄入摘要时出错: {str(e)}")
        return jsonify({"error": f"获取每周水摄入摘要失败: {str(e)}"}), 500 