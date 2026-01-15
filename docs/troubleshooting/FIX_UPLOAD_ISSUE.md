# 修复上传失败问题

## 问题描述

上传 `NewGlowingOres-§6[Border]§r.zip` 时出现错误：
- "上传失败:无法提取包信息,请确保文件是有效的Bedrock addon包"
- HTTP 400 Bad Request

## 诊断步骤

### 1. 使用诊断工具检查文件

```bash
# 如果你有文件路径
python3 scripts/diagnose_upload.py /path/to/NewGlowingOres-§6[Border]§r.zip

# 或者先找到文件
find ~ -name "*NewGlowingOres*" -type f
python3 scripts/diagnose_upload.py <找到的文件路径>
```

诊断工具会检查：
- ZIP 文件格式是否有效
- 是否包含 manifest.json
- manifest.json 格式是否正确
- UUID、名称、版本等字段是否完整
- 包类型（资源包/行为包）
- 目录结构

### 2. 查看服务器日志

上传失败时，服务器会输出详细的调试信息：

```bash
# 如果使用 systemd 运行
sudo journalctl -u bedrock-manager -f

# 或者查看应用日志
tail -f /home/ubuntu/bedrock-manager/*.log
```

### 3. 常见问题及解决方案

#### 问题1: ZIP 文件损坏

**症状**: 诊断工具显示 "无效的 ZIP 文件格式"

**解决**:
1. 重新下载文件
2. 检查文件是否完整下载
3. 尝试用其他工具解压验证

#### 问题2: manifest.json 不在预期位置

**症状**: 诊断工具显示 "未找到 manifest.json" 或 "manifest.json 在 X 层（嵌套过深）"

**解决**:
```bash
# 手动解压并检查结构
unzip -q NewGlowingOres*.zip -d /tmp/check/
ls -la /tmp/check/
find /tmp/check/ -name manifest.json

# 如果 manifest.json 在嵌套目录中，需要重新打包
# 例如：如果结构是 NewGlowingOres/NewGlowingOres/manifest.json
cd /tmp/check/NewGlowingOres/NewGlowingOres
zip -r /tmp/fixed.zip .
```

#### 问题3: manifest.json 格式错误

**症状**: 诊断工具显示 "manifest.json JSON 格式错误"

**解决**:
1. 手动解压文件
2. 检查 manifest.json 的 JSON 格式
3. 使用在线 JSON 验证工具检查
4. 修复后重新打包

#### 问题4: 文件名特殊字符问题

**症状**: 文件名包含 `§6`、`§r` 等 Minecraft 颜色代码

**解决**:
```bash
# 重命名文件（去掉特殊字符）
mv "NewGlowingOres-§6[Border]§r.zip" "NewGlowingOres-Border.zip"

# 或者使用诊断工具检查后，手动安装
python3 scripts/diagnose_upload.py "NewGlowingOres-§6[Border]§r.zip"
# 如果诊断通过，可以手动解压安装
```

## 手动安装方法（如果上传失败）

如果上传一直失败，可以手动安装：

### 方法1: 直接解压到服务器目录

```bash
# 1. 解压文件
cd /home/ubuntu/bedrock-server/resource_packs
unzip /path/to/NewGlowingOres*.zip

# 2. 确保结构正确
ls -la NewGlowingOres/
# 应该看到 manifest.json 在第一层

# 3. 如果有多层嵌套，调整结构
cd NewGlowingOres
if [ -d "NewGlowingOres" ]; then
    mv NewGlowingOres/* .
    rmdir NewGlowingOres
fi

# 4. 检查 manifest
cat manifest.json | python3 -m json.tool

# 5. 在 Web 界面点击"扫描已安装"
```

### 方法2: 使用检查脚本验证后手动配置

```bash
# 1. 解压到临时目录
unzip -q NewGlowingOres*.zip -d /tmp/newglowingores/

# 2. 检查 manifest
python3 scripts/check_manifest_compatibility.py \
  /tmp/newglowingores/NewGlowingOres/manifest.json

# 3. 如果检查通过，复制到服务器目录
cp -r /tmp/newglowingores/NewGlowingOres \
  /home/ubuntu/bedrock-server/resource_packs/

# 4. 添加到 world_resource_packs.json（使用脚本输出的配置片段）
nano "/home/ubuntu/bedrock-server/worlds/Bedrock level/world_resource_packs.json"
```

## 改进后的错误信息

现在上传失败时会显示更详细的错误信息：

1. **ZIP 文件结构** - 列出所有文件和目录
2. **manifest.json 位置** - 显示找到的所有 manifest.json
3. **JSON 格式错误** - 显示具体的错误位置
4. **字段缺失** - 明确指出缺少哪些必需字段

## 测试上传功能

改进后，你可以：

1. **查看详细日志**: 上传时会输出 ZIP 文件内容列表
2. **诊断文件**: 使用 `diagnose_upload.py` 提前检查文件
3. **手动安装**: 如果上传失败，可以手动安装

## 下一步

1. 运行诊断工具检查你的 ZIP 文件
2. 查看服务器日志获取详细错误信息
3. 根据错误信息修复问题
4. 如果问题持续，使用手动安装方法

## 需要帮助？

如果问题仍然存在，请提供：
1. 诊断工具的输出
2. 服务器日志中的错误信息
3. ZIP 文件的结构（使用 `unzip -l` 查看）

