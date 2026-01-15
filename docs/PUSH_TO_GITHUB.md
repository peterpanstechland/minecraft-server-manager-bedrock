# 推送到GitHub指南

## 快速推送命令

在项目根目录执行以下命令：

```bash
cd /home/ubuntu/bedrock-manager

# 1. 初始化Git仓库（如果还没有）
git init

# 2. 添加远程仓库
git remote add origin git@github.com:peterpanstechland/minecraft-server-manager-bedrock.git
# 或者如果已经存在，更新URL：
# git remote set-url origin git@github.com:peterpanstechland/minecraft-server-manager-bedrock.git

# 3. 添加所有文件
git add .

# 4. 提交更改
git commit -m "Initial commit: Bedrock Server Manager

- Complete web management interface for Minecraft Bedrock server
- Addon management with CurseForge integration
- Server control (start/stop/restart)
- Player management (invincible mode, kick, commands)
- Real-time log monitoring
- Security features (authentication, CSRF, rate limiting)
- Complete documentation and project structure"

# 5. 推送到GitHub
git branch -M main
git push -u origin main
```

## 或者使用脚本

```bash
chmod +x scripts/push_to_github.sh
./scripts/push_to_github.sh
```

## 注意事项

1. **确保SSH密钥已配置**
   ```bash
   # 测试SSH连接
   ssh -T git@github.com
   ```

2. **如果仓库已存在且有内容**
   ```bash
   # 先拉取远程内容
   git pull origin main --allow-unrelated-histories
   # 然后再推送
   git push -u origin main
   ```

3. **如果遇到权限问题**
   - 确保GitHub账户有权限访问该仓库
   - 检查SSH密钥是否正确配置

4. **.gitignore已配置**
   - 不会提交敏感文件（.env、数据库、日志等）
   - 不会提交虚拟环境（venv/）

## 推送后的操作

推送成功后，可以：
- 在GitHub上查看代码
- 设置GitHub Actions进行CI/CD
- 添加README徽章
- 设置项目描述和标签
