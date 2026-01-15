# Bedrock服务器连接错误排查指南

## 错误信息
- **错误代码**: `InitialConnection-44`
- **错误详情**: `GC-10.0.26200.7462`
- **客户端版本**: 1.21.131-Windows GDK Build
- **服务器版本**: 1.21.131.1

## 当前服务器状态
✅ **服务器正在运行**
- 进程ID: 45695
- 端口监听: UDP 19132 (IPv4), UDP6 19133 (IPv6)
- 服务状态: Active (running)

## 可能的原因和解决方案

### 1. 网络连接问题

**检查项：**
- 确保客户端和服务器在同一网络，或服务器IP地址可访问
- 检查防火墙是否阻止了UDP端口19132和19133

**解决方案：**
```bash
# 检查服务器IP地址
hostname -I

# 检查端口是否开放（在服务器上）
sudo ufw allow 19132/udp
sudo ufw allow 19133/udp

# 如果使用云服务器，检查安全组规则
# 确保UDP 19132和19133端口已开放
```

### 2. 版本不匹配

**当前状态：**
- 服务器版本: 1.21.131.1
- 客户端版本: 1.21.131

**解决方案：**
- 确保客户端和服务器版本完全匹配
- 如果版本不匹配，更新客户端或服务器到相同版本

### 3. 服务器配置问题

**检查server.properties：**
```bash
cat /home/ubuntu/bedrock-server/server.properties | grep -E "(online-mode|max-players|server-port)"
```

**关键配置：**
- `online-mode=true` - 要求Xbox Live认证
- `server-port=19132` - 服务器端口
- `max-players=10` - 最大玩家数

### 4. Xbox Live认证问题

如果使用 `online-mode=true`：
- 确保客户端已登录Microsoft账号
- 确保账号有权限访问服务器
- 检查账号是否被阻止

### 5. 防火墙/路由器配置

**如果从外部网络连接：**
1. 检查路由器端口转发（UDP 19132）
2. 检查云服务器安全组规则
3. 确保防火墙允许UDP流量

**测试连接：**
```bash
# 在客户端使用telnet或nc测试端口
# Windows PowerShell:
Test-NetConnection -ComputerName <服务器IP> -Port 19132 -Udp

# Linux/Mac:
nc -u -v <服务器IP> 19132
```

### 6. 服务器资源问题

**检查服务器资源：**
```bash
# 检查CPU和内存使用
top -p 45695

# 检查磁盘空间
df -h
```

### 7. 尝试重启服务器

如果以上都正常，尝试重启服务器：
```bash
sudo systemctl restart bedrock.service
```

## 快速检查清单

- [ ] 服务器正在运行
- [ ] 端口19132和19133已监听
- [ ] 客户端和服务器版本匹配
- [ ] 防火墙规则已配置
- [ ] 网络连接正常
- [ ] Xbox Live账号已登录
- [ ] 服务器资源充足

## 详细日志查看

```bash
# 查看服务器日志
tail -f /home/ubuntu/bedrock-server/Dedicated_Server.txt

# 查看systemd日志
sudo journalctl -u bedrock.service -f
```

## 常见错误代码

- **InitialConnection-44**: 初始连接失败，通常是网络或配置问题
- **GC-10.0.26200.7462**: 游戏客户端版本标识

## 联系支持

如果问题持续存在：
1. 收集服务器日志
2. 收集客户端错误截图
3. 记录服务器和客户端版本信息
4. 检查网络配置

