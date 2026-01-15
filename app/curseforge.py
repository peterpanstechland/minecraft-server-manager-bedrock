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
        
        # 尝试从URL中提取数字ID
        # 格式: https://www.curseforge.com/minecraft-bedrock/addons/{id}
        id_pattern = r'/(\d+)(?:/|$)'
        id_match = re.search(id_pattern, url_or_id)
        if id_match and id_match.group(1).isdigit():
            return id_match.group(1)
        
        # 如果没有找到数字ID，返回None，让调用者通过slug查找
        return None
    
    @staticmethod
    def extract_slug(url_or_id: str) -> Optional[str]:
        """从URL中提取slug"""
        # 格式: https://www.curseforge.com/minecraft-bedrock/addons/{slug}
        # 或: https://www.curseforge.com/minecraft-bedrock/addons/{slug}/files/{fileId}
        patterns = [
            r'curseforge\.com/[^/]+/[^/]+/([^/]+?)(?:/|$)',
            r'/([^/]+?)(?:/files/|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                slug = match.group(1)
                # 确保不是数字（数字应该是ID）
                if not slug.isdigit():
                    return slug
        
        # 如果整个字符串看起来像slug（没有特殊字符，不是URL）
        if not url_or_id.startswith('http') and not url_or_id.isdigit():
            return url_or_id
        
        return None
    
    @staticmethod
    def get_project_by_slug(slug: str) -> Optional[Dict]:
        """通过slug获取项目信息"""
        if not CurseForgeAPI.API_KEY:
            print("Error: CurseForge API密钥未配置")
            return None
        
        try:
            # 使用search API查找项目
            url = f"{CurseForgeAPI.BASE_URL}/mods/search"
            headers = {
                'x-api-key': CurseForgeAPI.API_KEY,
                'Accept': 'application/json'
            }
            params = {
                'gameId': 432,  # Minecraft Bedrock Edition
                'slug': slug,
                'pageSize': 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    return data['data'][0]
            elif response.status_code == 401:
                print("Error: CurseForge API密钥无效")
            elif response.status_code == 403:
                print("Error: CurseForge API访问被拒绝")
            else:
                print(f"Error: CurseForge API返回状态码 {response.status_code}")
                print(f"Response: {response.text[:200]}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching project by slug: {e}")
        except Exception as e:
            print(f"Error fetching project by slug: {e}")
            import traceback
            traceback.print_exc()
        
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
        # 检查API密钥
        if not CurseForgeAPI.API_KEY:
            return False, "CurseForge API密钥未配置。\n\n解决方案：\n1. 申请API密钥（见CURSEFORGE_SETUP.md）\n2. 或直接下载文件后使用'文件上传'功能", None, None
        
        # 提取项目ID
        project_id = CurseForgeAPI.extract_project_id(url_or_id)
        
        # 如果没有找到ID，尝试通过slug查找
        if not project_id:
            slug = CurseForgeAPI.extract_slug(url_or_id)
            if slug:
                print(f"通过slug查找项目: {slug}")
                project_info = CurseForgeAPI.get_project_by_slug(slug)
                if project_info:
                    project_id = str(project_info.get('id'))
                    print(f"找到项目ID: {project_id}")
                else:
                    return False, f"无法找到slug为 '{slug}' 的项目。请检查URL是否正确，或确保已配置有效的CurseForge API密钥", None, None
            else:
                return False, f"无法解析CurseForge项目ID或slug。请提供完整的URL（如：https://www.curseforge.com/minecraft-bedrock/addons/项目名）或项目ID", None, None
        
        if not project_id:
            return False, "无法解析CurseForge项目ID", None, None
        
        # 获取项目信息
        project_info = CurseForgeAPI.get_project_info(project_id)
        if not project_info:
            return False, f"无法获取项目信息（ID: {project_id}）。请检查项目ID是否正确，或确保已配置有效的CurseForge API密钥", None, None
        
        # 获取最新文件
        latest_file = CurseForgeAPI.get_latest_file(project_id)
        if not latest_file:
            return False, "无法获取最新文件。项目可能没有可用的文件", None, None
        
        # 下载文件
        file_path = CurseForgeAPI.download_file(str(latest_file['id']), project_id)
        if not file_path:
            return False, "下载失败。请检查网络连接或稍后重试", None, None
        
        return True, "下载成功", file_path, {
            'project_id': project_id,
            'project_name': project_info.get('name'),
            'file_id': latest_file['id'],
            'file_name': latest_file.get('fileName'),
            'version': latest_file.get('displayName', ''),
            'url': f"https://www.curseforge.com/minecraft-bedrock/addons/{project_info.get('slug', project_id)}"
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

