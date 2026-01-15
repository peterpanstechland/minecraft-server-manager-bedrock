# 脚本说明

## cleanup_orphans.py

清理孤立的bedrock_server进程（非systemd管理的进程）。

### 使用方法

```bash
# 手动运行
python3 scripts/cleanup_orphans.py

# 或直接执行
./scripts/cleanup_orphans.py
```

### 添加到crontab（可选）

定期清理孤立进程，例如每5分钟运行一次：

```bash
crontab -e
```

添加以下行：
```
*/5 * * * * cd /home/ubuntu/bedrock-manager && /home/ubuntu/bedrock-manager/venv/bin/python3 scripts/cleanup_orphans.py >> /var/log/bedrock-cleanup.log 2>&1
```

## setup-sudoers.sh

配置sudoers，允许无需密码执行systemd命令。

### 使用方法

```bash
sudo ./scripts/setup-sudoers.sh
```

**注意**：此脚本需要root权限，会修改 `/etc/sudoers` 文件。

