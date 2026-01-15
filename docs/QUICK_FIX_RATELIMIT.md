# 快速修复：429 限流错误

## 问题
Players页面出现429错误（请求过于频繁）

## 已完成的修复

1. ✅ 默认限流已从 `50 per hour` 提高到 `1000 per hour`（在 `app/__init__.py`）

## 需要手动完成的步骤

### 1. 重启Flask应用以清除限流状态

```bash
# 停止当前应用
pkill -f "python.*run.py"

# 等待2秒
sleep 2

# 重新启动
cd /home/ubuntu/bedrock-manager
source venv/bin/activate
nohup python3 run.py > /tmp/bedrock-manager.log 2>&1 &
```

### 2. （可选）为 `/api/players` 添加明确的限流装饰器

编辑 `app/routes.py`，在第459行（`@login_required_api` 之后）添加：

```python
@bp.route('/api/players', methods=['GET'])
@login_required_api
@limiter.limit("1000 per hour")  # 玩家列表刷新频繁，设置宽松的限制
def get_players():
```

修改后的代码应该是：

```python
# API路由 - 玩家管理
@bp.route('/api/players', methods=['GET'])
@login_required_api
@limiter.limit("1000 per hour")  # 玩家列表刷新频繁，设置宽松的限制
def get_players():
    """获取在线玩家列表"""
    success, message, players = PlayerManager.get_online_players()
    ...
```

### 3. 验证修复

重启后，刷新浏览器页面，429错误应该消失。

## 如果问题仍然存在

1. 检查Flask应用日志：
   ```bash
   tail -f /tmp/bedrock-manager.log
   ```

2. 检查限流配置：
   ```bash
   grep -A 3 "default_limits" app/__init__.py
   ```

3. 临时禁用限流（仅用于测试）：
   在 `app/__init__.py` 中注释掉 `limiter.init_app(app)`
