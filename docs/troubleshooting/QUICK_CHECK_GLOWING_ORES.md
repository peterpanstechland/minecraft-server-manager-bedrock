# 快速检查 New Glowing Ores Manifest

## 一句话结论

**New Glowing Ores 资源包的 manifest 兼容性检查工具已就绪！**

## 使用方法

### 如果你已经有资源包文件

```bash
# 方法1：如果已解压到服务器目录
python3 scripts/check_manifest_compatibility.py \
  /home/ubuntu/bedrock-server/resource_packs/NewGlowingOres/manifest.json

# 方法2：如果还在 zip 文件中
unzip -q NewGlowingOres*.zip -d /tmp/check_manifest/
python3 scripts/check_manifest_compatibility.py \
  /tmp/check_manifest/NewGlowingOres/manifest.json
```

### 检查结果示例

脚本会输出：

```
======================================================================
New Glowing Ores 资源包 Manifest 兼容性检查
======================================================================

检查文件: /home/ubuntu/bedrock-server/resource_packs/NewGlowingOres/manifest.json

======================================================================
检查结果
======================================================================

✅ 信息:
  ✅ 成功加载 manifest.json
  ✅ UUID: a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  ✅ 名称: New Glowing Ores
  ✅ 版本: [1, 0, 0]
  ✅ 确认为资源包类型
  ✅ 最小引擎版本: 1.16.x

⚠️  警告:
  ⚠️  server.properties: texturepack-required=false（建议改为 true）
  ⚠️  此资源包尚未添加到 world_resource_packs.json

======================================================================
✅ 结论: Manifest 兼容！可以安装到服务器
======================================================================

======================================================================
world_resource_packs.json 配置片段
======================================================================

将以下内容添加到 world_resource_packs.json:
[
  {
    "pack_id": "a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "version": [1, 0, 0]
  }
]
```

## 检查项说明

脚本会自动检查：

1. ✅ **manifest.json 格式** - JSON 是否有效
2. ✅ **UUID 格式** - 必须是有效的 UUID（使用 `header.uuid`）
3. ✅ **包类型** - 必须是资源包，不是行为包
4. ✅ **Manifest 位置** - 必须在第一层（`resource_packs/PackName/manifest.json`）
5. ✅ **版本格式** - 应该是 `[major, minor, patch]`
6. ⚠️ **服务器配置** - `texturepack-required` 是否设置为 `true`
7. ⚠️ **世界配置** - 是否已添加到 `world_resource_packs.json`

## 如果检查通过

按照脚本输出的配置片段，执行以下步骤：

### 1. 确保资源包位置正确

```bash
# 检查结构
ls -la /home/ubuntu/bedrock-server/resource_packs/NewGlowingOres/
# 应该看到：
# manifest.json
# textures/
# blocks.json
```

### 2. 添加到 world_resource_packs.json

```bash
nano "/home/ubuntu/bedrock-server/worlds/Bedrock level/world_resource_packs.json"
```

添加脚本输出的配置片段（如果已有其他资源包，添加到数组中）。

### 3. 设置强制加载

```bash
nano /home/ubuntu/bedrock-server/server.properties
```

设置：

```
texturepack-required=true
```

### 4. 重启服务器

```bash
sudo systemctl restart bedrock
```

## 如果检查失败

查看脚本输出的 ❌ 问题列表，常见问题：

1. **UUID 格式错误** - 检查 manifest.json 中的 `header.uuid`
2. **Manifest 位置错误** - 确保 manifest.json 在第一层，不是嵌套的
3. **包类型错误** - 确保是资源包，不是行为包

## 在代码中使用

```python
from pathlib import Path
from app.addon_manager import AddonManager

manifest_path = Path("/home/ubuntu/bedrock-server/resource_packs/NewGlowingOres/manifest.json")
is_compatible, results = AddonManager.check_manifest_compatibility(manifest_path)

if is_compatible:
    print(f"UUID: {results['uuid']}")
    print(f"配置:\n{results['config_snippet']}")
else:
    for issue in results['issues']:
        print(issue)
```

## 相关文档

- 详细检查指南：`CHECK_MANIFEST.md`
- 安装说明：`INSTALL_GLOWING_ORES.md`

