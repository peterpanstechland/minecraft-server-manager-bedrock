import os
from pathlib import Path

class Config:
    """应用配置类"""
    # 基础配置
    BASE_DIR = Path(__file__).parent
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据库配置
    DATABASE_PATH = BASE_DIR / 'database' / 'bedrock_manager.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR / "database" / "bedrock_manager.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Bedrock服务器配置
    BEDROCK_SERVER_DIR = Path(os.environ.get('BEDROCK_SERVER_DIR', '/home/ubuntu/bedrock-server'))
    BEDROCK_SERVER_BINARY = BEDROCK_SERVER_DIR / 'bedrock_server'
    BEHAVIOR_PACKS_DIR = BEDROCK_SERVER_DIR / 'behavior_packs'
    RESOURCE_PACKS_DIR = BEDROCK_SERVER_DIR / 'resource_packs'
    WORLD_DIR = BEDROCK_SERVER_DIR / 'worlds' / 'Bedrock level'
    WORLD_BEHAVIOR_PACKS_CONFIG = WORLD_DIR / 'world_behavior_packs.json'
    WORLD_RESOURCE_PACKS_CONFIG = WORLD_DIR / 'world_resource_packs.json'
    
    # 文件上传配置
    UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'mcpack', 'zip'}
    
    # CurseForge API配置
    CURSEFORGE_API_KEY = os.environ.get('CURSEFORGE_API_KEY', '')
    CURSEFORGE_API_URL = 'https://api.curseforge.com/v1'
    
    # 服务器配置
    SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
    
    # 日志配置
    LOG_FILE = BEDROCK_SERVER_DIR / 'Dedicated_Server.txt'

