# 立即修复连接问题

## 当前问题
即使设置了 `online-mode=false`，仍然无法连接。

## 可能的原因

### 1. 客户端缓存问题（最可能）

Minecraft客户端可能缓存了旧的连接信息或认证状态。

**解决方案：**
1. **完全退出Minecraft**
   - Windows: 任务管理器中结束所有Minecraft进程
   - 手机: 完全关闭应用（不是最小化）

2. **清除客户端数据**（如果可能）
   - 某些平台可以清除应用数据

3. **重新添加服务器**
   - 删除旧的服务器记录
   - 使用新地址添加：`192.168.66.118:19132`

### 2. 网络连接问题

**测试连接：**
```powershell
# Windows PowerShell
Test-NetConnection -ComputerName 192.168.66.118 -Port 19132 -Udp
```

### 3. 服务器需要完全重启

尝试完全停止并重新启动：
```bash
sudo systemctl stop bedrock.service
sleep 5
sudo systemctl start bedrock.service
```

## 立即尝试的步骤

### 步骤1：在服务器上启动监控
```bash
cd /home/ubuntu/bedrock-manager
./scripts/monitor_connections.sh
```

### 步骤2：在客户端
1. 完全退出Minecraft
2. 重新启动Minecraft
3. 删除旧的服务器记录（如果有）
4. 添加新服务器：`192.168.66.118:19132`
5. 尝试连接

### 步骤3：观察监控输出
- 如果有连接尝试，会显示在监控中
- 如果没有任何输出，说明连接请求没有到达服务器

## 如果仍然无法连接

### 检查客户端错误信息
- 具体显示什么错误？
- 还是InitialConnection-44吗？
- 还是其他错误信息？

### 检查网络
- 客户端和服务器是否在同一网络？
- 如果是云服务器，安全组是否开放了UDP 19132？

### 尝试其他方法
1. 使用服务器的公网IP（如果是云服务器）
2. 检查路由器端口转发
3. 尝试使用IPv6地址

## 重要提示

即使设置了 `online-mode=false`，某些客户端版本可能仍然：
- 尝试使用Xbox Live认证
- 需要额外的配置
- 或者官方服务器不支持完全禁用认证

如果以上都不行，可能需要：
1. 使用不同的Microsoft账号（推荐）
2. 或者使用LAN模式（只能在局域网内）

