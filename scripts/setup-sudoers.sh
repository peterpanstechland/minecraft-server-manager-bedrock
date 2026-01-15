#!/bin/bash
# 配置sudoers，允许特定用户无需密码执行特定命令
# 注意：此脚本需要root权限运行

echo "配置sudoers以允许无需密码执行Bedrock服务器管理命令..."
echo ""
echo "此脚本将添加以下配置到sudoers："
echo "  ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl start bedrock-server"
echo "  ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl stop bedrock-server"
echo "  ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart bedrock-server"
echo ""
read -p "是否继续？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 1
fi

# 创建临时sudoers文件
TMP_SUDOERS=$(mktemp)
sudo cp /etc/sudoers "$TMP_SUDOERS"

# 添加配置
cat >> "$TMP_SUDOERS" << 'EOF'

# Bedrock Server Manager - 允许ubuntu用户无需密码管理服务器
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl start bedrock-server
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl stop bedrock-server
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart bedrock-server
EOF

# 验证sudoers文件语法
if sudo visudo -c -f "$TMP_SUDOERS"; then
    sudo cp "$TMP_SUDOERS" /etc/sudoers
    echo "✓ sudoers配置已更新"
    echo ""
    echo "现在ubuntu用户可以无需密码执行："
    echo "  sudo systemctl start bedrock-server"
    echo "  sudo systemctl stop bedrock-server"
    echo "  sudo systemctl restart bedrock-server"
else
    echo "✗ sudoers文件语法错误，未应用更改"
    rm "$TMP_SUDOERS"
    exit 1
fi

rm "$TMP_SUDOERS"

