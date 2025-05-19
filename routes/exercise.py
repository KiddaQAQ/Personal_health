from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.exercise_service import ExerciseService
import logging

logger = logging.getLogger(__name__)

# 创建运动蓝图
exercise_bp = Blueprint('exercise', __name__, url_prefix='/api/exercise')

# 运动类型相关路由
@exercise_bp.route('/types', methods=['POST'])
@jwt_required()
def create_exercise_type():
    """创建新的运动类型"""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'success': False, 'message': '运动类型名称不能为空'}), 400
    
    result, status_code = ExerciseService.create_exercise_type(
        name=data['name'],
        category=data.get('category'),
        met_value=data.get('met_value'),
        description=data.get('description')
    )
    
    return jsonify(result), status_code

@exercise_bp.route('/types', methods=['GET'])
@jwt_required()
def get_exercise_types():
    """获取运动类型列表"""
    category = request.args.get('category')
    search = request.args.get('search')
    
    result = ExerciseService.get_exercise_types(category, search)
    
    # 确保返回的数据格式一致
    if result.get('success') and 'data' in result:
        return jsonify(result), 200
    else:
        # 如果没有数据字段，添加空数据字段
        return jsonify({
            'success': result.get('success', False),
            'message': result.get('message', '未找到运动类型数据'),
            'data': []
        }), 200 if result.get('success') else 400

@exercise_bp.route('/types/<int:type_id>', methods=['GET'])
@jwt_required()
def get_exercise_type(type_id):
    """获取单个运动类型详情"""
    result, status_code = ExerciseService.get_exercise_type(type_id)
    return jsonify(result), status_code

@exercise_bp.route('/types/initialize', methods=['POST'])
@jwt_required()
def initialize_exercise_types():
    """初始化预设的运动类型数据"""
    try:
        result = ExerciseService.initialize_exercise_types()
        return jsonify(result), 200 if result.get('success') else 500
    except Exception as e:
        logger.error(f"初始化运动类型数据时发生错误: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"初始化运动类型数据时发生错误: {str(e)}"
        }), 500

# 运动记录相关路由
@exercise_bp.route('/records', methods=['POST'])
@jwt_required()
def create_exercise_record():
    """创建新的运动记录"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '数据不能为空'}), 400
    
    # 检查必要字段
    required_fields = ['exercise_type_id', 'duration']
    if not all(field in data for field in required_fields):
        missing_fields = [field for field in required_fields if field not in data]
        return jsonify({
            'success': False, 
            'message': f'缺少必要字段: {", ".join(missing_fields)}'
        }), 400
    
    # 创建记录
    result = ExerciseService.create_exercise_record(
        user_id=user_id,
        record_date=data.get('record_date'),
        exercise_type_id=data.get('exercise_type_id'),
        duration=data.get('duration'),
        intensity=data.get('intensity'),
        calories_burned=data.get('calories_burned'),
        distance=data.get('distance'),
        notes=data.get('notes')
    )
    
    status_code = 201 if result.get('success') else 400
    return jsonify(result), status_code

@exercise_bp.route('/records', methods=['GET'])
@jwt_required()
def get_exercise_records():
    """获取运动记录列表"""
    user_id = get_jwt_identity()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    result = ExerciseService.get_exercise_records(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify(result), 200 if result.get('success') else 400

@exercise_bp.route('/records/<int:record_id>', methods=['GET'])
@jwt_required()
def get_exercise_record(record_id):
    """获取单个运动记录"""
    user_id = get_jwt_identity()
    
    # 获取运动记录
    result = ExerciseService.get_exercise_record(record_id, user_id)
    return jsonify(result), 200 if result.get('success') else 404

@exercise_bp.route('/records/<int:record_id>', methods=['PUT'])
@jwt_required()
def update_exercise_record(record_id):
    """更新运动记录"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '数据不能为空'}), 400
    
    # 修复：与get_user_exercise_records相同，只返回一个结果
    result = ExerciseService.update_exercise_record(record_id, user_id, data)
    return jsonify(result), 200 if result.get('success', False) else 400

@exercise_bp.route('/records/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_exercise_record(record_id):
    """删除运动记录"""
    user_id = get_jwt_identity()
    
    # 修复：与get_user_exercise_records相同，只返回一个结果
    result = ExerciseService.delete_exercise_record(record_id, user_id)
    return jsonify(result), 200 if result.get('success', False) else 404

@exercise_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_exercise_summary():
    """获取用户运动汇总"""
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        period = request.args.get('period', 'week')  # 默认为周汇总
        date = request.args.get('date')  # 指定日期
        
        # 修复：检查返回值是否为元组，如果是则解包
        result = ExerciseService.get_exercise_summary(
            user_id=user_id,
            period=period,
            date=date
        )
        
        # 处理可能的元组返回值
        if isinstance(result, tuple) and len(result) == 2:
            response_data, status_code = result
            return jsonify(response_data), status_code
        else:
            # 如果不是元组，直接返回
            return jsonify(result), 200 if result.get('success', False) else 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取运动数据汇总时发生错误: {str(e)}",
            "summary": None
        }), 500 