from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.health_metrics_service import HealthMetricsService
import logging

logger = logging.getLogger(__name__)

# 创建健康指标蓝图
health_metrics_bp = Blueprint('health_metrics', __name__, url_prefix='/api/health-metrics')

@health_metrics_bp.route('/records', methods=['POST'])
@jwt_required()
def create_health_metrics_record():
    """创建新的健康指标记录"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '数据不能为空'}), 400
    
    # 创建记录
    result = HealthMetricsService.create_health_metrics_record(
        user_id=user_id,
        record_date=data.get('record_date'),
        weight=data.get('weight'),
        height=data.get('height'),
        bmi=data.get('bmi'),
        blood_pressure_systolic=data.get('blood_pressure_systolic'),
        blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
        heart_rate=data.get('heart_rate'),
        blood_sugar=data.get('blood_sugar'),
        body_fat=data.get('body_fat'),
        sleep_hours=data.get('sleep_hours'),
        steps=data.get('steps'),
        notes=data.get('notes')
    )
    
    status_code = 201 if result.get('success') else 400
    return jsonify(result), status_code

@health_metrics_bp.route('/records', methods=['GET'])
@jwt_required()
def get_health_metrics_records():
    """获取健康指标记录列表"""
    user_id = get_jwt_identity()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    result = HealthMetricsService.get_health_metrics_records(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify(result), 200 if result.get('success') else 400 

@health_metrics_bp.route('/records/<int:record_id>', methods=['GET'])
@jwt_required()
def get_health_metrics_record(record_id):
    """获取单个健康指标记录"""
    user_id = get_jwt_identity()
    
    try:
        result = HealthMetricsService.get_health_metrics_record(record_id, user_id)
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"获取健康指标记录 {record_id} 时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500 