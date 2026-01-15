# Bedrock Manager - 安全改进完成报告

## 改进概述

本次安全改进针对Bedrock Manager的所有高危和中危安全漏洞进行了全面修复。

---

## ✅ 已完成的安全改进

### 1. 认证和授权系统 ✅

**问题：** 无任何鉴权保护，所有管理接口可被任意访问

**解决方案：**
- 添加 `Flask-Login` 用户认证系统
- 创建 `User` 模型，支持密码哈希存储
- 实现登录/登出功能
- 所有管理API添加 `@login_required_api` 装饰器
- 所有页面路由添加 `@login_required` 装饰器

**相关文件：**
- `app/models.py` - 添加User模型
- `app/auth.py` - 认证装饰器
- `app/routes.py` - 所有路由添加认证
- `templates/login.html` - 登录页面

### 2. Zip Slip漏洞修复 ✅

**问题：** 使用 `zipfile.extractall()` 直接解压，存在目录穿越风险

**解决方案：**
- 创建 `safe_extract_zip()` 函数，安全解压ZIP文件
- 验证每个文件路径，阻止 `../` 和绝对路径
- 检查解压后总大小限制
- 替换所有 `extractall()` 调用（3处）

**相关文件：**
- `app/security.py` - `safe_extract_zip()` 函数
- `app/addon_manager.py` - 3处修复
- `scripts/install_marketplace_packs.py` - 修复

### 3. 文件上传验证 ✅

**问题：** 文件上传缺乏充分验证

**解决方案：**
- 文件名清理：`sanitize_filename()` 移除危险字符
- 扩展名验证：`validate_file_extension()`
- 文件大小检查：`check_file_size()`
- 路径验证：`validate_path()` 防止路径穿越
- 使用UUID生成临时文件名

**相关文件：**
- `app/security.py` - 验证函数
- `app/routes.py` - upload_addon路由

### 4. CSRF保护 ✅

**问题：** 无CSRF保护，易受跨站请求伪造攻击

**解决方案：**
- 添加 `Flask-WTF` 的CSRFProtect
- 所有POST/PUT/DELETE请求自动验证CSRF token
- 登录表单包含CSRF token

**相关文件：**
- `app/__init__.py` - 初始化CSRFProtect
- `config.py` - CSRF配置
- `templates/login.html` - CSRF token

### 5. 速率限制 ✅

**问题：** 无速率限制，易受暴力破解和DoS攻击

**解决方案：**
- 添加 `Flask-Limiter`
- 全局限制：200/天，50/小时
- 登录：5次/分钟
- 上传：10次/小时
- 服务器控制：10次/小时
- 批量操作：5次/小时

**相关文件：**
- `app/__init__.py` - 初始化Limiter
- `app/routes.py` - 各路由添加限制

### 6. 错误处理改进 ✅

**问题：** 错误信息暴露内部实现细节

**解决方案：**
- 统一错误处理，不暴露traceback
- 使用通用错误消息
- 添加日志记录（不返回给客户端）
- 404/429/500错误处理器

**相关文件：**
- `app/__init__.py` - 错误处理器
- `app/routes.py` - 移除详细错误信息

### 7. 输入验证和清理 ✅

**问题：** 用户输入未经充分验证

**解决方案：**
- UUID验证：`validate_uuid()`
- 包类型验证：`validate_pack_type()`
- URL验证：`validate_url()`
- HTML清理：`sanitize_html()` 防止XSS
- 路径验证：防止目录穿越

**相关文件：**
- `app/security.py` - 验证函数

### 8. 其他安全改进 ✅

- **Session安全：** HttpOnly, SameSite=Lax cookies
- **密码存储：** 使用Werkzeug的密码哈希
- **SECRET_KEY：** 强制使用强随机密钥
- **依赖更新：** 添加安全相关包

---

## 📦 新增依赖

```
Flask-Login==0.6.3      # 用户认证
Flask-WTF==1.2.1        # CSRF保护
Flask-Limiter==3.5.0    # 速率限制
bleach==6.1.0           # HTML清理
```

---

## 🔧 配置要求

### 环境变量（.env文件）

```bash
# 必需 - 生产环境强密钥
SECRET_KEY=your-strong-random-key-here

# 必需 - 管理员账号
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# 可选
BEDROCK_SERVER_DIR=/home/ubuntu/bedrock-server
CURSEFORGE_API_KEY=your-api-key
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```

### 生成SECRET_KEY

```bash
python3 -c "import os; print(os.urandom(24).hex())"
```

---

## 📝 使用说明

### 首次设置

1. **安装依赖：**
```bash
cd /home/ubuntu/bedrock-manager
source venv/bin/activate
pip install -r requirements.txt
```

2. **配置环境变量：**
```bash
cp .env.example .env
nano .env  # 编辑并设置SECRET_KEY和ADMIN_PASSWORD
```

3. **启动服务：**
```bash
python3 run.py
```

4. **首次登录：**
- 访问：http://your-server:5000/login
- 用户名：admin（或您设置的ADMIN_USERNAME）
- 密码：您在.env中设置的ADMIN_PASSWORD

### 数据库迁移

首次运行时会自动创建：
- `User` 表（存储用户信息）
- 默认管理员账号（如果设置了ADMIN_PASSWORD）

---

## 🔒 安全最佳实践

### 生产环境部署

1. **使用HTTPS：**
```python
# config.py
SESSION_COOKIE_SECURE = True  # 仅在HTTPS下传输cookie
```

2. **反向代理（Nginx）：**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. **限制网络访问：**
```bash
# 仅允许特定IP访问
sudo ufw allow from YOUR_IP to any port 5000
```

4. **定期更新：**
```bash
pip list --outdated
pip install --upgrade flask flask-login flask-wtf
```

### 密码策略

- 最小长度：12字符
- 包含大小写字母、数字、特殊字符
- 定期更换（建议90天）
- 不使用常见密码

---

## 🧪 测试建议

### 安全测试

1. **未授权访问测试：**
```bash
# 应返回401
curl http://localhost:5000/api/addons
```

2. **CSRF测试：**
```bash
# 无CSRF token应被拒绝
curl -X POST http://localhost:5000/api/server/start
```

3. **速率限制测试：**
```bash
# 快速请求应触发429
for i in {1..10}; do curl http://localhost:5000/login; done
```

4. **Zip Slip测试：**
- 创建包含 `../../../etc/passwd` 的恶意ZIP
- 上传应被拒绝

---

## 📊 安全改进对比

| 项目 | 改进前 | 改进后 |
|------|--------|--------|
| 认证保护 | ❌ 无 | ✅ Flask-Login |
| Zip Slip防护 | ❌ 高危 | ✅ 已修复 |
| 文件上传验证 | ⚠️ 基础 | ✅ 全面验证 |
| CSRF保护 | ❌ 无 | ✅ 全局启用 |
| 速率限制 | ❌ 无 | ✅ 多层限制 |
| 错误信息泄露 | ⚠️ 详细 | ✅ 通用消息 |
| 输入验证 | ⚠️ 部分 | ✅ 全面验证 |
| Session安全 | ⚠️ 基础 | ✅ 安全配置 |

---

## 🚨 已知限制

1. **单用户系统：** 当前仅支持单个管理员账号
2. **内存存储：** Rate Limiter使用内存存储（重启后重置）
3. **Session存储：** 使用Flask默认session（考虑Redis）

## 🔮 未来改进建议

1. **多用户支持：** 添加用户管理和角色权限
2. **审计日志：** 记录所有管理操作
3. **两步验证：** TOTP或其他2FA方案
4. **API密钥：** 支持API token认证
5. **Redis集成：** 用于session和rate limiting
6. **WAF规则：** 添加ModSecurity规则

---

## 📞 安全问题报告

如发现安全问题，请：
1. 不要公开披露
2. 通过私密渠道联系维护者
3. 提供详细的复现步骤

---

**版本：** 2.0-security
**更新日期：** 2026-01-15
**状态：** ✅ 生产就绪
