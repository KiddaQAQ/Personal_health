from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.health_report_service import HealthReportService, ReminderService
from datetime import datetime
import traceback

health_report_bp = Blueprint('health_report', __name__)

@health_report_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_health_report():
    """生成健康报告"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        report_type = data.get('report_type', 'weekly')  # 默认为周报
        
        # 处理日期参数
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 生成报告
        report = HealthReportService.generate_health_report(
            user_id=user_id,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            "success": True,
            "message": "健康报告生成成功",
            "data": report.to_dict()
        }), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"生成健康报告出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@health_report_bp.route('/list', methods=['GET'])
@jwt_required()
def get_health_reports():
    """获取用户健康报告列表"""
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 10, type=int)
        
        reports = HealthReportService.get_user_reports(user_id, limit)
        reports_data = [report.to_dict() for report in reports]
        
        return jsonify({
            "success": True,
            "data": reports_data
        }), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"获取健康报告列表出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@health_report_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required()
def get_health_report(report_id):
    """获取健康报告详情"""
    try:
        user_id = get_jwt_identity()
        
        report = HealthReportService.get_report_by_id(report_id, user_id)
        if not report:
            return jsonify({
                "success": False,
                "message": "报告不存在或无权访问"
            }), 404
        
        return jsonify({
            "success": True,
            "data": report.to_dict()
        }), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"获取健康报告详情出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

# 提醒相关路由
@health_report_bp.route('/reminders', methods=['POST'])
@health_report_bp.route('/reminders/create', methods=['POST'])
@jwt_required()
def create_reminder():
    """创建提醒"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        reminder_type = data.get('reminder_type')
        title = data.get('title')
        description = data.get('description')
        reminder_date = data.get('reminder_date')
        reminder_time = data.get('reminder_time')
        recurrence = data.get('recurrence')
        
        # 输出调试信息
        print(f"创建提醒 - 用户ID: {user_id}, 类型: {reminder_type}, 标题: {title}, 日期: {reminder_date}, 时间: {reminder_time}")
        
        # 验证必要参数
        if not reminder_type or not title or not reminder_date or not reminder_time:
            return jsonify({
                "success": False,
                "message": "缺少必要参数"
            }), 400
        
        # 处理日期和时间
        try:
            reminder_date = datetime.strptime(reminder_date, '%Y-%m-%d').date()
            reminder_time = datetime.strptime(reminder_time, '%H:%M').time()
        except ValueError:
            return jsonify({
                "success": False,
                "message": "日期或时间格式错误，请使用YYYY-MM-DD和HH:MM格式"
            }), 400
        
        # 根据提醒类型创建不同的提醒
        if reminder_type == 'medication':
            # 获取药物记录ID并进行验证
            medication_record_id = data.get('medication_record_id')
            
            # 如果提供了药物记录ID，验证其是否为正整数
            if medication_record_id is not None:
                try:
                    medication_record_id = int(medication_record_id)
                    if medication_record_id <= 0:
                        medication_record_id = None
                        print("警告: 药物记录ID不是正整数，将被忽略")
                except (ValueError, TypeError):
                    medication_record_id = None
                    print("警告: 药物记录ID不是有效整数，将被忽略")
            
            try:
                # 创建药物提醒
                reminder = ReminderService.create_medication_reminder(
                    user_id=user_id,
                    medication_record_id=medication_record_id,
                    title=title,
                    description=description,
                    reminder_date=reminder_date,
                    reminder_time=reminder_time,
                    recurrence=recurrence
                )
            except Exception as e:
                # 如果创建失败，尝试不带medication_record_id再次创建
                print(f"使用medication_record_id创建提醒失败: {e}，尝试不使用medication_record_id")
                reminder = ReminderService.create_medication_reminder(
                    user_id=user_id,
                    medication_record_id=None,  # 明确设置为None
                    title=title,
                    description=description,
                    reminder_date=reminder_date,
                    reminder_time=reminder_time,
                    recurrence=recurrence
                )
            
        elif reminder_type == 'appointment':
            print(f"创建预约提醒 - 标题: {title}, 描述: {description}, 日期: {reminder_date}, 时间: {reminder_time}")
            reminder = ReminderService.create_appointment_reminder(
                user_id=user_id,
                title=title,
                description=description,
                reminder_date=reminder_date,
                reminder_time=reminder_time,
                recurrence=recurrence
            )
            
        else:
            return jsonify({
                "success": False,
                "message": "不支持的提醒类型，请使用medication或appointment"
            }), 400
            
        if not reminder:
            return jsonify({
                "success": False,
                "message": "创建提醒失败"
            }), 500
            
        # 输出创建结果
        print(f"提醒创建成功 - ID: {reminder.id}, 类型: {reminder.reminder_type}")
            
        return jsonify({
            "success": True,
            "message": "提醒创建成功",
            "data": reminder.to_dict()
        }), 201
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"创建提醒出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@health_report_bp.route('/reminders', methods=['GET'])
@jwt_required()
def get_reminders():
    """获取用户的提醒列表"""
    try:
        user_id = get_jwt_identity()
        date_str = request.args.get('date')  # 可以获取特定日期的提醒
        reminder_type = request.args.get('type')  # 可以获取特定类型的提醒
        
        # 处理日期参数
        date = None
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "日期格式错误，请使用YYYY-MM-DD格式"
                }), 400
        
        # 获取提醒列表
        reminders = ReminderService.get_user_reminders(
            user_id=user_id,
            date=date,
            reminder_type=reminder_type
        )
        
        # 添加调试日志
        medication_count = len([r for r in reminders if r.reminder_type == 'medication'])
        appointment_count = len([r for r in reminders if r.reminder_type == 'appointment'])
        print(f"获取提醒列表 - 用户ID: {user_id}, 日期: {date}, 总数: {len(reminders)}, 药物提醒: {medication_count}, 预约提醒: {appointment_count}")
        
        reminders_data = [reminder.to_dict() for reminder in reminders]
        
        return jsonify({
            "success": True,
            "data": reminders_data
        }), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"获取提醒列表出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@health_report_bp.route('/reminders/<int:reminder_id>/complete', methods=['POST'])
@jwt_required()
def complete_reminder(reminder_id):
    """标记提醒为已完成"""
    try:
        user_id = get_jwt_identity()
        
        reminder = ReminderService.mark_reminder_as_completed(reminder_id, user_id)
        if not reminder:
            return jsonify({
                "success": False,
                "message": "提醒不存在或无权操作"
            }), 404
            
        return jsonify({
            "success": True,
            "message": "提醒已标记为完成",
            "data": reminder.to_dict()
        }), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"完成提醒出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@health_report_bp.route('/reminders/<int:reminder_id>', methods=['PUT'])
@jwt_required()
def update_reminder(reminder_id):
    """更新提醒信息"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 处理日期和时间
        update_data = {}
        
        if 'title' in data:
            update_data['title'] = data['title']
            
        if 'description' in data:
            update_data['description'] = data['description']
            
        if 'reminder_date' in data:
            try:
                update_data['reminder_date'] = datetime.strptime(data['reminder_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "日期格式错误，请使用YYYY-MM-DD格式"
                }), 400
                
        if 'reminder_time' in data:
            try:
                update_data['reminder_time'] = datetime.strptime(data['reminder_time'], '%H:%M').time()
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "时间格式错误，请使用HH:MM格式"
                }), 400
                
        if 'recurrence' in data:
            update_data['recurrence'] = data['recurrence']
            
        if 'is_completed' in data:
            update_data['is_completed'] = data['is_completed']
        
        # 更新提醒
        reminder = ReminderService.update_reminder(reminder_id, user_id, **update_data)
        if not reminder:
            return jsonify({
                "success": False,
                "message": "提醒不存在或无权操作"
            }), 404
            
        return jsonify({
            "success": True,
            "message": "提醒更新成功",
            "data": reminder.to_dict()
        }), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"更新提醒出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@health_report_bp.route('/reminders/<int:reminder_id>', methods=['DELETE'])
@jwt_required()
def delete_reminder(reminder_id):
    """删除提醒"""
    try:
        user_id = get_jwt_identity()
        
        success = ReminderService.delete_reminder(reminder_id, user_id)
        if not success:
            return jsonify({
                "success": False,
                "message": "提醒不存在或无权操作"
            }), 404
            
        return jsonify({
            "success": True,
            "message": "提醒删除成功"
        }), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"删除提醒出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500

@health_report_bp.route('/reminders/generate-medication', methods=['POST'])
@jwt_required()
def generate_medication_reminders():
    """根据用药记录自动生成药物提醒"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        date_str = data.get('date')  # 可选，指定日期
        
        # 处理日期参数
        date = None
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "日期格式错误，请使用YYYY-MM-DD格式"
                }), 400
                
        # 自动生成提醒
        created_count = ReminderService.generate_medication_reminders_from_records(
            user_id=user_id,
            date=date
        )
        
        return jsonify({
            "success": True,
            "message": f"成功生成{created_count}个药物提醒",
            "data": {"created_count": created_count}
        }), 201
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"生成药物提醒出错: {str(e)}\n{error_trace}")
        return jsonify({
            "success": False,
            "message": f"服务器内部错误: {str(e)}"
        }), 500 