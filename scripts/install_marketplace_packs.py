#!/usr/bin/env python3
"""
从 Marketplace 下载的 zip 文件安装脚本
处理 resource_packs.zip 和 behavior_packs.zip
"""

import sys
import zipfile
import json
import shutil
from pathlib import Path
import tempfile
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 尝试激活venv（如果存在）
venv_python = project_root / 'venv' / 'bin' / 'python3'
if venv_python.exists():
    # 如果使用venv，确保使用venv的Python
    if sys.executable != str(venv_python):
        print(f"⚠️  建议使用venv: {venv_python}")
        print(f"   当前使用: {sys.executable}")

from config import Config

def safe_extract_member(zip_ref, member, target_dir):
    """安全解压单个成员，防止目录穿越"""
    target_dir = Path(target_dir).resolve()
    
    # 清理member路径
    member_path = member.rstrip('/')
    
    # 规范化路径，移除 .. 和其他危险字符
    parts = []
    for part in member_path.split('/'):
        if part and part != '.' and part != '..':
            parts.append(part)
    
    if not parts:
        return None
    
    # 构建目标路径
    target_path = target_dir
    for part in parts:
        target_path = target_path / part
    
    # 验证目标路径在允许的目录内
    try:
        target_path = target_path.resolve()
        if not str(target_path).startswith(str(target_dir)):
            print(f"   ⚠️  跳过不安全的路径: {member}")
            return None
    except Exception as e:
        print(f"   ⚠️  路径验证失败 {member}: {e}")
        return None
    
    return target_path

def extract_and_install_packs(zip_path: Path, pack_type: str):
    """从zip文件中提取并安装包"""
    if not zip_path.exists():
        print(f"❌ 文件不存在: {zip_path}")
        return False, []
    
    print(f"\n{'='*70}")
    print(f"处理 {pack_type}: {zip_path.name}")
    print(f"{'='*70}\n")
    
    installed_packs = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 安全解压zip文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            temp_path = Path(temp_dir)
            
            for member in zip_ref.namelist():
                # 跳过目录条目
                if member.endswith('/'):
                    continue
                
                try:
                    # 安全提取文件
                    target_file = safe_extract_member(zip_ref, member, temp_path)
                    if target_file is None:
                        continue
                    
                    # 确保父目录存在
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 读取并写入文件
                    data = zip_ref.read(member)
                    with open(target_file, 'wb') as f:
                        f.write(data)
                except Exception as e:
                    print(f"   ⚠️  提取文件失败 {member}: {e}")
                    continue
        
        # 确定目标目录
        if pack_type == 'resource':
            target_dir = Config.RESOURCE_PACKS_DIR
            config_file = Config.WORLD_RESOURCE_PACKS_CONFIG
        else:
            target_dir = Config.BEHAVIOR_PACKS_DIR
            config_file = Config.WORLD_BEHAVIOR_PACKS_CONFIG
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 查找所有包（可能是嵌套的zip文件或直接是目录）
        temp_path = Path(temp_dir)
        
        # 查找所有manifest.json文件
        manifest_files = list(temp_path.rglob('manifest.json'))
        
        if not manifest_files:
            print(f"⚠️  未找到任何 manifest.json 文件")
            # 检查是否有嵌套的zip文件
            zip_files = list(temp_path.rglob('*.zip'))
            if zip_files:
                print(f"找到 {len(zip_files)} 个嵌套的zip文件，尝试解压...")
                for zip_file in zip_files:
                    try:
                        with zipfile.ZipFile(zip_file, 'r') as nested_zip:
                            nested_dir = zip_file.parent / zip_file.stem
                            nested_dir.mkdir(exist_ok=True)
                            nested_zip.extractall(nested_dir)
                        zip_file.unlink()  # 删除zip文件
                    except Exception as e:
                        print(f"⚠️  解压 {zip_file.name} 失败: {e}")
                
                # 重新查找manifest.json
                manifest_files = list(temp_path.rglob('manifest.json'))
        
        if not manifest_files:
            print(f"❌ 仍然未找到 manifest.json 文件")
            return False, []
        
        print(f"✅ 找到 {len(manifest_files)} 个包\n")
        
        # 处理每个包
        for manifest_file in manifest_files:
            pack_root = manifest_file.parent
            
            # 读取manifest.json
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                header = manifest.get('header', {})
                uuid = header.get('uuid', '')
                name = header.get('name', pack_root.name)
                version = header.get('version', [1, 0, 0])
                
                # 清理名称
                if name.startswith('pack.') or name.startswith('resourcePack.'):
                    name = pack_root.name
                
                print(f"📦 包: {name}")
                print(f"   UUID: {uuid}")
                print(f"   版本: {version}")
                
                # 创建目标目录
                safe_name = name.replace(' ', '_').replace('§', '').replace('[', '').replace(']', '')
                safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')
                if not safe_name:
                    safe_name = uuid[:8] if uuid else pack_root.name
                
                target_pack_dir = target_dir / safe_name
                
                # 如果已存在，备份
                if target_pack_dir.exists():
                    backup_dir = target_dir / f"{safe_name}.backup.{int(__import__('time').time())}"
                    shutil.move(str(target_pack_dir), str(backup_dir))
                    print(f"   ⚠️  已备份现有包到: {backup_dir.name}")
                
                # 复制包到目标目录
                shutil.copytree(str(pack_root), str(target_pack_dir))
                print(f"   ✅ 已安装到: {target_pack_dir}")
                
                installed_packs.append({
                    'uuid': uuid,
                    'name': name,
                    'version': version,
                    'path': str(target_pack_dir)
                })
                
            except Exception as e:
                print(f"   ❌ 处理包失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 更新世界配置
        if installed_packs:
            update_world_config(installed_packs, pack_type, config_file)
        
        return True, installed_packs
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False, []
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)

def update_world_config(installed_packs, pack_type, config_file):
    """更新世界配置文件"""
    print(f"\n📝 更新世界配置...")
    
    # 读取现有配置
    existing_config = []
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
        except Exception as e:
            print(f"   ⚠️  读取现有配置失败: {e}")
            existing_config = []
    
    # 添加新包（避免重复）
    existing_uuids = {pack.get('pack_id') for pack in existing_config}
        
    for pack in installed_packs:
        uuid = pack['uuid']
        if uuid and uuid not in existing_uuids:
            existing_config.append({
                'pack_id': uuid,
                'version': pack['version'] if isinstance(pack['version'], list) else [1, 0, 0]
            })
            existing_uuids.add(uuid)
            print(f"   ✅ 已添加 {pack['name']} 到配置")
        else:
            print(f"   ⚠️  {pack['name']} 已在配置中，跳过")
    
    # 写入配置
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(existing_config, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 配置已保存到: {config_file}")

def main():
    if len(sys.argv) < 3:
        print("用法: python install_marketplace_packs.py <resource_packs.zip> <behavior_packs.zip>")
        print("\n示例:")
        print("  python install_marketplace_packs.py resource_packs.zip behavior_packs.zip")
        sys.exit(1)
    
    resource_zip = Path(sys.argv[1])
    behavior_zip = Path(sys.argv[2])
    
    print("="*70)
    print("Marketplace 包安装工具")
    print("="*70)
    
    # 安装资源包
    if resource_zip.exists():
        success, packs = extract_and_install_packs(resource_zip, 'resource')
        if success:
            print(f"\n✅ 成功安装 {len(packs)} 个资源包")
        else:
            print(f"\n❌ 资源包安装失败")
    else:
        print(f"\n⚠️  资源包文件不存在: {resource_zip}")
    
    # 安装行为包
    if behavior_zip.exists():
        success, packs = extract_and_install_packs(behavior_zip, 'behavior')
        if success:
            print(f"\n✅ 成功安装 {len(packs)} 个行为包")
        else:
            print(f"\n❌ 行为包安装失败")
    else:
        print(f"\n⚠️  行为包文件不存在: {behavior_zip}")
    
    print("\n" + "="*70)
    print("安装完成！")
    print("="*70)
    print("\n下一步:")
    print("1. 检查安装的包是否正确")
    print("2. 在 Web 界面扫描已安装的包")
    print("3. 启用需要的包")
    print("4. 重启服务器")
    print("="*70)

if __name__ == '__main__':
    main()

