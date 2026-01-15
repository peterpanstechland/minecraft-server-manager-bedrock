#!/bin/bash
# 配置GitHub SSH密钥

set -e

echo "🔑 GitHub SSH密钥配置向导"
echo ""

# 检查是否已有密钥
if [ -f ~/.ssh/id_ed25519.pub ]; then
    echo "✅ 发现现有SSH密钥: ~/.ssh/id_ed25519.pub"
    echo ""
    echo "公钥内容："
    cat ~/.ssh/id_ed25519.pub
    echo ""
    echo "请将上面的公钥添加到GitHub:"
    echo "1. 访问 https://github.com/settings/keys"
    echo "2. 点击 'New SSH key'"
    echo "3. 粘贴上面的公钥内容"
    echo "4. 点击 'Add SSH key'"
    echo ""
    read -p "添加完成后按Enter继续测试连接..."
elif [ -f ~/.ssh/id_rsa.pub ]; then
    echo "✅ 发现现有SSH密钥: ~/.ssh/id_rsa.pub"
    echo ""
    echo "公钥内容："
    cat ~/.ssh/id_rsa.pub
    echo ""
    echo "请将上面的公钥添加到GitHub:"
    echo "1. 访问 https://github.com/settings/keys"
    echo "2. 点击 'New SSH key'"
    echo "3. 粘贴上面的公钥内容"
    echo "4. 点击 'Add SSH key'"
    echo ""
    read -p "添加完成后按Enter继续测试连接..."
else
    echo "📝 未发现SSH密钥，开始生成..."
    echo ""
    
    # 询问邮箱
    read -p "请输入你的GitHub邮箱地址: " email
    
    if [ -z "$email" ]; then
        echo "❌ 邮箱地址不能为空"
        exit 1
    fi
    
    # 生成密钥
    echo "生成SSH密钥..."
    ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/id_ed25519 -N ""
    
    # 启动ssh-agent
    eval "$(ssh-agent -s)"
    
    # 添加密钥
    ssh-add ~/.ssh/id_ed25519
    
    echo ""
    echo "✅ SSH密钥已生成！"
    echo ""
    echo "公钥内容："
    cat ~/.ssh/id_ed25519.pub
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "请将上面的公钥添加到GitHub:"
    echo "1. 访问 https://github.com/settings/keys"
    echo "2. 点击 'New SSH key'"
    echo "3. Title: 输入一个名称（如：Ubuntu Server）"
    echo "4. Key: 粘贴上面的公钥内容"
    echo "5. 点击 'Add SSH key'"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "添加完成后按Enter继续测试连接..."
fi

# 测试连接
echo ""
echo "🧪 测试GitHub连接..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ SSH连接成功！可以推送到GitHub了。"
else
    echo "⚠️  连接测试未完全成功，但可能已经配置正确。"
    echo "如果看到 'Hi username! You've successfully authenticated' 说明配置成功。"
fi

echo ""
echo "📝 现在可以执行推送命令："
echo "   git push -u origin main"
