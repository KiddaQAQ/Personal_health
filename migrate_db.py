from database import db
from app import app
from models.health_record import HealthRecord

def migrate_add_sugar_field():
    """向health_records表添加sugar字段"""
    with app.app_context():
        # 检查数据库连接
        try:
            # 打印SQL语句并执行它
            sql = "ALTER TABLE health_records ADD COLUMN sugar FLOAT"
            print(f"执行SQL: {sql}")
            
            # 执行SQL
            conn = db.engine.connect()
            try:
                conn.execute(sql)
                conn.close()
                print("成功添加sugar字段到health_records表")
            except Exception as e:
                # 如果字段已存在，MySQL将报错，但SQLite会忽略
                # 我们捕获这个错误并继续
                print(f"添加字段时出错(可能字段已存在): {str(e)}")
                
            print("数据库迁移完成")
            
        except Exception as e:
            print(f"数据库连接或迁移出错: {str(e)}")

if __name__ == "__main__":
    migrate_add_sugar_field() 