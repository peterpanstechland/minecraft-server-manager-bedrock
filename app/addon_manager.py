import json
import shutil
import zipfile
import tempfile
import re
import time
from pathlib import Path
from typing import Optional, Dict, Tuple, List
from app import db
from app.models import Addon
from app.security import safe_extract_zip
from config import Config

class AddonManager:
    """管理Bedrock服务器addon的安装、部署和配置"""
    
    @staticmethod
    def extract_pack_info(pack_path: Path) -> Optional[Dict]:
        """从addon文件中提取包信息（支持.mcpack, .mcaddon, .zip）"""
        if not pack_path.exists():
            print(f"Error: 文件不存在: {pack_path}")
            return None
        
        # 检查文件扩展名
        file_ext = pack_path.suffix.lower()
        is_mcaddon = file_ext == '.mcaddon'
        
        temp_dir = tempfile.mkdtemp()
        try:
            # 安全解压文件（防止Zip Slip攻击）
            try:
                success, message = safe_extract_zip(pack_path, Path(temp_dir))
                if not success:
                    print(f"Error: {message}")
                return None
                    
                # 列出文件用于调试
                file_list = list(Path(temp_dir).rglob('*'))
                print(f"Debug: 解压后包含 {len(file_list)} 个文件/目录")
            except Exception as e:
                error_msg = f"解压文件失败: {e}"
                print(f"Error: {error_msg}")
                import traceback
                traceback.print_exc()
                return None
            
            # .mcaddon文件可能包含behavior_packs和resource_packs子目录
            if is_mcaddon:
                behavior_packs_dir = Path(temp_dir) / 'behavior_packs'
                resource_packs_dir = Path(temp_dir) / 'resource_packs'
                
                # 如果存在子目录结构，优先处理行为包
                if behavior_packs_dir.exists():
                    # 查找行为包中的manifest.json
                    for manifest_file in behavior_packs_dir.rglob('manifest.json'):
                        manifest_path = manifest_file
                        pack_root = manifest_file.parent
                        break
                    else:
                        manifest_path = None
                        pack_root = None
                elif resource_packs_dir.exists():
                    # 如果只有资源包
                    for manifest_file in resource_packs_dir.rglob('manifest.json'):
                        manifest_path = manifest_file
                        pack_root = manifest_file.parent
                        break
                    else:
                        manifest_path = None
                        pack_root = None
                else:
                    # 如果没有子目录结构，按普通包处理
                    manifest_path = None
                    pack_root = None
            else:
                manifest_path = None
                pack_root = None
            
            # 如果还没找到，尝试标准查找方式
            if not manifest_path or not pack_root:
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
                # 详细列出目录结构用于调试
                print(f"Error: 找不到manifest.json文件")
                print(f"  搜索路径: {temp_dir}")
                print(f"  文件结构:")
                try:
                    def list_dir_tree(path: Path, prefix="", max_depth=3, current_depth=0):
                        """递归列出目录树"""
                        if current_depth >= max_depth:
                            return
                        try:
                            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
                            for i, item in enumerate(items):
                                is_last = i == len(items) - 1
                                current_prefix = "└── " if is_last else "├── "
                                print(f"{prefix}{current_prefix}{item.name}")
                                if item.is_dir():
                                    next_prefix = prefix + ("    " if is_last else "│   ")
                                    list_dir_tree(item, next_prefix, max_depth, current_depth + 1)
                        except PermissionError:
                            print(f"{prefix}  [权限不足]")
                    
                    list_dir_tree(Path(temp_dir))
                    
                    # 也尝试查找所有可能的 manifest 文件
                    all_manifests = list(Path(temp_dir).rglob('manifest.json'))
                    if all_manifests:
                        print(f"  找到 {len(all_manifests)} 个 manifest.json 文件:")
                        for mf in all_manifests:
                            print(f"    - {mf.relative_to(temp_dir)}")
                    else:
                        print(f"  未找到任何 manifest.json 文件")
                        
                except Exception as e:
                    print(f"  无法列出目录内容: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 返回更详细的错误信息
                return None
            
            # 读取manifest.json
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error: manifest.json格式错误: {e}")
                return None
            except Exception as e:
                print(f"Error: 读取manifest.json失败: {e}")
                return None
            
            # 提取信息
            header = manifest.get('header', {})
            if not header:
                print(f"Error: manifest.json缺少header字段")
                return None
            
            uuid = header.get('uuid', '')
            if not uuid:
                print(f"Error: manifest.json缺少uuid")
                return None
            
            name = header.get('name', pack_path.stem)
            
            # 如果name是翻译键（如"pack.name"），使用目录名或description
            if name and (name.startswith('pack.') or name.startswith('resourcePack.') or name == 'pack.name'):
                # 尝试从description获取
                description = header.get('description', '')
                if description and not description.startswith('pack.') and not description.startswith('resourcePack.'):
                    name = description
                else:
                    # 使用文件/目录名，清理名称
                    name = pack_path.stem.replace('_', ' ').replace('-', ' ').title()
            
            # 如果name仍然为空或无效，使用文件/目录名
            if not name or name.startswith('pack.') or name.startswith('resourcePack.'):
                name = pack_path.stem.replace('_', ' ').replace('-', ' ').title()
            
            version = header.get('version', [0, 0, 0])
            if isinstance(version, list):
                version_str = '.'.join(map(str, version))
            else:
                version_str = str(version)
            
            # 确定包类型 - 根据manifest中的modules类型判断
            pack_type = 'behavior'
            modules = manifest.get('modules', [])
            if modules:
                # 检查modules中的type字段
                # 资源包的常见类型: "resources", "client_data", "client_scripts"
                # 行为包的常见类型: "data", "script", "server_data", "server_scripts"
                for module in modules:
                    module_type = module.get('type', '').lower()
                    # 优先检查资源包类型（精确匹配）
                    if module_type in ['resources', 'client_data', 'client_scripts']:
                        pack_type = 'resource'
                        break
                    # 然后检查行为包类型（精确匹配）
                    elif module_type in ['data', 'script', 'server_data', 'server_scripts']:
                        pack_type = 'behavior'
                        break
                    # 兼容性检查：包含关键词
                    elif 'resource' in module_type:
                        pack_type = 'resource'
                        break
                    elif 'data' in module_type or 'script' in module_type:
                        pack_type = 'behavior'
                        break
            
            # 如果无法从modules判断，检查文件结构
            if pack_type == 'behavior':
                has_functions = (pack_root / 'functions').exists()
                has_scripts = (pack_root / 'scripts').exists()
                has_entities = (pack_root / 'entities').exists()
                has_blocks = (pack_root / 'blocks').exists()
                has_loot_tables = (pack_root / 'loot_tables').exists()
                has_advancements = (pack_root / 'advancements').exists()
                
                # 资源包的特征目录
                has_textures = (pack_root / 'textures').exists()
                has_ui = (pack_root / 'ui').exists()
                has_texts = (pack_root / 'texts').exists()
                has_sounds = (pack_root / 'sounds').exists()
                has_animations = (pack_root / 'animations').exists()
                has_attachables = (pack_root / 'attachables').exists()
                
                # 如果没有行为包特征，但有资源包特征，则判定为资源包
                if not (has_functions or has_scripts or has_entities or has_blocks or has_loot_tables or has_advancements):
                    if has_textures or has_ui or has_texts or has_sounds or has_animations or has_attachables:
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
            error_msg = f"提取包信息时发生错误: {e}"
            print(f"Error: {error_msg}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # 清理临时文件
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"Warning: 清理临时目录失败: {e}")
    
    @staticmethod
    def deploy_addon(pack_path: Path, pack_info: Dict) -> Tuple[bool, str]:
        """部署addon到服务器目录（支持.mcaddon格式，可能包含多个包）"""
        try:
            file_ext = pack_path.suffix.lower()
            is_mcaddon = file_ext == '.mcaddon'
            
            # 确保目标目录存在
            if pack_info['type'] == 'behavior':
                target_dir = Config.BEHAVIOR_PACKS_DIR
            else:
                target_dir = Config.RESOURCE_PACKS_DIR
            
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 清理包名用于目录名
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', pack_info['name'])
            safe_name = re.sub(r'_+', '_', safe_name)
            safe_name = safe_name.strip('_')
            
            # 如果名称为空，使用UUID的前8位
            if not safe_name:
                safe_name = pack_info['uuid'][:8] if pack_info.get('uuid') else 'addon'
            
            target_pack_dir = target_dir / safe_name
            
            # 如果目录已存在，备份
            if target_pack_dir.exists():
                backup_dir = target_dir / f"{safe_name}.backup.{int(time.time())}"
                try:
                    shutil.move(str(target_pack_dir), str(backup_dir))
                    print(f"已备份现有addon到: {backup_dir}")
                except Exception as e:
                    print(f"警告: 备份失败: {e}")
                    # 如果备份失败，删除旧目录
                    shutil.rmtree(str(target_pack_dir), ignore_errors=True)
            
            # 安全解压并复制到目标目录
            temp_dir = tempfile.mkdtemp()
            try:
                # 使用安全解压函数
                success, message = safe_extract_zip(pack_path, Path(temp_dir))
                if not success:
                    return False, f"解压失败: {message}"
                
                # .mcaddon文件可能包含behavior_packs和resource_packs子目录
                if is_mcaddon:
                    behavior_packs_dir = Path(temp_dir) / 'behavior_packs'
                    resource_packs_dir = Path(temp_dir) / 'resource_packs'
                    
                    # 根据包类型选择对应的子目录
                    if pack_info['type'] == 'behavior' and behavior_packs_dir.exists():
                        # 查找行为包目录中的第一个包
                        behavior_packs = [d for d in behavior_packs_dir.iterdir() if d.is_dir()]
                        if behavior_packs:
                            pack_root = behavior_packs[0]  # 使用第一个行为包
                        else:
                            return False, ".mcaddon文件中未找到行为包"
                    elif pack_info['type'] == 'resource' and resource_packs_dir.exists():
                        # 查找资源包目录中的第一个包
                        resource_packs = [d for d in resource_packs_dir.iterdir() if d.is_dir()]
                        if resource_packs:
                            pack_root = resource_packs[0]  # 使用第一个资源包
                        else:
                            return False, ".mcaddon文件中未找到资源包"
                    else:
                        # 如果没有子目录结构，按普通包处理
                        pack_root = None
                else:
                    pack_root = None
                
                # 如果还没找到，尝试标准查找方式
                if not pack_root:
                    root_manifest = Path(temp_dir) / 'manifest.json'
                    if root_manifest.exists():
                        pack_root = Path(temp_dir)
                    else:
                        for manifest_file in Path(temp_dir).rglob('manifest.json'):
                            pack_root = manifest_file.parent
                            break
                
                if not pack_root:
                    return False, "找不到manifest.json或包目录"
                
                # 复制到目标目录
                shutil.copytree(str(pack_root), str(target_pack_dir))
                
                print(f"Addon已部署到: {target_pack_dir}")
                return True, str(target_pack_dir)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            error_msg = f"部署失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    @staticmethod
    def update_world_config():
        """更新世界配置文件以启用所有已启用的addon"""
        try:
            # 获取所有启用的addon
            enabled_addons = Addon.query.filter_by(enabled=True).all()
            
            behavior_packs = []
            resource_packs = []
            
            for addon in enabled_addons:
                # 从manifest.json读取真实版本号
                version = [1, 0, 0]  # 默认版本
                manifest_path = Path(addon.local_path) / 'manifest.json'
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                            manifest = json.load(f)
                            header = manifest.get('header', {})
                            version_raw = header.get('version', [1, 0, 0])
                            if isinstance(version_raw, list):
                                version = version_raw
                            elif isinstance(version_raw, str):
                                # 尝试解析版本字符串 "1.2.3" -> [1, 2, 3]
                                try:
                                    version = [int(x) for x in version_raw.split('.')]
                                except:
                                    version = [1, 0, 0]
                    except Exception as e:
                        print(f"Warning: 无法读取 {addon.name} 的版本号: {e}")
                
                pack_config = {
                    "pack_id": addon.uuid,
                    "version": version
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
        """安装addon（支持.mcpack, .mcaddon, .zip格式）"""
        try:
            # 验证文件
            if not pack_path.exists():
                return False, f"文件不存在: {pack_path}", None
            
            file_ext = pack_path.suffix.lower()
            if file_ext == '.mcaddon':
                # .mcaddon文件可能包含多个包，需要特殊处理
                return AddonManager._install_mcaddon(pack_path, curseforge_id, curseforge_url)
            
            # 提取包信息
            pack_info = AddonManager.extract_pack_info(pack_path)
            if not pack_info:
                # 尝试提供更详细的错误信息
                error_detail = "无法提取包信息。可能的原因：\n"
                error_detail += "1. 文件不是有效的 Bedrock addon 包\n"
                error_detail += "2. ZIP 文件损坏或格式不正确\n"
                error_detail += "3. manifest.json 文件缺失或位置不正确\n"
                error_detail += "4. manifest.json 格式错误\n"
                error_detail += "请检查服务器日志获取详细错误信息"
                return False, error_detail, None
            
            # 验证必需字段
            if not pack_info.get('uuid'):
                return False, "无法从manifest.json中提取UUID", None
            
            if not pack_info.get('name'):
                return False, "无法从manifest.json中提取名称", None
            
            # 检查是否已安装
            existing = Addon.query.filter_by(uuid=pack_info['uuid']).first()
            if existing:
                return False, f"Addon已存在: {existing.name} (UUID: {pack_info['uuid']})", existing
            
            # 部署addon
            success, message = AddonManager.deploy_addon(pack_path, pack_info)
            if not success:
                return False, message, None
            
            # 创建数据库记录
            try:
                addon = Addon(
                    name=pack_info['name'],
                    uuid=pack_info['uuid'],
                    pack_type=pack_info['type'],
                    version=pack_info.get('version', '1.0.0'),
                    curseforge_id=curseforge_id,
                    curseforge_url=curseforge_url,
                    local_path=message,
                    enabled=False
                )
                
                db.session.add(addon)
                db.session.commit()
                
                return True, f"安装成功: {pack_info['name']}", addon
            except Exception as e:
                db.session.rollback()
                # 如果数据库操作失败，清理已部署的文件
                if Path(message).exists():
                    shutil.rmtree(message, ignore_errors=True)
                return False, f"数据库操作失败: {str(e)}", None
        except Exception as e:
            error_msg = f"安装失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False, error_msg, None
    
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
    
    @staticmethod
    def scan_existing_addons() -> Tuple[int, List[str]]:
        """扫描服务器目录中已存在的addon并添加到数据库"""
        imported_count = 0
        errors = []
        
        # 扫描行为包
        if Config.BEHAVIOR_PACKS_DIR.exists():
            for bp_dir in Config.BEHAVIOR_PACKS_DIR.iterdir():
                if not bp_dir.is_dir() or bp_dir.name.startswith('.') or 'backup' in bp_dir.name.lower():
                    continue
                
                manifest_path = bp_dir / 'manifest.json'
                if manifest_path.exists():
                    try:
                        # 读取manifest.json（处理可能的格式问题）
                        with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            # 尝试修复常见的JSON格式问题
                            try:
                                manifest = json.loads(content)
                            except json.JSONDecodeError:
                                # 如果标准解析失败，尝试更宽松的解析
                                import re
                                # 移除注释（如果存在）
                                content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
                                manifest = json.loads(content)
                        
                        header = manifest.get('header', {})
                        uuid = header.get('uuid', '')
                        name = header.get('name', bp_dir.name)
                        
                        # 如果name是翻译键（如"pack.name"），使用目录名或description
                        if name and (name.startswith('pack.') or name.startswith('resourcePack.') or name == 'pack.name'):
                            # 尝试从description获取
                            description = header.get('description', '')
                            if description and not description.startswith('pack.') and not description.startswith('resourcePack.'):
                                name = description
                            else:
                                # 使用目录名，清理名称
                                name = bp_dir.name.replace('_', ' ').replace('-', ' ').title()
                        
                        # 如果name仍然为空或无效，使用目录名
                        if not name or name.startswith('pack.') or name.startswith('resourcePack.'):
                            name = bp_dir.name.replace('_', ' ').replace('-', ' ').title()
                        
                        version = header.get('version', [0, 0, 0])
                        version_str = '.'.join(map(str, version)) if isinstance(version, list) else str(version)
                        
                        if uuid:
                            # 检查是否已存在
                            existing = Addon.query.filter_by(uuid=uuid).first()
                            if not existing:
                                addon = Addon(
                                    name=name,
                                    uuid=uuid,
                                    pack_type='behavior',
                                    version=version_str,
                                    local_path=str(bp_dir),
                                    enabled=False  # 默认禁用，需要手动启用
                                )
                                db.session.add(addon)
                                imported_count += 1
                    except Exception as e:
                        errors.append(f"扫描 {bp_dir.name} 失败: {str(e)}")
        
        # 扫描资源包
        if Config.RESOURCE_PACKS_DIR.exists():
            for rp_dir in Config.RESOURCE_PACKS_DIR.iterdir():
                if not rp_dir.is_dir() or rp_dir.name.startswith('.') or 'backup' in rp_dir.name.lower():
                    continue
                
                manifest_path = rp_dir / 'manifest.json'
                if manifest_path.exists():
                    try:
                        # 读取manifest.json（处理可能的格式问题）
                        with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            # 尝试修复常见的JSON格式问题
                            try:
                                manifest = json.loads(content)
                            except json.JSONDecodeError:
                                # 如果标准解析失败，尝试更宽松的解析
                                import re
                                # 移除注释（如果存在）
                                content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
                                manifest = json.loads(content)
                        
                        header = manifest.get('header', {})
                        uuid = header.get('uuid', '')
                        name = header.get('name', rp_dir.name)
                        
                        # 如果name是翻译键（如"pack.name"），使用目录名或description
                        if name and (name.startswith('pack.') or name.startswith('resourcePack.') or name == 'pack.name'):
                            # 尝试从description获取
                            description = header.get('description', '')
                            if description and not description.startswith('pack.') and not description.startswith('resourcePack.'):
                                name = description
                            else:
                                # 使用目录名，清理名称
                                name = rp_dir.name.replace('_', ' ').replace('-', ' ').title()
                        
                        # 如果name仍然为空或无效，使用目录名
                        if not name or name.startswith('pack.') or name.startswith('resourcePack.'):
                            name = rp_dir.name.replace('_', ' ').replace('-', ' ').title()
                        
                        version = header.get('version', [0, 0, 0])
                        version_str = '.'.join(map(str, version)) if isinstance(version, list) else str(version)
                        
                        if uuid:
                            # 检查是否已存在
                            existing = Addon.query.filter_by(uuid=uuid).first()
                            if not existing:
                                addon = Addon(
                                    name=name,
                                    uuid=uuid,
                                    pack_type='resource',
                                    version=version_str,
                                    local_path=str(rp_dir),
                                    enabled=False  # 默认禁用，需要手动启用
                                )
                                db.session.add(addon)
                                imported_count += 1
                    except Exception as e:
                        errors.append(f"扫描 {rp_dir.name} 失败: {str(e)}")
        
        # 提交数据库更改
        if imported_count > 0:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                errors.append(f"数据库提交失败: {str(e)}")
        
        return imported_count, errors
    
    @staticmethod
    def _install_mcaddon(pack_path: Path, curseforge_id: Optional[str] = None, 
                         curseforge_url: Optional[str] = None) -> Tuple[bool, str, Optional[Addon]]:
        """安装.mcaddon文件（可能包含行为包和资源包）"""
        temp_dir = tempfile.mkdtemp()
        installed_addons = []
        errors = []
        
        try:
            # 安全解压.mcaddon文件
            success, message = safe_extract_zip(pack_path, Path(temp_dir))
            if not success:
                return False, f"解压.mcaddon失败: {message}", None
            
            behavior_packs_dir = Path(temp_dir) / 'behavior_packs'
            resource_packs_dir = Path(temp_dir) / 'resource_packs'
            
            # 安装行为包
            if behavior_packs_dir.exists():
                for bp_dir in behavior_packs_dir.iterdir():
                    if bp_dir.is_dir():
                        manifest_path = bp_dir / 'manifest.json'
                        if manifest_path.exists():
                            # 创建临时zip文件
                            temp_bp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                            temp_bp_path = Path(temp_bp_zip.name)
                            temp_bp_zip.close()
                            
                            # 将行为包打包成zip
                            with zipfile.ZipFile(temp_bp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                                for file in bp_dir.rglob('*'):
                                    if file.is_file():
                                        zipf.write(file, file.relative_to(bp_dir))
                            
                            # 安装行为包（递归调用，但跳过.mcaddon检查）
                            success, message, addon = AddonManager._install_single_pack(
                                temp_bp_path, curseforge_id, curseforge_url
                            )
                            if success and addon:
                                installed_addons.append(addon)
                            else:
                                errors.append(f"行为包安装失败: {message}")
                            
                            # 清理临时文件
                            temp_bp_path.unlink(missing_ok=True)
            
            # 安装资源包
            if resource_packs_dir.exists():
                for rp_dir in resource_packs_dir.iterdir():
                    if rp_dir.is_dir():
                        manifest_path = rp_dir / 'manifest.json'
                        if manifest_path.exists():
                            # 创建临时zip文件
                            temp_rp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                            temp_rp_path = Path(temp_rp_zip.name)
                            temp_rp_zip.close()
                            
                            # 将资源包打包成zip
                            with zipfile.ZipFile(temp_rp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                                for file in rp_dir.rglob('*'):
                                    if file.is_file():
                                        zipf.write(file, file.relative_to(rp_dir))
                            
                            # 安装资源包
                            success, message, addon = AddonManager._install_single_pack(
                                temp_rp_path, curseforge_id, curseforge_url
                            )
                            if success and addon:
                                installed_addons.append(addon)
                            else:
                                errors.append(f"资源包安装失败: {message}")
                            
                            # 清理临时文件
                            temp_rp_path.unlink(missing_ok=True)
            
            # 如果没有找到任何包，尝试按普通包处理
            if not installed_addons and not errors:
                # 查找根目录的manifest.json
                root_manifest = Path(temp_dir) / 'manifest.json'
                if root_manifest.exists():
                    # 按普通包处理
                    success, message, addon = AddonManager._install_single_pack(
                        pack_path, curseforge_id, curseforge_url
                    )
                    if success and addon:
                        return True, f"安装成功: {addon.name}", addon
                    else:
                        return False, message, None
                else:
                    return False, ".mcaddon文件中未找到有效的包", None
            
            # 返回结果
            if installed_addons:
                names = [a.name for a in installed_addons]
                message = f"成功安装 {len(installed_addons)} 个包: {', '.join(names)}"
                if errors:
                    message += f"\n警告: {len(errors)} 个包安装失败"
                return True, message, installed_addons[0]  # 返回第一个安装的包
            else:
                return False, f"安装失败: {'; '.join(errors)}", None
                
        except Exception as e:
            error_msg = f"安装.mcaddon文件失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False, error_msg, None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @staticmethod
    def _install_single_pack(pack_path: Path, curseforge_id: Optional[str] = None, 
                             curseforge_url: Optional[str] = None) -> Tuple[bool, str, Optional[Addon]]:
        """安装单个包（内部方法，不检查.mcaddon格式）"""
        # 提取包信息
        pack_info = AddonManager.extract_pack_info(pack_path)
        if not pack_info:
            return False, "无法提取包信息", None
        
        # 验证必需字段
        if not pack_info.get('uuid'):
            return False, "无法从manifest.json中提取UUID", None
        
        if not pack_info.get('name'):
            return False, "无法从manifest.json中提取名称", None
        
        # 检查是否已安装
        existing = Addon.query.filter_by(uuid=pack_info['uuid']).first()
        if existing:
            return False, f"Addon已存在: {existing.name}", existing
        
        # 部署addon
        success, message = AddonManager.deploy_addon(pack_path, pack_info)
        if not success:
            return False, message, None
        
        # 创建数据库记录
        try:
            addon = Addon(
                name=pack_info['name'],
                uuid=pack_info['uuid'],
                pack_type=pack_info['type'],
                version=pack_info.get('version', '1.0.0'),
                curseforge_id=curseforge_id,
                curseforge_url=curseforge_url,
                local_path=message,
                enabled=False
            )
            
            db.session.add(addon)
            db.session.commit()
            
            return True, f"安装成功: {pack_info['name']}", addon
        except Exception as e:
            db.session.rollback()
            # 如果数据库操作失败，清理已部署的文件
            if Path(message).exists():
                shutil.rmtree(message, ignore_errors=True)
            return False, f"数据库操作失败: {str(e)}", None
    
    @staticmethod
    def cleanup_orphaned_files(search_paths: Optional[List[Path]] = None, 
                               min_age_days: int = 7) -> Tuple[int, List[Path]]:
        """
        清理孤立的addon文件（不在数据库中的文件）
        
        Args:
            search_paths: 要搜索的路径列表，如果为None则使用默认路径（用户主目录）
            min_age_days: 文件最小存在天数，只有超过这个天数的文件才会被清理（默认7天）
        
        Returns:
            (清理的文件数量, 清理的文件路径列表)
        """
        cleaned_files = []
        
        # 获取数据库中所有addon的路径
        all_addons = Addon.query.all()
        db_paths = set()
        for addon in all_addons:
            if addon.local_path:
                db_paths.add(Path(addon.local_path).resolve())
        
        # 合法的目录（这些目录中的文件不应该被清理）
        protected_dirs = {
            Config.UPLOAD_FOLDER.resolve(),
            Config.BEHAVIOR_PACKS_DIR.resolve(),
            Config.RESOURCE_PACKS_DIR.resolve(),
            Config.BASE_DIR.resolve(),
        }
        
        # 默认搜索路径：用户主目录
        if search_paths is None:
            from os.path import expanduser
            search_paths = [Path(expanduser("~"))]
        
        # 支持的addon文件扩展名
        addon_extensions = {'.zip', '.mcpack', '.mcaddon'}
        
        # 计算最小时间戳（当前时间 - min_age_days）
        import time
        min_age_seconds = min_age_days * 24 * 60 * 60
        current_time = time.time()
        min_mtime = current_time - min_age_seconds
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            # 检查路径是否在受保护目录中
            search_path_resolved = search_path.resolve()
            is_protected = any(
                str(search_path_resolved).startswith(str(protected_dir))
                for protected_dir in protected_dirs
            )
            
            if is_protected:
                continue
            
            # 搜索addon文件
            try:
                for file_path in search_path.rglob('*'):
                    if not file_path.is_file():
                        continue
                    
                    # 检查文件扩展名
                    if file_path.suffix.lower() not in addon_extensions:
                        continue
                    
                    # 检查文件是否在数据库中
                    file_path_resolved = file_path.resolve()
                    if file_path_resolved in db_paths:
                        continue
                    
                    # 检查文件是否在受保护目录中
                    is_in_protected = any(
                        str(file_path_resolved).startswith(str(protected_dir))
                        for protected_dir in protected_dirs
                    )
                    
                    if is_in_protected:
                        continue
                    
                    # 检查文件修改时间，只清理超过min_age_days的文件
                    try:
                        file_mtime = file_path.stat().st_mtime
                        if file_mtime > min_mtime:
                            # 文件太新，跳过
                            continue
                    except (OSError, AttributeError):
                        # 如果无法获取文件时间，跳过
                        continue
                    
                    # 确认是孤立文件，删除
                    try:
                        file_path.unlink()
                        cleaned_files.append(file_path_resolved)
                    except Exception as e:
                        print(f"警告: 无法删除文件 {file_path}: {e}")
            except Exception as e:
                print(f"警告: 搜索路径 {search_path} 时出错: {e}")
        
        return len(cleaned_files), cleaned_files
    
    @staticmethod
    def check_manifest_compatibility(manifest_path: Path) -> Tuple[bool, Dict]:
        """
        检查资源包 manifest 的兼容性
        
        Args:
            manifest_path: manifest.json 的路径
            
        Returns:
            (is_compatible, results_dict)
            results_dict 包含:
            - issues: 问题列表
            - warnings: 警告列表
            - info: 信息列表
            - uuid: header.uuid（用于 world_resource_packs.json）
            - version: header.version（用于 world_resource_packs.json）
            - config_snippet: world_resource_packs.json 配置片段
        """
        issues = []
        warnings = []
        info = []
        
        try:
            # 加载 manifest
            if not manifest_path.exists():
                return False, {
                    'issues': [f"manifest.json 不存在: {manifest_path}"],
                    'warnings': [],
                    'info': [],
                    'uuid': None,
                    'version': None,
                    'config_snippet': None,
                }
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            info.append("✅ 成功加载 manifest.json")
            
            # 检查基本结构
            if 'header' not in manifest:
                issues.append("❌ 缺少 header 字段")
                return False, {'issues': issues, 'warnings': warnings, 'info': info, 'uuid': None, 'version': None, 'config_snippet': None}
            
            if 'modules' not in manifest:
                issues.append("❌ 缺少 modules 字段")
                return False, {'issues': issues, 'warnings': warnings, 'info': info, 'uuid': None, 'version': None, 'config_snippet': None}
            
            header = manifest['header']
            
            # 检查必需字段
            uuid = header.get('uuid', '')
            name = header.get('name', '')
            version = header.get('version', [1, 0, 0])
            
            if not uuid:
                issues.append("❌ header 缺少 uuid")
            else:
                # 验证 UUID 格式
                uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                if not re.match(uuid_pattern, uuid, re.IGNORECASE):
                    issues.append(f"❌ UUID 格式无效: {uuid}")
                else:
                    info.append(f"✅ UUID: {uuid}")
            
            if not name:
                warnings.append("⚠️  header 缺少 name（将使用目录名）")
            else:
                info.append(f"✅ 名称: {name}")
            
            # 检查版本格式
            if isinstance(version, list) and len(version) >= 3:
                info.append(f"✅ 版本: {version}")
            else:
                warnings.append(f"⚠️  版本格式可能有问题: {version}")
                if isinstance(version, list):
                    version = version + [0] * (3 - len(version))
                else:
                    version = [1, 0, 0]
            
            # 检查包类型（必须是资源包）
            modules = manifest.get('modules', [])
            resource_types = ['resources', 'client_data', 'client_scripts']
            behavior_types = ['data', 'script', 'server_data', 'server_scripts']
            
            is_resource = False
            is_behavior = False
            
            for module in modules:
                module_type = module.get('type', '').lower()
                if module_type in resource_types:
                    is_resource = True
                elif module_type in behavior_types:
                    is_behavior = True
            
            if is_behavior:
                issues.append("❌ 这是行为包，不是资源包！New Glowing Ores 应该是资源包")
            elif is_resource:
                info.append("✅ 确认为资源包类型")
            else:
                warnings.append("⚠️  无法从 modules 确定包类型")
            
            # 检查最小引擎版本
            min_engine = header.get('min_engine_version', [1, 0, 0])
            if isinstance(min_engine, list) and len(min_engine) >= 2:
                major, minor = min_engine[0], min_engine[1]
                info.append(f"✅ 最小引擎版本: {major}.{minor}.x")
                if major < 1 or (major == 1 and minor < 16):
                    warnings.append(f"⚠️  最小引擎版本较低 ({major}.{minor}.x)")
            
            # 检查 manifest 位置（应该在 resource_packs/PackName/manifest.json）
            parts = manifest_path.parts
            if 'resource_packs' in parts:
                rp_index = parts.index('resource_packs')
                if len(parts) - rp_index != 3:  # resource_packs/PackName/manifest.json
                    issues.append(f"❌ manifest.json 位置错误！应该在 resource_packs/PackName/manifest.json")
                    issues.append(f"   当前路径: {manifest_path}")
            
            # 检查服务器配置
            server_props = Config.BEDROCK_SERVER_DIR / 'server.properties'
            if server_props.exists():
                try:
                    with open(server_props, 'r') as f:
                        content = f.read()
                        if 'texturepack-required=true' not in content:
                            warnings.append("⚠️  server.properties: texturepack-required=false（建议改为 true）")
                        else:
                            info.append("✅ server.properties: texturepack-required=true")
                except Exception:
                    pass
            
            # 检查 world_resource_packs.json
            world_rp_config = Config.WORLD_RESOURCE_PACKS_CONFIG
            if world_rp_config.exists():
                try:
                    with open(world_rp_config, 'r') as f:
                        existing_config = json.load(f)
                        if uuid:
                            for pack in existing_config:
                                if pack.get('pack_id') == uuid:
                                    info.append("✅ 此资源包已在 world_resource_packs.json 中配置")
                                    break
                            else:
                                warnings.append("⚠️  此资源包尚未添加到 world_resource_packs.json")
                except Exception:
                    pass
            else:
                warnings.append(f"⚠️  world_resource_packs.json 不存在")
            
            # 生成配置片段
            config_snippet = None
            if uuid and version:
                config = {
                    "pack_id": uuid,
                    "version": version[:3] if isinstance(version, list) else [1, 0, 0]
                }
                config_snippet = json.dumps([config], indent=2, ensure_ascii=False)
            
            is_compatible = len(issues) == 0
            
            return is_compatible, {
                'issues': issues,
                'warnings': warnings,
                'info': info,
                'uuid': uuid,
                'version': version[:3] if isinstance(version, list) and len(version) >= 3 else [1, 0, 0],
                'config_snippet': config_snippet,
            }
            
        except json.JSONDecodeError as e:
            return False, {
                'issues': [f"manifest.json 格式错误: {e}"],
                'warnings': warnings,
                'info': info,
                'uuid': None,
                'version': None,
                'config_snippet': None,
            }
        except Exception as e:
            return False, {
                'issues': [f"检查失败: {e}"],
                'warnings': warnings,
                'info': info,
                'uuid': None,
                'version': None,
                'config_snippet': None,
            }

