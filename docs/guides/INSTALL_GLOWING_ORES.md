# 安装 NewGlowingOres 插件

## 文件信息
- 文件名: `NewGlowingOres-§6[Border]§r.zip`
- 格式: ZIP文件（需要解压后查看内容）

## 安装方法

### 方法1：通过Web界面上传（推荐）

1. 打开 Addon 管理页面
2. 点击"上传Addon"按钮
3. 选择 `NewGlowingOres-§6[Border]§r.zip` 文件
4. 点击"上传"
5. 上传成功后，点击"启用"按钮

### 方法2：手动安装

如果文件在服务器上：

```bash
# 1. 找到文件位置
find /home/ubuntu -name "*NewGlowingOres*"

# 2. 使用Manager的API安装
curl -X POST http://localhost:5000/api/addons/upload \
  -F "file=@/path/to/NewGlowingOres-§6[Border]§r.zip"
```

### 方法3：直接解压到服务器目录

```bash
# 如果是行为包
unzip NewGlowingOres-§6[Border]§r.zip -d /home/ubuntu/bedrock-server/behavior_packs/

# 如果是资源包
unzip NewGlowingOres-§6[Border]§r.zip -d /home/ubuntu/bedrock-server/resource_packs/

# 然后扫描
# 在Web界面点击"扫描已安装"
```

## 注意事项

文件名中包含特殊字符 `§6` 和 `§r`（Minecraft颜色代码）：
- 这些字符在文件名中可能被编码
- 上传时确保文件名正确
- 如果上传失败，可以重命名文件去掉特殊字符

## 检查安装状态

安装后，在Addon管理页面应该能看到：
- 名称：NewGlowingOres 或类似名称
- 类型：行为包或资源包
- 状态：已禁用（需要手动启用）

## 启用插件

1. 在Addon列表中找到该插件
2. 点击"启用"按钮
3. 或者使用"全部启用"按钮

