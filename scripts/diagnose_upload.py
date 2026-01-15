#!/usr/bin/env python3
"""
诊断上传失败的工具
用于检查 ZIP 文件的结构和内容
"""

import sys
import zipfile
import json
from pathlib import Path
import tempfile
import shutil

def diagnose_zip_file(zip_path: Path):
    """诊断 ZIP 文件的结构"""
    print("=" * 70)
    print(f"诊断文件: {zip_path}")
    print("=" * 70)
    
    if not zip_path.exists():
        print(f"❌ 文件不存在: {zip_path}")
        return False
    
    # 检查文件大小
    file_size = zip_path.stat().st_size
    print(f"\n文件大小: {file_size:,} 字节 ({file_size / 1024:.2f} KB)")
    
    if file_size == 0:
        print("❌ 文件为空")
        return False
    
    # 检查 ZIP 文件格式
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"\n✅ ZIP 文件格式有效")
            print(f"包含 {len(file_list)} 个文件/目录")
            
            # 查找 manifest.json
            manifest_files = [f for f in file_list if f.endswith('manifest.json')]
            
            if manifest_files:
                print(f"\n✅ 找到 {len(manifest_files)} 个 manifest.json:")
                for mf in manifest_files:
                    print(f"  - {mf}")
            else:
                print("\n❌ 未找到 manifest.json")
                print("\n文件列表（前20个）:")
                for f in file_list[:20]:
                    print(f"  - {f}")
                if len(file_list) > 20:
                    print(f"  ... 还有 {len(file_list) - 20} 个文件")
                return False
            
            # 尝试读取第一个 manifest.json
            if manifest_files:
                manifest_path = manifest_files[0]
                try:
                    manifest_content = zip_ref.read(manifest_path).decode('utf-8')
                    manifest_data = json.loads(manifest_content)
                    
                    print(f"\n✅ manifest.json 格式有效")
                    print(f"位置: {manifest_path}")
                    
                    # 检查必需字段
                    header = manifest_data.get('header', {})
                    if header:
                        print(f"\nHeader 信息:")
                        print(f"  UUID: {header.get('uuid', '缺失')}")
                        print(f"  名称: {header.get('name', '缺失')}")
                        print(f"  版本: {header.get('version', '缺失')}")
                        
                        if not header.get('uuid'):
                            print("  ❌ UUID 缺失")
                            return False
                    else:
                        print("  ❌ Header 字段缺失")
                        return False
                    
                    # 检查 modules
                    modules = manifest_data.get('modules', [])
                    if modules:
                        print(f"\nModules ({len(modules)} 个):")
                        for i, module in enumerate(modules):
                            module_type = module.get('type', '未知')
                            print(f"  [{i+1}] type: {module_type}")
                    else:
                        print("\n⚠️  Modules 字段缺失或为空")
                    
                    # 检查包类型
                    is_resource = False
                    is_behavior = False
                    for module in modules:
                        module_type = module.get('type', '').lower()
                        if module_type in ['resources', 'client_data', 'client_scripts']:
                            is_resource = True
                        elif module_type in ['data', 'script', 'server_data', 'server_scripts']:
                            is_behavior = True
                    
                    if is_resource:
                        print("\n✅ 确认为资源包 (Resource Pack)")
                    elif is_behavior:
                        print("\n⚠️  这是行为包 (Behavior Pack)，不是资源包")
                    else:
                        print("\n⚠️  无法确定包类型")
                    
                except json.JSONDecodeError as e:
                    print(f"\n❌ manifest.json JSON 格式错误: {e}")
                    print(f"内容预览（前500字符）:")
                    print(manifest_content[:500])
                    return False
                except Exception as e:
                    print(f"\n❌ 读取 manifest.json 失败: {e}")
                    return False
            
            # 检查目录结构
            print(f"\n目录结构分析:")
            top_level_dirs = set()
            for f in file_list:
                parts = f.split('/')
                if len(parts) > 1:
                    top_level_dirs.add(parts[0])
            
            if top_level_dirs:
                print(f"顶层目录 ({len(top_level_dirs)} 个):")
                for d in sorted(top_level_dirs):
                    print(f"  - {d}")
            
            # 检查是否有嵌套结构
            manifest_path = manifest_files[0] if manifest_files else None
            if manifest_path:
                depth = len(manifest_path.split('/'))
                if depth == 1:
                    print(f"\n✅ manifest.json 在第一层（正确）")
                elif depth == 2:
                    print(f"\n✅ manifest.json 在第二层（正常）")
                else:
                    print(f"\n⚠️  manifest.json 在 {depth} 层（可能嵌套过深）")
            
    except zipfile.BadZipFile:
        print("\n❌ 无效的 ZIP 文件格式")
        return False
    except Exception as e:
        print(f"\n❌ 读取 ZIP 文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("诊断完成")
    print("=" * 70)
    return True


def main():
    if len(sys.argv) < 2:
        print("用法: python diagnose_upload.py <zip文件路径>")
        print("\n示例:")
        print("  python diagnose_upload.py /path/to/NewGlowingOres.zip")
        print("  python diagnose_upload.py ~/Downloads/NewGlowingOres-§6[Border]§r.zip")
        sys.exit(1)
    
    zip_path = Path(sys.argv[1])
    success = diagnose_zip_file(zip_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

