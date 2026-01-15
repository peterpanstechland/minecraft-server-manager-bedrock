#!/usr/bin/env python3
"""创建管理员用户的辅助脚本"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models import User
from config import Config
from getpass import getpass

def create_admin():
    """创建管理员用户"""
    app = create_app()
    
    with app.app_context():
        print("=== Bedrock Manager - 创建管理员账号 ===\n")
        
        username = input("请输入用户名 [admin]: ").strip() or "admin"
        
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"\n⚠️  用户 '{username}' 已存在！")
            overwrite = input("是否覆盖密码？(y/N): ").strip().lower()
            if overwrite != 'y':
                print("操作已取消")
                return
            user = existing_user
        else:
            user = User(username=username)
        
        # 设置密码
        while True:
            password = getpass("请输入密码（至少8位）: ")
            if len(password) < 8:
                print("❌ 密码至少需要8位字符")
                continue
            
            password_confirm = getpass("请再次输入密码: ")
            if password != password_confirm:
                print("❌ 两次密码不一致")
                continue
            
            break
        
        user.set_password(password)
        
        if not existing_user:
            db.session.add(user)
        
        try:
            db.session.commit()
            print(f"\n✅ 成功{'更新' if existing_user else '创建'}管理员账号：{username}")
            print("\n现在可以使用此账号登录系统")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 操作失败：{e}")
            sys.exit(1)

if __name__ == '__main__':
    create_admin()
