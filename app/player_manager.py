"""
玩家管理模块 - 管理Bedrock服务器中的在线玩家
使用SQLite持久化存储玩家状态
支持查看在线玩家、无敌模式、踢出玩家等功能
"""
import re
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from config import Config


class PlayerManager:
    """管理Bedrock服务器玩家"""
    
    SYSTEMD_SERVICE = 'bedrock.service'
    SERVER_FIFO_PATH = Path('/home/ubuntu/bedrock-server/server_stdin.fifo')
    
    # 上次处理的日志位置（用于增量读取）
    _last_log_position: int = 0
    _last_log_inode: int = 0
    _current_server_session: Optional[str] = None
    _last_list_command_time: float = 0
    
    @classmethod
    def is_server_running(cls) -> bool:
        """检查服务器是否正在运行"""
        return cls.SERVER_FIFO_PATH.exists()
    
    @classmethod
    def send_command(cls, command: str) -> Tuple[bool, str]:
        """向Bedrock服务器发送命令"""
        if not cls.is_server_running():
            return False, "服务器命令通道不可用。请确认服务器是否正在运行。"
        
        try:
            with open(cls.SERVER_FIFO_PATH, 'w') as fifo:
                fifo.write(f"{command}\n")
            return True, f"命令已发送: {command}"
        except Exception as e:
            return False, f"发送命令失败: {str(e)}"
    
    @classmethod
    def refresh_player_list(cls) -> Tuple[bool, str]:
        """
        主动刷新玩家列表
        发送 list 命令，等待响应，然后解析日志
        """
        if not cls.is_server_running():
            return False, "服务器未运行"
        
        # 防止频繁调用
        now = time.time()
        if now - cls._last_list_command_time < 2:
            return True, "请稍后再刷新"
        cls._last_list_command_time = now
        
        # 记录当前日志位置
        log_file = Config.LOG_FILE
        try:
            start_pos = log_file.stat().st_size if log_file.exists() else 0
        except:
            start_pos = 0
        
        # 发送 list 命令
        success, msg = cls.send_command("list")
        if not success:
            return False, msg
        
        # 等待响应写入日志
        time.sleep(0.5)
        
        # 读取新的日志内容
        try:
            if not log_file.exists():
                return False, "日志文件不存在"
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(start_pos)
                new_content = f.read()
            
            # 解析 list 命令的响应
            # 格式: There are X/Y players online:
            # 或: There are X/Y players online: player1, player2
            list_pattern = re.compile(
                r'There are (\d+)/\d+ players online[:\s]*(.*?)(?:\n|$)',
                re.IGNORECASE
            )
            
            match = list_pattern.search(new_content)
            if match:
                count = int(match.group(1))
                players_str = match.group(2).strip()
                
                from app import db
                from app.models import PlayerSession
                
                # 获取当前数据库中的在线玩家
                current_online = {p.player_name for p in PlayerSession.query.filter_by(is_online=True).all()}
                
                if count == 0:
                    # 没有玩家在线，标记所有玩家离线
                    cls._mark_all_offline()
                    return True, "已更新：0 个在线玩家"
                else:
                    # 解析玩家名称
                    if players_str:
                        player_names = [p.strip() for p in players_str.split(',') if p.strip()]
                    else:
                        player_names = []
                    
                    # 重要：如果服务器报告有玩家但我们没有解析到名称，不要清空现有玩家！
                    if count > 0 and not player_names:
                        # 无法解析玩家名称，保持现有状态
                        return True, f"服务器报告 {count} 个在线玩家，但无法解析名称"
                    
                    # 更新数据库
                    new_players = set(player_names)
                    
                    # 标记离线的玩家
                    for name in current_online - new_players:
                        cls._player_disconnected(name)
                    
                    # 添加新玩家
                    for name in new_players - current_online:
                        cls._player_connected(name)
                    
                    return True, f"已更新：{len(new_players)} 个在线玩家"
            
            return True, "命令已发送，等待响应..."
            
        except Exception as e:
            return False, f"解析响应失败: {str(e)}"
    
    @classmethod
    def _get_server_session_id(cls) -> str:
        """获取当前服务器会话ID（基于服务器PID）"""
        pid_file = Path('/tmp/bedrock_server.pid')
        try:
            # 优先使用 PID 文件内容作为会话标识（更稳定）
            if pid_file.exists():
                pid = pid_file.read_text().strip()
                if pid:
                    return f"session_pid_{pid}"
        except:
            pass
        
        # 回退：使用 FIFO 文件的 mtime（修改时间比 ctime 更稳定）
        try:
            if cls.SERVER_FIFO_PATH.exists():
                stat = cls.SERVER_FIFO_PATH.stat()
                # 使用创建时间的整数部分，避免微小变化
                return f"session_{int(stat.st_mtime)}"
        except:
            pass
        return "session_unknown"
    
    @classmethod
    def _mark_all_offline(cls):
        """将所有玩家标记为离线（服务器重启时调用）"""
        from app import db
        from app.models import PlayerSession
        
        try:
            PlayerSession.query.filter_by(is_online=True).update({
                'is_online': False,
                'leave_time': datetime.utcnow()
            })
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error marking all players offline: {e}")
    
    @classmethod
    def _player_connected(cls, player_name: str, xuid: str = '', join_time: datetime = None):
        """记录玩家连接"""
        from app import db
        from app.models import PlayerSession
        
        if join_time is None:
            join_time = datetime.utcnow()
        
        try:
            # 检查是否已有该玩家的在线记录
            existing = PlayerSession.query.filter_by(
                player_name=player_name,
                is_online=True
            ).first()
            
            if existing:
                # 已经在线，更新时间
                existing.join_time = join_time
                if xuid:
                    existing.xuid = xuid
            else:
                # 创建新记录
                session = PlayerSession(
                    player_name=player_name,
                    xuid=xuid,
                    is_online=True,
                    join_time=join_time,
                    server_session_id=cls._current_server_session
                )
                db.session.add(session)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error recording player connect: {e}")
    
    @classmethod
    def _player_disconnected(cls, player_name: str):
        """记录玩家断开连接"""
        from app import db
        from app.models import PlayerSession
        
        try:
            # 找到该玩家的在线记录并标记为离线
            session = PlayerSession.query.filter_by(
                player_name=player_name,
                is_online=True
            ).first()
            
            if session:
                session.is_online = False
                session.leave_time = datetime.utcnow()
                session.is_invincible = False  # 离线时清除无敌状态
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error recording player disconnect: {e}")
    
    @classmethod
    def _get_stored_session_id(cls) -> Optional[str]:
        """从文件获取存储的服务器会话ID"""
        session_file = Path('/tmp/bedrock_session_id.txt')
        try:
            if session_file.exists():
                return session_file.read_text().strip()
        except:
            pass
        return None
    
    @classmethod
    def _store_session_id(cls, session_id: str):
        """存储服务器会话ID到文件"""
        session_file = Path('/tmp/bedrock_session_id.txt')
        try:
            session_file.write_text(session_id)
        except:
            pass
    
    @classmethod
    def _check_server_restart(cls) -> bool:
        """检查服务器是否重启过"""
        current_session = cls._get_server_session_id()
        
        # 从持久化存储获取上次的会话ID
        if cls._current_server_session is None:
            cls._current_server_session = cls._get_stored_session_id()
        
        if cls._current_server_session is None:
            # 首次运行，记录当前会话但不清空玩家（让日志解析来处理）
            cls._current_server_session = current_session
            cls._store_session_id(current_session)
            return False  # 首次启动不清空，让日志解析来确定玩家状态
        
        if current_session != cls._current_server_session:
            # 服务器确实重启了（FIFO 文件时间戳变化）
            cls._current_server_session = current_session
            cls._store_session_id(current_session)
            return True
        
        return False
    
    @classmethod
    def _process_log_file(cls):
        """处理日志文件，更新玩家状态"""
        log_file = Config.LOG_FILE
        if not log_file.exists():
            return
        
        try:
            # 检查文件是否被重置
            stat = log_file.stat()
            current_inode = stat.st_ino
            file_size = stat.st_size
            
            if current_inode != cls._last_log_inode:
                # 文件被重新创建
                cls._last_log_inode = current_inode
                cls._last_log_position = 0
            
            if file_size < cls._last_log_position:
                # 文件被截断
                cls._last_log_position = 0
            
            if file_size == cls._last_log_position:
                # 没有新内容
                return
            
            # 读取新内容
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(cls._last_log_position)
                new_content = f.read()
                cls._last_log_position = f.tell()
            
            if not new_content:
                return
            
            # 解析玩家事件
            lines = new_content.split('\n')
            cls._parse_player_events(lines)
            
        except Exception as e:
            print(f"Error processing log file: {e}")
    
    @classmethod
    def _parse_player_events(cls, lines: List[str]):
        """解析日志行中的玩家事件"""
        # 玩家连接模式
        join_pattern = re.compile(
            r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})[:\d]*\s+INFO\]\s+Player connected:\s+(\w+),\s*xuid:\s*(\d+)',
            re.IGNORECASE
        )
        # 玩家断开模式
        leave_pattern = re.compile(
            r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})[:\d]*\s+INFO\]\s+Player disconnected:\s+(\w+)',
            re.IGNORECASE
        )
        # 备用模式
        join_pattern_alt = re.compile(r'Player\s+connected:\s+(\w+)', re.IGNORECASE)
        leave_pattern_alt = re.compile(r'Player\s+disconnected:\s+(\w+)', re.IGNORECASE)
        
        # 注意：不再在这里检测服务器启动，因为这会导致每次读取日志都清空玩家
        # 服务器重启检测由 _check_server_restart() 通过 FIFO 文件时间戳来处理
        
        for line in lines:
            
            # 玩家连接
            match = join_pattern.search(line)
            if match:
                timestamp_str, player_name, xuid = match.groups()
                try:
                    join_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    join_time = datetime.utcnow()
                cls._player_connected(player_name, xuid, join_time)
                continue
            
            # 玩家断开
            match = leave_pattern.search(line)
            if match:
                _, player_name = match.groups()
                cls._player_disconnected(player_name)
                continue
            
            # 备用模式 - 连接
            match = join_pattern_alt.search(line)
            if match and 'disconnected' not in line.lower():
                player_name = match.group(1)
                cls._player_connected(player_name)
                continue
            
            # 备用模式 - 断开
            match = leave_pattern_alt.search(line)
            if match:
                player_name = match.group(1)
                cls._player_disconnected(player_name)
    
    @classmethod
    def get_online_players(cls) -> Tuple[bool, str, List[Dict]]:
        """获取在线玩家列表"""
        from app.models import PlayerSession
        
        # 检查服务器状态
        if not cls.is_server_running():
            # 服务器未运行，标记所有玩家离线
            cls._mark_all_offline()
            return True, "服务器未运行", []
        
        # 检查服务器是否重启
        if cls._check_server_restart():
            cls._mark_all_offline()
        
        # 处理新的日志
        cls._process_log_file()
        
        # 从数据库获取在线玩家
        try:
            online_players = PlayerSession.query.filter_by(is_online=True).all()
            players = [p.to_dict() for p in online_players]
            return True, f"找到 {len(players)} 个在线玩家", players
        except Exception as e:
            return False, f"获取玩家列表失败: {str(e)}", []
    
    @classmethod
    def is_player_invincible(cls, player_name: str) -> bool:
        """检查玩家是否处于无敌状态"""
        from app.models import PlayerSession
        
        try:
            session = PlayerSession.query.filter_by(
                player_name=player_name,
                is_online=True
            ).first()
            
            if session and session.is_invincible:
                if session.invincible_until is None or session.invincible_until > datetime.utcnow():
                    return True
        except:
            pass
        return False
    
    @classmethod
    def set_invincible(cls, player_name: str, enable: bool = True, duration: int = 999999) -> Tuple[bool, str]:
        """设置玩家无敌模式"""
        from app import db
        from app.models import PlayerSession
        
        if not player_name:
            return False, "玩家名称不能为空"
        
        # 清理玩家名称
        player_name = re.sub(r'[^\w]', '', player_name)
        if not player_name:
            return False, "无效的玩家名称"
        
        if enable:
            # 发送效果命令
            commands = [
                f'effect {player_name} resistance {duration} 255 true',
                f'effect {player_name} regeneration {duration} 255 true',
                f'effect {player_name} fire_resistance {duration} 255 true',
                f'effect {player_name} instant_health 1 255 true'
            ]
            
            success_count = 0
            for cmd in commands:
                success, _ = cls.send_command(cmd)
                if success:
                    success_count += 1
                time.sleep(0.1)
            
            if success_count > 0:
                # 更新数据库状态
                try:
                    session = PlayerSession.query.filter_by(
                        player_name=player_name,
                        is_online=True
                    ).first()
                    
                    if session:
                        session.is_invincible = True
                        session.invincible_until = datetime.utcnow() + timedelta(seconds=duration)
                        db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Error updating invincible status: {e}")
                
                return True, f"已为 {player_name} 启用无敌模式"
            else:
                return False, "发送效果命令失败"
        else:
            # 清除效果
            success, msg = cls.send_command(f'effect {player_name} clear')
            
            # 更新数据库状态
            try:
                session = PlayerSession.query.filter_by(
                    player_name=player_name,
                    is_online=True
                ).first()
                
                if session:
                    session.is_invincible = False
                    session.invincible_until = None
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
            
            if success:
                return True, f"已为 {player_name} 关闭无敌模式"
            else:
                return False, f"关闭无敌模式失败: {msg}"
    
    @classmethod
    def kick_player(cls, player_name: str, reason: str = "被管理员踢出") -> Tuple[bool, str]:
        """踢出玩家"""
        if not player_name:
            return False, "玩家名称不能为空"
        
        player_name = re.sub(r'[^\w]', '', player_name)
        if not player_name:
            return False, "无效的玩家名称"
        
        reason = re.sub(r'[^\w\s\u4e00-\u9fff]', '', reason)[:100]
        if not reason:
            reason = "被管理员踢出"
        
        success, msg = cls.send_command(f'kick {player_name} {reason}')
        
        if success:
            # 标记玩家离线
            cls._player_disconnected(player_name)
            return True, f"已踢出玩家 {player_name}"
        else:
            return False, f"踢出玩家失败: {msg}"
    
    @classmethod
    def send_message(cls, message: str, target: str = "@a") -> Tuple[bool, str]:
        """向玩家发送消息"""
        if not message:
            return False, "消息不能为空"
        
        message = re.sub(r'["\'\n\r]', '', message)[:200]
        success, msg = cls.send_command(f'say {message}')
        return success, msg if not success else "消息已发送"
    
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
