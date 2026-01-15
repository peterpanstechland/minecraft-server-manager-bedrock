#!/usr/bin/env python3
"""
修复资源包/行为包的文件名
处理特殊字符、空格、编码问题等
"""

import sys
import zipfile
import json
import shutil
import re
from pathlib import Path
import tempfile

def clean_filename(name):
    """清理文件名，移除特殊字符"""
    # 移除 Minecraft 颜色代码
    name = re.sub(r'§[0-9a-fk-or]', '', name, flags=re.IGNORECASE)
    # 移除其他特殊字符
    name = re.sub(r'[<>:"/\\|?*\[\]]', '', name)
    # 替换多个空格为单个下划线
    name = re.sub(r'\s+', '_', name)
    # 移除首尾空格和下划线
    name = name.strip('_').strip()
    # 如果为空，使用默认名称
    if not name:
        name = 'pack'
    return name

def extract_pack_name(manifest_path):
    """从 manifest.json 提取包名"""
    try:
        # 尝试不同的编码读取
        for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'cp936', 'latin1']:
            try:
                with open(manifest_path, 'r', encoding=encoding) as f:
                    manifest = json.load(f)
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        else:
            # 如果都失败，使用utf-8并忽略错误
            with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                manifest = json.load(f)
        
        header = manifest.get('header', {})
        name = header.get('name', '')
        
        # 如果是翻译键，尝试使用 description
        if name.startswith('pack.') or name.startswith('resourcePack.'):
            description = header.get('description', '')
            if description and not description.startswith('pack.'):
                name = description
            else:
                name = ''
        
        return clean_filename(name) if name else None
    except Exception as e:
        print(f"   ⚠️  读取 manifest.json 失败: {e}")
        return None

def fix_zip_pack_names(zip_path: Path, pack_type: str):
    """修复zip文件中的包名"""
    if not zip_path.exists():
        print(f"❌ 文件不存在: {zip_path}")
        return False
    
    print(f"\n{'='*70}")
    print(f"修复 {pack_type} 文件名: {zip_path.name}")
    print(f"{'='*70}\n")
    
    temp_dir = tempfile.mkdtemp()
    fixed_packs = []
    
    try:
        # 解压zip文件（处理编码问题）
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 尝试不同的编码
            for encoding in ['utf-8', 'gbk', 'cp936', 'latin1']:
                try:
                    # 设置文件名编码
                    zip_ref.setpassword(None)
                    # 尝试解压
                    for member in zip_ref.namelist():
                        try:
                            # 尝试解码文件名
                            if isinstance(member, bytes):
                                decoded_name = member.decode(encoding)
                            else:
                                decoded_name = member
                            # 提取文件
                            zip_ref.extract(member, temp_dir)
                            # 如果文件名需要重命名
                            if decoded_name != member:
                                extracted_path = Path(temp_dir) / member
                                if extracted_path.exists():
                                    target_path = Path(temp_dir) / decoded_name
                                    target_path.parent.mkdir(parents=True, exist_ok=True)
                                    if extracted_path.is_file():
                                        shutil.move(str(extracted_path), str(target_path))
                                    elif extracted_path.is_dir():
                                        shutil.move(str(extracted_path), str(target_path))
                        except (UnicodeDecodeError, UnicodeError):
                            continue
                    break  # 成功解压，退出循环
                except Exception:
                    continue
            
            # 如果上面的方法失败，使用标准方法
            try:
                zip_ref.extractall(temp_dir)
            except:
                pass
        
        temp_path = Path(temp_dir)
        
        # 查找所有manifest.json
        manifest_files = list(temp_path.rglob('manifest.json'))
        
        if not manifest_files:
            # 检查是否有嵌套的zip文件
            zip_files = list(temp_path.rglob('*.zip'))
            if zip_files:
                print(f"找到 {len(zip_files)} 个嵌套的zip文件，解压中...")
                for zip_file in zip_files:
                    try:
                        nested_dir = zip_file.parent / zip_file.stem
                        nested_dir.mkdir(exist_ok=True)
                        with zipfile.ZipFile(zip_file, 'r') as nested_zip:
                            nested_zip.extractall(nested_dir)
                        zip_file.unlink()
                    except Exception as e:
                        print(f"   ⚠️  解压 {zip_file.name} 失败: {e}")
                
                manifest_files = list(temp_path.rglob('manifest.json'))
        
        if not manifest_files:
            print(f"❌ 未找到任何 manifest.json 文件")
            return False
        
        print(f"✅ 找到 {len(manifest_files)} 个包\n")
        
        # 处理每个包
        for manifest_file in manifest_files:
            pack_root = manifest_file.parent
            
            # 获取原始目录名
            original_name = pack_root.name
            print(f"📦 处理: {original_name}")
            
            # 从manifest.json获取正确的名称
            pack_name = extract_pack_name(manifest_file)
            
            if pack_name:
                # 使用manifest中的名称
                new_name = pack_name
                print(f"   ✅ 使用manifest名称: {new_name}")
            else:
                # 清理原始名称
                new_name = clean_filename(original_name)
                print(f"   ⚠️  使用清理后的名称: {new_name}")
            
            # 如果名称改变，重命名目录
            if new_name != original_name:
                new_pack_root = pack_root.parent / new_name
                if new_pack_root.exists():
                    # 如果目标已存在，添加后缀
                    counter = 1
                    while (pack_root.parent / f"{new_name}_{counter}").exists():
                        counter += 1
                    new_name = f"{new_name}_{counter}"
                    new_pack_root = pack_root.parent / new_name
                
                shutil.move(str(pack_root), str(new_pack_root))
                pack_root = new_pack_root
                print(f"   ✅ 已重命名为: {new_name}")
            
            fixed_packs.append({
                'original': original_name,
                'fixed': new_name,
                'path': pack_root
            })
        
        # 创建修复后的zip文件
        output_zip = zip_path.parent / f"{zip_path.stem}_fixed.zip"
        print(f"\n📦 创建修复后的zip文件: {output_zip.name}")
        
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_out:
            for pack in fixed_packs:
                pack_path = pack['path']
                # 添加整个包目录到zip
                for file_path in pack_path.rglob('*'):
                    if file_path.is_file():
                        # 计算相对路径（从包根目录开始）
                        try:
                            arcname = str(file_path.relative_to(pack_path.parent))
                            # 确保使用UTF-8编码
                            if isinstance(arcname, bytes):
                                arcname = arcname.decode('utf-8', errors='replace')
                            # 写入文件，使用UTF-8编码
                            zip_out.write(file_path, arcname.encode('utf-8', errors='replace').decode('utf-8'))
                        except Exception as e:
                            print(f"   ⚠️  添加文件失败 {file_path}: {e}")
                            continue
        
        print(f"✅ 修复完成！")
        print(f"\n修复后的文件: {output_zip}")
        print(f"\n修复的包:")
        for pack in fixed_packs:
            if pack['original'] != pack['fixed']:
                print(f"  {pack['original']} → {pack['fixed']}")
            else:
                print(f"  {pack['fixed']} (无需修改)")
        
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
        print("用法: python fix_pack_names.py <zip文件1> [zip文件2] ...")
        print("\n示例:")
        print("  python fix_pack_names.py resource_packs.zip")
        print("  python fix_pack_names.py resource_packs.zip behavior_packs.zip")
        sys.exit(1)
    
    print("="*70)
    print("包文件名修复工具")
    print("="*70)
    
    success_count = 0
    for zip_file in sys.argv[1:]:
        zip_path = Path(zip_file)
        
        # 判断包类型
        if 'resource' in zip_path.name.lower():
            pack_type = 'resource'
        elif 'behavior' in zip_path.name.lower():
            pack_type = 'behavior'
        else:
            pack_type = 'unknown'
        
        if fix_zip_pack_names(zip_path, pack_type):
            success_count += 1
    
    print("\n" + "="*70)
    print(f"完成！成功修复 {success_count}/{len(sys.argv)-1} 个文件")
    print("="*70)
    print("\n下一步:")
    print("1. 检查修复后的 *_fixed.zip 文件")
    print("2. 使用修复后的文件安装:")
    print("   python scripts/install_marketplace_packs.py resource_packs_fixed.zip behavior_packs_fixed.zip")
    print("="*70)

if __name__ == '__main__':
    main()

