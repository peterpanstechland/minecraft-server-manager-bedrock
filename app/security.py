"""安全工具函数"""
import os
import re
import zipfile
from pathlib import Path
from typing import Tuple, Optional
import bleach

def sanitize_filename(filename: str) -> str:
    """清理文件名，防止目录穿越攻击"""
    # 移除路径分隔符和特殊字符
    filename = os.path.basename(filename)
    # 只保留字母、数字、下划线、连字符和点
    filename = re.sub(r'[^\w\-.]', '_', filename)
    # 防止隐藏文件
    if filename.startswith('.'):
        filename = '_' + filename
    return filename

def validate_path(base_path: Path, target_path: Path) -> bool:
    """验证目标路径是否在基础路径内，防止目录穿越"""
    try:
        base_path = base_path.resolve()
        target_path = target_path.resolve()
        return str(target_path).startswith(str(base_path))
    except Exception:
        return False

def safe_extract_zip(zip_path: Path, extract_to: Path, max_size: int = 500 * 1024 * 1024) -> Tuple[bool, str]:
    """
    安全解压ZIP文件，防止Zip Slip攻击
    
    Args:
        zip_path: ZIP文件路径
        extract_to: 解压目标目录
        max_size: 最大解压后文件大小（默认500MB）
    
    Returns:
        (成功标志, 错误消息或成功消息)
    """
    try:
        extract_to = extract_to.resolve()
        total_size = 0
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 检查ZIP文件完整性
            if zip_ref.testzip() is not None:
                return False, 'ZIP文件损坏或不完整'
            
            for member in zip_ref.namelist():
                # 检查路径穿越
                member_path = (extract_to / member).resolve()
                if not str(member_path).startswith(str(extract_to)):
                    return False, f'检测到不安全的文件路径: {member}'
                
                # 检查文件大小
                file_info = zip_ref.getinfo(member)
                total_size += file_info.file_size
                if total_size > max_size:
                    return False, f'解压后文件总大小超过限制 ({max_size / 1024 / 1024}MB)'
                
                # 安全解压单个文件
                if not member.endswith('/'):
                    # 确保父目录存在
                    member_path.parent.mkdir(parents=True, exist_ok=True)
                    # 读取内容并写入（避免直接extractall）
                    with zip_ref.open(member) as source, open(member_path, 'wb') as target:
                        target.write(source.read())
                else:
                    # 创建目录
                    member_path.mkdir(parents=True, exist_ok=True)
        
        return True, f'成功解压到 {extract_to}'
    
    except zipfile.BadZipFile:
        return False, 'ZIP文件格式错误'
    except PermissionError:
        return False, '没有权限访问目标目录'
    except Exception as e:
        return False, f'解压失败: {str(e)}'

def validate_uuid(uuid_str: str) -> bool:
    """验证UUID格式"""
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, uuid_str.lower()))

def validate_pack_type(pack_type: str) -> bool:
    """验证包类型"""
    return pack_type in ['behavior', 'resource']

def sanitize_html(text: str) -> str:
    """清理HTML，防止XSS攻击"""
    if not text:
        return ''
    # 只允许安全的标签和属性
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'code', 'pre']
    return bleach.clean(text, tags=allowed_tags, strip=True)

def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """验证文件扩展名"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def check_file_size(file_size: int, max_size: int) -> Tuple[bool, Optional[str]]:
    """检查文件大小"""
    if file_size > max_size:
        return False, f'文件大小 ({file_size / 1024 / 1024:.2f}MB) 超过限制 ({max_size / 1024 / 1024}MB)'
    return True, None

def validate_url(url: str) -> bool:
    """验证URL格式（基础验证）"""
    url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    return bool(re.match(url_pattern, url))
