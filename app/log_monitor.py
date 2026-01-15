import time
import threading
import subprocess
from pathlib import Path
from typing import List, Optional, Callable
from config import Config
from flask import Response, stream_with_context

class LogMonitor:
    """监控服务器日志"""
    
    def __init__(self):
        self.log_file = Config.LOG_FILE
        self.last_position = 0
        self.running = False
        self.callbacks: List[Callable] = []
        self.use_systemd = self._check_systemd_available()
    
    def _check_systemd_available(self) -> bool:
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
    
    def _get_logs_from_systemd(self, lines: int = 100) -> List[str]:
        """从systemd journal获取日志"""
        if not self.use_systemd:
            return []
        
        try:
            result = subprocess.run(
                ['journalctl', '-u', 'bedrock.service', '-n', str(lines), '--no-pager', '-o', 'cat'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout:
                log_lines = result.stdout.strip().split('\n')
                # 过滤掉空行
                return [line.rstrip('\n\r') for line in log_lines if line.strip()]
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"Error reading from systemd: {e}")
        
        return []
    
    def get_logs(self, lines: int = 100) -> List[str]:
        """获取最近的日志行"""
        # 优先从日志文件读取
        file_logs = []
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    # 过滤掉第一行如果是文件名（Bedrock服务器会在文件开头写入文件名）
                    if all_lines and all_lines[0].strip() == 'Dedicated_Server.txt':
                        all_lines = all_lines[1:]
                    # 过滤掉空行并去除末尾换行符
                    file_logs = [line.rstrip('\n\r') for line in all_lines if line.strip()]
            except Exception as e:
                print(f"Error reading log file: {e}")
        
        # 如果日志文件为空或不存在，尝试从systemd journal读取
        if not file_logs and self.use_systemd:
            systemd_logs = self._get_logs_from_systemd(lines)
            if systemd_logs:
                return systemd_logs[-lines:] if len(systemd_logs) > lines else systemd_logs
        
        # 返回文件日志
        return file_logs[-lines:] if len(file_logs) > lines else file_logs
    
    def search_logs(self, query: str, lines: int = 1000) -> List[str]:
        """搜索日志"""
        if not self.log_file.exists():
            return []
        
        try:
            results = []
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                # 过滤掉第一行如果是文件名
                if all_lines and all_lines[0].strip() == 'Dedicated_Server.txt':
                    all_lines = all_lines[1:]
                # 只搜索最近的lines行
                search_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in search_lines:
                    line_stripped = line.strip()
                    if line_stripped and query.lower() in line_stripped.lower():
                        results.append(line_stripped)
            
            return results
        except Exception as e:
            print(f"Error searching logs: {e}")
            return []
    
    def get_new_logs(self) -> List[str]:
        """获取自上次读取以来的新日志"""
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
                # 过滤掉空行和文件名行
                return [line.strip() for line in new_lines if line.strip() and line.strip() != 'Dedicated_Server.txt']
        except Exception as e:
            print(f"Error reading new logs: {e}")
            return []
    
    def stream_logs(self):
        """流式传输日志（SSE格式）"""
        def generate():
            # 发送初始的最近日志
            recent_logs = self.get_logs(50)
            for line in recent_logs:
                line_stripped = line.strip()
                if line_stripped:
                    yield f"data: {line_stripped}\n\n"
            
            # 持续监控新日志
            while True:
                new_logs = self.get_new_logs()
                for line in new_logs:
                    if line:
                        yield f"data: {line}\n\n"
                
                time.sleep(0.5)  # 每0.5秒检查一次
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    
    def format_log_line(self, line: str) -> dict:
        """格式化日志行，提取时间戳、级别等信息"""
        # 简单的日志解析（可以根据实际格式调整）
        log_entry = {
            'raw': line,
            'timestamp': None,
            'level': 'info',
            'message': line
        }
        
        # 尝试提取时间戳（Bedrock服务器日志格式可能不同）
        # 这里提供一个基础框架，可以根据实际日志格式调整
        if 'ERROR' in line.upper():
            log_entry['level'] = 'error'
        elif 'WARN' in line.upper():
            log_entry['level'] = 'warning'
        
        return log_entry

# 全局日志监控实例
log_monitor = LogMonitor()

