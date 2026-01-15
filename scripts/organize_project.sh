#!/bin/bash
# 项目整理脚本

cd /home/ubuntu/bedrock-manager

# 创建文档目录
mkdir -p docs/guides docs/troubleshooting docs/development

# 移动文档文件到docs目录
# 故障排除文档
mv FIX_*.md docs/troubleshooting/ 2>/dev/null
mv DEBUG_*.md docs/troubleshooting/ 2>/dev/null
mv CONNECTION_TROUBLESHOOTING.md docs/troubleshooting/ 2>/dev/null
mv TEST_*.md docs/troubleshooting/ 2>/dev/null
mv QUICK_CHECK_*.md docs/troubleshooting/ 2>/dev/null

# 指南文档
mv INSTALL_*.md docs/guides/ 2>/dev/null
mv SETUP_*.md docs/guides/ 2>/dev/null
mv QUICKSTART*.md docs/guides/ 2>/dev/null
mv FAMILY_ACCOUNT_SETUP.md docs/guides/ 2>/dev/null
mv BEDROCK_MULTI_DEVICE.md docs/guides/ 2>/dev/null
mv CHECK_*.md docs/guides/ 2>/dev/null
mv CURSEFORGE_*.md docs/guides/ 2>/dev/null
mv LAN_VS_SERVER_MODE.md docs/guides/ 2>/dev/null

# 开发文档
mv SECURITY*.md docs/development/ 2>/dev/null
mv IMPROVEMENTS.md docs/development/ 2>/dev/null
mv PUSH_INSTRUCTIONS.md docs/development/ 2>/dev/null

# 删除临时文件
rm -f *.zip 2>/dev/null
rm -f setup_screen_server.sh 2>/dev/null  # 已被server_runner.py替代
rm -f setup_security.sh 2>/dev/null  # 已集成到主应用
rm -f install.sh 2>/dev/null  # 使用README中的安装步骤
rm -f sync_to_github.sh 2>/dev/null  # 开发脚本，不需要

# 清理bedrock-server目录中的临时文件
cd /home/ubuntu/bedrock-server
rm -f screen_wrapper.sh screen_wrapper.log screen.log start_server.sh server_wrapper.py 2>/dev/null
rm -f *.backup.* 2>/dev/null

echo "项目整理完成！"
echo "文档已移动到 docs/ 目录"
echo "临时文件已删除"
