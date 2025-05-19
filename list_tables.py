from database import db
from flask import Flask
import os
import sqlite3

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/personal_health.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def list_tables():
    app = create_app()
    
    # 检查数据库文件
    db_path = os.path.join(os.getcwd(), 'instance', 'personal_health.db')
    print(f"检查数据库文件: {db_path}")
    if os.path.exists(db_path):
        print(f"数据库文件存在，大小: {os.path.getsize(db_path) / 1024:.2f} KB")
    else:
        print(f"数据库文件不存在!")
        
    # 尝试直接打开SQLite文件
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\n直接从SQLite读取的表:")
        for i, (table_name,) in enumerate(tables, 1):
            print(f"{i}. {table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                col_id, name, type_name, notnull, default_val, pk = col
                print(f"  - {name}: {type_name}")
                
        conn.close()
    except Exception as e:
        print(f"直接连接SQLite数据库失败: {str(e)}")
        
    # 尝试通过SQLAlchemy读取
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("\nSQLAlchemy读取的表:")
            for i, table in enumerate(tables, 1):
                print(f"{i}. {table}")
                
            if not tables:
                print("SQLAlchemy没有检测到任何表，可能数据库配置不正确或数据库为空")
        except Exception as e:
            print(f"SQLAlchemy检查数据库失败: {str(e)}")

if __name__ == "__main__":
    list_tables() 