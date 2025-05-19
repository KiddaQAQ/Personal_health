from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.medication_service import MedicationService
from utils.request_utils import validate_params, get_pagination_params
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

medication_bp = Blueprint('medication', __name__, url_prefix='/api/medication')

# 药物类型路由
@medication_bp.route('/types', methods=['POST'])
@jwt_required()
def create_medication_type():
    """创建新的药物类型"""
    try:
        data = request.get_json()
        required_params = ['name']
        optional_params = ['category', 'description', 'common_dosage', 'side_effects', 'precautions']
        
        if not validate_params(data, required_params):
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
            
        medication_type = MedicationService.create_medication_type(
            name=data['name'],
            category=data.get('category'),
            description=data.get('description'),
            common_dosage=data.get('common_dosage'),
            side_effects=data.get('side_effects'),
            precautions=data.get('precautions')
        )
        
        return jsonify({
            'success': True,
            'message': '药物类型创建成功',
            'data': medication_type.to_dict()
        }), 201
    except Exception as e:
        logger.error(f"创建药物类型时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

@medication_bp.route('/types', methods=['GET'])
@jwt_required()
def get_medication_types():
    """获取药物类型列表"""
    category = request.args.get('category')
    search = request.args.get('search')
    
    try:
        medication_types = MedicationService.get_medication_types(category, search)
        return jsonify({
            'success': True,
            'medication_types': [mt.to_dict() for mt in medication_types]
        }), 200
    except Exception as e:
        logger.error(f"获取药物类型列表时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取药物类型列表时出错: {str(e)}",
            'medication_types': []
        }), 500

@medication_bp.route('/types/<int:type_id>', methods=['GET'])
@jwt_required()
def get_medication_type(type_id):
    """获取单个药物类型详情"""
    try:
        medication_type = MedicationService.get_medication_type(type_id)
        if not medication_type:
            return jsonify({
                'success': False,
                'message': f"未找到ID为{type_id}的药物类型"
            }), 404
        
        return jsonify({
            'success': True,
            'medication_type': medication_type.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"获取药物类型详情时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取药物类型详情时出错: {str(e)}"
        }), 500

@medication_bp.route('/types/<int:type_id>', methods=['PUT'])
@jwt_required()
def update_medication_type(type_id):
    """更新药物类型信息"""
    try:
        data = request.get_json()
        optional_params = ['name', 'category', 'description', 'common_dosage', 'side_effects', 'precautions']
        
        update_data = {k: v for k, v in data.items() if k in optional_params}
        if not update_data:
            return jsonify({'success': False, 'message': '没有提供有效的更新字段'}), 400
            
        medication_type = MedicationService.update_medication_type(
            type_id=type_id,
            **update_data
        )
        
        if not medication_type:
            return jsonify({'success': False, 'message': '未找到药物类型'}), 404
            
        return jsonify({
            'success': True,
            'message': '药物类型更新成功',
            'data': medication_type.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"更新药物类型 {type_id} 时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

# 药物记录路由
@medication_bp.route('/records', methods=['POST'])
@jwt_required()
def create_medication_record():
    """创建新的服药记录"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '数据不能为空'}), 400
    
    # 检查必要字段
    required_fields = ['medication_type_id', 'record_date', 'dosage', 'dosage_unit']
    if not all(field in data for field in required_fields):
        missing_fields = [field for field in required_fields if field not in data]
        return jsonify({
            'success': False, 
            'message': f'缺少必要字段: {", ".join(missing_fields)}'
        }), 400
    
    try:
        # 记录请求数据，便于调试
        logger.info(f"接收到的药物记录数据: {data}")
        
        result = MedicationService.create_medication_record(
            user_id=user_id,
            record_date=data['record_date'],
            medication_type_id=data['medication_type_id'],
            medication_name=data.get('medication_name'),
            time_taken=data.get('time_taken'),
            dosage=data['dosage'],
            dosage_unit=data['dosage_unit'],
            frequency=data.get('frequency'),
            with_food=data.get('with_food', False),
            effectiveness=data.get('effectiveness'),
            side_effects=data.get('side_effects'),
            notes=data.get('notes')
        )
        
        status_code = 201 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"创建服药记录时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"创建服药记录时出错: {str(e)}"
        }), 500

@medication_bp.route('/records', methods=['GET'])
@jwt_required()
def get_user_medication_records():
    """获取用户的服药记录"""
    try:
        user_id = get_jwt_identity()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 从HealthRecord表中获取药物记录
        result = MedicationService.get_medication_records(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"获取用户服药记录时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

@medication_bp.route('/records/<int:record_id>', methods=['GET'])
@jwt_required()
def get_medication_record(record_id):
    """获取指定的服药记录"""
    try:
        user_id = get_jwt_identity()
        result = MedicationService.get_medication_record(record_id, user_id)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"获取服药记录 {record_id} 时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

@medication_bp.route('/records/<int:record_id>', methods=['PUT'])
@jwt_required()
def update_medication_record(record_id):
    """更新服药记录"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '没有提供有效的更新字段'}), 400
            
        result = MedicationService.update_medication_record(
            record_id=record_id,
            user_id=user_id,
            **data
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"更新服药记录 {record_id} 时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

@medication_bp.route('/records/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_medication_record(record_id):
    """删除服药记录"""
    try:
        user_id = get_jwt_identity()
        result = MedicationService.delete_medication_record(record_id, user_id)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"删除服药记录 {record_id} 时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

@medication_bp.route('/schedule', methods=['GET'])
@jwt_required()
def get_medication_schedule():
    """获取用户的服药计划"""
    try:
        user_id = get_jwt_identity()
        date = request.args.get('date')
        
        schedule = MedicationService.get_medication_schedule(user_id, date)
        
        return jsonify({
            'success': True,
            'data': schedule
        }), 200
    except Exception as e:
        logger.error(f"获取用户服药计划时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500 