#!/usr/bin/env python3
"""检查并启用addon"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db, create_app
from app.models import Addon
from app.addon_manager import AddonManager

app = create_app()
with app.app_context():
    print("=== 检查Addon状态 ===\n")
    
    all_addons = Addon.query.all()
    enabled = [a for a in all_addons if a.enabled]
    disabled = [a for a in all_addons if not a.enabled]
    
    print(f"总addon数: {len(all_addons)}")
    print(f"已启用: {len(enabled)}")
    print(f"已禁用: {len(disabled)}\n")
    
    if disabled:
        print("已禁用的addon:")
        for a in disabled:
            print(f"  - {a.name} ({a.pack_type}) - ID: {a.id}")
        
        print("\n是否要启用所有已禁用的addon？")
        print("(这将更新world配置文件)")
    else:
        print("✅ 所有addon都已启用")

