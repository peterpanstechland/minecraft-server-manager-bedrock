# LAN模式 vs 在线服务器模式 - 同账号多设备登录

## 为什么LAN模式可以，服务器模式不行？

### LAN模式（本地世界）
- ✅ **允许同一账号多设备登录**
- 原因：LAN模式设计用于家庭/局域网，Minecraft允许同一账号在局域网内多设备同时登录
- 限制：只能在局域网内使用，无法从外部网络连接

### 在线服务器模式（online-mode=true）
- ❌ **不允许同一账号多设备登录**
- 原因：Xbox Live认证系统限制，同一Microsoft账号不能同时在多台设备上在线
- 这是Xbox Live的安全机制，防止账号共享和滥用

## 解决方案

### 方案1：设置 online-mode=false（实验性）

**警告：这会降低安全性，仅用于测试**

```bash
# 编辑server.properties
nano /home/ubuntu/bedrock-server/server.properties

# 修改：
online-mode=false

# 保存后重启服务器
sudo systemctl restart bedrock.service
```

**效果：**
- 可能允许同一账号多设备登录（类似LAN模式）
- 但会失去Xbox Live认证保护
- 安全性降低，任何人都可以连接（除非使用白名单）

**风险：**
- ⚠️ 安全性降低
- ⚠️ 可能违反Minecraft服务条款
- ⚠️ 无法使用Xbox Live功能（成就、好友等）

### 方案2：使用不同的Microsoft账号（推荐）

为每台设备使用不同的账号：
- 电脑：账号A
- 手机：账号B

**优点：**
- ✅ 完全支持，无限制
- ✅ 安全性高
- ✅ 符合官方建议

### 方案3：使用白名单 + online-mode=false

如果必须使用同一账号，可以：
1. 设置 `online-mode=false`
2. 启用白名单 `allow-list=true`
3. 在 `whitelist.json` 中添加允许的玩家

这样可以：
- 允许同账号多设备登录
- 限制只有白名单中的玩家可以连接
- 但仍有安全风险

## 当前配置

您的服务器：
- `online-mode=true` - 要求Xbox Live认证（限制同账号多设备）
- `enable-lan-visibility=true` - 启用LAN可见性（但这是服务器发现，不是LAN模式）

## 重要区别

**LAN模式** = 在一台设备上创建本地世界，其他设备通过局域网加入
- 这是客户端功能，不是服务器配置
- 服务器无法完全模拟LAN模式的行为

**服务器模式** = 专用服务器，支持远程连接
- `online-mode=true` = 需要Xbox Live认证（限制同账号）
- `online-mode=false` = 不需要认证（可能允许同账号，但安全性低）

## 建议

如果您确实需要同账号多设备登录：

1. **短期测试**：可以尝试设置 `online-mode=false` 看看是否有效
2. **长期使用**：建议使用不同的Microsoft账号（最安全可靠）
3. **如果必须同账号**：考虑使用LAN模式（但只能在局域网内）

## 如何测试

1. 备份当前配置：
```bash
cp /home/ubuntu/bedrock-server/server.properties /home/ubuntu/bedrock-server/server.properties.backup
```

2. 修改配置：
```bash
sed -i 's/online-mode=true/online-mode=false/' /home/ubuntu/bedrock-server/server.properties
```

3. 重启服务器：
```bash
sudo systemctl restart bedrock.service
```

4. 测试连接：
- 尝试用两个设备（同一账号）连接
- 如果成功，说明配置有效
- 如果失败，恢复配置：`cp server.properties.backup server.properties`

5. 恢复配置（如果需要）：
```bash
cp /home/ubuntu/bedrock-server/server.properties.backup /home/ubuntu/bedrock-server/server.properties
sudo systemctl restart bedrock.service
```

