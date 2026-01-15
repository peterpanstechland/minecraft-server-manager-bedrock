#!/usr/bin/env python3
"""
修复zip文件的编码问题
处理Windows创建的zip文件（GBK编码）在Linux上的乱码问题
"""

import sys
import zipfile
import shutil
from pathlib import Path
import tempfile

def fix_zip_encoding(zip_path: Path):
    """修复zip文件的编码问题"""
    if not zip_path.exists():
        print(f"❌ 文件不存在: {zip_path}")
        return False
    
    print(f"\n{'='*70}")
    print(f"修复编码: {zip_path.name}")
    print(f"{'='*70}\n")
    
    temp_dir = tempfile.mkdtemp()
    output_zip = zip_path.parent / f"{zip_path.stem}_fixed.zip"
    
    try:
        # 读取原始zip文件
        with zipfile.ZipFile(zip_path, 'r') as zip_in:
            # 获取所有文件名
            file_list = zip_in.namelist()
            print(f"找到 {len(file_list)} 个文件/目录\n")
            
            # 第一步：创建所有目录结构
            dirs_created = set()
            for member in file_list:
                # 尝试不同的编码解码文件名
                decoded_name = None
                for encoding in ['utf-8', 'gbk', 'cp936', 'latin1']:
                    try:
                        if isinstance(member, bytes):
                            decoded_name = member.decode(encoding)
                        else:
                            # 尝试编码后再解码
                            decoded_name = member.encode('latin1').decode(encoding)
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                
                if decoded_name is None:
                    decoded_name = member
                
                # 移除末尾的 = 如果存在（这是编码问题的表现）
                if decoded_name.endswith('=') and decoded_name.count('=') == 1 and '/' not in decoded_name.split('=')[0]:
                    # 这可能是base64编码的目录名，保留原样
                    pass
                
                # 创建目录结构
                parts = decoded_name.split('/')
                for i in range(1, len(parts)):
                    dir_path = '/'.join(parts[:i])
                    if dir_path and dir_path not in dirs_created:
                        target_dir = Path(temp_dir) / dir_path
                        # 如果路径以 = 结尾，可能是目录
                        if target_dir.name.endswith('='):
                            # 确保是目录
                            target_dir.mkdir(parents=True, exist_ok=True)
                            dirs_created.add(dir_path)
                        else:
                            target_dir.mkdir(parents=True, exist_ok=True)
                            dirs_created.add(dir_path)
            
            # 第二步：提取所有文件
            for member in file_list:
                try:
                    # 尝试不同的编码解码文件名
                    decoded_name = None
                    for encoding in ['utf-8', 'gbk', 'cp936', 'latin1']:
                        try:
                            if isinstance(member, bytes):
                                decoded_name = member.decode(encoding)
                            else:
                                decoded_name = member.encode('latin1').decode(encoding)
                            break
                        except (UnicodeDecodeError, UnicodeError):
                            continue
                    
                    if decoded_name is None:
                        decoded_name = member
                    
                    # 跳过目录条目（以 / 结尾）
                    if decoded_name.endswith('/'):
                        continue
                    
                    # 提取文件
                    try:
                        data = zip_in.read(member)
                    except Exception as e:
                        continue
                    
                    # 创建目标路径
                    target_path = Path(temp_dir) / decoded_name
                    # 确保父目录存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 如果父目录是文件（错误情况），删除它
                    if target_path.parent.exists() and target_path.parent.is_file():
                        target_path.parent.unlink()
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 写入文件
                    with open(target_path, 'wb') as f:
                        f.write(data)
                    
                except Exception as e:
                    continue
        
        # 创建新的zip文件（使用UTF-8编码）
        print(f"\n📦 创建修复后的zip文件...")
        file_count = 0
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            temp_path = Path(temp_dir)
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    try:
                        # 使用UTF-8编码的文件名
                        arcname = str(file_path.relative_to(temp_path))
                        # 确保路径使用正斜杠
                        arcname = arcname.replace('\\', '/')
                        zip_out.write(file_path, arcname)
                        file_count += 1
                    except Exception as e:
                        continue
        
        print(f"   ✅ 已添加 {file_count} 个文件到zip")
        
        print(f"✅ 修复完成！")
        print(f"   输出文件: {output_zip}")
        
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
        print("用法: python fix_encoding.py <zip文件1> [zip文件2] ...")
        print("\n示例:")
        print("  python fix_encoding.py resource_packs.zip")
        print("  python fix_encoding.py resource_packs.zip behavior_packs.zip")
        sys.exit(1)
    
    print("="*70)
    print("ZIP文件编码修复工具")
    print("="*70)
    
    success_count = 0
    for zip_file in sys.argv[1:]:
        if fix_zip_encoding(Path(zip_file)):
            success_count += 1
    
    print("\n" + "="*70)
    print(f"完成！成功修复 {success_count}/{len(sys.argv)-1} 个文件")
    print("="*70)

if __name__ == '__main__':
    main()

