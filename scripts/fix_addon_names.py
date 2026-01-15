#!/usr/bin/env python3
"""修复addon名称：将翻译键（如pack.name）替换为实际名称"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db, create_app
from app.models import Addon

app = create_app()
with app.app_context():
    print("=== 修复Addon名称 ===\n")
    
    all_addons = Addon.query.all()
    updated_count = 0
    
    for addon in all_addons:
        # 检查名称是否是翻译键
        if addon.name and (addon.name.startswith('pack.') or addon.name.startswith('resourcePack.') or addon.name == 'pack.name'):
            manifest_path = Path(addon.local_path) / 'manifest.json'
            
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                        manifest = json.load(f)
                    
                    header = manifest.get('header', {})
                    name = header.get('name', '')
                    description = header.get('description', '')
                    
                    # 尝试获取实际名称
                    new_name = None
                    
                    # 1. 尝试从description获取
                    if description and not description.startswith('pack.') and not description.startswith('resourcePack.'):
                        new_name = description
                    # 2. 使用目录名
                    elif addon.local_path:
                        dir_name = Path(addon.local_path).name
                        new_name = dir_name.replace('_', ' ').replace('-', ' ').title()
                    
                    if new_name and new_name != addon.name:
                        print(f"更新: {addon.name} -> {new_name}")
                        addon.name = new_name
                        updated_count += 1
                except Exception as e:
                    print(f"处理 {addon.name} 失败: {e}")
    
    if updated_count > 0:
        db.session.commit()
        print(f"\n✅ 已更新 {updated_count} 个addon的名称")
    else:
        print("\n✅ 所有addon名称已正确")

