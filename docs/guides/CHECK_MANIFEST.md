# New Glowing Ores Manifest 兼容性检查指南

## 快速检查

如果你已经有 New Glowing Ores 资源包文件（.zip 或已解压），运行：

```bash
# 如果已解压到 resource_packs 目录
python scripts/check_manifest_compatibility.py /home/ubuntu/bedrock-server/resource_packs/NewGlowingOres/manifest.json

# 如果还在 zip 文件中，先解压
unzip NewGlowingOres*.zip -d /tmp/check_manifest/
python scripts/check_manifest_compatibility.py /tmp/check_manifest/NewGlowingOres/manifest.json
```

## 检查清单

脚本会自动检查以下内容：

### ✅ 必需检查项

1. **manifest.json 存在且格式正确**
   - JSON 格式有效
   - 包含必需的字段

2. **Header 字段完整性**
   - `header.uuid` - 用于 world_resource_packs.json
   - `header.name` - 资源包名称
   - `header.version` - 版本号（格式：[major, minor, patch]）

3. **UUID 格式**
   - 必须是有效的 UUID 格式：`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - ⚠️ **重要**：使用 `header.uuid`，不是 `modules.uuid`

4. **包类型**
   - 必须是资源包（Resource Pack）
   - modules 类型应该是：`resources`, `client_data`, `client_scripts`
   - ❌ 不能是行为包（Behavior Pack）

5. **Manifest 位置**
   - 必须在第一层：`resource_packs/PackName/manifest.json`
   - ❌ 不能嵌套：`resource_packs/PackName/PackName/manifest.json`

### ⚠️ 建议检查项

1. **最小引擎版本**
   - 建议 >= 1.16.0
   - 过低可能导致兼容性问题

2. **服务器配置**
   - `texturepack-required=true` - 强制玩家加载材质包
   - 如果为 `false`，玩家可能拒绝下载

3. **世界配置**
   - `world_resource_packs.json` 中是否已包含此包
   - UUID 和版本号是否正确

## 检查结果说明

### ✅ 信息（Info）
- 正常情况，无需处理

### ⚠️ 警告（Warnings）
- 不影响安装，但建议修复
- 例如：`texturepack-required=false` 应该改为 `true`

### ❌ 问题（Issues）
- 必须修复才能正常使用
- 例如：UUID 格式错误、manifest 位置错误

## 安装步骤（检查通过后）

### 1. 解压资源包到正确位置

```bash
cd /home/ubuntu/bedrock-server/resource_packs
unzip NewGlowingOres*.zip

# 确保结构是：
# resource_packs/NewGlowingOres/manifest.json
# resource_packs/NewGlowingOres/textures/
# resource_packs/NewGlowingOres/blocks.json
```

### 2. 添加到 world_resource_packs.json

检查脚本会输出配置片段，例如：

```json
[
  {
    "pack_id": "a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "version": [1, 0, 0]
  }
]
```

编辑世界配置文件：

```bash
nano "/home/ubuntu/bedrock-server/worlds/Bedrock level/world_resource_packs.json"
```

将配置片段添加到现有数组中（如果已有其他资源包）。

### 3. 设置服务器强制加载

```bash
nano /home/ubuntu/bedrock-server/server.properties
```

确保：

```
texturepack-required=true
```

### 4. 重启服务器

```bash
sudo systemctl restart bedrock
```

## 常见问题

### Q: 检查脚本说 UUID 格式错误？

A: 确保使用的是 `header.uuid`，不是 `modules[].uuid`。检查 manifest.json：

```json
{
  "header": {
    "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  ← 用这个
    ...
  },
  "modules": [
    {
      "uuid": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",  ← 不是这个
      ...
    }
  ]
}
```

### Q: 检查脚本说 manifest.json 位置错误？

A: 确保解压后 manifest.json 在第一层：

```
❌ 错误：
resource_packs/NewGlowingOres/NewGlowingOres/manifest.json

✅ 正确：
resource_packs/NewGlowingOres/manifest.json
```

解决方法：重新解压，或移动文件：

```bash
cd /home/ubuntu/bedrock-server/resource_packs/NewGlowingOres
# 如果有多层嵌套，移动文件
mv NewGlowingOres/* .
rmdir NewGlowingOres
```

### Q: 检查通过但玩家进服没效果？

A: 检查：

1. `texturepack-required=true` 是否设置
2. `world_resource_packs.json` 中 UUID 是否正确
3. 玩家客户端是否有冲突的材质包（让玩家关闭本地材质包）
4. 服务器日志是否有错误信息

### Q: 如何验证资源包已正确加载？

A: 查看服务器日志：

```bash
tail -f /home/ubuntu/bedrock-server/Dedicated_Server.txt | grep -i "resource\|pack\|uuid"
```

玩家进服时会看到：
- "Downloading Resource Packs…"
- "Importing Content…"

## 在代码中使用

你也可以在 Python 代码中使用检查功能：

```python
from pathlib import Path
from app.addon_manager import AddonManager

manifest_path = Path("/home/ubuntu/bedrock-server/resource_packs/NewGlowingOres/manifest.json")
is_compatible, results = AddonManager.check_manifest_compatibility(manifest_path)

if is_compatible:
    print("✅ 兼容！")
    print(f"UUID: {results['uuid']}")
    print(f"配置片段:\n{results['config_snippet']}")
else:
    print("❌ 不兼容，请修复以下问题：")
    for issue in results['issues']:
        print(f"  {issue}")
```

## 进阶：批量检查

检查所有已安装的资源包：

```bash
for pack_dir in /home/ubuntu/bedrock-server/resource_packs/*/; do
    manifest="$pack_dir/manifest.json"
    if [ -f "$manifest" ]; then
        echo "检查: $pack_dir"
        python scripts/check_manifest_compatibility.py "$manifest"
        echo ""
    fi
done
```

