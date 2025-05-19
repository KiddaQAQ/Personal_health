from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.analysis_service import AnalysisService
import traceback

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/nutrition', methods=['GET'])
@jwt_required()
def get_nutrition_analysis():
    """获取用户营养分析"""
    try:
        user_id = get_jwt_identity()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 参数验证
        if not user_id:
            return jsonify({
                "success": False,
                "message": "请先登录"
            }), 401
        
        result = AnalysisService.get_nutrition_analysis(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # 即使分析失败也返回200，避免前端误判为权限错误
        return jsonify(result), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"营养分析出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}",
            "daily_nutrition": [],  # 提供空的数据结构以便前端处理
            "average": {},
            "recommended": {},
            "analysis": []
        }), 200  # 返回200而不是500，让前端能够显示错误信息

@analysis_bp.route('/exercise-recommendations', methods=['GET'])
@jwt_required()
def get_exercise_recommendations():
    """获取用户运动建议"""
    try:
        user_id = get_jwt_identity()
        based_on_diet_param = request.args.get('based_on_diet', 'true').lower()
        based_on_diet = based_on_diet_param in ('true', 'yes', '1')
        
        # 安全地转换days参数
        days = 7  # 默认值
        days_param = request.args.get('days')
        if days_param:
            try:
                days = int(days_param)
                if days <= 0:
                    days = 7
            except (ValueError, TypeError):
                days = 7
        
        # 参数验证
        if not user_id:
            return jsonify({
                "success": False,
                "message": "请先登录"
            }), 401
            
        result = AnalysisService.get_exercise_recommendations(
            user_id=user_id,
            based_on_diet=based_on_diet,
            days=days
        )
        
        # 即使分析失败也返回200，避免前端误判为权限错误
        return jsonify(result), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"获取运动建议出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}",
            "data": {  # 提供空的数据结构以便前端处理
                "recommendations": [],
                "weekly_plan": [],
                "current_status": {}
            }
        }), 200  # 返回200而不是500，让前端能够显示错误信息 