"""
玩家管理模块 - 管理Bedrock服务器中的在线玩家
支持查看在线玩家、无敌模式、踢出玩家等功能
"""
import subprocess
import re
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from config import Config


class PlayerManager:
    """管理Bedrock服务器玩家"""
    
    SCREEN_SESSION_NAME = 'bedrock'
    SYSTEMD_SERVICE = 'bedrock.service'
    SERVER_FIFO_PATH = Path('/home/ubuntu/bedrock-server/server_stdin.fifo')
    
    # 玩家效果状态缓存 (player_name -> {effect_name: expiry_time})
    _player_effects: Dict[str, Dict[str, datetime]] = {}
    
    # 持久化的在线玩家会话 (player_name -> session_info)
    _online_players: Dict[str, Dict] = {}
    
    # 上次处理的日志位置（用于增量读取）
    _last_log_position: int = 0
    _last_log_inode: int = 0
    
    # 上次检测到的服务器启动时间
    _last_server_start: Optional[datetime] = None
    
    @classmethod
    def is_screen_session_active(cls) -> bool:
        """检查服务器命令通道是否可用（使用FIFO管道）"""
        return cls.SERVER_FIFO_PATH.exists()
    
    @classmethod
    def send_command(cls, command: str) -> Tuple[bool, str]:
        """
        向Bedrock服务器发送命令
        使用命名管道(FIFO)发送命令
        """
        if not cls.is_screen_session_active():
            return False, "服务器命令通道不可用。请确认服务器是否正在运行。"
        
        try:
            # 向FIFO写入命令
            # 注意：必须添加换行符
            # 使用非阻塞方式写入可能会更好，但这里简单起见使用阻塞写入
            # 因为FIFO读取端应该是活跃的
            with open(cls.SERVER_FIFO_PATH, 'w') as fifo:
                fifo.write(f"{command}\n")
            
            return True, f"命令已发送: {command}"
        except Exception as e:
            return False, f"发送命令失败: {str(e)}"
    
    @classmethod
    def _check_server_restart(cls, log_file: Path) -> bool:
        """检查服务器是否重启过（通过检测日志文件变化）"""
        try:
            stat = log_file.stat()
            current_inode = stat.st_ino
            
            # 如果 inode 变化了，说明日志文件被重新创建（服务器重启）
            if cls._last_log_inode != 0 and current_inode != cls._last_log_inode:
                cls._last_log_inode = current_inode
                cls._last_log_position = 0
                return True
            
            cls._last_log_inode = current_inode
            return False
        except:
            return False
    
    @classmethod
    def _detect_server_start_from_log(cls, lines: List[str]) -> bool:
        """从日志中检测服务器启动事件"""
        # 检测服务器启动标志
        start_patterns = [
            r'Server started\.',
            r'IPv4 supported, port:',
            r'opening worlds',
        ]
        
        for line in lines:
            for pattern in start_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    return True
        return False
    
    @classmethod
    def _process_log_lines(cls, lines: List[str]):
        """处理日志行，更新在线玩家列表"""
        # 解析玩家加入/离开事件
        join_pattern = re.compile(
            r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})[:\d]*\s+INFO\]\s+Player connected:\s+(\w+),\s*xuid:\s*(\d+)',
            re.IGNORECASE
        )
        leave_pattern = re.compile(
            r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})[:\d]*\s+INFO\]\s+Player disconnected:\s+(\w+)',
            re.IGNORECASE
        )
        
        # 备用模式
        join_pattern_alt = re.compile(r'Player\s+connected:\s+(\w+)', re.IGNORECASE)
        leave_pattern_alt = re.compile(r'Player\s+disconnected:\s+(\w+)', re.IGNORECASE)
        
        for line in lines:
            # 尝试主模式 - 玩家加入
            join_match = join_pattern.search(line)
            if join_match:
                timestamp_str, player_name, xuid = join_match.groups()
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    timestamp = datetime.now()
                
                cls._online_players[player_name] = {
                    'name': player_name,
                    'xuid': xuid,
                    'join_time': timestamp,
                }
                continue
            
            # 尝试主模式 - 玩家离开
            leave_match = leave_pattern.search(line)
            if leave_match:
                timestamp_str, player_name = leave_match.groups()
                cls._online_players.pop(player_name, None)
                cls._player_effects.pop(player_name, None)
                continue
            
            # 尝试备用模式 - 玩家加入
            join_alt = join_pattern_alt.search(line)
            if join_alt and 'disconnected' not in line.lower():
                player_name = join_alt.group(1)
                if player_name not in cls._online_players:
                    cls._online_players[player_name] = {
                        'name': player_name,
                        'xuid': '',
                        'join_time': datetime.now(),
                    }
                continue
            
            # 尝试备用模式 - 玩家离开
            leave_alt = leave_pattern_alt.search(line)
            if leave_alt:
                player_name = leave_alt.group(1)
                cls._online_players.pop(player_name, None)
                cls._player_effects.pop(player_name, None)
    
    @classmethod
    def get_online_players(cls) -> Tuple[bool, str, List[Dict]]:
        """
        获取在线玩家列表
        使用增量日志读取和持久化的玩家会话跟踪
        """
        log_file = Config.LOG_FILE
        if not log_file.exists():
            return True, "日志文件不存在", []
        
        try:
            # 检查服务器是否重启过
            if cls._check_server_restart(log_file):
                # 服务器重启，清空玩家列表
                cls._online_players.clear()
                cls._player_effects.clear()
                cls._last_log_position = 0
            
            # 检查 FIFO 是否存在（服务器是否运行）
            if not cls.SERVER_FIFO_PATH.exists():
                # 服务器未运行，清空玩家列表
                cls._online_players.clear()
                cls._player_effects.clear()
                cls._last_log_position = 0
                return True, "服务器未运行", []
            
            # 读取新增的日志
            file_size = log_file.stat().st_size
            
            if file_size < cls._last_log_position:
                # 日志文件被截断或重置
                cls._last_log_position = 0
                cls._online_players.clear()
                cls._player_effects.clear()
            
            new_lines = []
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                if cls._last_log_position == 0:
                    # 首次读取或重置后，读取全部日志检测服务器启动和玩家状态
                    content = f.read()
                    new_lines = content.split('\n')
                    
                    # 检测服务器启动事件，如果检测到则清空之前的玩家列表
                    if cls._detect_server_start_from_log(new_lines):
                        cls._online_players.clear()
                        cls._player_effects.clear()
                else:
                    # 增量读取
                    f.seek(cls._last_log_position)
                    content = f.read()
                    new_lines = content.split('\n')
                
                cls._last_log_position = f.tell()
            
            # 处理新日志行
            if new_lines:
                cls._process_log_lines(new_lines)
            
            # 构建返回的玩家列表
            players = []
            for name, info in cls._online_players.items():
                player_data = {
                    'name': name,
                    'xuid': info.get('xuid', ''),
                    'join_time': info.get('join_time', datetime.now()).isoformat(),
                    'invincible': cls.is_player_invincible(name)
                }
                players.append(player_data)
            
            return True, f"找到 {len(players)} 个在线玩家", players
            
        except Exception as e:
            return False, f"获取玩家列表失败: {str(e)}", []
    
    @classmethod
    def is_player_invincible(cls, player_name: str) -> bool:
        """检查玩家是否处于无敌状态"""
        if player_name not in cls._player_effects:
            return False
        
        effects = cls._player_effects[player_name]
        if 'invincible' not in effects:
            return False
        
        # 检查效果是否过期
        if effects['invincible'] > datetime.now():
            return True
        else:
            del effects['invincible']
            return False
    
    @classmethod
    def set_invincible(cls, player_name: str, enable: bool = True, duration: int = 999999) -> Tuple[bool, str]:
        """
        设置玩家无敌模式
        通过给予玩家高等级的抗性提升和生命恢复效果实现
        """
        if not player_name:
            return False, "玩家名称不能为空"
        
        # 清理玩家名称，防止命令注入
        player_name = re.sub(r'[^\w]', '', player_name)
        if not player_name:
            return False, "无效的玩家名称"
        
        if enable:
            # 给予效果：抗性提升255级 + 生命恢复255级 + 防火
            # effect <player> <effect> [seconds] [amplifier] [hideParticles]
            commands = [
                f'effect {player_name} resistance {duration} 255 true',
                f'effect {player_name} regeneration {duration} 255 true', 
                f'effect {player_name} fire_resistance {duration} 255 true',
                f'effect {player_name} instant_health 1 255 true'
            ]
            
            success_count = 0
            for cmd in commands:
                success, msg = cls.send_command(cmd)
                if success:
                    success_count += 1
                time.sleep(0.1)  # 短暂延迟防止命令堆积
            
            if success_count > 0:
                # 记录效果状态
                if player_name not in cls._player_effects:
                    cls._player_effects[player_name] = {}
                cls._player_effects[player_name]['invincible'] = datetime.now() + timedelta(seconds=duration)
                
                return True, f"已为 {player_name} 启用无敌模式"
            else:
                return False, "发送效果命令失败"
        else:
            # 清除所有效果
            success, msg = cls.send_command(f'effect {player_name} clear')
            
            # 清除缓存状态
            if player_name in cls._player_effects:
                cls._player_effects[player_name].pop('invincible', None)
            
            if success:
                return True, f"已为 {player_name} 关闭无敌模式"
            else:
                return False, f"关闭无敌模式失败: {msg}"
    
    @classmethod
    def kick_player(cls, player_name: str, reason: str = "被管理员踢出") -> Tuple[bool, str]:
        """踢出玩家"""
        if not player_name:
            return False, "玩家名称不能为空"
        
        # 清理玩家名称，防止命令注入
        player_name = re.sub(r'[^\w]', '', player_name)
        if not player_name:
            return False, "无效的玩家名称"
        
        # 清理踢出原因，限制长度并移除特殊字符
        reason = re.sub(r'[^\w\s\u4e00-\u9fff]', '', reason)[:100]
        if not reason:
            reason = "被管理员踢出"
        
        success, msg = cls.send_command(f'kick {player_name} {reason}')
        
        if success:
            # 清除该玩家的效果缓存
            cls._player_effects.pop(player_name, None)
            return True, f"已踢出玩家 {player_name}"
        else:
            return False, f"踢出玩家失败: {msg}"
    
    @classmethod
    def send_message(cls, message: str, target: str = "@a") -> Tuple[bool, str]:
        """向玩家发送消息"""
        if not message:
            return False, "消息不能为空"
        
        # 清理消息内容
        message = re.sub(r'["\'\n\r]', '', message)[:200]
        
        success, msg = cls.send_command(f'say {message}')
        return success, msg if not success else f"消息已发送"
    
    @classmethod
    def teleport_player(cls, player_name: str, x: float, y: float, z: float) -> Tuple[bool, str]:
        """传送玩家到指定坐标"""
        if not player_name:
            return False, "玩家名称不能为空"
        
        player_name = re.sub(r'[^\w]', '', player_name)
        if not player_name:
            return False, "无效的玩家名称"
        
        try:
            x, y, z = float(x), float(y), float(z)
        except (ValueError, TypeError):
            return False, "坐标必须是数字"
        
        success, msg = cls.send_command(f'tp {player_name} {x} {y} {z}')
        return success, f"已传送 {player_name} 到 ({x}, {y}, {z})" if success else msg
    
    @classmethod
    def get_screen_setup_instructions(cls) -> str:
        """获取配置screen会话的说明"""
        return """
要启用玩家管理功能，需要将服务器配置为在screen会话中运行。

请运行以下命令进行配置：

1. 停止当前服务：
   sudo systemctl stop bedrock.service

2. 创建screen启动脚本：
   将服务器改为通过screen运行

3. 重新启动服务：
   sudo systemctl start bedrock.service

或者运行提供的安装脚本：
   sudo bash /home/ubuntu/bedrock-manager/setup_screen_server.sh
"""
