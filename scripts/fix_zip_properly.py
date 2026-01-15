#!/usr/bin/env python3
"""
正确修复zip文件 - 处理编码和目录结构问题
"""

import sys
import subprocess
import zipfile
import shutil
from pathlib import Path
import tempfile
import json

def fix_zip_properly(zip_path: Path):
    """使用系统unzip命令正确解压，然后重新打包"""
    if not zip_path.exists():
        print(f"❌ 文件不存在: {zip_path}")
        return False
    
    print(f"\n{'='*70}")
    print(f"修复: {zip_path.name}")
    print(f"{'='*70}\n")
    
    temp_dir = tempfile.mkdtemp()
    output_zip = zip_path.parent / f"{zip_path.stem}_fixed.zip"
    
    try:
        # 方法1: 尝试使用系统unzip（支持-O选项指定编码）
        print("📦 尝试使用系统unzip解压...")
        try:
            # 尝试GBK编码（Windows中文）
            result = subprocess.run(
                ['unzip', '-q', '-O', 'gbk', str(zip_path), '-d', temp_dir],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("   ✅ 使用GBK编码成功解压")
            else:
                # 尝试UTF-8
                result = subprocess.run(
                    ['unzip', '-q', '-O', 'utf-8', str(zip_path), '-d', temp_dir],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("   ✅ 使用UTF-8编码成功解压")
                else:
                    raise Exception("unzip失败")
        except Exception as e:
            print(f"   ⚠️  系统unzip失败: {e}")
            print("   📦 使用Python zipfile解压...")
            # 回退到Python zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_in:
                zip_in.extractall(temp_dir)
        
        # 修复目录结构（处理以=结尾的目录名）
        print("\n🔧 修复目录结构...")
        temp_path = Path(temp_dir)
        
        # 查找所有以=结尾的文件/目录
        for item in temp_path.rglob('*'):
            if item.name.endswith('=') and item.is_file():
                # 这应该是一个目录，但被当作文件了
                # 检查是否有同名目录
                parent = item.parent
                dir_name = item.name
                
                # 如果这是一个应该作为目录的条目
                # 检查是否有子文件需要这个目录
                has_children = False
                for other_item in parent.iterdir():
                    if other_item.name.startswith(dir_name + '/'):
                        has_children = True
                        break
                
                if has_children or item.suffix == '':
                    # 创建目录并移动内容
                    target_dir = parent / dir_name
                    if not target_dir.exists():
                        target_dir.mkdir()
                        print(f"   ✅ 创建目录: {target_dir.relative_to(temp_path)}")
        
        # 查找manifest.json并重命名目录
        print("\n📝 查找并重命名包目录...")
        manifest_files = list(temp_path.rglob('manifest.json'))
        
        for manifest_file in manifest_files:
            pack_root = manifest_file.parent
            
            # 读取manifest获取正确名称
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                header = manifest.get('header', {})
                pack_name = header.get('name', '')
                
                # 清理名称
                if pack_name.startswith('pack.') or pack_name.startswith('resourcePack.'):
                    pack_name = pack_root.name
                else:
                    # 移除颜色代码和特殊字符
                    import re
                    pack_name = re.sub(r'§[0-9a-fk-or]', '', pack_name, flags=re.IGNORECASE)
                    pack_name = re.sub(r'[<>:"/\\|?*\[\]()]', '', pack_name)
                    pack_name = re.sub(r'\s+', '_', pack_name).strip('_')
                
                if not pack_name:
                    pack_name = pack_root.name
                
                # 如果名称不同，重命名
                if pack_name != pack_root.name:
                    new_pack_root = pack_root.parent / pack_name
                    if not new_pack_root.exists():
                        shutil.move(str(pack_root), str(new_pack_root))
                        print(f"   ✅ {pack_root.name} → {pack_name}")
                    else:
                        print(f"   ⚠️  {pack_name} 已存在，跳过重命名")
                        
            except Exception as e:
                print(f"   ⚠️  处理 {manifest_file} 失败: {e}")
        
        # 创建新的zip文件
        print(f"\n📦 创建修复后的zip文件...")
        file_count = 0
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    try:
                        arcname = str(file_path.relative_to(temp_path)).replace('\\', '/')
                        zip_out.write(file_path, arcname)
                        file_count += 1
                    except Exception as e:
                        continue
        
        print(f"   ✅ 已添加 {file_count} 个文件")
        print(f"   ✅ 输出文件: {output_zip}")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    if len(sys.argv) < 2:
        print("用法: python fix_zip_properly.py <zip文件1> [zip文件2] ...")
        sys.exit(1)
    
    print("="*70)
    print("ZIP文件修复工具（正确处理编码和目录结构）")
    print("="*70)
    
    success_count = 0
    for zip_file in sys.argv[1:]:
        if fix_zip_properly(Path(zip_file)):
            success_count += 1
    
    print("\n" + "="*70)
    print(f"完成！成功修复 {success_count}/{len(sys.argv)-1} 个文件")
    print("="*70)

if __name__ == '__main__':
    main()

