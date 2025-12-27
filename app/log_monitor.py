import time
import threading
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
    
    def get_logs(self, lines: int = 100) -> List[str]:
        """获取最近的日志行"""
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            print(f"Error reading logs: {e}")
            return []
    
    def search_logs(self, query: str, lines: int = 1000) -> List[str]:
        """搜索日志"""
        if not self.log_file.exists():
            return []
        
        try:
            results = []
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                # 只搜索最近的lines行
                search_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in search_lines:
                    if query.lower() in line.lower():
                        results.append(line.strip())
            
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
                return [line.strip() for line in new_lines if line.strip()]
        except Exception as e:
            print(f"Error reading new logs: {e}")
            return []
    
    def stream_logs(self):
        """流式传输日志（SSE格式）"""
        def generate():
            # 发送初始的最近日志
            recent_logs = self.get_logs(50)
            for line in recent_logs:
                if line.strip():
                    yield f"data: {line}\n\n"
            
            # 持续监控新日志
            while True:
                new_logs = self.get_new_logs()
                for line in new_logs:
                    if line.strip():
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

