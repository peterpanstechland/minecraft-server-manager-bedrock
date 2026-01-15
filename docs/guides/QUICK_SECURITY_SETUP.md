# 快速安全配置指南

## 🚀 5分钟快速配置

### 1. 创建环境变量文件

```bash
cd /home/ubuntu/bedrock-manager
cp .env.example .env
nano .env  # 编辑并填入实际值
chmod 600 .env  # 设置权限，只有所有者可读
```

### 2. 生成安全的SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

将输出复制到 `.env` 文件的 `SECRET_KEY=` 后面。

### 3. 避免需要sudo密码（推荐方法）

#### 方法A：配置sudoers（如果确实需要sudo）

```bash
sudo visudo
```

添加以下行：
```
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl start bedrock-server
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl stop bedrock-server
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart bedrock-server
```

或者使用提供的脚本：
```bash
sudo ./scripts/setup-sudoers.sh
```

#### 方法B：使用systemd服务（最佳实践）

创建systemd服务，以特定用户运行，完全避免需要sudo：

```bash
sudo nano /etc/systemd/system/bedrock-manager.service
```

内容：
```ini
[Unit]
Description=Bedrock Server Manager
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bedrock-manager
Environment="PATH=/home/ubuntu/bedrock-manager/venv/bin"
ExecStart=/home/ubuntu/bedrock-manager/venv/bin/python3 run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动：
```bash
sudo systemctl daemon-reload
sudo systemctl enable bedrock-manager
sudo systemctl start bedrock-manager
```

### 4. 验证配置

```bash
# 检查.env文件权限
ls -la .env  # 应该显示 -rw------- (600)

# 检查是否在Git中
git status .env  # 应该显示 "nothing to commit"

# 测试环境变量加载
python3 -c "from config import Config; print('SECRET_KEY loaded:', Config.SECRET_KEY[:20] + '...')"
```

## ✅ 安全检查清单

- [ ] `.env` 文件已创建
- [ ] `.env` 文件权限为 600
- [ ] `SECRET_KEY` 已更改为强随机字符串
- [ ] `.env` 不在Git中（`git status` 不显示）
- [ ] 已配置sudoers或systemd服务（如需要）
- [ ] 所有API密钥已配置

## 🔒 重要提醒

1. **永远不要**：
   - 在代码中硬编码密码
   - 将 `.env` 文件提交到Git
   - 在公开场合分享密钥

2. **应该做**：
   - 使用环境变量
   - 定期轮换密钥
   - 使用强密码
   - 配置sudoers避免需要密码

## 📚 更多信息

查看 `SECURITY.md` 了解详细的安全配置指南。

