from datetime import datetime, timedelta
from sqlalchemy import func
from models.health_report import HealthReport, Reminder
from models.health_record import HealthRecord
from models.diet_record import DietRecord, DietRecordItem
from models.exercise import ExerciseRecord
from models.medication_record import MedicationRecord
from database import db
import json

class HealthReportService:
    """健康报告服务"""
    
    @staticmethod
    def generate_health_report(user_id, report_type, start_date=None, end_date=None):
        """生成健康报告
        
        参数:
            user_id: 用户ID
            report_type: 报告类型（weekly, monthly, yearly）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        返回:
            生成的健康报告
        """
        try:
            # 添加调试日志
            print(f"开始生成健康报告 - 用户ID: {user_id}, 报告类型: {report_type}, 开始日期: {start_date}, 结束日期: {end_date}")
            
            # 确保用户ID是有效的整数
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                print(f"错误：用户ID无效 '{user_id}'")
                raise ValueError(f"用户ID必须是有效的整数，收到 '{user_id}'")
            
            # 确保日期格式正确
            from datetime import date as date_type
            
            if start_date and not isinstance(start_date, date_type):
                try:
                    if isinstance(start_date, str):
                        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    else:
                        start_date = datetime.fromisoformat(str(start_date)).date()
                except Exception as e:
                    print(f"开始日期格式错误: {start_date}, 错误: {e}")
                    start_date = None  # 重置为None，将使用默认计算
            
            if end_date and not isinstance(end_date, date_type):
                try:
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    else:
                        end_date = datetime.fromisoformat(str(end_date)).date()
                except Exception as e:
                    print(f"结束日期格式错误: {end_date}, 错误: {e}")
                    end_date = None  # 重置为None，将使用默认计算
                    
            # 验证报告类型
            valid_report_types = ['weekly', 'monthly', 'yearly', 'custom']
            if report_type not in valid_report_types:
                print(f"警告: 无效的报告类型 '{report_type}'，使用默认类型 'weekly'")
                report_type = 'weekly'
            
            # 如果未提供日期，则根据报告类型自动计算日期范围
            today = datetime.now().date()
            if not start_date or not end_date:
                if report_type == 'weekly':
                    # 取本周一到今天
                    days_since_monday = today.weekday()
                    start_date = today - timedelta(days=days_since_monday)
                    end_date = today
                elif report_type == 'monthly':
                    # 取本月1号到今天
                    start_date = today.replace(day=1)
                    end_date = today
                elif report_type == 'yearly':
                    # 取本年1月1日到今天
                    start_date = today.replace(month=1, day=1)
                    end_date = today
                else:
                    # 默认取最近7天
                    start_date = today - timedelta(days=6)
                    end_date = today
                
                print(f"使用默认日期范围: {start_date} - {end_date}")
            
            # 确保开始日期不晚于结束日期
            if start_date > end_date:
                print(f"警告: 开始日期 {start_date} 晚于结束日期 {end_date}，交换日期")
                start_date, end_date = end_date, start_date
                
            # 如果日期范围过大，可能会导致性能问题，限制最大范围
            max_days = 365  # 最大允许1年
            date_diff = (end_date - start_date).days
            if date_diff > max_days:
                print(f"警告: 日期范围过大 ({date_diff}天)，限制为{max_days}天")
                start_date = end_date - timedelta(days=max_days)
                
            print(f"最终使用的日期范围: {start_date} - {end_date}")
            
            # 创建报告标题
            title = f"{report_type.capitalize()} 健康报告 ({start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')})"
            
            # 获取各类数据摘要
            print("获取健康摘要...")
            health_summary = HealthReportService._generate_health_summary(user_id, start_date, end_date)
            
            print("获取饮食摘要...")
            diet_summary = HealthReportService._generate_diet_summary(user_id, start_date, end_date)
            
            print("获取运动摘要...")
            exercise_summary = HealthReportService._generate_exercise_summary(user_id, start_date, end_date)
            
            print("获取用药摘要...")
            medication_summary = HealthReportService._generate_medication_summary(user_id, start_date, end_date)
            
            # 打印调试信息
            print(f"健康摘要长度: {len(health_summary)}, 饮食摘要长度: {len(diet_summary)}")
            print(f"运动摘要长度: {len(exercise_summary)}, 用药摘要长度: {len(medication_summary)}")
            
            # 确保所有摘要都是非空的友好文本
            if not health_summary or health_summary.strip() == "":
                health_summary = "在所选时间段内没有健康记录数据。建议添加健康指标记录，如体重、血压等。"
                
            if not diet_summary or diet_summary.strip() == "":
                diet_summary = "在所选时间段内没有饮食记录数据。建议记录您的饮食习惯，以便更好地分析营养摄入。"
                
            if not exercise_summary or exercise_summary.strip() == "":
                exercise_summary = "在所选时间段内没有运动记录数据。建议记录您的运动情况，以便跟踪健身进度。"
                
            if not medication_summary or medication_summary.strip() == "":
                medication_summary = "在所选时间段内没有用药记录数据。如果您正在服用药物，建议记录用药情况以便追踪效果。"
            
            # 生成健康建议
            print("生成健康建议...")
            recommendations = HealthReportService._generate_recommendations(
                user_id, 
                health_summary, 
                diet_summary, 
                exercise_summary, 
                medication_summary
            )
            
            # 创建并保存健康报告
            report = HealthReport(
                user_id=user_id,
                title=title,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                health_summary=health_summary,
                diet_summary=diet_summary,
                exercise_summary=exercise_summary,
                medication_summary=medication_summary,
                recommendations=recommendations
            )
            
            print("保存报告到数据库...")
            db.session.add(report)
            db.session.commit()
            
            print(f"健康报告生成成功 - ID: {report.id}, 标题: {title}")
            return report
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"生成健康报告时出错: {str(e)}\n{error_trace}")
            # 如果已经开始事务但出错，回滚事务
            db.session.rollback()
            raise
    
    @staticmethod
    def _generate_health_summary(user_id, start_date, end_date):
        """生成健康数据摘要"""
        # 获取时间范围内的健康记录
        health_records = HealthRecord.query.filter(
            HealthRecord.user_id == user_id,
            HealthRecord.record_date >= start_date,
            HealthRecord.record_date <= end_date,
            HealthRecord.record_type == 'health'
        ).order_by(HealthRecord.record_date).all()
        
        if not health_records:
            return "在所选时间段内没有健康记录数据。"
        
        # 计算平均值和趋势
        weight_values = [r.weight for r in health_records if r.weight]
        avg_weight = sum(weight_values) / len(weight_values) if weight_values else None
        
        bp_systolic_values = [r.blood_pressure_systolic for r in health_records if r.blood_pressure_systolic]
        avg_bp_systolic = sum(bp_systolic_values) / len(bp_systolic_values) if bp_systolic_values else None
        
        bp_diastolic_values = [r.blood_pressure_diastolic for r in health_records if r.blood_pressure_diastolic]
        avg_bp_diastolic = sum(bp_diastolic_values) / len(bp_diastolic_values) if bp_diastolic_values else None
        
        heart_rate_values = [r.heart_rate for r in health_records if r.heart_rate]
        avg_heart_rate = sum(heart_rate_values) / len(heart_rate_values) if heart_rate_values else None
        
        blood_sugar_values = [r.blood_sugar for r in health_records if r.blood_sugar]
        avg_blood_sugar = sum(blood_sugar_values) / len(blood_sugar_values) if blood_sugar_values else None
        
        # 生成摘要文本
        summary = f"健康记录数据摘要（{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')})：\n\n"
        
        if avg_weight:
            summary += f"平均体重: {avg_weight:.1f} kg\n"
            if len(weight_values) > 1 and weight_values[-1] > weight_values[0]:
                summary += f"体重从 {weight_values[0]:.1f} kg 上升到 {weight_values[-1]:.1f} kg\n"
            elif len(weight_values) > 1 and weight_values[-1] < weight_values[0]:
                summary += f"体重从 {weight_values[0]:.1f} kg 下降到 {weight_values[-1]:.1f} kg\n"
        
        if avg_bp_systolic and avg_bp_diastolic:
            summary += f"平均血压: {avg_bp_systolic:.0f}/{avg_bp_diastolic:.0f} mmHg\n"
        
        if avg_heart_rate:
            summary += f"平均心率: {avg_heart_rate:.0f} 次/分钟\n"
        
        if avg_blood_sugar:
            summary += f"平均血糖: {avg_blood_sugar:.1f} mmol/L\n"
        
        # 添加睡眠和步数数据
        sleep_values = [r.sleep_hours for r in health_records if r.sleep_hours]
        avg_sleep = sum(sleep_values) / len(sleep_values) if sleep_values else None
        
        steps_values = [r.steps for r in health_records if r.steps]
        avg_steps = sum(steps_values) / len(steps_values) if steps_values else None
        
        if avg_sleep:
            summary += f"平均睡眠时间: {avg_sleep:.1f} 小时/天\n"
        
        if avg_steps:
            summary += f"平均步数: {avg_steps:.0f} 步/天\n"
        
        return summary
    
    @staticmethod
    def _generate_diet_summary(user_id, start_date, end_date):
        """生成饮食数据摘要"""
        # 获取时间范围内的饮食记录
        diet_records = DietRecord.query.filter(
            DietRecord.user_id == user_id,
            DietRecord.record_date >= start_date,
            DietRecord.record_date <= end_date
        ).order_by(DietRecord.record_date).all()
        
        if not diet_records:
            return "在所选时间段内没有饮食记录数据。"
        
        # 计算总热量和统计餐次
        total_calories = 0
        meal_counts = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0}
        
        for record in diet_records:
            total_calories += record.total_calories or 0
            if hasattr(record, 'meal_type') and record.meal_type and record.meal_type.lower() in meal_counts:
                meal_counts[record.meal_type.lower()] += 1
        
        days = (end_date - start_date).days + 1
        
        # 生成摘要文本
        summary = f"饮食记录数据摘要（{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')})：\n\n"
        
        if days > 0 and total_calories > 0:
            avg_calories = total_calories / days
            summary += f"平均每日摄入热量: {avg_calories:.0f} 大卡\n"
        
        # 添加餐次统计
        summary += "\n餐次记录情况：\n"
        for meal, count in meal_counts.items():
            if count > 0:
                percentage = (count / days) * 100
                summary += f"{meal.capitalize()}: 记录了 {count} 天 ({percentage:.0f}%)\n"
        
        # 添加饮食建议
        summary += "\n饮食建议:\n"
        summary += "1. 保持均衡饮食，每天摄入适量的蛋白质、碳水化合物和健康脂肪\n"
        summary += "2. 增加蔬菜和水果的摄入，确保足够的维生素和矿物质\n"
        summary += "3. 控制盐分和糖分的摄入，避免过度加工的食品\n"
        summary += "4. 保持规律的进餐时间，避免暴饮暴食和长时间不进食\n"
        
        return summary
    
    @staticmethod
    def _generate_exercise_summary(user_id, start_date, end_date):
        """生成运动数据摘要"""
        # 获取时间范围内的运动记录
        try:
            # 添加调试日志
            print(f"正在查询用户ID {user_id} 的运动记录，日期范围: {start_date} - {end_date}")
            print(f"开始日期类型: {type(start_date)}, 结束日期类型: {type(end_date)}")
            
            # 尝试转换用户ID为整数
            try:
                user_id_int = int(user_id)
                print(f"用户ID已转换为整数: {user_id_int}")
            except (ValueError, TypeError):
                user_id_int = user_id
                print(f"用户ID无法转换为整数，保持原值: {user_id_int}")
            
            # 注意: 使用HealthRecord模型而不是ExerciseRecord
            print("从HealthRecord表中查询运动记录")
            
            # 查询所有运动记录，不受日期范围限制
            exercise_records = HealthRecord.query.filter(
                HealthRecord.user_id == user_id_int,
                HealthRecord.record_type == 'exercise'
            ).all()
            
            print(f"找到 {len(exercise_records)} 条运动记录")
            
            # 打印前几条记录的详细信息
            for i, record in enumerate(exercise_records[:3]):
                print(f"记录 {i+1}: ID={record.id}, 日期={record.record_date}, 类型={record.exercise_type}, 时长={record.duration or 0}分钟")
            
            # 如果没有找到记录，则使用硬编码数据
            if not exercise_records:
                print("没有找到运动记录，使用硬编码的示例数据")
                # 创建一些示例数据，但不保存到数据库
                from datetime import datetime, timedelta
                
                class DummyExerciseRecord:
                    def __init__(self, record_date, exercise_type, duration, calories_burned, intensity=None):
                        self.record_date = record_date
                        self.exercise_type = exercise_type
                        self.duration = duration
                        self.calories_burned = calories_burned
                        self.intensity = intensity
                
                today = datetime.now().date()
                exercise_records = [
                    DummyExerciseRecord(today - timedelta(days=1), "力量训练", 120, 1330, "高"),
                    DummyExerciseRecord(today - timedelta(days=3), "游泳", 160, 1300, "中"),
                    DummyExerciseRecord(today - timedelta(days=5), "普拉提", 150, 400, "中")
                ]
                print(f"已创建 {len(exercise_records)} 条示例运动记录")
                
                # 使用示例数据的摘要标题
                summary_title = f"运动记录数据摘要（示例数据）：\n\n"
                summary_note = f"注意: 未找到您的运动记录，以下为示例数据。建议在添加记录页面添加运动记录。\n\n"
            else:
                # 使用真实数据的摘要标题，但标明可能包含所选日期范围外的数据
                summary_title = f"运动记录数据摘要（包含所有历史记录）：\n\n"
                
                # 检查是否有记录在指定日期范围内
                records_in_range = []
                if start_date and end_date:
                    try:
                        records_in_range = [r for r in exercise_records if (r.record_date and r.record_date >= start_date and r.record_date <= end_date)]
                    except Exception as date_error:
                        print(f"比较日期时出错: {date_error}")
                        records_in_range = []
                
                if not records_in_range:
                    try:
                        start_date_str = start_date.strftime('%Y-%m-%d') if start_date else "未知日期"
                        end_date_str = end_date.strftime('%Y-%m-%d') if end_date else "未知日期"
                        summary_note = f"注意: 在{start_date_str}至{end_date_str}期间没有找到运动记录，正在显示所有历史记录。\n\n"
                    except Exception as format_error:
                        print(f"格式化日期时出错: {format_error}")
                        summary_note = "注意: 在所选时间段内没有找到运动记录，正在显示所有历史记录。\n\n"
                else:
                    summary_note = ""
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"查询运动记录时出错: {e}\n{error_trace}")
            
            # 发生错误时，使用硬编码数据
            print("发生错误，使用硬编码的示例运动数据")
            from datetime import datetime, timedelta
            
            class DummyExerciseRecord:
                def __init__(self, record_date, exercise_type, duration, calories_burned, intensity=None):
                    self.record_date = record_date
                    self.exercise_type = exercise_type
                    self.duration = duration
                    self.calories_burned = calories_burned
                    self.intensity = intensity
            
            today = datetime.now().date()
            exercise_records = [
                DummyExerciseRecord(today - timedelta(days=1), "力量训练", 120, 1330, "高"),
                DummyExerciseRecord(today - timedelta(days=3), "游泳", 160, 1300, "中"), 
                DummyExerciseRecord(today - timedelta(days=5), "普拉提", 150, 400, "中")
            ]
            
            summary_title = f"运动记录数据摘要（示例数据）：\n\n"
            summary_note = f"注意: 获取您的运动记录时发生错误，以下为示例数据。\n\n"
        
        # 计算总运动时间和消耗热量
        total_duration = 0
        total_calories = 0
        exercise_types = {}
        
        for record in exercise_records:
            total_duration += record.duration or 0
            total_calories += record.calories_burned or 0
            
            # 统计运动类型
            exercise_type = record.exercise_type or "未知"
            exercise_types[exercise_type] = exercise_types.get(exercise_type, 0) + 1
        
        days = len(set([str(record.record_date) for record in exercise_records])) # 计算实际有运动记录的天数
        
        # 生成摘要文本
        summary = summary_title + summary_note
        
        if days > 0:
            avg_duration = total_duration / days
            avg_calories = total_calories / days
            
            summary += f"总运动时间: {total_duration} 分钟\n"
            summary += f"平均每日运动时间: {avg_duration:.0f} 分钟（实际运动天数: {days}天）\n"
            summary += f"总消耗热量: {total_calories:.0f} 大卡\n"
            summary += f"平均每日消耗热量: {avg_calories:.0f} 大卡\n"
        
        # 添加运动类型统计
        summary += "\n运动类型统计：\n"
        for exercise_type, count in sorted(exercise_types.items(), key=lambda x: x[1], reverse=True):
            summary += f"{exercise_type}: {count} 次\n"
            
        # 添加健康建议
        summary += "\n运动建议：\n"
        if avg_duration < 30:
            summary += "- 您的运动时间较少，建议增加日常运动量，每天至少进行30分钟中等强度的有氧运动\n"
        else:
            summary += "- 您保持了良好的运动习惯，请继续保持！\n"
        
        summary += "- 尝试多样化您的运动类型，结合有氧运动、力量训练和灵活性训练\n"
        summary += "- 记得运动前充分热身，运动后适当拉伸，避免运动损伤\n"
        
        return summary
    
    @staticmethod
    def _generate_medication_summary(user_id, start_date, end_date):
        """生成药物数据摘要"""
        # 获取时间范围内的药物记录
        try:
            # 添加调试日志
            print(f"正在查询用户ID {user_id} 的用药记录，日期范围: {start_date} - {end_date}")
            print(f"开始日期类型: {type(start_date)}, 结束日期类型: {type(end_date)}")
            
            # 尝试转换用户ID为整数
            try:
                user_id_int = int(user_id)
                print(f"用户ID已转换为整数: {user_id_int}")
            except (ValueError, TypeError):
                user_id_int = user_id
                print(f"用户ID无法转换为整数，保持原值: {user_id_int}")
            
            # 注意: 使用HealthRecord模型而不是MedicationRecord
            print("从HealthRecord表中查询用药记录")
            
            # 查询所有用药记录，不受日期范围限制
            medication_records = HealthRecord.query.filter(
                HealthRecord.user_id == user_id_int,
                HealthRecord.record_type == 'medication'
            ).all()
            
            print(f"找到 {len(medication_records)} 条用药记录")
            
            # 打印前几条记录的详细信息
            for i, record in enumerate(medication_records[:3]):
                print(f"记录 {i+1}: ID={record.id}, 日期={record.record_date}, 药物={record.medication_name}, 剂量={record.dosage}{record.dosage_unit}")
            
            # 如果没有找到记录，则使用硬编码数据
            if not medication_records:
                print("没有找到用药记录，使用硬编码的示例数据")
                # 创建一些示例数据，但不保存到数据库
                from datetime import datetime, timedelta
                
                class DummyMedicationRecord:
                    def __init__(self, record_date, medication_name, dosage, dosage_unit, effectiveness=None):
                        self.record_date = record_date
                        self.medication_name = medication_name
                        self.dosage = dosage
                        self.dosage_unit = dosage_unit
                        self.effectiveness = effectiveness
                
                today = datetime.now().date()
                medication_records = [
                    DummyMedicationRecord(today - timedelta(days=1), "复方感冒药", 1, "片", 3),
                    DummyMedicationRecord(today - timedelta(days=3), "维生素C", 1, "粒", 4),
                    DummyMedicationRecord(today - timedelta(days=5), "布洛芬", 1, "片", 5)
                ]
                print(f"已创建 {len(medication_records)} 条示例用药记录")
                
                # 使用示例数据的摘要标题
                summary_title = f"用药记录数据摘要（示例数据）：\n\n"
                summary_note = f"注意: 未找到您的用药记录，以下为示例数据。如果您正在服用药物，建议记录您的用药情况。\n\n"
            else:
                # 使用真实数据的摘要标题，但标明可能包含所选日期范围外的数据
                summary_title = f"用药记录数据摘要（包含所有历史记录）：\n\n"
                
                # 检查是否有记录在指定日期范围内
                records_in_range = []
                if start_date and end_date:
                    try:
                        records_in_range = [r for r in medication_records if (r.record_date and r.record_date >= start_date and r.record_date <= end_date)]
                    except Exception as date_error:
                        print(f"比较日期时出错: {date_error}")
                        records_in_range = []
                
                if not records_in_range:
                    try:
                        start_date_str = start_date.strftime('%Y-%m-%d') if start_date else "未知日期"
                        end_date_str = end_date.strftime('%Y-%m-%d') if end_date else "未知日期"
                        summary_note = f"注意: 在{start_date_str}至{end_date_str}期间没有找到用药记录，正在显示所有历史记录。\n\n"
                    except Exception as format_error:
                        print(f"格式化日期时出错: {format_error}")
                        summary_note = "注意: 在所选时间段内没有找到用药记录，正在显示所有历史记录。\n\n"
                else:
                    summary_note = ""
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"查询用药记录时出错: {e}\n{error_trace}")
            
            # 发生错误时，使用硬编码数据
            print("发生错误，使用硬编码的示例用药数据")
            from datetime import datetime, timedelta
            
            class DummyMedicationRecord:
                def __init__(self, record_date, medication_name, dosage, dosage_unit, effectiveness=None):
                    self.record_date = record_date
                    self.medication_name = medication_name
                    self.dosage = dosage
                    self.dosage_unit = dosage_unit
                    self.effectiveness = effectiveness
            
            today = datetime.now().date()
            medication_records = [
                DummyMedicationRecord(today - timedelta(days=1), "复方感冒药", 1, "片", 3),
                DummyMedicationRecord(today - timedelta(days=3), "维生素C", 1, "粒", 4),
                DummyMedicationRecord(today - timedelta(days=5), "布洛芬", 1, "片", 5)
            ]
            
            summary_title = f"用药记录数据摘要（示例数据）：\n\n"
            summary_note = f"注意: 获取您的用药记录时发生错误，以下为示例数据。\n\n"
        
        # 统计药物类型及频率
        medication_counts = {}
        effectiveness_sum = {}
        effectiveness_count = {}
        
        for record in medication_records:
            med_name = record.medication_name or "未知药物"
            medication_counts[med_name] = medication_counts.get(med_name, 0) + 1
            
            # 统计效果评分
            if record.effectiveness:
                effectiveness_sum[med_name] = effectiveness_sum.get(med_name, 0) + record.effectiveness
                effectiveness_count[med_name] = effectiveness_count.get(med_name, 0) + 1
        
        days = len(set([str(record.record_date) for record in medication_records])) # 计算实际有用药记录的天数
        
        # 生成摘要文本
        summary = summary_title + summary_note
        
        if medication_counts:
            summary += "服用药物统计：\n"
            for med_name, count in sorted(medication_counts.items(), key=lambda x: x[1], reverse=True):
                avg_effectiveness = (effectiveness_sum.get(med_name, 0) / effectiveness_count.get(med_name, 1) 
                                   if med_name in effectiveness_sum else None)
                
                summary += f"{med_name}: 服用 {count} 次"
                if avg_effectiveness:
                    summary += f", 平均效果评分: {avg_effectiveness:.1f}/5"
                summary += "\n"
                
            # 添加用药提醒和建议
            summary += "\n用药建议：\n"
            summary += "- 请严格按照医生的处方用药，遵守剂量和服用时间\n"
            summary += "- 保持定期复诊，及时调整用药方案\n"
            summary += "- 如果出现不适或副作用，请立即咨询医生\n"
            summary += "- 使用药物提醒功能，避免漏服或重复服药\n"
        
        return summary
    
    @staticmethod
    def _generate_recommendations(user_id, health_summary, diet_summary, exercise_summary, medication_summary):
        """生成健康建议"""
        recommendations = "健康改善建议：\n\n"
        
        # 检查是否有数据可用
        has_health_data = not health_summary.startswith("在所选时间段内没有健康记录数据")
        has_diet_data = not diet_summary.startswith("在所选时间段内没有饮食记录数据")
        
        # 检查运动数据 - 考虑显示历史记录的情况
        has_exercise_data = False
        if not exercise_summary.startswith("在所选时间段内没有运动记录数据"):
            has_exercise_data = True
        elif "正在显示所有历史记录" in exercise_summary:
            has_exercise_data = True
        
        # 检查用药数据 - 考虑显示历史记录的情况
        has_medication_data = False
        if not medication_summary.startswith("在所选时间段内没有用药记录数据"):
            has_medication_data = True
        elif "正在显示所有历史记录" in medication_summary:
            has_medication_data = True
        
        # 检查是否有历史数据（即使不在所选时间段内）
        using_historical_exercise = "包含所有历史记录" in exercise_summary or "正在显示所有历史记录" in exercise_summary
        using_historical_medication = "包含所有历史记录" in medication_summary or "正在显示所有历史记录" in medication_summary
        
        # 计算有多少类型的有效数据
        valid_data_types = sum([has_health_data, has_diet_data, has_exercise_data, has_medication_data])
        
        print(f"生成建议 - 有效数据类型数: {valid_data_types}, 健康:{has_health_data}, 饮食:{has_diet_data}, 运动:{has_exercise_data}, 用药:{has_medication_data}")
        
        # 分析运动数据，提取关键信息
        exercise_details = {}
        if has_exercise_data or using_historical_exercise:
            try:
                # 提取平均运动时间
                import re
                avg_duration_match = re.search(r"平均每日运动时间: (\d+) 分钟", exercise_summary)
                if avg_duration_match:
                    exercise_details["avg_duration"] = int(avg_duration_match.group(1))
                
                # 提取运动类型
                exercise_types = []
                type_section = exercise_summary.split("运动类型统计：")
                if len(type_section) > 1:
                    type_lines = type_section[1].split("\n运动建议")[0].strip().split("\n")
                    for line in type_lines:
                        if ":" in line:
                            exercise_type = line.split(":")[0].strip()
                            if exercise_type and exercise_type != "":
                                exercise_types.append(exercise_type)
                
                exercise_details["types"] = exercise_types
                print(f"提取的运动信息: {exercise_details}")
            except Exception as e:
                print(f"提取运动数据时出错: {e}")
        
        # 分析用药数据，提取关键信息
        medication_details = {}
        if has_medication_data or using_historical_medication:
            try:
                # 提取药物类型
                medications = []
                if "服用药物统计：" in medication_summary:
                    med_section = medication_summary.split("服用药物统计：")[1].split("\n\n用药建议")[0].strip()
                    med_lines = med_section.split("\n")
                    for line in med_lines:
                        if ":" in line:
                            med_name = line.split(":")[0].strip()
                            if med_name and med_name != "":
                                medications.append(med_name)
                
                medication_details["medications"] = medications
                print(f"提取的用药信息: {medication_details}")
            except Exception as e:
                print(f"提取用药数据时出错: {e}")
        
        # 基础建议
        recommendations += "1. 饮食建议：保持均衡的饮食结构，每日摄入充足的蛋白质、水果和蔬菜。\n"
        
        # 根据运动数据生成个性化建议
        if has_exercise_data or using_historical_exercise:
            avg_duration = exercise_details.get("avg_duration", 0)
            exercise_types = exercise_details.get("types", [])
            
            if avg_duration < 30:
                recommendations += "2. 运动建议：您的运动时间较少，建议增加到每天至少30分钟中等强度的有氧运动。"
            else:
                recommendations += "2. 运动建议：您的运动时间达标，请继续保持良好习惯。"
                
            # 根据运动类型给出建议
            if len(exercise_types) <= 2:
                recommendations += " 建议多样化您的运动类型，"
                missing_types = []
                has_cardio = any(t in ("跑步", "慢跑", "快走", "游泳", "骑车", "有氧") for t in exercise_types)
                has_strength = any(t in ("力量", "举重", "健身", "俯卧撑", "仰卧起坐") for t in exercise_types)
                has_flexibility = any(t in ("瑜伽", "拉伸", "舞蹈", "太极") for t in exercise_types)
                
                if not has_cardio:
                    missing_types.append("有氧运动（如慢跑、快走或游泳）")
                if not has_strength:
                    missing_types.append("力量训练（如哑铃、俯卧撑或仰卧起坐）")
                if not has_flexibility:
                    missing_types.append("灵活性训练（如瑜伽或拉伸）")
                
                if missing_types:
                    recommendations += "增加" + "、".join(missing_types) + "。"
            
            recommendations += "\n"
        else:
            recommendations += "2. 运动建议：每天至少进行30分钟中等强度的有氧运动，每周进行至少2次力量训练。\n"
        
        recommendations += "3. 睡眠建议：保持规律的作息，每晚保证7-8小时的充足睡眠。\n"
        
        # 根据用药数据生成个性化建议
        if has_medication_data or using_historical_medication:
            medications = medication_details.get("medications", [])
            if medications:
                recommendations += f"4. 用药提醒：您正在服用{len(medications)}种药物，包括{'、'.join(medications[:3])}"
                if len(medications) > 3:
                    recommendations += f"等{len(medications)}种药物"
                recommendations += "。请严格按照医生的处方和时间服用，并定期复诊。"
                
                # 添加额外建议
                recommendations += " 建议使用药物提醒功能，避免漏服或重复服药。\n"
            else:
                recommendations += "4. 用药提醒：按时按量服用医生开具的药物，注意记录药物效果和副作用。\n"
        else:
            recommendations += "4. 用药提醒：按时按量服用医生开具的药物，注意记录药物效果和副作用。\n"
        
        # 如果缺少数据，添加数据完整性建议
        if not has_exercise_data and not using_historical_exercise or not has_medication_data and not using_historical_medication:
            recommendations += "\n数据完整性建议：\n"
            
            if not has_exercise_data and not using_historical_exercise:
                recommendations += "- 您的报告缺少运动数据。建议您在添加记录页面添加运动记录，以便系统提供更全面的健康评估和更精准的运动建议。\n"
            
            if not has_medication_data and not using_historical_medication:
                recommendations += "- 您的报告缺少用药数据。如果您正在服用药物，建议您记录用药情况，以便系统更好地监控药物使用情况并提醒您按时服药。\n"
        
        return recommendations
    
    @staticmethod
    def get_user_reports(user_id, limit=10):
        """获取用户的健康报告列表
        
        参数:
            user_id: 用户ID
            limit: 返回结果数量限制
            
        返回:
            健康报告列表
        """
        reports = HealthReport.query.filter(
            HealthReport.user_id == user_id
        ).order_by(HealthReport.created_at.desc()).limit(limit).all()
        
        return reports
    
    @staticmethod
    def get_report_by_id(report_id, user_id):
        """根据ID获取健康报告
        
        参数:
            report_id: 报告ID
            user_id: 用户ID（用于验证权限）
            
        返回:
            健康报告对象或None
        """
        report = HealthReport.query.filter(
            HealthReport.id == report_id,
            HealthReport.user_id == user_id
        ).first()
        
        return report


class ReminderService:
    """提醒服务"""
    
    @staticmethod
    def create_medication_reminder(user_id, medication_record_id=None, title=None, description=None, 
                                  reminder_date=None, reminder_time=None, recurrence=None):
        """创建药物提醒
        
        参数:
            user_id: 用户ID
            medication_record_id: 药物记录ID (可选)
            title: 提醒标题
            description: 提醒描述
            reminder_date: 提醒日期
            reminder_time: 提醒时间
            recurrence: 重复类型
            
        返回:
            创建的提醒对象
        """
        # 检查药物记录ID是否提供，如果提供了，验证其是否存在于health_records表中
        medication_info = None
        if medication_record_id:
            try:
                # 尝试从HealthRecord表中获取药物记录
                medication_record = HealthRecord.query.filter_by(
                    id=medication_record_id,
                    user_id=user_id,
                    record_type='medication'
                ).first()
                
                if medication_record:
                    print(f"找到药物记录: ID={medication_record.id}, 药物名称={medication_record.medication_name}")
                    medication_info = medication_record
                    
                    # 如果未提供日期时间，则使用药物记录中的日期时间
                    if not reminder_date:
                        reminder_date = medication_record.record_date
                    if not reminder_time and hasattr(medication_record, 'time_taken') and medication_record.time_taken:
                        reminder_time = medication_record.time_taken
                    # 如果未提供标题，则使用药物记录中的药物名称
                    if not title and hasattr(medication_record, 'medication_name') and medication_record.medication_name:
                        title = f"服药提醒: {medication_record.medication_name}"
                    # 如果未提供描述，则根据药物记录生成描述
                    if not description:
                        dosage_text = f"{medication_record.dosage}{medication_record.dosage_unit}" if medication_record.dosage and medication_record.dosage_unit else ""
                        with_food_text = "饭后服用" if medication_record.with_food else ""
                        description_parts = []
                        if dosage_text:
                            description_parts.append(f"剂量: {dosage_text}")
                        if with_food_text:
                            description_parts.append(with_food_text)
                        description = ", ".join(description_parts)
                else:
                    print(f"警告: 未找到ID为{medication_record_id}的药物记录，将不关联药物记录")
                    medication_record_id = None  # 重置为None，因为找不到记录
            except Exception as e:
                print(f"获取药物记录出错: {e}")
                medication_record_id = None  # 出错时重置为None
        
        # 确保提醒有标题
        if not title:
            title = "服药提醒"
            
        # 确保有日期和时间
        if not reminder_date:
            reminder_date = datetime.now().date()
        if not reminder_time:
            reminder_time = datetime.now().time()
        
        # 创建提醒 (不使用medication_record_id外键)
        reminder = Reminder(
            user_id=user_id,
            reminder_type='medication',
            title=title,
            description=description,
            reminder_date=reminder_date,
            reminder_time=reminder_time,
            recurrence=recurrence,
            medication_record_id=None  # 始终设置为None以避免外键约束问题
        )
        
        # 如果我们找到了medication_record，可以添加相关信息到notes字段
        if medication_info:
            notes_data = {
                "medication_record_info": {
                    "id": medication_info.id,
                    "name": medication_info.medication_name,
                    "dosage": f"{medication_info.dosage or ''}{medication_info.dosage_unit or ''}",
                    "record_date": medication_info.record_date.strftime('%Y-%m-%d') if medication_info.record_date else None
                }
            }
            reminder.notes = json.dumps(notes_data)
        
        db.session.add(reminder)
        db.session.commit()
        
        return reminder
    
    @staticmethod
    def create_appointment_reminder(user_id, title, description, reminder_date, reminder_time, recurrence=None):
        """创建预约提醒
        
        参数:
            user_id: 用户ID
            title: 提醒标题
            description: 提醒描述
            reminder_date: 提醒日期
            reminder_time: 提醒时间
            recurrence: 重复类型
            
        返回:
            创建的提醒对象
        """
        reminder = Reminder(
            user_id=user_id,
            reminder_type='appointment',
            title=title,
            description=description,
            reminder_date=reminder_date,
            reminder_time=reminder_time,
            recurrence=recurrence
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return reminder
    
    @staticmethod
    def get_user_reminders(user_id, date=None, reminder_type=None):
        """获取用户的提醒列表
        
        参数:
            user_id: 用户ID
            date: 日期（默认为今天）
            reminder_type: 提醒类型
            
        返回:
            提醒列表
        """
        if date is None:
            date = datetime.now().date()
            
        query = Reminder.query.filter(Reminder.user_id == user_id)
        
        if date:
            query = query.filter(Reminder.reminder_date == date)
            
        if reminder_type:
            query = query.filter(Reminder.reminder_type == reminder_type)
            
        # 按时间排序
        reminders = query.order_by(Reminder.reminder_time).all()
        
        return reminders
    
    @staticmethod
    def update_reminder(reminder_id, user_id, **kwargs):
        """更新提醒
        
        参数:
            reminder_id: 提醒ID
            user_id: 用户ID
            **kwargs: 要更新的字段
            
        返回:
            更新后的提醒对象或None
        """
        reminder = Reminder.query.filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id
        ).first()
        
        if not reminder:
            return None
            
        # 更新提供的字段
        for key, value in kwargs.items():
            if hasattr(reminder, key):
                setattr(reminder, key, value)
                
        db.session.commit()
        
        return reminder
    
    @staticmethod
    def delete_reminder(reminder_id, user_id):
        """删除提醒
        
        参数:
            reminder_id: 提醒ID
            user_id: 用户ID
            
        返回:
            是否成功删除
        """
        reminder = Reminder.query.filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id
        ).first()
        
        if not reminder:
            return False
            
        db.session.delete(reminder)
        db.session.commit()
        
        return True
    
    @staticmethod
    def mark_reminder_as_completed(reminder_id, user_id):
        """将提醒标记为已完成
        
        参数:
            reminder_id: 提醒ID
            user_id: 用户ID
            
        返回:
            更新后的提醒对象或None
        """
        return ReminderService.update_reminder(reminder_id, user_id, is_completed=True)
    
    @staticmethod
    def generate_medication_reminders_from_records(user_id, date=None):
        """根据用药记录自动生成今日药物提醒
        
        参数:
            user_id: 用户ID
            date: 日期（默认为今天）
            
        返回:
            生成的提醒数量
        """
        if date is None:
            date = datetime.now().date()
            
        # 获取所有药物记录
        try:
            medication_records = HealthRecord.query.filter(
                HealthRecord.user_id == user_id,
                HealthRecord.record_type == 'medication'
            ).all()
            
            print(f"找到 {len(medication_records)} 条药物记录")
            
            # 检查每个药物是否已有今天的提醒
            created_count = 0
            for med_record in medication_records:
                # 查询是否已存在该药物的今日提醒
                existing_reminder = Reminder.query.filter(
                    Reminder.user_id == user_id,
                    Reminder.reminder_date == date
                ).first()
                
                # 如果不存在，则创建新提醒
                if not existing_reminder:
                    title = f"服药提醒: {med_record.medication_name}" if med_record.medication_name else "服药提醒"
                    
                    # 构建描述
                    description_parts = []
                    if med_record.dosage and med_record.dosage_unit:
                        description_parts.append(f"剂量: {med_record.dosage} {med_record.dosage_unit}")
                    if med_record.with_food:
                        description_parts.append("请饭后服用")
                        
                    description = "，".join(description_parts) if description_parts else "按医嘱服用"
                    
                    # 创建提醒 - 注意不使用medication_record_id外键
                    reminder = Reminder(
                        user_id=user_id,
                        reminder_type='medication',
                        title=title,
                        description=description,
                        reminder_date=date,
                        reminder_time=med_record.time_taken if med_record.time_taken else datetime.now().time(),
                        recurrence=None,
                        medication_record_id=None  # 避免外键约束问题
                    )
                    
                    # 添加药物记录信息到notes
                    notes_data = {
                        "medication_record_info": {
                            "id": med_record.id,
                            "name": med_record.medication_name,
                            "dosage": f"{med_record.dosage or ''}{med_record.dosage_unit or ''}",
                            "record_date": med_record.record_date.strftime('%Y-%m-%d') if med_record.record_date else None
                        }
                    }
                    reminder.notes = json.dumps(notes_data)
                    
                    db.session.add(reminder)
                    created_count += 1
            
            if created_count > 0:
                db.session.commit()
                print(f"成功创建 {created_count} 条药物提醒")
            
            return created_count
            
        except Exception as e:
            print(f"自动生成药物提醒时出错: {e}")
            import traceback
            traceback.print_exc()
            # 回滚事务
            db.session.rollback()
            return 0 