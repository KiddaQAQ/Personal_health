from flask import Blueprint, render_template, redirect, url_for, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def index():
    """首页"""
    return redirect(url_for('pages.login'))

@pages_bp.route('/login')
def login():
    """登录页面"""
    return render_template('login.html')

@pages_bp.route('/register')
def register():
    """注册页面"""
    return render_template('register.html')

@pages_bp.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    return render_template('dashboard.html')

@pages_bp.route('/analysis')
def analysis():
    """营养分析与运动建议页面"""
    return render_template('analysis.html')

@pages_bp.route('/records')
def records():
    """所有记录页面"""
    return render_template('records.html')

@pages_bp.route('/health/records')
def health_records():
    """健康记录页面"""
    return render_template('health_records.html')

@pages_bp.route('/health-report')
def health_report():
    return render_template('health_report.html')

@pages_bp.route('/reminders')
def reminders():
    return render_template('reminders.html')

@pages_bp.route('/social')
def social():
    """社交互动页面"""
    return render_template('social.html')

@pages_bp.route('/social/share/<int:share_id>')
def share_detail(share_id):
    """分享详情页面"""
    return render_template('share_detail.html', share_id=share_id)

@pages_bp.route('/settings')
def settings():
    return redirect(url_for('pages.dashboard')) 