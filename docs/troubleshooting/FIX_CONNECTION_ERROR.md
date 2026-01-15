# 修复 InitialConnection-44 错误

## 问题诊断

根据检查，您的服务器：
- ✅ 正在运行
- ✅ 端口19132和19133已监听
- ✅ 版本匹配（1.21.131）
- ⚠️ 服务器IP: 192.168.66.118

## 最可能的原因

### 1. 云服务器安全组未开放端口（最可能）

如果服务器在云上（AWS、Azure、阿里云等），需要：
1. 登录云控制台
2. 找到安全组/防火墙规则
3. 添加入站规则：
   - 协议: UDP
   - 端口: 19132
   - 源: 0.0.0.0/0（或您的IP）

### 2. 本地网络路由器配置

如果服务器在本地网络：
1. 检查路由器端口转发
2. 确保UDP 19132端口已转发到服务器IP

### 3. 客户端连接地址

**确保使用正确的连接地址：**
- 如果从同一网络连接：使用 `192.168.66.118:19132`
- 如果从外部连接：使用公网IP地址

### 4. 尝试的解决方案

#### 方案A：检查并开放防火墙（如果使用云服务器）

```bash
# 如果使用ufw
sudo ufw allow 19132/udp
sudo ufw allow 19133/udp

# 如果使用iptables
sudo iptables -A INPUT -p udp --dport 19132 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 19133 -j ACCEPT
```

#### 方案B：临时测试（关闭online-mode）

**注意：这会降低安全性，仅用于测试**

```bash
# 编辑server.properties
nano /home/ubuntu/bedrock-server/server.properties

# 修改：
online-mode=false

# 重启服务器
sudo systemctl restart bedrock.service
```

如果这样可以连接，说明是Xbox Live认证问题。

#### 方案C：检查客户端网络

1. 确保客户端网络正常
2. 尝试ping服务器IP
3. 检查是否有VPN或代理影响连接

## 快速测试步骤

1. **测试端口连通性**（在客户端）：
   ```powershell
   # Windows PowerShell
   Test-NetConnection -ComputerName 192.168.66.118 -Port 19132 -Udp
   ```

2. **检查服务器日志**：
   ```bash
   tail -f /home/ubuntu/bedrock-server/Dedicated_Server.txt
   ```
   然后尝试连接，查看是否有新的错误信息

3. **重启服务器**：
   ```bash
   sudo systemctl restart bedrock.service
   ```

## 常见解决方案优先级

1. **检查云服务器安全组**（如果是云服务器）- 90%的问题在这里
2. **检查防火墙规则** - 确保UDP端口开放
3. **检查网络连接** - 确保客户端能访问服务器IP
4. **检查版本匹配** - 确保客户端和服务器版本一致
5. **检查Xbox Live登录** - 确保客户端已登录Microsoft账号

## 需要更多帮助？

如果以上都不行，请提供：
1. 服务器是在云上还是本地？
2. 客户端和服务器是否在同一网络？
3. 尝试连接时的具体错误信息
4. 服务器日志中的相关错误

