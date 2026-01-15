#!/bin/bash
# 实时监控服务器连接

echo "=== Bedrock服务器连接监控 ==="
echo "按 Ctrl+C 停止监控"
echo ""
echo "等待连接尝试..."
echo ""

tail -f /home/ubuntu/bedrock-server/Dedicated_Server.txt 2>/dev/null | while read line; do
    if echo "$line" | grep -qE "(Player|Connection|Error|client|connect|disconnect|join|leave|Failed|Refused)"; then
        echo "[$(date '+%H:%M:%S')] $line"
    fi
done

