from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import logging
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "10000 per day"],  # 提高默认限制，避免频繁刷新导致429
    storage_uri="memory://"
)

def create_app(config_class=Config):
    app = Flask(__name__, template_folder=str(config_class.BASE_DIR / 'templates'))
    app.config.from_object(config_class)
    
    # 生成强随机SECRET_KEY（如果未设置）
    if app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
        app.logger.warning('使用默认SECRET_KEY，生产环境请设置环境变量SECRET_KEY')
        app.config['SECRET_KEY'] = os.urandom(24).hex()
    
    # 设置文件上传大小限制
    app.config['MAX_CONTENT_LENGTH'] = config_class.MAX_UPLOAD_SIZE
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # 配置LoginManager
    login_manager.login_view = 'main.login'
    login_manager.login_message = '请先登录'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # 确保数据库目录存在
    config_class.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{config_class.DATABASE_PATH}'
    
    # 确保上传目录存在
    config_class.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    
    from app.routes import bp
    app.register_blueprint(bp)
    
    # 错误处理
    @app.errorhandler(413)
    def request_entity_too_large(error):
        max_size_mb = config_class.MAX_UPLOAD_SIZE / (1024 * 1024)
        return jsonify({
            'success': False,
            'message': f'文件太大。最大允许: {max_size_mb}MB'
        }), 413
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            'success': False,
            'message': '请求过于频繁，请稍后再试'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal error: {error}')
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500
    
    with app.app_context():
        db.create_all()
        # 创建默认管理员用户（如果不存在）
        from app.models import User
        admin_username = app.config.get('ADMIN_USERNAME', 'admin')
        admin_password = app.config.get('ADMIN_PASSWORD', '')
        
        if not User.query.filter_by(username=admin_username).first():
            if admin_password:
                admin = User(username=admin_username)
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                app.logger.info(f'创建默认管理员用户: {admin_username}')
            else:
                app.logger.warning('未设置ADMIN_PASSWORD环境变量，请手动创建管理员用户')
    
    return app

