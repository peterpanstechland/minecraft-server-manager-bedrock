# ServerManager 改进说明

## 🎯 改进目标

解决Bedrock服务器进程冲突问题，确保服务稳定运行。

## ✨ 主要改进

### 1. 自动清理孤立进程

**问题**：旧的bedrock_server进程可能占用端口，导致新进程无法启动。

**解决方案**：
- `cleanup_orphaned_processes()` - 自动检测并清理非systemd管理的孤立进程
- 在每次获取服务器状态时自动执行清理
- 智能识别systemd管理的进程，避免误杀

### 2. Systemd集成

**问题**：同时使用systemd和Manager可能导致进程冲突。

**解决方案**：
- 优先使用systemd管理服务（如果可用）
- 自动检测systemd服务状态
- 启动/停止/重启操作优先通过systemd执行
- 如果systemd不可用，自动回退到直接管理

### 3. 进程检测增强

**改进**：
- `find_all_bedrock_processes()` - 查找所有bedrock_server进程
- `is_systemd_managed()` - 检测服务是否由systemd管理
- `get_server_pid()` - 优先从systemd获取PID

### 4. 状态信息增强

**新增字段**：
- `managed_by`: 显示服务管理方式（'systemd' 或 'manual'）
- `cleaned_orphans`: 显示清理的孤立进程数量

## 📋 新增方法

### ServerManager类

```python
# 检测systemd是否可用
is_systemd_available() -> bool

# 检测服务是否由systemd管理
is_systemd_managed() -> bool

# 查找所有bedrock_server进程
find_all_bedrock_processes() -> List[Dict]

# 清理孤立进程
cleanup_orphaned_processes() -> Tuple[int, List[int]]
```

## 🛠️ 使用方式

### Web界面

所有改进对用户透明，Web界面操作保持不变：
- 启动服务器 - 自动使用systemd（如果可用）
- 停止服务器 - 自动使用systemd（如果可用）
- 重启服务器 - 自动使用systemd（如果可用）
- 查看状态 - 自动清理孤立进程并显示管理方式

### 命令行工具

```bash
# 清理孤立进程
python3 scripts/cleanup_orphans.py

# 添加到crontab定期清理（可选）
*/5 * * * * cd /home/ubuntu/bedrock-manager && /home/ubuntu/bedrock-manager/venv/bin/python3 scripts/cleanup_orphans.py
```

## 🔍 工作原理

1. **状态检查时**：
   - 自动清理孤立进程
   - 检测systemd服务状态
   - 返回当前运行状态和管理方式

2. **启动服务器时**：
   - 先清理孤立进程
   - 尝试使用systemd启动
   - 如果systemd不可用，回退到直接启动

3. **停止服务器时**：
   - 优先使用systemd停止
   - 如果systemd不可用，直接停止进程

4. **重启服务器时**：
   - 优先使用systemd重启
   - 如果systemd不可用，手动停止后启动

## ✅ 测试结果

- ✓ 自动检测systemd服务状态
- ✓ 正确识别systemd管理的进程
- ✓ 成功清理孤立进程
- ✓ 状态信息包含管理方式
- ✓ 向后兼容，不影响现有功能

## 📝 注意事项

1. **sudo权限**：如果使用systemd管理，需要配置sudoers允许无需密码执行systemd命令（见 `scripts/setup-sudoers.sh`）

2. **进程识别**：系统会智能识别systemd管理的进程，不会误杀

3. **自动清理**：每次状态检查都会自动清理孤立进程，无需手动操作

4. **向后兼容**：如果systemd不可用，会自动回退到原来的直接管理方式

## 🚀 未来改进

- [ ] 添加进程监控和自动重启
- [ ] 添加端口占用检测和自动处理
- [ ] 添加更详细的日志记录
- [ ] 支持多个服务器实例管理

