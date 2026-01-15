# 修复客户端资源包未加载问题

## 问题分析

你看到的3个资源包（Looky Tool、Inventory Manager、Gravestone）只在**客户端**安装了，但**服务器端**没有。

### 当前服务器上的资源包：
1. ✅ Glowing Ores by javierbendezuv
2. ✅ Multiplayer Waypoint System
3. ✅ chemistry
4. ✅ editor
5. ✅ vanilla

### 缺失的资源包：
- ❌ Looky Tool
- ❌ Inventory Manager (Lite)
- ❌ Gravestone

## 为什么没有加载？

在 Bedrock 服务器中，资源包需要：
1. **服务器端安装** - 放在 `resource_packs/` 目录
2. **世界配置** - 添加到 `world_resource_packs.json`
3. **服务器强制加载** - `texturepack-required=true`

如果只在客户端安装，服务器不会加载这些包。

## 解决方案

### 方案1: 从客户端导出并上传到服务器（推荐）

1. **找到客户端资源包位置**
   - Windows: `%localappdata%\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang\resource_packs\`
   - 或通过游戏内导出

2. **导出资源包**
   - 在游戏内：设置 → 全局资源 → 找到对应包 → 导出
   - 或直接复制文件夹

3. **上传到服务器**
   - 使用 Web 界面上传
   - 或手动复制到 `/home/ubuntu/bedrock-server/resource_packs/`

4. **添加到世界配置**
   - 使用检查脚本获取 UUID
   - 添加到 `world_resource_packs.json`

### 方案2: 从原始来源重新下载

如果这些包来自：
- **CurseForge** - 使用 Web 界面的 CurseForge 安装功能
- **MCPEDL** - 下载后上传
- **Marketplace** - 需要购买/下载后导出

### 方案3: 检查是否已安装但未启用

运行扫描功能：

```bash
# 在 Web 界面点击"扫描已安装"
# 或使用命令行
python3 -c "
from app.addon_manager import AddonManager
count, errors = AddonManager.scan_existing_addons()
print(f'扫描完成，找到 {count} 个资源包')
"
```

## 快速检查脚本

创建一个脚本来检查这些包：

```bash
#!/bin/bash
# 检查特定资源包是否在服务器上

PACKS=("Looky Tool" "Inventory Manager" "Gravestone")

echo "检查资源包..."
for pack in "${PACKS[@]}"; do
    found=false
    for dir in /home/ubuntu/bedrock-server/resource_packs/*/; do
        if [ -f "$dir/manifest.json" ]; then
            name=$(cat "$dir/manifest.json" | python3 -c "import sys, json; print(json.load(sys.stdin).get('header',{}).get('name',''))" 2>/dev/null)
            if echo "$name" | grep -qi "$pack"; then
                echo "✅ 找到: $pack"
                found=true
                break
            fi
        fi
    done
    if [ "$found" = false ]; then
        echo "❌ 未找到: $pack"
    fi
done
```

## 手动添加步骤

如果找到了这些包的文件夹：

1. **检查 manifest.json**
   ```bash
   cat /path/to/pack/manifest.json | python3 -m json.tool
   ```

2. **获取 UUID 和版本**
   ```bash
   python3 scripts/check_manifest_compatibility.py /path/to/pack/manifest.json
   ```

3. **添加到 world_resource_packs.json**
   ```bash
   nano "/home/ubuntu/bedrock-server/worlds/Bedrock level/world_resource_packs.json"
   ```

4. **重启服务器**
   ```bash
   sudo systemctl restart bedrock
   ```

## 注意事项

1. **行为包 vs 资源包**
   - Looky Tool、Inventory Manager、Gravestone 可能是**行为包**，不是资源包
   - 行为包需要放在 `behavior_packs/` 目录
   - 需要添加到 `world_behavior_packs.json`

2. **客户端 vs 服务器**
   - 客户端安装的包只影响本地游戏
   - 服务器需要单独安装才能让所有玩家使用

3. **版本兼容性**
   - 确保服务器和客户端的包版本一致
   - 检查 `min_engine_version` 是否兼容

## 下一步

1. 确认这些包是资源包还是行为包
2. 从客户端导出或重新下载
3. 上传到服务器
4. 添加到相应的配置文件
5. 重启服务器

