#!/usr/bin/env python3
"""检查并显示已启用的addon"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db, create_app
from app.models import Addon
from app.addon_manager import AddonManager

app = create_app()
with app.app_context():
    print("=== 检查已启用的Addon ===\n")
    
    # 检查数据库中的启用状态
    enabled = Addon.query.filter_by(enabled=True).all()
    disabled = Addon.query.filter_by(enabled=False).all()
    
    print(f"数据库状态:")
    print(f"  已启用: {len(enabled)} 个")
    print(f"  已禁用: {len(disabled)} 个")
    print()
    
    if enabled:
        print("已启用的Addon:")
        for a in enabled:
            print(f"  ✅ {a.name} ({a.pack_type}) - UUID: {a.uuid}")
    else:
        print("⚠️  没有已启用的Addon")
    
    print()
    
    # 检查配置文件
    from config import Config
    import json
    
    bp_config = Config.WORLD_BEHAVIOR_PACKS_CONFIG
    rp_config = Config.WORLD_RESOURCE_PACKS_CONFIG
    
    print("配置文件状态:")
    if bp_config.exists():
        with open(bp_config, 'r') as f:
            bp_data = json.load(f)
            print(f"  行为包配置: {len(bp_data)} 个")
    else:
        print(f"  行为包配置: 文件不存在")
    
    if rp_config.exists():
        with open(rp_config, 'r') as f:
            rp_data = json.load(f)
            print(f"  资源包配置: {len(rp_data)} 个")
    else:
        print(f"  资源包配置: 文件不存在")
    
    print()
    print("建议:")
    if len(enabled) == 0:
        print("  - 在Web界面启用需要的addon")
    elif len(enabled) != (len(bp_data) + len(rp_data) if bp_config.exists() and rp_config.exists() else 0):
        print("  - 配置文件和数据库不同步，建议重新更新配置")
        print("  - 运行: 在Web界面重新启用addon，或手动调用update_world_config()")

