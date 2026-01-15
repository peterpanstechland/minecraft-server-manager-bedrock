from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        """设置密码（哈希存储）"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Addon(db.Model):
    __tablename__ = 'addons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    pack_type = db.Column(db.String(20), nullable=False)  # 'behavior' or 'resource'
    version = db.Column(db.String(50))
    curseforge_id = db.Column(db.String(50), nullable=True)
    curseforge_url = db.Column(db.String(500), nullable=True)
    local_path = db.Column(db.String(500), nullable=False)
    enabled = db.Column(db.Boolean, default=False)
    installed_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_checked = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'uuid': self.uuid,
            'type': self.pack_type,
            'version': self.version,
            'curseforge_id': self.curseforge_id,
            'curseforge_url': self.curseforge_url,
            'local_path': self.local_path,
            'enabled': self.enabled,
            'installed_date': self.installed_date.isoformat() if self.installed_date else None,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'description': self.description
        }
    
    def __repr__(self):
        return f'<Addon {self.name} ({self.pack_type})>'

