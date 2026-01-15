#!/bin/bash
# 快速检查资源包类型（Java vs Bedrock）

ZIP_FILE="$1"

if [ -z "$ZIP_FILE" ]; then
    echo "用法: $0 <zip文件路径>"
    exit 1
fi

if [ ! -f "$ZIP_FILE" ]; then
    echo "❌ 文件不存在: $ZIP_FILE"
    exit 1
fi

echo "检查文件: $ZIP_FILE"
echo ""

# 检查 manifest.json (Bedrock)
if unzip -l "$ZIP_FILE" 2>/dev/null | grep -q "manifest.json"; then
    echo "✅ 找到 manifest.json - Bedrock Edition 资源包"
    BEDROCK=true
else
    echo "❌ 没有 manifest.json"
    BEDROCK=false
fi

# 检查 pack.mcmeta (Java)
if unzip -l "$ZIP_FILE" 2>/dev/null | grep -q "pack.mcmeta"; then
    echo "⚠️  找到 pack.mcmeta - Java Edition 资源包"
    JAVA=true
else
    echo "✅ 没有 pack.mcmeta"
    JAVA=false
fi

echo ""
echo "顶层文件/目录:"
unzip -l "$ZIP_FILE" 2>/dev/null | grep -E "^\s+[0-9]" | awk '{print $4}' | cut -d'/' -f1 | sort -u | head -10

echo ""
if [ "$BEDROCK" = true ]; then
    echo "✅ 结论: 这是 Bedrock Edition 资源包，可以上传"
elif [ "$JAVA" = true ]; then
    echo "❌ 结论: 这是 Java Edition 资源包，无法在 Bedrock 服务器使用"
    echo "   请下载 Bedrock 版本"
else
    echo "⚠️  无法确定包类型，请手动检查"
fi
