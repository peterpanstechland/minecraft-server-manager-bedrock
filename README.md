# Bedrock Server Manager

Minecraft Bedrock服务器的Web管理平台，提供addon管理、服务器控制和日志监控功能。

## 功能特性

- 📦 **Addon管理**: 上传、安装、启用/禁用addon
- 🔗 **CurseForge集成**: 通过URL或项目ID自动下载addon
- 🔄 **自动更新**: 检查并更新CurseForge上的addon
- 🎮 **服务器控制**: 启动、停止、重启服务器
- 📊 **实时日志**: 实时查看服务器日志，支持搜索和过滤
- 💾 **数据库存储**: 使用SQLite存储addon信息和配置

## 安装

1. **安装Python依赖**:
```bash
cd bedrock-manager
pip3 install -r requirements.txt
```

2. **配置环境变量** (可选):
```bash
export BEDROCK_SERVER_DIR=/home/ubuntu/bedrock-server
export CURSEFORGE_API_KEY=your_api_key_here
export SERVER_PORT=5000
```

3. **启动应用**:
```bash
python3 run.py
```

4. **访问Web界面**:
打开浏览器访问 `http://localhost:5000`

## 配置说明

编辑 `config.py` 或设置环境变量：

- `BEDROCK_SERVER_DIR`: Bedrock服务器目录路径（默认: `/home/ubuntu/bedrock-server`）
- `CURSEFORGE_API_KEY`: CurseForge API密钥（可选，用于下载addon）
- `SERVER_PORT`: Web服务端口（默认: 5000）
- `SERVER_HOST`: Web服务绑定地址（默认: 0.0.0.0）

## 使用说明

### Addon管理

1. **上传Addon**: 点击"上传Addon"按钮，选择.mcpack或.zip文件
2. **从CurseForge安装**: 在"CurseForge"标签页输入项目URL或ID
3. **启用/禁用**: 在addon列表中点击对应的按钮
4. **检查更新**: 对于从CurseForge安装的addon，可以点击"检查更新"

### 服务器控制

- **启动服务器**: 点击"启动服务器"按钮
- **停止服务器**: 点击"停止服务器"按钮
- **重启服务器**: 点击"重启服务器"按钮
- 服务器状态会自动刷新

### 日志查看

- 日志会自动实时更新
- 使用搜索框可以搜索特定内容
- 点击"清空显示"清除当前显示的日志
- 可以开启/关闭自动滚动

## API端点

### Addon管理
- `GET /api/addons` - 获取所有addon
- `POST /api/addons/upload` - 上传addon文件
- `POST /api/addons/install` - 从CurseForge安装
- `PUT /api/addons/<id>/enable` - 启用addon
- `PUT /api/addons/<id>/disable` - 禁用addon
- `POST /api/addons/<id>/update` - 检查并更新addon
- `DELETE /api/addons/<id>` - 删除addon

### 服务器控制
- `GET /api/server/status` - 获取服务器状态
- `POST /api/server/start` - 启动服务器
- `POST /api/server/stop` - 停止服务器
- `POST /api/server/restart` - 重启服务器

### 日志
- `GET /api/logs` - 获取日志
- `GET /api/logs/search?q=query` - 搜索日志
- `GET /api/logs/stream` - 流式传输日志（SSE）

## 注意事项

1. 确保Bedrock服务器目录路径正确
2. CurseForge API密钥需要从 [CurseForge开发者页面](https://console.curseforge.com/) 获取
3. 服务器控制功能需要适当的权限
4. 建议在生产环境中添加用户认证

## 故障排除

### 无法启动服务器
- 检查服务器二进制文件是否存在
- 检查文件权限
- 查看日志获取详细错误信息

### Addon无法安装
- 检查文件格式是否正确（.mcpack或.zip）
- 确认文件包含manifest.json
- 查看服务器日志

### 日志无法显示
- 检查日志文件路径是否正确
- 确认日志文件存在且有读取权限

## 许可证

MIT License

