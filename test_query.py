from database import db
from sqlalchemy import text
from flask import Flask
import sys

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///personalhealth.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def test_query(record_id, record_type='diet'):
    app = create_app()
    with app.app_context():
        try:
            # 检查health_records表
            query = text(f"SELECT * FROM health_records WHERE id = :id AND record_type = :record_type LIMIT 1")
            result = db.session.execute(query, {"id": record_id, "record_type": record_type}).fetchone()
            if result:
                print(f"记录ID={record_id}在health_records表中找到，记录类型={record_type}")
                # 打印记录详情
                columns = result.keys()
                for col in columns:
                    print(f"{col}: {result[col]}")
                return True
            else:
                print(f"记录ID={record_id}在health_records表中未找到，记录类型={record_type}")
                
            # 尝试检查其他可能的表
            if record_type == 'diet':
                query = text("SELECT * FROM diet_records WHERE id = :id LIMIT 1")
                result = db.session.execute(query, {"id": record_id}).fetchone()
                if result:
                    print(f"记录ID={record_id}在diet_records表中找到")
                    return True
            
            # 最后检查所有记录
            query = text("SELECT * FROM health_records WHERE id = :id LIMIT 1")
            result = db.session.execute(query, {"id": record_id}).fetchone()
            if result:
                print(f"记录ID={record_id}在health_records表中找到，但记录类型={result['record_type']}，与期望的{record_type}不符")
                return False
                
            print(f"记录ID={record_id}的记录不存在")
            return False
            
        except Exception as e:
            print(f"查询时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    record_id = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    record_type = sys.argv[2] if len(sys.argv) > 2 else 'diet'
    test_query(record_id, record_type) 