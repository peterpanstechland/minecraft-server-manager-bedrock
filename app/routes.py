from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from pathlib import Path
import os
from app import db
from app.models import Addon
from app.addon_manager import AddonManager
from app.curseforge import CurseForgeAPI
from app.server_manager import ServerManager
from app.log_monitor import log_monitor
from config import Config
from datetime import datetime

bp = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# 前端页面路由
@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/addons')
def addons_page():
    return render_template('addons.html')

@bp.route('/server')
def server_page():
    return render_template('server.html')

@bp.route('/logs')
def logs_page():
    return render_template('logs.html')

# API路由 - Addon管理
@bp.route('/api/addons', methods=['GET'])
def get_addons():
    """获取所有addon列表"""
    addons = Addon.query.all()
    return jsonify([addon.to_dict() for addon in addons])

@bp.route('/api/addons/<int:addon_id>', methods=['GET'])
def get_addon(addon_id):
    """获取单个addon信息"""
    addon = Addon.query.get_or_404(addon_id)
    return jsonify(addon.to_dict())

@bp.route('/api/addons/upload', methods=['POST'])
def upload_addon():
    """上传addon文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '文件名为空'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '不支持的文件类型'}), 400
    
    try:
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = Config.UPLOAD_FOLDER / filename
        file.save(str(file_path))
        
        # 安装addon
        success, message, addon = AddonManager.install_addon(file_path)
        
        # 删除临时文件
        file_path.unlink(missing_ok=True)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'addon': addon.to_dict() if addon else None
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'}), 500

@bp.route('/api/addons/install', methods=['POST'])
def install_from_curseforge():
    """从CurseForge安装addon"""
    data = request.get_json()
    url_or_id = data.get('url') or data.get('id')
    
    if not url_or_id:
        return jsonify({'success': False, 'message': '缺少URL或ID'}), 400
    
    try:
        # 从CurseForge下载
        success, message, file_path, cf_info = CurseForgeAPI.install_from_curseforge(url_or_id)
        
        if not success:
            return jsonify({'success': False, 'message': message}), 400
        
        # 安装addon
        install_success, install_message, addon = AddonManager.install_addon(
            file_path,
            curseforge_id=cf_info.get('project_id'),
            curseforge_url=cf_info.get('url')
        )
        
        # 删除临时文件
        if file_path.exists():
            file_path.unlink()
        
        if install_success:
            return jsonify({
                'success': True,
                'message': install_message,
                'addon': addon.to_dict() if addon else None
            })
        else:
            return jsonify({'success': False, 'message': install_message}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'安装失败: {str(e)}'}), 500

@bp.route('/api/addons/<int:addon_id>/enable', methods=['PUT'])
def enable_addon(addon_id):
    """启用addon"""
    success, message = AddonManager.enable_addon(addon_id)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/addons/<int:addon_id>/disable', methods=['PUT'])
def disable_addon(addon_id):
    """禁用addon"""
    success, message = AddonManager.disable_addon(addon_id)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/addons/<int:addon_id>/update', methods=['POST'])
def check_update_addon(addon_id):
    """检查addon更新"""
    addon = Addon.query.get_or_404(addon_id)
    
    if not addon.curseforge_id:
        return jsonify({'success': False, 'message': '此addon没有关联CurseForge项目'}), 400
    
    try:
        has_update, update_info = CurseForgeAPI.check_update(addon)
        
        if has_update:
            # 下载并更新
            success, message, file_path, cf_info = CurseForgeAPI.install_from_curseforge(
                addon.curseforge_id
            )
            
            if success:
                # 先禁用旧版本
                AddonManager.disable_addon(addon_id)
                
                # 删除旧文件
                if Path(addon.local_path).exists():
                    import shutil
                    shutil.rmtree(addon.local_path, ignore_errors=True)
                
                # 部署新版本
                pack_info = AddonManager.extract_pack_info(file_path)
                if pack_info:
                    deploy_success, deploy_message = AddonManager.deploy_addon(file_path, pack_info)
                    if deploy_success:
                        # 更新数据库记录
                        addon.version = pack_info['version']
                        addon.local_path = deploy_message
                        addon.last_checked = datetime.utcnow()
                        db.session.commit()
                        
                        # 重新启用
                        AddonManager.enable_addon(addon_id)
                
                # 删除临时文件
                if file_path.exists():
                    file_path.unlink()
                
                return jsonify({
                    'success': True,
                    'message': '更新成功',
                    'update_info': update_info
                })
            else:
                return jsonify({'success': False, 'message': message}), 400
        else:
            addon.last_checked = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'success': True,
                'message': '已是最新版本',
                'update_info': None
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'检查更新失败: {str(e)}'}), 500

@bp.route('/api/addons/<int:addon_id>', methods=['DELETE'])
def delete_addon(addon_id):
    """删除addon"""
    success, message = AddonManager.delete_addon(addon_id)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

# API路由 - 服务器控制
@bp.route('/api/server/status', methods=['GET'])
def server_status():
    """获取服务器状态"""
    status = ServerManager.get_server_status()
    return jsonify(status)

@bp.route('/api/server/start', methods=['POST'])
def start_server():
    """启动服务器"""
    success, message = ServerManager.start_server()
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/server/stop', methods=['POST'])
def stop_server():
    """停止服务器"""
    success, message = ServerManager.stop_server()
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/server/restart', methods=['POST'])
def restart_server():
    """重启服务器"""
    success, message = ServerManager.restart_server()
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

# API路由 - 日志
@bp.route('/api/logs', methods=['GET'])
def get_logs():
    """获取日志"""
    lines = request.args.get('lines', 100, type=int)
    logs = log_monitor.get_logs(lines)
    return jsonify({'logs': logs})

@bp.route('/api/logs/search', methods=['GET'])
def search_logs():
    """搜索日志"""
    query = request.args.get('q', '')
    lines = request.args.get('lines', 1000, type=int)
    
    if not query:
        return jsonify({'logs': []})
    
    results = log_monitor.search_logs(query, lines)
    return jsonify({'logs': results})

@bp.route('/api/logs/stream')
def stream_logs():
    """流式传输日志（SSE）"""
    return log_monitor.stream_logs()

