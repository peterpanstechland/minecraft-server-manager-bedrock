# 快速开始指南

## 1. 安装依赖

运行安装脚本：
```bash
cd bedrock-manager
./install.sh
```

或者手动安装：
```bash
pip3 install -r requirements.txt
```

## 2. 配置（可选）

如果需要自定义配置，可以设置环境变量：
```bash
export BEDROCK_SERVER_DIR=/path/to/your/bedrock-server
export CURSEFORGE_API_KEY=your_api_key_here
export SERVER_PORT=5000
```

或者直接编辑 `config.py` 文件。

## 3. 启动应用

```bash
cd bedrock-manager
python3 run.py
```

应用将在 `http://localhost:5000` 启动。

## 4. 访问Web界面

打开浏览器访问：
- 本地访问: http://localhost:5000
- 远程访问: http://your-server-ip:5000

## 5. 基本使用

### 上传Addon
1. 点击"Addon管理"
2. 点击"上传Addon"按钮
3. 选择.mcpack或.zip文件
4. 等待上传完成

### 从CurseForge安装
1. 点击"Addon管理"
2. 点击"上传Addon"按钮
3. 切换到"CurseForge"标签页
4. 输入CurseForge项目URL或ID
5. 点击"下载并安装"

### 控制服务器
1. 点击"服务器控制"
2. 查看服务器状态
3. 使用按钮启动/停止/重启服务器

### 查看日志
1. 点击"日志查看"
2. 实时查看服务器日志
3. 使用搜索框搜索特定内容

## 故障排除

### 端口被占用
修改 `config.py` 中的 `SERVER_PORT` 或设置环境变量：
```bash
export SERVER_PORT=8080
```

### 无法访问服务器
确保防火墙允许端口访问：
```bash
sudo ufw allow 5000/tcp
```

### 权限问题
确保有权限访问Bedrock服务器目录：
```bash
chmod -R 755 /home/ubuntu/bedrock-server
```

## 下一步

- 查看 `README.md` 了解详细功能
- 配置CurseForge API密钥以使用自动下载功能
- 考虑添加用户认证以提高安全性

