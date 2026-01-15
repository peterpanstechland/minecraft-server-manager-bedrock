# Bedrock Manager - 快速开始指南

## 🚀 安全版本快速设置

### 1. 安装依赖

```bash
cd /home/ubuntu/bedrock-manager
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 运行安全设置向导

```bash
./setup_security.sh
```

向导会引导你：
- 生成强随机SECRET_KEY
- 设置管理员账号和密码
- 配置Bedrock服务器路径
- 配置Web服务器端口

### 3. 启动服务

```bash
python3 run.py
```

### 4. 访问管理界面

```
http://your-server-ip:5000/login
```

使用设置向导中创建的管理员账号登录。

---

## 📋 主要改进

✅ **认证系统** - 所有管理功能需要登录
✅ **Zip Slip修复** - 防止目录穿越攻击  
✅ **文件上传验证** - 全面的文件安全检查
✅ **CSRF保护** - 防止跨站请求伪造
✅ **速率限制** - 防止暴力破解和DoS
✅ **错误处理** - 不泄露内部信息
✅ **输入验证** - 防止注入攻击

详见：`SECURITY_IMPROVEMENTS.md`

---

## 🔧 手动配置（如果不使用向导）

### 生成SECRET_KEY

```bash
python3 -c "import os; print(os.urandom(24).hex())"
```

### 创建.env文件

```bash
cp .env.example .env
nano .env
```

填写：
- SECRET_KEY（上面生成的）
- ADMIN_USERNAME
- ADMIN_PASSWORD

### 创建管理员

```bash
python3 create_admin.py
```

---

## 🔒 生产环境注意事项

### 1. 使用HTTPS

```nginx
# Nginx配置示例
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 限制网络访问

```bash
# 仅允许特定IP
sudo ufw allow from YOUR_IP to any port 5000

# 或使用VPN/SSH隧道
```

### 3. 定期备份

```bash
# 备份数据库
cp database/bedrock_manager.db database/bedrock_manager.db.backup

# 备份.env
cp .env .env.backup
```

---

## 📞 需要帮助？

查看完整文档：`SECURITY_IMPROVEMENTS.md`
