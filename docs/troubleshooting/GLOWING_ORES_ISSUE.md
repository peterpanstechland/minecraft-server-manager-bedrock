# 发光矿石材质包问题诊断

## 问题现状
矿石在游戏中没有显示发光效果

## 已完成的配置 ✅

1. **服务器配置**
   - `texturepack-required=true` ✅
   - 材质包已在 `world_resource_packs.json` 中配置 ✅
   - 材质包顺序已调整到第一位 ✅
   - 目录权限已修复为 755 ✅

2. **材质包信息**
   - 名称: Glowing Ores by javierbendezuv
   - UUID: c71c3fa1-2d92-4d7d-9e6d-2f3f4f0c6abc
   - 最小引擎版本: 1.21.70
   - Capabilities: **PBR** (关键！)

## 问题根源 ⚠️

这个材质包使用 **PBR (Physically Based Rendering)** 技术实现发光效果：

```json
{
  "format_version": "1.16.100",
  "minecraft:texture_set": {
    "color": "copper_ore",
    "metalness_emissive_roughness": "copper_ore_glow"  ← 发光贴图
  }
}
```

**PBR发光效果需要以下条件：**

### 1. 客户端版本要求
- Minecraft Bedrock 版本 >= **1.21.70**
- 如果客户端版本低于此版本，材质包不会加载或不显示效果

### 2. 客户端渲染设置
PBR材质包需要启用**高级渲染功能**：

#### Windows 10/11版本：
- 设置 → 视频 → 渲染龙（Render Dragon）已启用
- 不需要RTX显卡，但需要支持PBR的客户端

#### 其他平台：
- 部分平台可能不支持PBR渲染
- 移动设备可能需要特定设置

### 3. 显卡/性能要求
- PBR渲染对显卡有一定要求
- 低端设备可能自动禁用PBR效果

## 解决方案

### 方案1: 验证客户端版本和设置（推荐）

1. **检查客户端版本**
   - 进入游戏设置 → 关于
   - 确认版本号 >= 1.21.70

2. **检查渲染设置**
   - Windows: 设置 → 视频 → 确认渲染龙已启用
   - 图形质量设置为"高"或"超高"

3. **重新连接服务器**
   - 完全退出Minecraft（不要只是断开连接）
   - 重新启动游戏
   - 重新连接服务器
   - 等待材质包下载完成（会显示"Downloading Resource Packs..."）

### 方案2: 使用非PBR发光矿石材质包

如果客户端不支持PBR或版本过低，可以使用传统的发光矿石材质包（不依赖PBR）：

**推荐的替代材质包：**
- Better Ores (传统发光效果)
- Glowing Ores Lite (不使用PBR)
- Simple Glowing Ores (兼容旧版本)

### 方案3: 修改现有材质包（高级）

移除PBR依赖，使用传统的发光效果（需要手动编辑）：

1. 移除 `manifest.json` 中的 `capabilities: ["pbr"]`
2. 删除所有 `.texture_set.json` 文件
3. 将 `*_glow.png` 文件与基础纹理合并（使用alpha通道实现发光）

**注意：** 这种方法需要专业的材质包制作知识

## 快速测试步骤

### 测试1: 验证材质包已下载
1. 连接服务器时观察是否显示 "Downloading Resource Packs..."
2. 如果没有显示，说明客户端没有下载材质包

### 测试2: 检查客户端材质包
1. 进入游戏设置 → 全局资源
2. 查看是否有 "Glowing Ores by javierbendezuv"
3. 确认状态为"活动"

### 测试3: 验证PBR支持
1. 在游戏中按 F3 或查看调试信息
2. 查找渲染器信息
3. 确认是否显示 "Render Dragon" 或 PBR 相关信息

## 当前服务器状态

```bash
# 材质包位置
/home/ubuntu/bedrock-server/resource_packs/Glowing_Ores_by_javierbendezuv/

# 配置文件
world_resource_packs.json: ✅ 已配置，顺序第一
server.properties: ✅ texturepack-required=true

# 权限
755 (所有人可读可执行) ✅
```

## 下一步建议

1. **首先确认客户端版本**
   - 如果 < 1.21.70，升级客户端或更换材质包

2. **检查渲染设置**
   - 确保启用了高级渲染功能

3. **尝试其他玩家**
   - 让其他玩家连接测试
   - 确认是否所有玩家都看不到效果

4. **查看客户端日志**
   - Windows: `%localappdata%\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\logs\`
   - 查找材质包加载相关的错误

## 联系信息

如果问题仍未解决，请提供：
1. 客户端 Minecraft 版本号
2. 操作系统和显卡型号
3. 连接服务器时是否看到材质包下载提示
4. 游戏设置中的渲染器类型

