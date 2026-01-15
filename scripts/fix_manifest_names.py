#!/usr/bin/env python3
"""
修复 manifest.json 中的名称问题
检查并修复所有包的 manifest.json 文件
"""

import sys
import json
import re
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

def clean_name(name):
    """清理包名"""
    if not name:
        return None
    
    # 移除 Minecraft 颜色代码
    name = re.sub(r'§[0-9a-fk-or]', '', name, flags=re.IGNORECASE)
    # 移除特殊字符
    name = re.sub(r'[<>:"/\\|?*\[\]()]', '', name)
    # 替换多个空格为单个空格
    name = re.sub(r'\s+', ' ', name)
    # 移除首尾空格
    name = name.strip()
    
    return name if name else None

def fix_manifest(manifest_path: Path):
    """修复单个 manifest.json 文件"""
    try:
        # 读取文件
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        header = manifest.get('header', {})
        if not header:
            print(f"   ⚠️  缺少 header 字段")
            return False
        
        original_name = header.get('name', '')
        description = header.get('description', '')
        
        # 检查名称是否有问题
        needs_fix = False
        issues = []
        
        # 检查是否是翻译键
        if original_name.startswith('pack.') or original_name.startswith('resourcePack.') or original_name == 'pack.name':
            issues.append(f"名称是翻译键: {original_name}")
            needs_fix = True
        
        # 检查是否有颜色代码
        if '§' in original_name:
            issues.append(f"包含颜色代码")
            needs_fix = True
        
        # 检查是否为空
        if not original_name or original_name.strip() == '':
            issues.append("名称为空")
            needs_fix = True
        
        if not needs_fix:
            return True
        
        print(f"\n📦 修复: {manifest_path.parent.name}")
        for issue in issues:
            print(f"   ⚠️  {issue}")
        
        # 尝试修复
        fixed_name = None
        
        # 方法1: 使用 description
        if description and not description.startswith('pack.') and not description.startswith('resourcePack.'):
            fixed_name = clean_name(description)
            print(f"   ✅ 使用 description: {fixed_name}")
        
        # 方法2: 使用目录名
        if not fixed_name:
            dir_name = manifest_path.parent.name
            # 移除可能的编码问题（如末尾的=）
            dir_name = dir_name.rstrip('=')
            fixed_name = clean_name(dir_name)
            print(f"   ✅ 使用目录名: {fixed_name}")
        
        # 方法3: 使用默认名称
        if not fixed_name:
            if 'resource' in str(manifest_path).lower():
                fixed_name = "Resource Pack"
            else:
                fixed_name = "Behavior Pack"
            print(f"   ⚠️  使用默认名称: {fixed_name}")
        
        # 更新 manifest
        header['name'] = fixed_name
        
        # 备份原文件
        backup_path = manifest_path.with_suffix('.json.backup')
        shutil.copy(manifest_path, backup_path)
        
        # 写入修复后的文件
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ 已修复: {original_name} → {fixed_name}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def scan_and_fix_packs():
    """扫描并修复所有包的 manifest.json"""
    print("="*70)
    print("修复 manifest.json 名称问题")
    print("="*70)
    
    fixed_count = 0
    error_count = 0
    
    # 扫描资源包
    print("\n📦 扫描资源包...")
    rp_dir = Config.RESOURCE_PACKS_DIR
    if rp_dir.exists():
        for pack_dir in rp_dir.iterdir():
            if not pack_dir.is_dir():
                continue
            
            manifest_path = pack_dir / 'manifest.json'
            if manifest_path.exists():
                if fix_manifest(manifest_path):
                    fixed_count += 1
                else:
                    error_count += 1
    
    # 扫描行为包
    print("\n📦 扫描行为包...")
    bp_dir = Config.BEHAVIOR_PACKS_DIR
    if bp_dir.exists():
        for pack_dir in bp_dir.iterdir():
            if not pack_dir.is_dir():
                continue
            
            manifest_path = pack_dir / 'manifest.json'
            if manifest_path.exists():
                if fix_manifest(manifest_path):
                    fixed_count += 1
                else:
                    error_count += 1
    
    print("\n" + "="*70)
    print(f"完成！修复了 {fixed_count} 个包，{error_count} 个错误")
    print("="*70)
    
    if fixed_count > 0:
        print("\n下一步:")
        print("1. 重新尝试重启服务器")
        print("2. 如果还有问题，检查服务器日志")
    
    return fixed_count > 0

def main():
    success = scan_and_fix_packs()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

