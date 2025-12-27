import os
import signal
import subprocess
import psutil
from pathlib import Path
from typing import Dict, Optional, Tuple
from config import Config

class ServerManager:
    """管理Bedrock服务器进程"""
    
    PID_FILE = Path('/tmp/bedrock_server.pid')
    
    @staticmethod
    def get_server_status() -> Dict:
        """获取服务器状态"""
        pid = ServerManager.get_server_pid()
        
        if pid is None:
            return {
                'running': False,
                'pid': None,
                'status': 'stopped'
            }
        
        try:
            process = psutil.Process(pid)
            return {
                'running': True,
                'pid': pid,
                'status': 'running',
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'create_time': process.create_time()
            }
        except psutil.NoSuchProcess:
            # PID文件存在但进程不存在
            ServerManager.PID_FILE.unlink(missing_ok=True)
            return {
                'running': False,
                'pid': None,
                'status': 'stopped'
            }
        except Exception as e:
            return {
                'running': False,
                'pid': None,
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def get_server_pid() -> Optional[int]:
        """获取服务器进程PID"""
        if not ServerManager.PID_FILE.exists():
            # 尝试通过进程名查找
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and 'bedrock_server' in ' '.join(cmdline):
                        pid = proc.info['pid']
                        # 保存PID到文件
                        ServerManager.PID_FILE.write_text(str(pid))
                        return pid
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return None
        
        try:
            pid = int(ServerManager.PID_FILE.read_text().strip())
            # 验证进程是否存在
            if psutil.pid_exists(pid):
                return pid
            else:
                # 进程不存在，删除PID文件
                ServerManager.PID_FILE.unlink(missing_ok=True)
                return None
        except (ValueError, FileNotFoundError):
            return None
    
    @staticmethod
    def start_server() -> Tuple[bool, str]:
        """启动服务器"""
        status = ServerManager.get_server_status()
        if status['running']:
            return False, "服务器已在运行中"
        
        if not Config.BEDROCK_SERVER_BINARY.exists():
            return False, f"服务器文件不存在: {Config.BEDROCK_SERVER_BINARY}"
        
        try:
            # 切换到服务器目录
            server_dir = Config.BEDROCK_SERVER_DIR
            
            # 启动服务器进程
            process = subprocess.Popen(
                [str(Config.BEDROCK_SERVER_BINARY)],
                cwd=str(server_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # 创建新的进程组
            )
            
            # 保存PID
            ServerManager.PID_FILE.write_text(str(process.pid))
            
            return True, f"服务器已启动 (PID: {process.pid})"
        except Exception as e:
            return False, f"启动失败: {str(e)}"
    
    @staticmethod
    def stop_server() -> Tuple[bool, str]:
        """停止服务器"""
        pid = ServerManager.get_server_pid()
        
        if pid is None:
            return False, "服务器未运行"
        
        try:
            process = psutil.Process(pid)
            
            # 发送SIGTERM信号
            process.terminate()
            
            # 等待进程结束（最多10秒）
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                # 如果10秒后还没结束，强制杀死
                process.kill()
                process.wait()
            
            # 删除PID文件
            ServerManager.PID_FILE.unlink(missing_ok=True)
            
            return True, "服务器已停止"
        except psutil.NoSuchProcess:
            ServerManager.PID_FILE.unlink(missing_ok=True)
            return False, "进程不存在"
        except Exception as e:
            return False, f"停止失败: {str(e)}"
    
    @staticmethod
    def restart_server() -> Tuple[bool, str]:
        """重启服务器"""
        # 先停止
        if ServerManager.get_server_status()['running']:
            success, message = ServerManager.stop_server()
            if not success:
                return False, f"停止失败: {message}"
            
            # 等待一下确保进程完全结束
            import time
            time.sleep(2)
        
        # 再启动
        return ServerManager.start_server()
    
    @staticmethod
    def send_command(command: str) -> Tuple[bool, str]:
        """向服务器发送命令（如果服务器支持stdin）"""
        pid = ServerManager.get_server_pid()
        if pid is None:
            return False, "服务器未运行"
        
        # 注意：Bedrock服务器通常不支持通过stdin发送命令
        # 这个方法可能需要通过RCON或其他方式实现
        # 这里提供一个基础框架
        return False, "命令发送功能需要RCON支持"

