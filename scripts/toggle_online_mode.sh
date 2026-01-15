#!/bin/bash
# 切换online-mode配置的脚本

SERVER_PROPERTIES="/home/ubuntu/bedrock-server/server.properties"
BACKUP_FILE="/home/ubuntu/bedrock-server/server.properties.backup"

if [ ! -f "$SERVER_PROPERTIES" ]; then
    echo "错误: server.properties文件不存在"
    exit 1
fi

# 检查当前状态
CURRENT_MODE=$(grep "^online-mode=" "$SERVER_PROPERTIES" | cut -d'=' -f2)

echo "当前 online-mode 设置: $CURRENT_MODE"
echo ""

if [ "$CURRENT_MODE" = "true" ]; then
    echo "当前模式: online-mode=true (需要Xbox Live认证，不允许同账号多设备)"
    echo ""
    read -p "是否要切换到 online-mode=false? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 备份
        cp "$SERVER_PROPERTIES" "$BACKUP_FILE"
        echo "✓ 已备份配置文件"
        
        # 修改
        sed -i 's/^online-mode=true/online-mode=false/' "$SERVER_PROPERTIES"
        echo "✓ 已修改为 online-mode=false"
        echo ""
        echo "⚠️  警告："
        echo "  - 安全性降低，不需要Xbox Live认证"
        echo "  - 可能允许同账号多设备登录（需要测试）"
        echo "  - 建议启用白名单以提高安全性"
        echo ""
        read -p "是否要重启服务器以应用更改? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo systemctl restart bedrock.service
            echo "✓ 服务器已重启"
        fi
    fi
else
    echo "当前模式: online-mode=false (不需要Xbox Live认证)"
    echo ""
    read -p "是否要切换回 online-mode=true? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 恢复备份或直接修改
        if [ -f "$BACKUP_FILE" ]; then
            cp "$BACKUP_FILE" "$SERVER_PROPERTIES"
            echo "✓ 已从备份恢复配置"
        else
            sed -i 's/^online-mode=false/online-mode=true/' "$SERVER_PROPERTIES"
            echo "✓ 已修改为 online-mode=true"
        fi
        echo ""
        read -p "是否要重启服务器以应用更改? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo systemctl restart bedrock.service
            echo "✓ 服务器已重启"
        fi
    fi
fi

