# 安全配置指南

## 凭证管理最佳实践

### 1. 环境变量配置（推荐）

**永远不要**在代码中硬编码密码、密钥或敏感信息！

#### 使用 .env 文件

1. 复制 `.env.example` 为 `.env`：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入实际值：
```bash
nano .env
```

3. 确保 `.env` 文件已被 `.gitignore` 排除（已配置）

4. 加载环境变量：
```bash
# 使用 python-dotenv 自动加载（已在代码中配置）
source .env  # 或者手动加载
```

#### 系统环境变量（更安全）

在 `/etc/environment` 或用户 `~/.bashrc` 中设置：
```bash
export SECRET_KEY="your-secret-key"
export CURSEFORGE_API_KEY="your-api-key"
```

### 2. Sudo权限管理（避免密码）

**最佳实践：配置sudoers，让应用用户无需密码执行特定命令**

#### 方法1：配置sudoers（推荐）

1. 编辑sudoers配置：
```bash
sudo visudo
```

2. 添加以下配置（允许ubuntu用户无需密码执行特定命令）：
```
# Bedrock Manager - 允许启动/停止服务器
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl start bedrock-server
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl stop bedrock-server
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart bedrock-server
```

3. 或者更细粒度（只允许特定脚本）：
```
ubuntu ALL=(ALL) NOPASSWD: /home/ubuntu/bedrock-manager/scripts/start-server.sh
ubuntu ALL=(ALL) NOPASSWD: /home/ubuntu/bedrock-manager/scripts/stop-server.sh
```

#### 方法2：使用SSH密钥（推荐用于远程操作）

1. 生成SSH密钥对：
```bash
ssh-keygen -t ed25519 -C "bedrock-manager"
```

2. 将公钥添加到authorized_keys：
```bash
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

3. 使用SSH密钥认证，无需密码

#### 方法3：使用systemd服务（推荐用于生产环境）

创建systemd服务文件，以特定用户运行，避免需要sudo：

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

### 3. 文件权限

确保敏感文件权限正确：
```bash
# .env文件只有所有者可读
chmod 600 .env

# 配置文件
chmod 644 config.py

# 脚本文件
chmod 755 *.sh
```

### 4. Git安全

#### 检查是否已提交敏感信息

```bash
# 检查Git历史中是否有敏感信息
git log --all --full-history --source -- "*password*" "*secret*" "*key*"
```

#### 如果已提交敏感信息，需要清理

1. 使用git-filter-repo清理历史：
```bash
pip install git-filter-repo
git filter-repo --invert-paths --path sensitive-file.txt
```

2. 强制推送（谨慎操作）：
```bash
git push origin --force --all
```

### 5. 生产环境检查清单

- [ ] `.env` 文件已创建且包含所有必需配置
- [ ] `.env` 文件权限为 600（仅所有者可读）
- [ ] `.env` 已在 `.gitignore` 中
- [ ] `SECRET_KEY` 已更改为强随机字符串
- [ ] 所有API密钥已配置
- [ ] sudoers已配置（如需要）
- [ ] 防火墙已配置
- [ ] 使用HTTPS（生产环境）
- [ ] 定期更新依赖包
- [ ] 启用日志审计

### 6. 生成安全的SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 7. 定期安全审计

```bash
# 检查是否有硬编码的敏感信息
grep -r "password\|secret\|key" --include="*.py" --include="*.sh" | grep -v ".env" | grep -v ".git"
```

## 常见错误

❌ **不要这样做：**
- 在代码中硬编码密码
- 将 `.env` 文件提交到Git
- 在GitHub Issues或PR中分享密钥
- 使用弱密码或默认密码

✅ **应该这样做：**
- 使用环境变量
- 使用 `.env.example` 作为模板
- 配置sudoers避免需要密码
- 使用强随机密钥
- 定期轮换密钥

