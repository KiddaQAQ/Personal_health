from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.diet_service import DietService
import logging

logger = logging.getLogger(__name__)

# 食物相关路由
diet_bp = Blueprint('diet', __name__, url_prefix='/api/diet')

@diet_bp.route('/foods', methods=['POST'])
@jwt_required()
def create_food():
    """创建新的食物"""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'success': False, 'message': '食物名称不能为空'}), 400
    
    result, status_code = DietService.create_food(
        name=data['name'],
        category=data.get('category'),
        calories=data.get('calories'),
        protein=data.get('protein'),
        fat=data.get('fat'),
        carbohydrate=data.get('carbohydrate'),
        fiber=data.get('fiber'),
        sugar=data.get('sugar'),
        sodium=data.get('sodium'),
        serving_size=data.get('serving_size')
    )
    
    return jsonify(result), status_code

@diet_bp.route('/foods', methods=['GET'])
@jwt_required()
def get_foods():
    """获取食物列表"""
    category = request.args.get('category')
    search = request.args.get('search')
    
    result, status_code = DietService.get_foods(category, search)
    return jsonify(result), status_code

@diet_bp.route('/foods/<int:food_id>', methods=['GET'])
@jwt_required()
def get_food(food_id):
    """获取单个食物详情"""
    result, status_code = DietService.get_food(food_id)
    return jsonify(result), status_code

# 饮食记录相关路由
@diet_bp.route('/records', methods=['POST'])
@jwt_required()
def create_diet_record():
    """创建新的饮食记录"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '数据不能为空'}), 400
    
    # 检查必要字段
    required_fields = ['food_name', 'amount']
    if not all(field in data for field in required_fields):
        missing_fields = [field for field in required_fields if field not in data]
        return jsonify({
            'success': False, 
            'message': f'缺少必要字段: {", ".join(missing_fields)}'
        }), 400
    
    # 创建记录
    result = DietService.create_diet_record(
        user_id=user_id,
        record_date=data.get('record_date'),
        food_name=data.get('food_name'),
        meal_type=data.get('meal_type'),
        amount=data.get('amount'),
        sugar=data.get('sugar'),
        calories_burned=data.get('calories_burned'),
        notes=data.get('notes')
    )
    
    status_code = 201 if result.get('success') else 400
    return jsonify(result), status_code

@diet_bp.route('/records', methods=['GET'])
@jwt_required()
def get_diet_records():
    """获取饮食记录列表"""
    user_id = get_jwt_identity()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    result = DietService.get_diet_records(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify(result), 200 if result.get('success') else 400

@diet_bp.route('/records/<int:record_id>', methods=['GET'])
@jwt_required()
def get_diet_record(record_id):
    """获取单个饮食记录"""
    user_id = get_jwt_identity()
    
    try:
        result = DietService.get_diet_record(record_id, user_id)
        # 如果返回的是元组，只取第一个元素(结果)
        if isinstance(result, tuple) and len(result) >= 1:
            result = result[0]
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"获取饮食记录 {record_id} 时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@diet_bp.route('/records/<int:record_id>', methods=['PUT'])
@jwt_required()
def update_diet_record(record_id):
    """更新饮食记录"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '数据不能为空'}), 400
    
    result, status_code = DietService.update_diet_record(record_id, user_id, data)
    return jsonify(result), status_code

@diet_bp.route('/records/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_diet_record(record_id):
    """删除饮食记录"""
    user_id = get_jwt_identity()
    
    result, status_code = DietService.delete_diet_record(record_id, user_id)
    return jsonify(result), status_code

@diet_bp.route('/nutrition/summary', methods=['GET'])
@jwt_required()
def get_nutrition_summary():
    """获取用户营养摄入汇总"""
    user_id = get_jwt_identity()
    date = request.args.get('date')  # 单日汇总
    
    result, status_code = DietService.get_nutrition_summary(user_id, date)
    return jsonify(result), status_code 