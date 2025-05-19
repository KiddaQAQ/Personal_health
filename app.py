from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from database import db, init_db, update_password_hash_field
from datetime import timedelta

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# 配置
app.config['SECRET_KEY'] = 'personal_health_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/personal_health_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)  # 设置JWT令牌过期时间为1天
app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'  # 确保错误消息以message键返回

# 初始化插件
jwt = JWTManager(app)
init_db(app)
update_password_hash_field(app)

# 自定义JWT错误处理
@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"JWT错误 - 未授权: {error}")
    return jsonify({
        'success': False,
        'message': '缺少JWT令牌, 请先登录',
        'records': [],
        'count': 0
    }), 200  # 返回200而不是401，避免前端中断

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"JWT错误 - 令牌无效: {error}")
    return jsonify({
        'success': False,
        'message': 'JWT令牌无效或已过期',
        'records': [],
        'count': 0
    }), 200  # 返回200而不是422，避免前端中断

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print("JWT错误 - 令牌已过期")
    return jsonify({
        'success': False,
        'message': 'JWT令牌已过期，请重新登录',
        'records': [],
        'count': 0
    }), 200  # 返回200而不是401，避免前端中断

# 先导入所有模型，确保它们被加载
from models.user import User
from models.health_record import HealthRecord
from models.diet_record import DietRecord, Food, DietRecordItem
from models.health_goal import HealthGoal
from models.medication_record import MedicationType, MedicationRecord
from models.exercise import ExerciseType, ExerciseRecord
from models.water_intake import WaterIntake
from models.health_report import HealthReport, Reminder
from models.social import Share, Like, Comment

# 导入蓝图
from routes.auth import auth_bp
from routes.health import health_bp
from routes.pages import pages_bp
from routes.analysis import analysis_bp
from routes.diet import diet_bp
from routes.exercise import exercise_bp
from routes.medication import medication_bp
from routes.health_report import health_report_bp
from routes.social import social_bp
# 导入独立的记录类型蓝图
from routes.health_metrics import health_metrics_bp
from routes.water import water_bp

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(health_bp, url_prefix='/api/health')
app.register_blueprint(pages_bp)
app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
app.register_blueprint(diet_bp)
app.register_blueprint(exercise_bp, url_prefix='/api/exercise')
app.register_blueprint(medication_bp, url_prefix='/api/medication')
app.register_blueprint(health_report_bp, url_prefix='/api/health-report')
app.register_blueprint(social_bp, url_prefix='/api/social')
# 注册独立的记录类型蓝图
app.register_blueprint(health_metrics_bp)
app.register_blueprint(water_bp)

# 全局错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': '未找到请求的资源'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': '服务器内部错误'}), 500

@app.route('/')
def index():
    return 'Personal Health API'

if __name__ == '__main__':
    app.run(debug=True)
