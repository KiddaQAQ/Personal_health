from database import db
from flask import Flask
import sys

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///personalhealth.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def check_record(record_id, record_type=None):
    app = create_app()
    with app.app_context():
        # 首先从统一的健康记录表中查询
        try:
            from models.health_record import HealthRecord
            hr_record = HealthRecord.query.filter_by(id=record_id).first()
            if hr_record:
                print(f'在HealthRecord表中找到记录ID={record_id}:')
                print(f'记录类型: {hr_record.record_type}')
                print(f'记录日期: {hr_record.record_date}')
                print(f'用户ID: {hr_record.user_id}')
                if hr_record.record_type == 'diet':
                    print(f'食物名称: {hr_record.food_name}')
                    print(f'餐食类型: {hr_record.meal_type}')
                    print(f'食物量: {hr_record.food_amount}')
                elif hr_record.record_type == 'exercise':
                    print(f'运动类型: {hr_record.exercise_type}')
                    print(f'持续时间: {hr_record.duration}分钟')
                return
        except Exception as e:
            print(f"检查HealthRecord表时出错: {str(e)}")
        
        # 根据类型检查专用表
        if record_type == 'diet' or not record_type:
            try:
                from models.diet_record import DietRecord
                diet_record = DietRecord.query.filter_by(id=record_id).first()
                if diet_record:
                    print(f'在DietRecord表中找到记录ID={record_id}:')
                    print(f'用户ID: {diet_record.user_id}')
                    print(f'记录日期: {diet_record.record_date}')
                    print(f'餐食类型: {diet_record.meal_type}')
                    return
            except Exception as e:
                print(f"检查DietRecord表时出错: {str(e)}")
        
        if record_type == 'exercise' or not record_type:
            try:
                from models.exercise import ExerciseRecord
                exercise_record = ExerciseRecord.query.filter_by(id=record_id).first()
                if exercise_record:
                    print(f'在ExerciseRecord表中找到记录ID={record_id}:')
                    print(f'用户ID: {exercise_record.user_id}')
                    print(f'记录日期: {exercise_record.record_date}')
                    print(f'运动类型: {exercise_record.exercise_type}')
                    return
            except Exception as e:
                print(f"检查ExerciseRecord表时出错: {str(e)}")
        
        if record_type == 'medication' or not record_type:
            try:
                from models.medication_record import MedicationRecord
                med_record = MedicationRecord.query.filter_by(id=record_id).first()
                if med_record:
                    print(f'在MedicationRecord表中找到记录ID={record_id}:')
                    print(f'用户ID: {med_record.user_id}')
                    print(f'记录日期: {med_record.record_date}')
                    try:
                        print(f'药物名称: {med_record.medication_type.name}')
                    except:
                        print(f'药物ID: {med_record.medication_type_id}')
                    return
            except Exception as e:
                print(f"检查MedicationRecord表时出错: {str(e)}")
        
        print(f'记录ID={record_id}在所有表中均未找到')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        record_id = int(sys.argv[1])
        record_type = sys.argv[2] if len(sys.argv) > 2 else None
        check_record(record_id, record_type)
    else:
        print('请提供记录ID作为参数')
        print('示例: python check_record.py 35 [diet|exercise|medication]') 