#!/bin/bash
# Bedrock服务器连接检查脚本

echo "=== Bedrock服务器连接检查 ==="
echo ""

# 检查服务器是否运行
echo "1. 检查服务器状态..."
if ps aux | grep -q "[b]edrock_server"; then
    PID=$(ps aux | grep "[b]edrock_server" | awk '{print $2}' | head -1)
    echo "   ✅ 服务器正在运行 (PID: $PID)"
else
    echo "   ❌ 服务器未运行"
    exit 1
fi

# 检查端口监听
echo ""
echo "2. 检查端口监听..."
if sudo netstat -tulnp 2>/dev/null | grep -q ":19132"; then
    echo "   ✅ 端口19132 (UDP) 正在监听"
else
    echo "   ❌ 端口19132未监听"
fi

if sudo netstat -tulnp 2>/dev/null | grep -q ":19133"; then
    echo "   ✅ 端口19133 (UDP6) 正在监听"
else
    echo "   ⚠️  端口19133未监听（IPv6，可能不影响）"
fi

# 检查服务器版本
echo ""
echo "3. 检查服务器版本..."
VERSION=$(grep "Version:" /home/ubuntu/bedrock-server/Dedicated_Server.txt 2>/dev/null | tail -1 | awk '{print $2}')
if [ -n "$VERSION" ]; then
    echo "   ✅ 服务器版本: $VERSION"
else
    echo "   ⚠️  无法获取版本信息"
fi

# 检查防火墙
echo ""
echo "4. 检查防火墙..."
if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null | head -1)
    echo "   $UFW_STATUS"
    if echo "$UFW_STATUS" | grep -q "inactive"; then
        echo "   ⚠️  防火墙未启用"
    else
        if sudo ufw status | grep -q "19132"; then
            echo "   ✅ 端口19132已在防火墙规则中"
        else
            echo "   ⚠️  端口19132可能未在防火墙规则中"
            echo "   建议运行: sudo ufw allow 19132/udp"
        fi
    fi
else
    echo "   ⚠️  ufw未安装，无法检查防火墙"
fi

# 检查服务器配置
echo ""
echo "5. 检查服务器配置..."
if [ -f /home/ubuntu/bedrock-server/server.properties ]; then
    ONLINE_MODE=$(grep "^online-mode=" /home/ubuntu/bedrock-server/server.properties | cut -d'=' -f2)
    MAX_PLAYERS=$(grep "^max-players=" /home/ubuntu/bedrock-server/server.properties | cut -d'=' -f2)
    SERVER_PORT=$(grep "^server-port=" /home/ubuntu/bedrock-server/server.properties | cut -d'=' -f2)
    
    echo "   online-mode: $ONLINE_MODE"
    echo "   max-players: $MAX_PLAYERS"
    echo "   server-port: $SERVER_PORT"
else
    echo "   ❌ server.properties文件不存在"
fi

# 检查最近连接
echo ""
echo "6. 最近连接记录..."
tail -20 /home/ubuntu/bedrock-server/Dedicated_Server.txt 2>/dev/null | grep -E "(Player|Connection|Error)" | tail -5

# 获取服务器IP
echo ""
echo "7. 服务器IP地址..."
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "   服务器IP: $SERVER_IP"
echo "   连接地址: $SERVER_IP:19132"

echo ""
echo "=== 检查完成 ==="
echo ""
echo "如果客户端无法连接，请检查："
echo "1. 客户端版本是否与服务器匹配"
echo "2. 防火墙/路由器是否允许UDP 19132端口"
echo "3. 如果使用云服务器，检查安全组规则"
echo "4. 确保客户端已登录Microsoft账号（如果online-mode=true）"

