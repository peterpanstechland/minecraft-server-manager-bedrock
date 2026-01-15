from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import uuid
import traceback
from app import db, limiter
from app.models import Addon, User
from app.addon_manager import AddonManager
from app.curseforge import CurseForgeAPI
from app.server_manager import ServerManager
from app.log_monitor import log_monitor
from app.player_manager import PlayerManager
from app.auth import login_required_api, validate_request_data
from app.security import (
    sanitize_filename, validate_path, validate_file_extension,
    check_file_size, validate_uuid, validate_pack_type, sanitize_html
)
from config import Config
from datetime import datetime

bp = Blueprint('main', __name__)

def allowed_file(filename):
    return validate_file_extension(filename, Config.ALLOWED_EXTENSIONS)

# 认证路由
@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html'), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page and validate_path(Path('/'), Path(next_page)):
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('用户名或密码错误', 'error')
            return render_template('login.html'), 401
    
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('已成功登出', 'success')
    return redirect(url_for('main.login'))

# 前端页面路由
@bp.route('/')
@login_required
def index():
    return render_template('index.html')

@bp.route('/addons')
@login_required
def addons_page():
    return render_template('addons.html')

@bp.route('/server')
@login_required
def server_page():
    return render_template('server.html')

@bp.route('/logs')
@login_required
def logs_page():
    return render_template('logs.html')

@bp.route('/players')
@login_required
def players_page():
    return render_template('players.html')

# API路由 - Addon管理
@bp.route('/api/addons', methods=['GET'])
@login_required_api
def get_addons():
    """获取所有addon列表"""
    addons = Addon.query.all()
    return jsonify([addon.to_dict() for addon in addons])

@bp.route('/api/addons/scan', methods=['POST'])
@login_required_api
@limiter.limit("10 per minute")
def scan_addons():
    """扫描服务器目录中已存在的addon"""
    try:
        imported_count, errors = AddonManager.scan_existing_addons()
        message = f"扫描完成，导入 {imported_count} 个addon"
        if errors:
            message += f"，{len(errors)} 个错误"
        return jsonify({
            'success': True,
            'message': message,
            'imported_count': imported_count,
            'errors': errors
        })
    except Exception as e:
        current_app.logger.error(f'扫描addon失败: {str(e)}')
        return jsonify({'success': False, 'message': '扫描失败'}), 500

@bp.route('/api/addons/<int:addon_id>', methods=['GET'])
@login_required_api
def get_addon(addon_id):
    """获取单个addon信息"""
    addon = Addon.query.get_or_404(addon_id)
    return jsonify(addon.to_dict())

@bp.route('/api/addons/upload', methods=['POST'])
@login_required_api
@limiter.limit("10 per hour")
def upload_addon():
    """上传addon文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有文件'}), 400
        
        file = request.files['file']
        
        if not file.filename or file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400
        
        # 清理并验证文件名
        original_filename = sanitize_filename(file.filename)
        
        # 检查文件扩展名
        if not allowed_file(original_filename):
            file_ext = Path(original_filename).suffix.lower() if '.' in original_filename else '无'
            return jsonify({
                'success': False, 
                'message': f'不支持的文件类型 "{file_ext}"。支持的类型: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }), 400
        
        # 确保上传目录存在
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        
        file_path = None
        try:
            # 使用UUID生成安全的临时文件名
            file_ext = Path(original_filename).suffix or '.zip'
            if not file_ext.startswith('.'):
                file_ext = '.' + file_ext
            temp_filename = f"{uuid.uuid4().hex}{file_ext}"
            file_path = Config.UPLOAD_FOLDER / temp_filename
            
            # 验证路径安全性
            if not validate_path(Config.UPLOAD_FOLDER, file_path):
                return jsonify({'success': False, 'message': '文件路径无效'}), 400
            
            # 保存上传的文件
            file.save(str(file_path))
            
            # 验证文件是否成功保存
            if not file_path.exists():
                return jsonify({'success': False, 'message': '文件保存失败'}), 500
            
            file_size = file_path.stat().st_size
            
            # 验证文件大小
            size_ok, size_error = check_file_size(file_size, Config.MAX_UPLOAD_SIZE)
            if not size_ok:
                file_path.unlink(missing_ok=True)
                return jsonify({'success': False, 'message': size_error}), 400
            
            if file_size == 0:
                file_path.unlink(missing_ok=True)
                return jsonify({'success': False, 'message': '文件为空'}), 400
            
            # 安装addon
            success, message, addon = AddonManager.install_addon(file_path)
            
            # 删除临时文件
            if file_path.exists():
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
            # 清理临时文件
            if file_path and file_path.exists():
                file_path.unlink(missing_ok=True)
            raise
    except Exception as e:
        return jsonify({'success': False, 'message': '上传失败'}), 500

@bp.route('/api/addons/install', methods=['POST'])
@login_required_api
@limiter.limit("10 per hour")
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
        return jsonify({'success': False, 'message': '安装失败'}), 500

@bp.route('/api/addons/<int:addon_id>/enable', methods=['PUT'])
@login_required_api
@limiter.limit("30 per minute")
def enable_addon(addon_id):
    """启用addon"""
    success, message = AddonManager.enable_addon(addon_id)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/addons/<int:addon_id>/disable', methods=['PUT'])
@login_required_api
@limiter.limit("30 per minute")
def disable_addon(addon_id):
    """禁用addon"""
    success, message = AddonManager.disable_addon(addon_id)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/addons/enable-all', methods=['POST'])
@login_required_api
@limiter.limit("5 per hour")
def enable_all_addons():
    """启用所有addon"""
    try:
        addons = Addon.query.filter_by(enabled=False).all()
        enabled_count = 0
        errors = []
        
        for addon in addons:
            success, message = AddonManager.enable_addon(addon.id)
            if success:
                enabled_count += 1
            else:
                errors.append(f"{addon.name}: {message}")
        
        if enabled_count > 0:
            # 最后更新一次世界配置
            AddonManager.update_world_config()
            message = f"成功启用 {enabled_count} 个addon"
            if errors:
                message += f"，{len(errors)} 个失败"
            return jsonify({
                'success': True,
                'message': message,
                'enabled_count': enabled_count,
                'errors': errors
            })
        else:
            return jsonify({
                'success': False,
                'message': '没有可启用的addon' if not errors else f'启用失败: {"; ".join(errors)}'
            }), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'批量启用失败: {str(e)}'}), 500

@bp.route('/api/addons/<int:addon_id>/update', methods=['POST'])
@login_required_api
@limiter.limit("10 per hour")
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
@login_required_api
@limiter.limit("20 per hour")
def delete_addon(addon_id):
    """删除addon"""
    success, message = AddonManager.delete_addon(addon_id)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

# API路由 - 服务器控制
@bp.route('/api/server/status', methods=['GET'])
@login_required_api
def server_status():
    """获取服务器状态"""
    status = ServerManager.get_server_status()
    return jsonify(status)

@bp.route('/api/server/start', methods=['POST'])
@login_required_api
@limiter.limit("10 per hour")
def start_server():
    """启动服务器"""
    success, message = ServerManager.start_server()
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/server/stop', methods=['POST'])
@login_required_api
@limiter.limit("10 per hour")
def stop_server():
    """停止服务器"""
    success, message = ServerManager.stop_server()
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/server/restart', methods=['POST'])
@login_required_api
@limiter.limit("10 per hour")
def restart_server():
    """重启服务器"""
    success, message = ServerManager.restart_server()
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

# API路由 - 日志
@bp.route('/api/logs', methods=['GET'])
@login_required_api
def get_logs():
    """获取日志"""
    lines = request.args.get('lines', 100, type=int)
    logs = log_monitor.get_logs(lines)
    return jsonify({'logs': logs})

@bp.route('/api/logs/search', methods=['GET'])
@login_required_api
def search_logs():
    """搜索日志"""
    query = request.args.get('q', '')
    lines = request.args.get('lines', 1000, type=int)
    
    if not query:
        return jsonify({'logs': []})
    
    results = log_monitor.search_logs(query, lines)
    return jsonify({'logs': results})

@bp.route('/api/logs/stream')
@login_required_api
def stream_logs():
    """流式传输日志（SSE）"""
    return log_monitor.stream_logs()

# API路由 - 玩家管理
@bp.route('/api/players', methods=['GET'])
@login_required_api
@limiter.limit("1000 per hour")  # 玩家列表刷新频繁，设置宽松的限制
@limiter.limit("1000 per hour")  # 玩家列表刷新频繁，设置宽松的限制
def get_players():
    """获取在线玩家列表"""
    success, message, players = PlayerManager.get_online_players()
    return jsonify({
        'success': success,
        'message': message,
        'players': players
    })

@bp.route('/api/players/invincible', methods=['POST'])
@login_required_api
@limiter.limit("30 per minute")
def set_player_invincible():
    """设置玩家无敌模式"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '缺少请求数据'}), 400
    
    player_name = data.get('player', '').strip()
    enable = data.get('enable', True)
    
    if not player_name:
        return jsonify({'success': False, 'message': '缺少玩家名称'}), 400
    
    success, message = PlayerManager.set_invincible(player_name, enable)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/players/kick', methods=['POST'])
@login_required_api
@limiter.limit("20 per minute")
def kick_player():
    """踢出玩家"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '缺少请求数据'}), 400
    
    player_name = data.get('player', '').strip()
    reason = data.get('reason', '被管理员踢出')
    
    if not player_name:
        return jsonify({'success': False, 'message': '缺少玩家名称'}), 400
    
    success, message = PlayerManager.kick_player(player_name, reason)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/players/command', methods=['POST'])
@login_required_api
@limiter.limit("30 per minute")
def send_server_command():
    """发送服务器命令"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '缺少请求数据'}), 400
    
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({'success': False, 'message': '缺少命令'}), 400
    
    # 安全检查：限制某些危险命令
    dangerous_commands = ['stop', 'reload', 'save-off']
    cmd_lower = command.lower().split()[0] if command else ''
    
    if cmd_lower in dangerous_commands:
        return jsonify({
            'success': False, 
            'message': f'命令 "{cmd_lower}" 被禁止，请使用服务器控制页面'
        }), 403
    
    success, message = PlayerManager.send_command(command)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/api/players/message', methods=['POST'])
@login_required_api
@limiter.limit("20 per minute")
def send_message_to_players():
    """向玩家发送消息"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '缺少请求数据'}), 400
    
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'message': '缺少消息内容'}), 400
    
    success, msg = PlayerManager.send_message(message)
    
    if success:
        return jsonify({'success': True, 'message': msg})
    else:
        return jsonify({'success': False, 'message': msg}), 400

