import os
import signal
import subprocess
import psutil
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from config import Config

class ServerManager:
    """管理Bedrock服务器进程"""
    
    PID_FILE = Path('/tmp/bedrock_server.pid')
    SYSTEMD_SERVICE = 'bedrock.service'
    
    @staticmethod
    def get_server_status() -> Dict:
        """获取服务器状态"""
        # 自动清理孤立进程
        cleaned_count, _ = ServerManager.cleanup_orphaned_processes()
        
        pid = ServerManager.get_server_pid()
        
        if pid is None:
            return {
                'running': False,
                'pid': None,
                'status': 'stopped',
                'managed_by': 'systemd' if ServerManager.is_systemd_available() else 'manual'
            }
        
        try:
            process = psutil.Process(pid)
            is_systemd = ServerManager.is_systemd_managed()
            return {
                'running': True,
                'pid': pid,
                'status': 'running',
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'create_time': process.create_time(),
                'managed_by': 'systemd' if is_systemd else 'manual',
                'cleaned_orphans': cleaned_count
            }
        except psutil.NoSuchProcess:
            # PID文件存在但进程不存在
            ServerManager.PID_FILE.unlink(missing_ok=True)
            return {
                'running': False,
                'pid': None,
                'status': 'stopped',
                'managed_by': 'systemd' if ServerManager.is_systemd_available() else 'manual'
            }
        except Exception as e:
            return {
                'running': False,
                'pid': None,
                'status': 'error',
                'error': str(e),
                'managed_by': 'systemd' if ServerManager.is_systemd_available() else 'manual'
            }
    
    @staticmethod
    def is_systemd_managed() -> bool:
        """检查服务器是否由systemd管理"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', ServerManager.SYSTEMD_SERVICE],
                capture_output=True,
                text=True,
                timeout=2
            )
            # 接受 active 或 activating 状态
            status = result.stdout.strip()
            return status in ('active', 'activating')
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def find_all_bedrock_processes() -> List[Dict]:
        """查找所有bedrock_server进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid', 'create_time']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'bedrock_server' in ' '.join(cmdline):
                    processes.append({
                        'pid': proc.info['pid'],
                        'ppid': proc.info.get('ppid'),
                        'cmdline': ' '.join(cmdline),
                        'create_time': proc.info.get('create_time', 0)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    
    @staticmethod
    def cleanup_orphaned_processes() -> Tuple[int, List[int]]:
        """清理孤立的bedrock_server进程（非systemd管理的）"""
        cleaned_pids = []
        all_processes = ServerManager.find_all_bedrock_processes()
        
        # 如果systemd服务正在运行，获取systemd管理的PID
        systemd_pid = None
        if ServerManager.is_systemd_managed():
            try:
                result = subprocess.run(
                    ['systemctl', 'show', '--property=MainPID', '--value', ServerManager.SYSTEMD_SERVICE],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and result.stdout.strip():
                    systemd_pid = int(result.stdout.strip())
            except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
                pass
        
        for proc_info in all_processes:
            pid = proc_info['pid']
            ppid = proc_info.get('ppid')
            
            # 跳过systemd管理的进程（包括直接由systemd启动的wrapper及其子进程）
            if systemd_pid:
                # 如果进程本身就是systemd MainPID，跳过
                if pid == systemd_pid:
                    continue
                # 如果进程的父进程是systemd MainPID（说明是由wrapper启动的），跳过
                if ppid == systemd_pid:
                    continue
            
            # 检查是否是systemd的子进程（父进程是init/systemd）
            try:
                parent = psutil.Process(pid).parent()
                # systemd的PID通常是1，或者父进程是systemd
                if parent.pid == 1 or 'systemd' in parent.name().lower():
                    continue
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            # 清理孤立进程
            try:
                process = psutil.Process(pid)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    process.kill()
                    process.wait()
                cleaned_pids.append(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                pass
        
        # 清理PID文件（如果存在且对应的进程已被清理）
        if ServerManager.PID_FILE.exists():
            try:
                pid_from_file = int(ServerManager.PID_FILE.read_text().strip())
                if pid_from_file in cleaned_pids or not psutil.pid_exists(pid_from_file):
                    ServerManager.PID_FILE.unlink(missing_ok=True)
            except (ValueError, FileNotFoundError):
                ServerManager.PID_FILE.unlink(missing_ok=True)
        
        return len(cleaned_pids), cleaned_pids
    
    @staticmethod
    def get_server_pid() -> Optional[int]:
        """获取服务器进程PID"""
        # 优先读取PID文件（包含真实的bedrock_server PID）
        if ServerManager.PID_FILE.exists():
            try:
                pid = int(ServerManager.PID_FILE.read_text().strip())
                # 验证进程是否存在
                if psutil.pid_exists(pid):
                    return pid
                else:
                    # 进程不存在，删除PID文件
                    ServerManager.PID_FILE.unlink(missing_ok=True)
            except (ValueError, FileNotFoundError):
                pass
        
        # 如果PID文件不可用，尝试从systemd获取（可能是wrapper的PID）
        if ServerManager.is_systemd_managed():
            try:
                result = subprocess.run(
                    ['systemctl', 'show', '--property=MainPID', '--value', ServerManager.SYSTEMD_SERVICE],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and result.stdout.strip():
                    pid = int(result.stdout.strip())
                    if pid > 0 and psutil.pid_exists(pid):
                        return pid
            except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
                pass
        
        # 回退到原来的方法
        if not ServerManager.PID_FILE.exists():
            # 尝试通过进程名查找
            processes = ServerManager.find_all_bedrock_processes()
            if processes:
                # 返回最新的进程
                latest = max(processes, key=lambda x: x.get('create_time', 0))
                pid = latest['pid']
                ServerManager.PID_FILE.write_text(str(pid))
                return pid
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
        """启动服务器（优先使用systemd）"""
        status = ServerManager.get_server_status()
        if status['running']:
            return False, "服务器已在运行中"
        
        # 清理孤立的进程
        cleaned_count, cleaned_pids = ServerManager.cleanup_orphaned_processes()
        if cleaned_count > 0:
            time.sleep(1)  # 等待进程完全退出
        
        # 优先使用systemd启动
        if ServerManager.is_systemd_available():
            try:
                result = subprocess.run(
                    ['sudo', 'systemctl', 'start', ServerManager.SYSTEMD_SERVICE],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    time.sleep(2)  # 等待服务启动
                    if ServerManager.is_systemd_managed():
                        pid = ServerManager.get_server_pid()
                        return True, f"服务器已通过systemd启动 (PID: {pid})"
                    else:
                        return False, "systemd启动命令成功，但服务未运行"
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    return False, f"systemd启动失败: {error_msg}"
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                # systemd不可用，回退到直接启动
                pass
        
        # 回退到直接启动（如果没有systemd）
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
    def is_systemd_available() -> bool:
        """检查systemd是否可用"""
        try:
            result = subprocess.run(
                ['systemctl', '--version'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def stop_server() -> Tuple[bool, str]:
        """停止服务器（优先使用systemd）"""
        # 如果由systemd管理，使用systemd停止
        if ServerManager.is_systemd_managed():
            try:
                result = subprocess.run(
                    ['sudo', 'systemctl', 'stop', ServerManager.SYSTEMD_SERVICE],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    time.sleep(1)  # 等待服务停止
                    return True, "服务器已通过systemd停止"
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    return False, f"systemd停止失败: {error_msg}"
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                # systemd不可用，回退到直接停止
                pass
        
        # 回退到直接停止
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
        """重启服务器（优先使用systemd）"""
        # 如果由systemd管理，使用systemd重启
        if ServerManager.is_systemd_available():
            try:
                result = subprocess.run(
                    ['sudo', 'systemctl', 'restart', ServerManager.SYSTEMD_SERVICE],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if result.returncode == 0:
                    time.sleep(2)  # 等待服务重启
                    if ServerManager.is_systemd_managed():
                        pid = ServerManager.get_server_pid()
                        return True, f"服务器已通过systemd重启 (PID: {pid})"
                    else:
                        return False, "systemd重启命令成功，但服务未运行"
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    return False, f"systemd重启失败: {error_msg}"
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                # systemd不可用，回退到手动重启
                pass
        
        # 回退到手动重启
        # 先停止
        if ServerManager.get_server_status()['running']:
            success, message = ServerManager.stop_server()
            if not success:
                return False, f"停止失败: {message}"
            
            # 等待一下确保进程完全结束
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

