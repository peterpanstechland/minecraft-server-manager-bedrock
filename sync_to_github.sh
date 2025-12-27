#!/bin/bash

# 同步项目到GitHub仓库的脚本

set -e

cd /home/ubuntu/bedrock-manager

echo "=== 初始化Git仓库 ==="
if [ ! -d .git ]; then
    git init
fi

echo "=== 创建必要的占位文件 ==="
touch static/uploads/.gitkeep database/.gitkeep 2>/dev/null || true

echo "=== 配置远程仓库 ==="
git remote remove origin 2>/dev/null || true
git remote add origin git@github.com:peterpanstechland/minecraft-server-manager-bedrock.git

echo "=== 添加所有文件 ==="
git add .

echo "=== 检查状态 ==="
git status

echo ""
echo "=== 提交更改 ==="
git commit -m "Initial commit: Bedrock Server Manager

Features:
- Addon management (upload, install from CurseForge, enable/disable)
- Server control (start, stop, restart, status monitoring)
- Real-time log monitoring with search functionality
- Web interface with Bootstrap 5
- SQLite database for addon tracking
- CurseForge API integration for automatic downloads and updates"

echo ""
echo "=== 设置主分支 ==="
git branch -M main

echo ""
echo "=== 推送到GitHub ==="
echo "如果这是第一次推送，可能需要设置SSH密钥或使用HTTPS"
echo "推送命令: git push -u origin main"
echo ""
read -p "是否现在推送到GitHub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push -u origin main
    echo "推送完成！"
else
    echo "跳过推送。您可以稍后运行: git push -u origin main"
fi

