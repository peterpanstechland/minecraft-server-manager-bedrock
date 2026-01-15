# 修复包文件名

## 问题

Marketplace 下载的包文件名可能包含：
- 特殊字符（§、[]、空格等）
- 编码问题
- 不友好的格式

## 快速修复

### 使用修复脚本

```bash
cd /home/ubuntu/bedrock-manager
source venv/bin/activate

# 修复资源包
python3 scripts/fix_pack_names.py resource_packs.zip

# 修复行为包
python3 scripts/fix_pack_names.py behavior_packs.zip

# 或同时修复两个
python3 scripts/fix_pack_names.py resource_packs.zip behavior_packs.zip
```

脚本会：
1. ✅ 解压zip文件
2. ✅ 读取每个包的 manifest.json
3. ✅ 提取正确的包名
4. ✅ 清理特殊字符和空格
5. ✅ 重命名目录
6. ✅ 创建修复后的zip文件（`*_fixed.zip`）

## 修复规则

- 移除 Minecraft 颜色代码（§0-§f, §k-§r）
- 移除特殊字符：`<>:"/\|?*[]`
- 替换空格为下划线
- 使用 manifest.json 中的名称（如果可用）
- 如果名称冲突，添加数字后缀

## 使用修复后的文件

修复完成后，使用修复后的文件安装：

```bash
source venv/bin/activate
python3 scripts/install_marketplace_packs.py resource_packs_fixed.zip behavior_packs_fixed.zip
```

## 示例

**修复前：**
```
§6Looky Tool§r/
§dInventory Manager (Lite)§r/
Gravestone [v2.0]/
```

**修复后：**
```
Looky_Tool/
Inventory_Manager_Lite/
Gravestone_v2_0/
```

