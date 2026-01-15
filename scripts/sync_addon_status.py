#!/usr/bin/env python3
"""同步addon状态：根据配置文件更新数据库中的启用状态"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db, create_app
from app.models import Addon
from config import Config

app = create_app()
with app.app_context():
    print("=== 同步Addon状态 ===\n")
    
    # 读取配置文件中的UUID
    enabled_uuids = set()
    
    # 读取行为包配置
    if Config.WORLD_BEHAVIOR_PACKS_CONFIG.exists():
        with open(Config.WORLD_BEHAVIOR_PACKS_CONFIG, 'r') as f:
            bp_data = json.load(f)
            for pack in bp_data:
                enabled_uuids.add(pack['pack_id'])
            print(f"配置文件中的行为包: {len(bp_data)} 个")
    
    # 读取资源包配置
    if Config.WORLD_RESOURCE_PACKS_CONFIG.exists():
        with open(Config.WORLD_RESOURCE_PACKS_CONFIG, 'r') as f:
            rp_data = json.load(f)
            for pack in rp_data:
                enabled_uuids.add(pack['pack_id'])
            print(f"配置文件中的资源包: {len(rp_data)} 个")
    
    print(f"\n配置文件中总共有 {len(enabled_uuids)} 个addon\n")
    
    # 更新数据库
    all_addons = Addon.query.all()
    updated_count = 0
    
    for addon in all_addons:
        should_be_enabled = addon.uuid in enabled_uuids
        if addon.enabled != should_be_enabled:
            old_status = "已启用" if addon.enabled else "已禁用"
            addon.enabled = should_be_enabled
            new_status = "已启用" if should_be_enabled else "已禁用"
            print(f"更新: {addon.name} - {old_status} -> {new_status}")
            updated_count += 1
    
    if updated_count > 0:
        db.session.commit()
        print(f"\n✅ 已更新 {updated_count} 个addon的状态")
    else:
        print("\n✅ 所有addon状态已同步")
    
    # 显示当前状态
    enabled = Addon.query.filter_by(enabled=True).all()
    print(f"\n当前已启用的addon: {len(enabled)} 个")
    for a in enabled:
        print(f"  - {a.name} ({a.pack_type})")

