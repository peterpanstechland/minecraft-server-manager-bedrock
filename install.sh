#!/bin/bash

echo "安装Bedrock Server Manager依赖..."

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 安装pip（如果不存在）
if ! command -v pip3 &> /dev/null; then
    echo "安装pip3..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

# 安装依赖
echo "安装Python依赖包..."
pip3 install -r requirements.txt

echo "安装完成！"
echo ""
echo "启动应用:"
echo "  cd bedrock-manager"
echo "  python3 run.py"
echo ""
echo "然后访问: http://localhost:5000"

