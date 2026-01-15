#!/usr/bin/env python3
"""
验证世界配置文件格式
检查 world_resource_packs.json 和 world_behavior_packs.json
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

def validate_config(config_path: Path, config_type: str):
    """验证配置文件"""
    print(f"\n{'='*70}")
    print(f"检查 {config_type}: {config_path.name}")
    print(f"{'='*70}\n")
    
    if not config_path.exists():
        print(f"⚠️  文件不存在: {config_path}")
        return False, []
    
    issues = []
    packs = []
    
    try:
        # 读取文件
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证JSON格式
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON格式错误:")
            print(f"   行 {e.lineno}, 列 {e.colno}")
            print(f"   错误: {e.msg}")
            print(f"\n   问题内容:")
            lines = content.split('\n')
            error_line = lines[e.lineno - 1] if e.lineno <= len(lines) else ""
            print(f"   {error_line}")
            if e.colno:
                print(f"   {' ' * (e.colno - 1)}^")
            return False, []
        
        if not isinstance(data, list):
            print(f"❌ 配置应该是数组格式，当前是: {type(data).__name__}")
            return False, []
        
        print(f"✅ JSON格式正确")
        print(f"✅ 包含 {len(data)} 个包\n")
        
        # 验证每个包
        for i, pack in enumerate(data, 1):
            pack_issues = []
            
            # 检查必需字段
            if 'pack_id' not in pack:
                pack_issues.append("缺少 pack_id 字段")
            else:
                uuid = pack['pack_id']
                # 验证UUID格式
                import re
                uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                if not re.match(uuid_pattern, uuid, re.IGNORECASE):
                    pack_issues.append(f"UUID格式无效: {uuid}")
            
            if 'version' not in pack:
                pack_issues.append("缺少 version 字段")
            else:
                version = pack['version']
                if not isinstance(version, list):
                    pack_issues.append(f"version 应该是数组，当前是: {type(version).__name__}")
                elif len(version) < 3:
                    pack_issues.append(f"version 数组长度不足（应该是3个元素）: {version}")
            
            if pack_issues:
                print(f"❌ 包 [{i}]:")
                for issue in pack_issues:
                    print(f"   - {issue}")
                issues.extend(pack_issues)
            else:
                print(f"✅ 包 [{i}]: UUID={pack.get('pack_id', 'N/A')[:8]}..., version={pack.get('version', 'N/A')}")
            
            packs.append(pack)
        
        if issues:
            print(f"\n❌ 发现 {len(issues)} 个问题")
            return False, issues
        else:
            print(f"\n✅ 所有包配置正确！")
            return True, []
            
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]

def fix_config(config_path: Path, config_type: str):
    """修复配置文件"""
    print(f"\n🔧 尝试修复 {config_path.name}...")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试修复常见的JSON问题
        # 移除尾随逗号
        import re
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        # 尝试解析
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            print("   ❌ 无法自动修复，需要手动编辑")
            return False
        
        # 验证和修复每个包
        fixed_data = []
        for pack in data:
            fixed_pack = {}
            
            # 确保pack_id存在且格式正确
            if 'pack_id' in pack:
                uuid = pack['pack_id']
                # 移除空格
                uuid = uuid.strip()
                fixed_pack['pack_id'] = uuid
            else:
                print(f"   ⚠️  跳过缺少pack_id的包")
                continue
            
            # 确保version格式正确
            if 'version' in pack:
                version = pack['version']
                if isinstance(version, list):
                    # 确保有3个元素
                    while len(version) < 3:
                        version.append(0)
                    fixed_pack['version'] = version[:3]
                elif isinstance(version, str):
                    # 尝试解析版本字符串
                    try:
                        parts = version.split('.')
                        fixed_pack['version'] = [int(p) for p in parts[:3]] + [0] * (3 - len(parts[:3]))
                    except:
                        fixed_pack['version'] = [1, 0, 0]
                else:
                    fixed_pack['version'] = [1, 0, 0]
            else:
                fixed_pack['version'] = [1, 0, 0]
            
            fixed_data.append(fixed_pack)
        
        # 备份原文件
        backup_path = config_path.with_suffix('.json.backup')
        import shutil
        shutil.copy(config_path, backup_path)
        print(f"   ✅ 已备份到: {backup_path.name}")
        
        # 写入修复后的文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ 配置文件已修复")
        return True
        
    except Exception as e:
        print(f"   ❌ 修复失败: {e}")
        return False

def main():
    print("="*70)
    print("世界配置文件验证工具")
    print("="*70)
    
    # 检查资源包配置
    rp_config = Config.WORLD_RESOURCE_PACKS_CONFIG
    rp_valid, rp_issues = validate_config(rp_config, "资源包配置")
    
    # 检查行为包配置
    bp_config = Config.WORLD_BEHAVIOR_PACKS_CONFIG
    bp_valid, bp_issues = validate_config(bp_config, "行为包配置")
    
    # 总结
    print("\n" + "="*70)
    print("验证结果")
    print("="*70)
    
    all_valid = rp_valid and bp_valid
    
    if all_valid:
        print("✅ 所有配置文件格式正确！")
    else:
        print("❌ 发现配置问题，可能导致服务器无法启动")
        print("\n尝试自动修复...")
        
        if not rp_valid:
            fix_config(rp_config, "资源包")
        if not bp_valid:
            fix_config(bp_config, "行为包")
        
        print("\n修复后请重新验证:")
        print("  python3 scripts/validate_world_configs.py")
    
    print("="*70)
    
    sys.exit(0 if all_valid else 1)

if __name__ == '__main__':
    main()

