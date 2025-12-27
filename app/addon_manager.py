import json
import shutil
import zipfile
import tempfile
import re
import time
from pathlib import Path
from typing import Optional, Dict, Tuple
from app import db
from app.models import Addon
from config import Config

class AddonManager:
    """管理Bedrock服务器addon的安装、部署和配置"""
    
    @staticmethod
    def extract_pack_info(pack_path: Path) -> Optional[Dict]:
        """从addon文件中提取包信息"""
        temp_dir = tempfile.mkdtemp()
        try:
            # 解压文件
            with zipfile.ZipFile(pack_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 查找manifest.json
            manifest_path = None
            pack_root = None
            
            # 检查根目录
            root_manifest = Path(temp_dir) / 'manifest.json'
            if root_manifest.exists():
                manifest_path = root_manifest
                pack_root = Path(temp_dir)
            else:
                # 查找子目录中的manifest.json
                for manifest_file in Path(temp_dir).rglob('manifest.json'):
                    manifest_path = manifest_file
                    pack_root = manifest_file.parent
                    break
            
            if not manifest_path or not manifest_path.exists():
                return None
            
            # 读取manifest.json
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # 提取信息
            header = manifest.get('header', {})
            uuid = header.get('uuid', '')
            name = header.get('name', pack_path.stem)
            version = header.get('version', [0, 0, 0])
            version_str = '.'.join(map(str, version))
            
            # 确定包类型
            pack_type = 'behavior'
            if 'resources' in str(manifest_path).lower() or header.get('type') == 'resources':
                pack_type = 'resource'
            elif 'data' in str(manifest_path).lower() or header.get('type') == 'data':
                pack_type = 'behavior'
            
            # 检查是否有functions、scripts等行为包特征
            if pack_type == 'behavior':
                has_functions = (pack_root / 'functions').exists()
                has_scripts = (pack_root / 'scripts').exists()
                has_entities = (pack_root / 'entities').exists()
                if not (has_functions or has_scripts or has_entities):
                    # 检查是否有textures等资源包特征
                    if (pack_root / 'textures').exists() or (pack_root / 'ui').exists():
                        pack_type = 'resource'
            
            return {
                'uuid': uuid,
                'name': name,
                'version': version_str,
                'type': pack_type,
                'manifest': manifest,
                'pack_root': pack_root
            }
        except Exception as e:
            print(f"Error extracting pack info: {e}")
            return None
        finally:
            # 清理临时文件
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @staticmethod
    def deploy_addon(pack_path: Path, pack_info: Dict) -> Tuple[bool, str]:
        """部署addon到服务器目录"""
        try:
            # 确定目标目录
            if pack_info['type'] == 'behavior':
                target_dir = Config.BEHAVIOR_PACKS_DIR
            else:
                target_dir = Config.RESOURCE_PACKS_DIR
            
            # 清理包名用于目录名
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', pack_info['name'])
            safe_name = re.sub(r'_+', '_', safe_name)
            target_pack_dir = target_dir / safe_name
            
            # 如果目录已存在，备份
            if target_pack_dir.exists():
                backup_dir = target_dir / f"{safe_name}.backup.{int(time.time())}"
                shutil.move(str(target_pack_dir), str(backup_dir))
            
            # 解压并复制到目标目录
            temp_dir = tempfile.mkdtemp()
            try:
                with zipfile.ZipFile(pack_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # 查找实际的包根目录
                pack_root = None
                root_manifest = Path(temp_dir) / 'manifest.json'
                if root_manifest.exists():
                    pack_root = Path(temp_dir)
                else:
                    for manifest_file in Path(temp_dir).rglob('manifest.json'):
                        pack_root = manifest_file.parent
                        break
                
                if not pack_root:
                    return False, "找不到manifest.json"
                
                # 复制到目标目录
                shutil.copytree(str(pack_root), str(target_pack_dir))
                
                return True, str(target_pack_dir)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            return False, f"部署失败: {str(e)}"
    
    @staticmethod
    def update_world_config():
        """更新世界配置文件以启用所有已启用的addon"""
        try:
            # 获取所有启用的addon
            enabled_addons = Addon.query.filter_by(enabled=True).all()
            
            behavior_packs = []
            resource_packs = []
            
            for addon in enabled_addons:
                pack_config = {
                    "pack_id": addon.uuid,
                    "version": [1, 0, 0]  # 默认版本，可以从manifest中读取
                }
                
                if addon.pack_type == 'behavior':
                    behavior_packs.append(pack_config)
                else:
                    resource_packs.append(pack_config)
            
            # 写入配置文件
            Config.WORLD_DIR.mkdir(parents=True, exist_ok=True)
            
            if behavior_packs:
                with open(Config.WORLD_BEHAVIOR_PACKS_CONFIG, 'w') as f:
                    json.dump(behavior_packs, f, indent=2)
            
            if resource_packs:
                with open(Config.WORLD_RESOURCE_PACKS_CONFIG, 'w') as f:
                    json.dump(resource_packs, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error updating world config: {e}")
            return False
    
    @staticmethod
    def install_addon(pack_path: Path, curseforge_id: Optional[str] = None, 
                     curseforge_url: Optional[str] = None) -> Tuple[bool, str, Optional[Addon]]:
        """安装addon"""
        # 提取包信息
        pack_info = AddonManager.extract_pack_info(pack_path)
        if not pack_info:
            return False, "无法提取包信息", None
        
        # 检查是否已安装
        existing = Addon.query.filter_by(uuid=pack_info['uuid']).first()
        if existing:
            return False, f"Addon已存在: {existing.name}", existing
        
        # 部署addon
        success, message = AddonManager.deploy_addon(pack_path, pack_info)
        if not success:
            return False, message, None
        
        # 创建数据库记录
        addon = Addon(
            name=pack_info['name'],
            uuid=pack_info['uuid'],
            pack_type=pack_info['type'],
            version=pack_info['version'],
            curseforge_id=curseforge_id,
            curseforge_url=curseforge_url,
            local_path=message,
            enabled=False
        )
        
        db.session.add(addon)
        db.session.commit()
        
        return True, "安装成功", addon
    
    @staticmethod
    def enable_addon(addon_id: int) -> Tuple[bool, str]:
        """启用addon"""
        addon = Addon.query.get(addon_id)
        if not addon:
            return False, "Addon不存在"
        
        addon.enabled = True
        db.session.commit()
        
        # 更新世界配置
        AddonManager.update_world_config()
        
        return True, "已启用"
    
    @staticmethod
    def disable_addon(addon_id: int) -> Tuple[bool, str]:
        """禁用addon"""
        addon = Addon.query.get(addon_id)
        if not addon:
            return False, "Addon不存在"
        
        addon.enabled = False
        db.session.commit()
        
        # 更新世界配置
        AddonManager.update_world_config()
        
        return True, "已禁用"
    
    @staticmethod
    def delete_addon(addon_id: int) -> Tuple[bool, str]:
        """删除addon"""
        addon = Addon.query.get(addon_id)
        if not addon:
            return False, "Addon不存在"
        
        # 删除文件
        if Path(addon.local_path).exists():
            shutil.rmtree(addon.local_path, ignore_errors=True)
        
        # 删除数据库记录
        db.session.delete(addon)
        db.session.commit()
        
        # 更新世界配置
        AddonManager.update_world_config()
        
        return True, "已删除"

