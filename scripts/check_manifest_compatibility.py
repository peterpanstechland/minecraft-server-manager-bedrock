#!/usr/bin/env python3
"""
New Glowing Ores 资源包 Manifest 兼容性检查工具

检查资源包的 manifest.json 是否适配当前 Bedrock 服务器配置
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import Config
except ImportError:
    # 如果无法导入 Config，使用默认值
    import os
    class Config:
        BEDROCK_SERVER_DIR = Path(os.environ.get('BEDROCK_SERVER_DIR', '/home/ubuntu/bedrock-server'))
        WORLD_DIR = BEDROCK_SERVER_DIR / 'worlds' / 'Bedrock level'
        WORLD_RESOURCE_PACKS_CONFIG = WORLD_DIR / 'world_resource_packs.json'


class ManifestChecker:
    """Manifest 兼容性检查器"""
    
    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self.manifest = None
        self.issues = []
        self.warnings = []
        self.info = []
        
    def load_manifest(self) -> bool:
        """加载 manifest.json"""
        try:
            if not self.manifest_path.exists():
                self.issues.append(f"❌ manifest.json 不存在: {self.manifest_path}")
                return False
            
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
            
            self.info.append(f"✅ 成功加载 manifest.json")
            return True
        except json.JSONDecodeError as e:
            self.issues.append(f"❌ manifest.json 格式错误: {e}")
            return False
        except Exception as e:
            self.issues.append(f"❌ 读取 manifest.json 失败: {e}")
            return False
    
    def check_structure(self) -> bool:
        """检查 manifest 基本结构"""
        if not self.manifest:
            return False
        
        checks = {
            'header': '缺少 header 字段',
            'modules': '缺少 modules 字段',
        }
        
        all_ok = True
        for key, error_msg in checks.items():
            if key not in self.manifest:
                self.issues.append(f"❌ {error_msg}")
                all_ok = False
            else:
                self.info.append(f"✅ 存在 {key} 字段")
        
        return all_ok
    
    def check_header(self) -> bool:
        """检查 header 字段"""
        if not self.manifest or 'header' not in self.manifest:
            return False
        
        header = self.manifest['header']
        all_ok = True
        
        # 检查必需字段
        required_fields = {
            'uuid': 'UUID',
            'name': '名称',
            'version': '版本',
        }
        
        for field, display_name in required_fields.items():
            if field not in header:
                self.issues.append(f"❌ header 缺少 {display_name} ({field})")
                all_ok = False
            else:
                self.info.append(f"✅ header.{field}: {header[field]}")
        
        # 检查 UUID 格式
        if 'uuid' in header:
            uuid = header['uuid']
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            if not re.match(uuid_pattern, uuid, re.IGNORECASE):
                self.issues.append(f"❌ UUID 格式无效: {uuid}")
                all_ok = False
            else:
                self.info.append(f"✅ UUID 格式正确: {uuid}")
        
        # 检查版本格式
        if 'version' in header:
            version = header['version']
            if isinstance(version, list) and len(version) == 3:
                self.info.append(f"✅ 版本格式正确: {version}")
            else:
                self.warnings.append(f"⚠️  版本格式可能有问题: {version} (应该是 [major, minor, patch])")
        
        return all_ok
    
    def check_pack_type(self) -> bool:
        """检查包类型（必须是资源包）"""
        if not self.manifest or 'modules' not in self.manifest:
            return False
        
        modules = self.manifest['modules']
        if not isinstance(modules, list) or len(modules) == 0:
            self.issues.append("❌ modules 为空或格式错误")
            return False
        
        # 检查模块类型
        resource_types = ['resources', 'client_data', 'client_scripts']
        behavior_types = ['data', 'script', 'server_data', 'server_scripts']
        
        is_resource = False
        is_behavior = False
        
        for module in modules:
            module_type = module.get('type', '').lower()
            if module_type in resource_types:
                is_resource = True
            elif module_type in behavior_types:
                is_behavior = True
        
        if is_behavior:
            self.issues.append("❌ 这是行为包，不是资源包！New Glowing Ores 应该是资源包")
            return False
        
        if is_resource:
            self.info.append("✅ 确认为资源包类型")
            return True
        
        # 如果无法确定，检查文件结构
        self.warnings.append("⚠️  无法从 modules 确定包类型，将检查文件结构")
        return True  # 暂时通过，后续检查文件结构
    
    def check_min_engine_version(self) -> bool:
        """检查最小引擎版本兼容性"""
        if not self.manifest or 'header' not in self.manifest:
            return False
        
        header = self.manifest['header']
        min_engine = header.get('min_engine_version', [1, 0, 0])
        
        if isinstance(min_engine, list) and len(min_engine) >= 2:
            major, minor = min_engine[0], min_engine[1]
            self.info.append(f"✅ 最小引擎版本: {major}.{minor}.x")
            
            # Bedrock 服务器通常支持 1.16.0+
            if major < 1 or (major == 1 and minor < 16):
                self.warnings.append(f"⚠️  最小引擎版本较低 ({major}.{minor}.x)，可能不兼容新版本服务器")
            else:
                self.info.append(f"✅ 引擎版本兼容性良好")
        
        return True
    
    def check_uuid_for_world_config(self) -> Optional[str]:
        """提取用于 world_resource_packs.json 的 UUID"""
        if not self.manifest or 'header' not in self.manifest:
            return None
        
        header = self.manifest['header']
        uuid = header.get('uuid')
        
        if uuid:
            self.info.append(f"📋 用于 world_resource_packs.json 的 UUID: {uuid}")
            self.info.append(f"   注意：使用 header.uuid，不是 modules.uuid")
        
        return uuid
    
    def check_version_for_world_config(self) -> Optional[List[int]]:
        """提取用于 world_resource_packs.json 的版本"""
        if not self.manifest or 'header' not in self.manifest:
            return None
        
        header = self.manifest['header']
        version = header.get('version')
        
        if isinstance(version, list) and len(version) >= 3:
            self.info.append(f"📋 用于 world_resource_packs.json 的版本: {version}")
            return version[:3]
        elif isinstance(version, list):
            # 补齐到3位
            version_padded = version + [0] * (3 - len(version))
            self.info.append(f"📋 用于 world_resource_packs.json 的版本（已补齐）: {version_padded}")
            return version_padded
        
        return None
    
    def check_manifest_location(self) -> bool:
        """检查 manifest.json 是否在第一层（不是嵌套的）"""
        # 检查路径深度
        parts = self.manifest_path.parts
        # 如果 manifest.json 在 resource_packs/ 目录下，应该在 resource_packs/PackName/manifest.json
        # 即深度应该是 3（resource_packs + PackName + manifest.json）
        
        # 这里我们假设 manifest_path 是完整路径
        # 如果是在 resource_packs 目录下，应该只有一层子目录
        if 'resource_packs' in parts:
            rp_index = parts.index('resource_packs')
            if len(parts) - rp_index == 3:  # resource_packs/PackName/manifest.json
                self.info.append("✅ manifest.json 位置正确（在第一层）")
                return True
            else:
                self.issues.append(f"❌ manifest.json 位置错误！应该在 resource_packs/PackName/manifest.json")
                self.issues.append(f"   当前路径深度: {len(parts) - rp_index} 层")
                return False
        
        return True  # 如果不在 resource_packs 下，可能是检查文件，暂时通过
    
    def generate_world_config_snippet(self) -> Optional[str]:
        """生成 world_resource_packs.json 配置片段"""
        uuid = self.check_uuid_for_world_config()
        version = self.check_version_for_world_config()
        
        if not uuid or not version:
            return None
        
        config = {
            "pack_id": uuid,
            "version": version
        }
        
        return json.dumps([config], indent=2, ensure_ascii=False)
    
    def check_server_config(self) -> Dict[str, bool]:
        """检查服务器配置"""
        results = {
            'texturepack_required': False,
            'world_config_exists': False,
        }
        
        # 检查 server.properties
        server_props = Config.BEDROCK_SERVER_DIR / 'server.properties'
        if server_props.exists():
            try:
                with open(server_props, 'r') as f:
                    content = f.read()
                    if 'texturepack-required=true' in content:
                        results['texturepack_required'] = True
                        self.info.append("✅ server.properties: texturepack-required=true")
                    else:
                        self.warnings.append("⚠️  server.properties: texturepack-required=false（建议改为 true）")
            except Exception as e:
                self.warnings.append(f"⚠️  无法读取 server.properties: {e}")
        else:
            self.warnings.append("⚠️  server.properties 不存在")
        
        # 检查 world_resource_packs.json
        world_rp_config = Config.WORLD_RESOURCE_PACKS_CONFIG
        if world_rp_config.exists():
            results['world_config_exists'] = True
            self.info.append(f"✅ world_resource_packs.json 存在: {world_rp_config}")
            
            # 检查是否已包含此包
            try:
                with open(world_rp_config, 'r') as f:
                    existing_config = json.load(f)
                    uuid = self.check_uuid_for_world_config()
                    if uuid:
                        for pack in existing_config:
                            if pack.get('pack_id') == uuid:
                                self.info.append(f"✅ 此资源包已在 world_resource_packs.json 中配置")
                                return results
                        self.warnings.append(f"⚠️  此资源包尚未添加到 world_resource_packs.json")
            except Exception as e:
                self.warnings.append(f"⚠️  无法读取 world_resource_packs.json: {e}")
        else:
            self.warnings.append(f"⚠️  world_resource_packs.json 不存在: {world_rp_config}")
        
        return results
    
    def run_all_checks(self) -> Tuple[bool, Dict]:
        """运行所有检查"""
        if not self.load_manifest():
            return False, {
                'issues': self.issues,
                'warnings': self.warnings,
                'info': self.info
            }
        
        checks = [
            ('结构检查', self.check_structure),
            ('Header 检查', self.check_header),
            ('包类型检查', self.check_pack_type),
            ('引擎版本检查', self.check_min_engine_version),
            ('Manifest 位置检查', self.check_manifest_location),
        ]
        
        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self.issues.append(f"❌ {check_name} 执行失败: {e}")
        
        # 检查服务器配置
        self.check_server_config()
        
        # 生成配置片段
        config_snippet = self.generate_world_config_snippet()
        
        is_compatible = len(self.issues) == 0
        
        return is_compatible, {
            'issues': self.issues,
            'warnings': self.warnings,
            'info': self.info,
            'config_snippet': config_snippet,
            'uuid': self.check_uuid_for_world_config(),
            'version': self.check_version_for_world_config(),
        }


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python check_manifest_compatibility.py <manifest.json路径>")
        print("\n示例:")
        print("  python check_manifest_compatibility.py /home/ubuntu/bedrock-server/resource_packs/NewGlowingOres/manifest.json")
        print("  python check_manifest_compatibility.py /path/to/extracted/NewGlowingOres/manifest.json")
        sys.exit(1)
    
    manifest_path = Path(sys.argv[1])
    
    print("=" * 70)
    print("New Glowing Ores 资源包 Manifest 兼容性检查")
    print("=" * 70)
    print(f"\n检查文件: {manifest_path}\n")
    
    checker = ManifestChecker(manifest_path)
    is_compatible, results = checker.run_all_checks()
    
    # 输出结果
    print("\n" + "=" * 70)
    print("检查结果")
    print("=" * 70)
    
    if results['info']:
        print("\n✅ 信息:")
        for info in results['info']:
            print(f"  {info}")
    
    if results['warnings']:
        print("\n⚠️  警告:")
        for warning in results['warnings']:
            print(f"  {warning}")
    
    if results['issues']:
        print("\n❌ 问题:")
        for issue in results['issues']:
            print(f"  {issue}")
    
    print("\n" + "=" * 70)
    if is_compatible:
        print("✅ 结论: Manifest 兼容！可以安装到服务器")
    else:
        print("❌ 结论: Manifest 存在兼容性问题，请先修复")
    
    # 输出配置片段
    if results.get('config_snippet'):
        print("\n" + "=" * 70)
        print("world_resource_packs.json 配置片段")
        print("=" * 70)
        print("\n将以下内容添加到 world_resource_packs.json:")
        print(results['config_snippet'])
        print("\n完整路径:")
        print(f"  {Config.WORLD_RESOURCE_PACKS_CONFIG}")
    
    print("\n" + "=" * 70)
    print("下一步操作")
    print("=" * 70)
    print("\n1. 确保资源包已解压到:")
    print(f"   {Config.RESOURCE_PACKS_DIR}/NewGlowingOres/")
    print("\n2. 确保 manifest.json 在第一层:")
    print(f"   {Config.RESOURCE_PACKS_DIR}/NewGlowingOres/manifest.json")
    print("\n3. 将资源包添加到 world_resource_packs.json（使用上面的配置片段）")
    print("\n4. 设置 server.properties:")
    print("   texturepack-required=true")
    print("\n5. 重启服务器")
    print("=" * 70)
    
    sys.exit(0 if is_compatible else 1)


if __name__ == '__main__':
    main()

