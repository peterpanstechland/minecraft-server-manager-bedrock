# 项目结构说明

## 目录结构

```
bedrock-manager/
├── app/                          # 应用核心代码
│   ├── __init__.py              # Flask应用初始化
│   ├── routes.py                 # 路由和API端点定义
│   ├── models.py                 # 数据库模型
│   ├── auth.py                   # 用户认证
│   ├── security.py               # 安全功能
│   ├── server_manager.py         # 服务器进程管理
│   ├── player_manager.py         # 玩家管理功能
│   ├── addon_manager.py          # Addon管理逻辑
│   ├── log_monitor.py            # 日志监控
│   └── curseforge.py             # CurseForge API集成
│
├── templates/                     # HTML模板
│   ├── base.html                 # 基础模板（包含导航和CSRF设置）
│   ├── index.html                # 首页
│   ├── addons.html               # Addon管理页面
│   ├── server.html               # 服务器控制页面
│   ├── players.html              # 玩家管理页面
│   └── logs.html                 # 日志查看页面
│
├── static/                        # 静态文件
│   └── uploads/                  # 上传文件临时目录
│
├── scripts/                       # 工具脚本
│   ├── setup/                    # 安装和配置脚本
│   ├── utils/                    # 工具函数
│   └── organize_project.sh       # 项目整理脚本
│
├── database/                      # SQLite数据库目录
│   └── bedrock_manager.db        # 主数据库文件
│
├── docs/                          # 文档目录
│   ├── guides/                   # 使用指南
│   ├── troubleshooting/          # 故障排除文档
│   ├── development/              # 开发文档
│   └── PROJECT_STRUCTURE.md      # 本文档
│
├── venv/                          # Python虚拟环境（不提交到git）
│
├── config.py                     # 应用配置文件
├── run.py                        # 应用入口点
├── create_admin.py               # 创建管理员账户脚本
├── requirements.txt              # Python依赖列表
├── .env.example                  # 环境变量示例文件
└── README.md                     # 项目主文档
```

## 核心模块说明

### app/routes.py
- 定义所有Web路由和API端点
- 处理HTTP请求和响应
- 集成认证、限流和安全检查

### app/server_manager.py
- 管理Bedrock服务器进程
- 检测服务器状态（运行中/已停止）
- 启动、停止、重启服务器
- 清理孤立进程
- 获取CPU和内存使用情况

### app/player_manager.py
- 获取在线玩家列表
- 解析服务器日志获取玩家信息
- 发送命令到服务器（通过FIFO管道）
- 管理玩家无敌模式
- 踢出玩家功能

### app/addon_manager.py
- 处理addon上传和安装
- 解析manifest.json文件
- 管理世界配置文件（world_behavior_packs.json等）
- 启用/禁用addon
- 扫描服务器目录中的addon

### app/log_monitor.py
- 实时监控服务器日志文件
- 使用Server-Sent Events (SSE)推送日志
- 日志搜索和过滤功能
- 日志级别识别和高亮

## 已废弃的文件

以下文件已被新实现替代，可以安全删除：

- `scripts/attach_screen.sh` - 已被server_runner.py和FIFO管道替代
- `setup_screen_server.sh` - 已被server_runner.py替代
- `bedrock-server/screen_wrapper.sh` - 已被server_runner.py替代
- `bedrock-server/start_server.sh` - 已被server_runner.py替代

## Bedrock服务器目录结构

```
bedrock-server/
├── bedrock_server                # 服务器可执行文件
├── server_runner.py              # Python包装脚本（必需）
├── server_stdin.fifo             # 命名管道（用于命令输入）
├── server.properties             # 服务器配置文件
├── behavior_packs/               # 行为包目录
├── resource_packs/               # 资源包目录
├── worlds/                       # 世界目录
│   └── Bedrock level/           # 默认世界
│       ├── world_behavior_packs.json
│       └── world_resource_packs.json
└── Dedicated_Server.txt          # 服务器日志文件
```

## 重要文件说明

### server_runner.py
这是Bedrock服务器的启动包装脚本，负责：
- 启动bedrock_server进程
- 创建FIFO管道用于命令输入
- 写入PID文件供管理工具使用
- 处理信号和优雅关闭

### .env文件
包含敏感配置信息，不应提交到版本控制：
- SECRET_KEY - Flask密钥
- ADMIN_PASSWORD - 管理员密码
- CURSEFORGE_API_KEY - API密钥

### database/bedrock_manager.db
SQLite数据库文件，存储：
- 用户账户信息
- Addon元数据
- Addon启用状态
- CurseForge更新信息

## 部署注意事项

1. **权限**: 确保应用有权限访问Bedrock服务器目录
2. **FIFO管道**: server_runner.py会自动创建，确保目录可写
3. **PID文件**: 写入到/tmp/bedrock_server.pid，确保/tmp可写
4. **日志文件**: 确保可以读取Dedicated_Server.txt
5. **Systemd服务**: 推荐使用systemd管理两个服务（bedrock.service和bedrock-manager.service）
