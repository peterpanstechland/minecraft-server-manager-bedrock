from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    
    # 确保数据库目录存在
    config_class.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{config_class.DATABASE_PATH}'
    
    # 确保上传目录存在
    config_class.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    
    from app.routes import bp
    app.register_blueprint(bp)
    
    with app.app_context():
        db.create_all()
    
    return app

