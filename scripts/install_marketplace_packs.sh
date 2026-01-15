#!/bin/bash
# Marketplace 包安装脚本（使用 venv）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 激活venv
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    echo "✅ 已激活 venv"
else
    echo "⚠️  venv 不存在，使用系统 Python"
fi

# 运行Python脚本
cd "$PROJECT_ROOT"
"$PROJECT_ROOT/venv/bin/python3" scripts/install_marketplace_packs.py "$@"

