# 安装 Marketplace 包到服务器

## 文件说明

你有两个从 Marketplace 下载的 zip 文件：
- `resource_packs.zip` - 包含资源包（Looky Tool, Inventory Manager, Gravestone 的资源部分）
- `behavior_packs.zip` - 包含行为包（Looky Tool, Inventory Manager, Gravestone 的行为部分）

## 快速安装

### 方法1: 使用安装脚本（推荐）

**使用 venv（推荐）：**
```bash
cd /home/ubuntu/bedrock-manager
source venv/bin/activate
python3 scripts/install_marketplace_packs.py resource_packs.zip behavior_packs.zip
```

**或使用便捷脚本：**
```bash
cd /home/ubuntu/bedrock-manager
./scripts/install_marketplace_packs.sh resource_packs.zip behavior_packs.zip
```

脚本会自动：
1. ✅ 解压 zip 文件
2. ✅ 查找所有 manifest.json
3. ✅ 提取 UUID、名称、版本
4. ✅ 安装到服务器目录
5. ✅ 添加到世界配置文件
6. ✅ 备份已存在的包

### 方法2: 手动安装

#### 步骤1: 解压资源包

```bash
cd /home/ubuntu/bedrock-server/resource_packs
unzip /home/ubuntu/bedrock-manager/resource_packs.zip

# 检查结构
ls -la
# 应该看到各个包的目录
```

#### 步骤2: 解压行为包

```bash
cd /home/ubuntu/bedrock-server/behavior_packs
unzip /home/ubuntu/bedrock-manager/behavior_packs.zip

# 检查结构
ls -la
```

#### 步骤3: 检查 manifest.json

```bash
# 检查资源包
for dir in /home/ubuntu/bedrock-server/resource_packs/*/; do
    if [ -f "$dir/manifest.json" ]; then
        echo "=== $(basename "$dir") ==="
        cat "$dir/manifest.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"UUID: {d.get('header',{}).get('uuid')}\"); print(f\"Name: {d.get('header',{}).get('name')}\")"
        echo ""
    fi
done

# 检查行为包
for dir in /home/ubuntu/bedrock-server/behavior_packs/*/; do
    if [ -f "$dir/manifest.json" ]; then
        echo "=== $(basename "$dir") ==="
        cat "$dir/manifest.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"UUID: {d.get('header',{}).get('uuid')}\"); print(f\"Name: {d.get('header',{}).get('name')}\")"
        echo ""
    fi
done
```

#### 步骤4: 添加到世界配置

使用检查脚本获取 UUID：

```bash
# 检查资源包
python3 scripts/check_manifest_compatibility.py /home/ubuntu/bedrock-server/resource_packs/LookyTool/manifest.json

# 将输出的配置片段添加到 world_resource_packs.json
nano "/home/ubuntu/bedrock-server/worlds/Bedrock level/world_resource_packs.json"
```

#### 步骤5: 在 Web 界面扫描

1. 打开 Web 界面
2. 进入 Addon 管理页面
3. 点击"扫描已安装"
4. 启用需要的包

## 注意事项

### Marketplace 包的特殊性

1. **可能包含嵌套结构**
   - Marketplace 下载的包可能是多层嵌套的
   - 脚本会自动处理嵌套的 zip 文件

2. **可能需要资源包+行为包**
   - Looky Tool、Inventory Manager、Gravestone 通常需要：
     - 资源包（UI、纹理）
     - 行为包（功能逻辑）

3. **版本兼容性**
   - 确保包版本与服务器版本兼容
   - 检查 `min_engine_version` 字段

### 常见问题

#### Q: 解压后找不到 manifest.json？

A: 可能是嵌套的 zip 文件，脚本会自动处理。如果手动解压：
```bash
# 查找所有zip文件并解压
find /home/ubuntu/bedrock-server/resource_packs -name "*.zip" -exec unzip -d {}.extracted {} \;
```

#### Q: UUID 格式错误？

A: 确保使用 `header.uuid`，不是 `modules.uuid`

#### Q: 包安装后不工作？

A: 检查：
1. 资源包和行为包是否都已安装
2. 是否都已添加到世界配置
3. 是否都已启用
4. 服务器日志是否有错误

## 验证安装

安装后验证：

```bash
# 检查资源包
ls -la /home/ubuntu/bedrock-server/resource_packs/ | grep -E "Looky|Inventory|Gravestone"

# 检查行为包
ls -la /home/ubuntu/bedrock-server/behavior_packs/ | grep -E "Looky|Inventory|Gravestone"

# 检查世界配置
cat "/home/ubuntu/bedrock-server/worlds/Bedrock level/world_resource_packs.json" | python3 -m json.tool
cat "/home/ubuntu/bedrock-server/worlds/Bedrock level/world_behavior_packs.json" | python3 -m json.tool
```

## 重启服务器

安装完成后重启服务器：

```bash
sudo systemctl restart bedrock
```

## 下一步

1. ✅ 运行安装脚本
2. ✅ 在 Web 界面扫描已安装的包
3. ✅ 启用需要的包
4. ✅ 重启服务器
5. ✅ 测试功能

