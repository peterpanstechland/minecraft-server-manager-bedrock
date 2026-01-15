# 连接问题调试指南

## 当前状态

✅ **服务器运行正常**
- 进程ID: 64355
- 端口监听: UDP 19132 (IPv4), UDP6 19133 (IPv6)
- online-mode: false
- allow-list: false

## 可能的问题

### 1. 客户端仍然显示 InitialConnection-44 错误

即使设置了 `online-mode=false`，客户端可能仍然：
- 缓存了旧的连接信息
- 仍然尝试使用Xbox Live认证
- 网络连接问题

### 2. 需要检查的事项

#### A. 客户端操作
1. **完全退出Minecraft客户端**
   - 不要只是关闭窗口，要完全退出应用
   - 重新启动Minecraft

2. **清除客户端缓存**（如果可能）
   - 某些客户端会缓存服务器信息

3. **重新添加服务器**
   - 删除旧的服务器记录
   - 重新添加服务器地址：`192.168.66.118:19132`

#### B. 网络连接
1. **确认客户端能访问服务器IP**
   ```powershell
   # Windows PowerShell
   Test-NetConnection -ComputerName 192.168.66.118 -Port 19132 -Udp
   ```

2. **检查防火墙**
   - 确保客户端防火墙允许Minecraft
   - 确保服务器防火墙允许UDP 19132

#### C. 服务器日志
实时监控连接尝试：
```bash
cd /home/ubuntu/bedrock-manager
./scripts/monitor_connections.sh
```

然后在客户端尝试连接，查看是否有连接尝试记录。

### 3. 可能需要的额外配置

#### 检查server.properties的其他设置
```bash
cat /home/ubuntu/bedrock-server/server.properties | grep -E "(server-name|gamemode|difficulty)"
```

#### 尝试完全重启
```bash
sudo systemctl stop bedrock.service
sleep 5
sudo systemctl start bedrock.service
```

## 调试步骤

### 步骤1：实时监控
在一个终端运行：
```bash
cd /home/ubuntu/bedrock-manager
./scripts/monitor_connections.sh
```

### 步骤2：尝试连接
在客户端尝试连接服务器

### 步骤3：查看日志
检查监控脚本的输出，看是否有：
- 连接尝试
- 错误信息
- 玩家加入/离开

### 步骤4：如果没有任何日志
说明连接请求根本没有到达服务器，可能是：
- 网络问题
- 防火墙阻止
- IP地址错误
- 端口未开放

## 快速测试

### 测试1：检查服务器是否响应
```bash
# 在服务器上
sudo tcpdump -i any -n udp port 19132
```
然后在客户端尝试连接，看是否有UDP包到达。

### 测试2：检查客户端错误
- 客户端显示的具体错误信息是什么？
- 是InitialConnection-44还是其他错误？
- 错误信息中是否有其他线索？

## 如果仍然无法连接

请提供：
1. 客户端显示的具体错误信息
2. 监控脚本的输出（如果有）
3. 客户端和服务器是否在同一网络
4. 服务器是在云上还是本地

