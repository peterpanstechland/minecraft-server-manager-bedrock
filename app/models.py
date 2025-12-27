from app import db
from datetime import datetime

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

