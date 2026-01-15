#!/usr/bin/env python3
"""
快速修复重启时的 BAD REQUEST 错误
检查并修复 world_resource_packs.json 和 world_behavior_packs.json
"""

import sys
import json
import re
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

def validate_uuid(uuid):
    """验证UUID格式"""
    if not uuid:
        return False
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, str(uuid), re.IGNORECASE))

def fix_config_file(config_path: Path):
    """修复配置文件"""
    if not config_path.exists():
        print(f"⚠️  文件不存在: {config_path}")
        return False
    
    print(f"\n检查: {config_path.name}")
    
    try:
        # 读取文件
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON格式错误: {e}")
            print(f"   尝试修复...")
            
            # 移除尾随逗号
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            # 移除注释（如果存在）
            content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            
            try:
                data = json.loads(content)
                print(f"   ✅ JSON已修复")
            except:
                print(f"   ❌ 无法自动修复，需要手动编辑")
                return False
        
        if not isinstance(data, list):
            print(f"❌ 配置应该是数组，当前是: {type(data).__name__}")
            return False
        
        # 修复每个包
        fixed_packs = []
        removed_count = 0
        
        for pack in data:
            fixed_pack = {}
            
            # 检查pack_id
            pack_id = pack.get('pack_id', '').strip()
            if not pack_id:
                print(f"   ⚠️  跳过缺少pack_id的包")
                removed_count += 1
                continue
            
            if not validate_uuid(pack_id):
                print(f"   ⚠️  跳过无效UUID的包: {pack_id[:20]}...")
                removed_count += 1
                continue
            
            fixed_pack['pack_id'] = pack_id
            
            # 检查version
            version = pack.get('version', [1, 0, 0])
            if isinstance(version, list):
                # 确保有3个整数元素
                version = [int(v) for v in version[:3]]
                while len(version) < 3:
                    version.append(0)
                fixed_pack['version'] = version
            elif isinstance(version, str):
                # 尝试解析版本字符串
                try:
                    parts = version.split('.')
                    fixed_pack['version'] = [int(p) for p in parts[:3]] + [0] * max(0, 3 - len(parts))
                except:
                    fixed_pack['version'] = [1, 0, 0]
            else:
                fixed_pack['version'] = [1, 0, 0]
            
            fixed_packs.append(fixed_pack)
        
        if removed_count > 0:
            print(f"   ⚠️  移除了 {removed_count} 个无效的包配置")
        
        # 备份原文件
        backup_path = config_path.with_suffix('.json.backup')
        shutil.copy(config_path, backup_path)
        print(f"   ✅ 已备份到: {backup_path.name}")
        
        # 写入修复后的文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(fixed_packs, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ 已修复 {len(fixed_packs)} 个包配置")
        return True
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*70)
    print("修复 BAD REQUEST 错误")
    print("="*70)
    
    rp_config = Config.WORLD_RESOURCE_PACKS_CONFIG
    bp_config = Config.WORLD_BEHAVIOR_PACKS_CONFIG
    
    rp_ok = fix_config_file(rp_config)
    bp_ok = fix_config_file(bp_config)
    
    print("\n" + "="*70)
    if rp_ok and bp_ok:
        print("✅ 配置文件已修复！")
        print("\n下一步:")
        print("1. 重新尝试重启服务器")
        print("2. 如果还有问题，检查服务器日志")
    else:
        print("⚠️  部分配置文件修复失败，请手动检查")
    print("="*70)

if __name__ == '__main__':
    main()

