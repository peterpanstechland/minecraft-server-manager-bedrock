# 修复客户端闪退问题

## 问题分析

客户端进入地图时闪退，可能的原因：

### 1. 行为包脚本错误 ⚠️
服务器日志显示：
```
[Scripting] Plugin [[BP] Instant Structures v7 1.21+ BONY162 - 1.0.0] - [main.js] could not load main.
```

### 2. 客户端资源包与服务器冲突
你客户端有3个资源包：
- Looky Tool
- Inventory Manager (Lite)  
- Gravestone

这些包在服务器上**没有安装**，可能导致：
- 客户端尝试加载服务器不存在的资源
- 资源包版本不匹配
- 客户端和服务器资源冲突

### 3. 资源包/行为包过多
服务器已加载：
- 5个资源包
- 15个行为包

过多的包可能导致客户端内存不足或冲突。

## 立即解决方案

### 方案1: 禁用有问题的行为包（推荐）

```bash
# 1. 禁用 Instant Structures 行为包
# 在 Web 界面找到 "[BP] Instant Structures v7 1.21+ BONY162"
# 点击"禁用"

# 或手动编辑 world_behavior_packs.json
nano "/home/ubuntu/bedrock-server/worlds/Bedrock level/world_behavior_packs.json"
# 删除或注释掉 Instant Structures 的配置

# 2. 重启服务器
sudo systemctl restart bedrock
```

### 方案2: 禁用客户端资源包

在客户端：
1. 打开 Minecraft → 设置 → 全局资源
2. **临时禁用**这三个包：
   - Looky Tool
   - Inventory Manager (Lite)
   - Gravestone
3. 重新尝试连接服务器

### 方案3: 检查并修复 Instant Structures 包

```bash
# 检查包文件
ls -la /home/ubuntu/bedrock-server/behavior_packs/_BP_Instant_Structures_v7_1_21_BONY162/

# 检查是否有 main.js
find /home/ubuntu/bedrock-server/behavior_packs/_BP_Instant_Structures_v7_1_21_BONY162/ -name "main.js"

# 如果文件损坏，可能需要重新安装
```

## 诊断步骤

### 1. 检查服务器日志中的错误

```bash
# 查看最近的错误
tail -200 /home/ubuntu/bedrock-server/Dedicated_Server.txt | grep -iE "error|crash|exception|player.*disconnect|kick"
```

### 2. 检查客户端资源包冲突

客户端资源包可能与服务器资源包冲突：
- 服务器有：Glowing Ores, Waypoint System 等
- 客户端有：Looky Tool, Inventory Manager, Gravestone

**建议**：先禁用客户端资源包，测试是否能正常进入。

### 3. 逐步启用包

如果禁用客户端资源包后能正常进入：

1. **逐个启用客户端资源包**，找出导致崩溃的包
2. **检查包版本**，确保与服务器兼容
3. **在服务器上安装对应的包**（如果需要）

## 常见闪退原因

### 1. 内存不足
- 客户端：关闭其他应用，增加内存
- 服务器：检查内存使用 `free -h`

### 2. 包版本不兼容
- 确保所有包与 Minecraft 版本兼容
- 检查 `min_engine_version` 字段

### 3. 包冲突
- 多个包修改相同的资源
- 客户端和服务器包不一致

### 4. 脚本错误
- 行为包的 JavaScript 文件错误
- 服务器无法加载脚本

## 快速修复清单

- [ ] 禁用 Instant Structures 行为包
- [ ] 禁用客户端全局资源包（临时）
- [ ] 重启服务器
- [ ] 尝试连接
- [ ] 如果成功，逐个启用包找出问题
- [ ] 检查服务器日志是否有新错误

## 如果问题持续

1. **收集信息**：
   - 客户端 Minecraft 版本
   - 闪退时的具体错误（如果有）
   - 服务器日志中的相关错误

2. **尝试最小配置**：
   - 禁用所有非必需的行为包
   - 禁用所有客户端资源包
   - 只保留服务器必需的基础包

3. **逐步添加**：
   - 每次只启用一个包
   - 测试是否能正常进入
   - 找出导致问题的包

## 预防措施

1. **统一资源包**：
   - 在服务器上安装所有需要的资源包
   - 使用 `texturepack-required=true` 强制加载
   - 避免客户端单独安装资源包

2. **测试新包**：
   - 新包先在测试环境测试
   - 检查日志是否有错误
   - 确认兼容性后再启用

3. **定期检查**：
   - 检查服务器日志
   - 监控错误和警告
   - 及时修复问题

