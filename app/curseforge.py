import re
import requests
import tempfile
from pathlib import Path
from typing import Optional, Dict, Tuple
from config import Config

class CurseForgeAPI:
    """CurseForge API集成"""
    
    BASE_URL = Config.CURSEFORGE_API_URL
    API_KEY = Config.CURSEFORGE_API_KEY
    
    @staticmethod
    def extract_project_id(url_or_id: str) -> Optional[str]:
        """从URL或直接ID中提取项目ID"""
        # 如果是纯数字，直接返回
        if url_or_id.isdigit():
            return url_or_id
        
        # 尝试从URL中提取
        # 格式: https://www.curseforge.com/minecraft-bedrock/addons/{slug}
        # 或: https://www.curseforge.com/minecraft-bedrock/addons/{slug}/files/{fileId}
        patterns = [
            r'curseforge\.com/[^/]+/[^/]+/([^/]+)',
            r'/(\d+)/',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                # 如果是数字，直接返回
                if match.group(1).isdigit():
                    return match.group(1)
                # 否则需要通过slug查找项目ID
        
        return None
    
    @staticmethod
    def get_project_by_slug(slug: str) -> Optional[Dict]:
        """通过slug获取项目信息"""
        if not CurseForgeAPI.API_KEY:
            return None
        
        try:
            url = f"{CurseForgeAPI.BASE_URL}/mods/search"
            headers = {
                'x-api-key': CurseForgeAPI.API_KEY,
                'Accept': 'application/json'
            }
            params = {
                'gameId': 432,  # Minecraft Bedrock Edition
                'slug': slug
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    return data['data'][0]
        except Exception as e:
            print(f"Error fetching project by slug: {e}")
        
        return None
    
    @staticmethod
    def get_project_info(project_id: str) -> Optional[Dict]:
        """获取项目信息"""
        if not CurseForgeAPI.API_KEY:
            return None
        
        try:
            url = f"{CurseForgeAPI.BASE_URL}/mods/{project_id}"
            headers = {
                'x-api-key': CurseForgeAPI.API_KEY,
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json().get('data')
        except Exception as e:
            print(f"Error fetching project info: {e}")
        
        return None
    
    @staticmethod
    def get_latest_file(project_id: str) -> Optional[Dict]:
        """获取项目的最新文件"""
        if not CurseForgeAPI.API_KEY:
            return None
        
        try:
            url = f"{CurseForgeAPI.BASE_URL}/mods/{project_id}/files"
            headers = {
                'x-api-key': CurseForgeAPI.API_KEY,
                'Accept': 'application/json'
            }
            params = {
                'gameVersion': '',  # 可以指定游戏版本
                'index': 0,
                'pageSize': 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    return data['data'][0]
        except Exception as e:
            print(f"Error fetching latest file: {e}")
        
        return None
    
    @staticmethod
    def download_file(file_id: str, project_id: str) -> Optional[Path]:
        """下载文件"""
        if not CurseForgeAPI.API_KEY:
            return None
        
        try:
            # 获取下载URL
            url = f"{CurseForgeAPI.BASE_URL}/mods/{project_id}/files/{file_id}/download-url"
            headers = {
                'x-api-key': CurseForgeAPI.API_KEY,
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            download_url = response.json().get('data')
            if not download_url:
                return None
            
            # 下载文件
            file_response = requests.get(download_url, timeout=30, stream=True)
            if file_response.status_code != 200:
                return None
            
            # 保存到临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mcpack')
            temp_path = Path(temp_file.name)
            
            with open(temp_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return temp_path
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
    
    @staticmethod
    def install_from_curseforge(url_or_id: str) -> Tuple[bool, str, Optional[Path], Optional[Dict]]:
        """从CurseForge安装addon"""
        # 提取项目ID
        project_id = CurseForgeAPI.extract_project_id(url_or_id)
        
        if not project_id:
            # 尝试通过slug查找
            slug_match = re.search(r'/([^/]+)/?$', url_or_id)
            if slug_match:
                slug = slug_match.group(1)
                project_info = CurseForgeAPI.get_project_by_slug(slug)
                if project_info:
                    project_id = str(project_info.get('id'))
        
        if not project_id:
            return False, "无法解析CurseForge项目ID", None, None
        
        # 获取项目信息
        project_info = CurseForgeAPI.get_project_info(project_id)
        if not project_info:
            return False, "无法获取项目信息", None, None
        
        # 获取最新文件
        latest_file = CurseForgeAPI.get_latest_file(project_id)
        if not latest_file:
            return False, "无法获取最新文件", None, None
        
        # 下载文件
        file_path = CurseForgeAPI.download_file(str(latest_file['id']), project_id)
        if not file_path:
            return False, "下载失败", None, None
        
        return True, "下载成功", file_path, {
            'project_id': project_id,
            'project_name': project_info.get('name'),
            'file_id': latest_file['id'],
            'file_name': latest_file.get('fileName'),
            'version': latest_file.get('displayName', ''),
            'url': f"https://www.curseforge.com/minecraft-bedrock/addons/{project_info.get('slug')}"
        }
    
    @staticmethod
    def check_update(addon: 'Addon') -> Tuple[bool, Optional[Dict]]:
        """检查addon是否有更新"""
        if not addon.curseforge_id:
            return False, None
        
        try:
            # 获取最新文件信息
            latest_file = CurseForgeAPI.get_latest_file(addon.curseforge_id)
            if not latest_file:
                return False, None
            
            # 比较版本（简单比较文件名或显示名称）
            latest_version = latest_file.get('displayName', '')
            current_version = addon.version or ''
            
            # 如果版本不同，返回更新信息
            if latest_version != current_version:
                return True, {
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'file_id': latest_file['id'],
                    'file_name': latest_file.get('fileName')
                }
            
            return False, None
        except Exception as e:
            print(f"Error checking update: {e}")
            return False, None

