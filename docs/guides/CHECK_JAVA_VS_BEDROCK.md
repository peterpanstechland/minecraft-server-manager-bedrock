# Java Edition vs Bedrock Edition 资源包区别

## 问题诊断

你的 `NewGlowingOres-§6[Border]§r.zip` 文件是 **Java Edition** 的资源包，不是 Bedrock Edition 的。

### Java Edition 资源包特征：
- ✅ 有 `pack.mcmeta` 文件
- ✅ 有 `assets/` 目录
- ❌ **没有** `manifest.json` 文件

### Bedrock Edition 资源包特征：
- ✅ 有 `manifest.json` 文件（必需）
- ✅ 有 `textures/` 目录
- ✅ 可能有 `blocks.json`、`items.json` 等
- ❌ **没有** `pack.mcmeta` 文件

## 解决方案

### 方案1: 下载 Bedrock 版本（推荐）

1. **在 CurseForge 查找 Bedrock 版本**
   - 访问 CurseForge 搜索 "New Glowing Ores Bedrock"
   - 确保下载的是 Bedrock Edition 版本

2. **检查文件内容**
   - 下载后先用诊断工具检查：
   ```bash
   python3 scripts/diagnose_upload.py <下载的文件>
   ```
   - 应该看到 `manifest.json` 文件

### 方案2: 手动转换（高级）

如果你有 Java Edition 的资源包，可以尝试转换为 Bedrock 格式：

1. **创建 manifest.json**
   ```json
   {
     "format_version": 2,
     "header": {
       "name": "New Glowing Ores",
       "description": "Glowing ores resource pack",
       "uuid": "生成一个UUID",
       "version": [1, 0, 0],
       "min_engine_version": [1, 16, 0]
     },
     "modules": [
       {
         "type": "resources",
         "uuid": "生成另一个UUID",
         "version": [1, 0, 0]
       }
     ]
   }
   ```

2. **转换目录结构**
   - Java: `assets/minecraft/textures/blocks/`
   - Bedrock: `textures/blocks/` 或 `textures/terrain_texture.json`

3. **转换纹理格式**
   - Java 使用 PNG，Bedrock 也使用 PNG，但路径不同
   - 需要创建 `textures/terrain_texture.json` 来映射纹理

**注意**：转换过程比较复杂，建议直接下载 Bedrock 版本。

### 方案3: 查找替代方案

如果找不到 Bedrock 版本，可以搜索：
- "Bedrock glowing ores"
- "Bedrock resource pack glowing"
- 在 CurseForge/MCPEDL 等 Bedrock 专用网站搜索

## 如何识别 Bedrock 资源包

下载前检查文件内容：

```bash
# 列出 ZIP 文件内容
unzip -l NewGlowingOres*.zip | head -20

# 应该看到：
# manifest.json  ← 必需！
# textures/
# blocks.json 或 items.json（可选）
```

## 快速检查脚本

创建一个检查脚本：

```bash
#!/bin/bash
ZIP_FILE="$1"

echo "检查文件: $ZIP_FILE"
echo ""

# 检查是否有 manifest.json
if unzip -l "$ZIP_FILE" | grep -q "manifest.json"; then
    echo "✅ 找到 manifest.json - 这是 Bedrock Edition 资源包"
else
    echo "❌ 没有 manifest.json"
fi

# 检查是否有 pack.mcmeta
if unzip -l "$ZIP_FILE" | grep -q "pack.mcmeta"; then
    echo "⚠️  找到 pack.mcmeta - 这可能是 Java Edition 资源包"
fi

# 列出顶层文件
echo ""
echo "顶层文件/目录:"
unzip -l "$ZIP_FILE" | grep -E "^\s+[0-9]" | awk '{print $4}' | cut -d'/' -f1 | sort -u | head -10
```

## 总结

**你的文件是 Java Edition 格式，无法直接在 Bedrock 服务器上使用。**

**下一步**：
1. 在 CurseForge/MCPEDL 搜索 Bedrock 版本的 "New Glowing Ores"
2. 下载 Bedrock 版本后重新上传
3. 或者使用其他 Bedrock 兼容的发光矿石资源包

