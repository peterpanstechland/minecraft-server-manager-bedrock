# GitHub SSH密钥配置指南

## 问题
`git@github.com: Permission denied (publickey)` 表示SSH密钥未配置或未添加到GitHub。

## 解决方案

### 方法1：生成新的SSH密钥（推荐）

```bash
# 1. 生成SSH密钥（使用你的GitHub邮箱）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 按Enter使用默认路径 (~/.ssh/id_ed25519)
# 设置密码（可选，但推荐）

# 2. 启动ssh-agent
eval "$(ssh-agent -s)"

# 3. 添加SSH密钥到ssh-agent
ssh-add ~/.ssh/id_ed25519

# 4. 复制公钥内容
cat ~/.ssh/id_ed25519.pub

# 5. 将公钥添加到GitHub
# - 访问 https://github.com/settings/keys
# - 点击 "New SSH key"
# - 粘贴公钥内容
# - 点击 "Add SSH key"

# 6. 测试连接
ssh -T git@github.com
```

### 方法2：使用HTTPS方式推送（无需SSH密钥）

如果不想配置SSH密钥，可以使用HTTPS方式：

```bash
# 1. 更改远程仓库URL为HTTPS
git remote set-url origin https://github.com/peterpanstechland/minecraft-server-manager-bedrock.git

# 2. 推送时输入GitHub用户名和Personal Access Token（不是密码）
git push -u origin main
```

**获取Personal Access Token：**
- 访问 https://github.com/settings/tokens
- 点击 "Generate new token (classic)"
- 选择权限：至少需要 `repo` 权限
- 复制生成的token（只显示一次）

### 方法3：检查现有密钥

```bash
# 检查是否有现有密钥
ls -la ~/.ssh/

# 如果有 id_rsa.pub 或 id_ed25519.pub，显示公钥
cat ~/.ssh/id_rsa.pub
# 或
cat ~/.ssh/id_ed25519.pub

# 然后将公钥添加到GitHub（步骤同方法1的步骤5）
```

## 快速脚本

已创建自动化脚本 `scripts/setup_ssh_key.sh`，可以自动完成配置。
