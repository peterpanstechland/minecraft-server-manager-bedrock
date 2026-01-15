#!/usr/bin/env python3
"""
清理孤立的bedrock_server进程和addon文件
可以添加到crontab定期运行
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.server_manager import ServerManager
from app.addon_manager import AddonManager
from app import create_app, db

def main():
    """清理孤立进程和文件"""
    app = create_app()
    with app.app_context():
        # 清理孤立进程
        print("检查并清理孤立的bedrock_server进程...")
        cleaned_count, cleaned_pids = ServerManager.cleanup_orphaned_processes()
        
        if cleaned_count > 0:
            print(f"✓ 清理了 {cleaned_count} 个孤立进程: {cleaned_pids}")
        else:
            print("✓ 没有发现孤立进程")
        
        # 显示当前状态
        status = ServerManager.get_server_status()
        if status['running']:
            print(f"✓ 服务器正在运行 (PID: {status['pid']}, 管理方式: {status.get('managed_by', 'unknown')})")
        else:
            print("✓ 服务器未运行")
        
        print()
        
        # 清理孤立文件
        print("检查并清理孤立的addon文件...")
        from os.path import expanduser
        search_paths = [Path(expanduser("~"))]
        
        cleaned_files_count, cleaned_files = AddonManager.cleanup_orphaned_files(search_paths)
        
        if cleaned_files_count > 0:
            print(f"✓ 清理了 {cleaned_files_count} 个孤立文件:")
            for file_path in cleaned_files:
                print(f"    - {file_path}")
        else:
            print("✓ 没有发现孤立文件")

if __name__ == '__main__':
    main()

