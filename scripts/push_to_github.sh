#!/bin/bash
# 推送项目到GitHub

set -e

cd /home/ubuntu/bedrock-manager

echo "🚀 开始推送到GitHub..."

# 1. 初始化git仓库（如果还没有）
if [ ! -d .git ]; then
    echo "📦 初始化Git仓库..."
    git init
fi

# 2. 添加远程仓库
REMOTE_URL="git@github.com:peterpanstechland/minecraft-server-manager-bedrock.git"
if git remote get-url origin >/dev/null 2>&1; then
    echo "🔄 更新远程仓库URL..."
    git remote set-url origin "$REMOTE_URL"
else
    echo "➕ 添加远程仓库..."
    git remote add origin "$REMOTE_URL"
fi

# 3. 确保.gitignore存在
if [ ! -f .gitignore ]; then
    echo "⚠️  警告: .gitignore文件不存在"
fi

# 4. 添加所有文件
echo "📝 添加文件到暂存区..."
git add .

# 5. 检查是否有更改
if git diff --cached --quiet && git diff --quiet; then
    echo "✅ 没有更改需要提交"
    exit 0
fi

# 6. 提交更改
echo "💾 提交更改..."
git commit -m "Initial commit: Bedrock Server Manager

- Complete web management interface for Minecraft Bedrock server
- Addon management with CurseForge integration
- Server control (start/stop/restart)
- Player management (invincible mode, kick, commands)
- Real-time log monitoring
- Security features (authentication, CSRF, rate limiting)
- Complete documentation and project structure"

# 7. 推送到GitHub
echo "📤 推送到GitHub..."
git branch -M main
git push -u origin main

echo "✅ 推送完成！"
echo "🔗 仓库地址: https://github.com/peterpanstechland/minecraft-server-manager-bedrock"
