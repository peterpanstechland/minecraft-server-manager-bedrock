# CurseForge API 密钥配置指南（简化版）

## 🚀 快速获取 API 密钥（3步）

### 步骤1：访问申请页面
打开：https://support.curseforge.com/en/support/solutions/articles/9000208346

### 步骤2：填写申请表格（需要英文填写）

**重要：所有字段都需要用英文填写！**

#### 第一部分：基本信息

1. **Project name*** (项目名称，最多30字符)
   ```
   Bedrock Server Manager
   ```

2. **Your nickname*** (你的昵称)
   ```
   你的英文昵称或用户名
   ```

3. **Your real name*** (真实姓名)
   ```
   你的真实姓名（拼音或英文）
   ```

4. **Email*** (邮箱)
   ```
   你的邮箱地址
   ```

5. **Your full Discord username*** (Discord用户名)
   ```
   例如: username#1234
   如果没有Discord，可以填写: N/A#0000
   ```

6. **Describe the project goal and scope*** (项目目标和范围)
   ```
   A web-based management tool for Minecraft Bedrock Edition server addons. 
   It allows server administrators to upload, install, enable/disable addons 
   from CurseForge, and manage server addons through a web interface.
   ```

7. **Why are you building this project?*** (为什么创建这个项目，最多2000字符)
   ```
   I'm building this project to simplify addon management for Minecraft Bedrock 
   Edition servers. Currently, server administrators need to manually download 
   and install addons, which is time-consuming. This tool automates the process 
   and provides a user-friendly web interface for managing server addons.
   ```

#### 第二部分：项目详情

8. **Game Selection** (游戏选择)
   - 选择：**Minecraft**

9. **Website URL*** (网站URL)
   ```
   https://github.com/peterpanstechland/minecraft-server-manager-bedrock
   ```
   如果没有，可以填写：`N/A`

10. **Git URL*** (Git仓库URL)
    ```
    https://github.com/peterpanstechland/minecraft-server-manager-bedrock
    ```
    如果没有，可以填写：`N/A`

11. **Mod Author Approval Acknowledgment*** (模组作者批准确认)
    - ☑️ 勾选：我理解通过API分发文件需要模组作者批准

12. **Are you looking to monetize the project?*** (是否计划盈利)
    - 选择：**No**

13. **If you have a business model please describe it*** (如果有商业模式请描述)
    ```
    This is a free, open-source project for personal use. No monetization planned.
    ```

14. **If you're planning to distribute mods, how would you contribute to the mod authors?*** (如果计划分发模组，如何回馈作者)
    ```
    This tool is for personal server management only. All addons will be downloaded 
    directly from CurseForge with proper attribution. Users will be directed to 
    CurseForge pages for addon information and updates.
    ```

15. **I understand that above certain volumes I might be required to reduce API calls, or alternatively, pay associated bandwidth costs**
    - ☑️ 勾选（通常已默认勾选）

16. **I have read and agree to the API's TOS*** (我已阅读并同意API服务条款)
    - ☑️ 勾选
    - 先点击链接阅读条款：https://support.curseforge.com/en/support/solutions/articles/9000207405-curse-forge-3rd-party-api-terms-and-conditions

17. **Additional notes** (附加说明，可选)
    ```
    This is a personal project for managing my own Minecraft Bedrock server. 
    The API will be used only for downloading addons that I personally use on my server.
    ```

### 步骤3：提交并等待审核（通常24-48小时）
- 提交申请后，CurseForge团队会在24-48小时内审核
- 审核通过后，会通过邮件发送API密钥
- 收到密钥后，添加到 `.env` 文件：
```bash
CURSEFORGE_API_KEY=你的API密钥
```

## 💡 替代方案：直接上传文件（推荐）

**如果觉得申请API密钥太麻烦，可以直接使用文件上传功能：**

1. 在CurseForge网站找到addon
2. 点击"Download"下载文件（.mcpack或.zip）
3. 在Manager中使用"文件上传"功能上传

**优点：**
- ✅ 无需申请API密钥
- ✅ 无需等待审核
- ✅ 立即可以使用
- ✅ 同样方便快捷

**建议：** 日常使用直接上传文件即可，更简单快捷！

## ⚙️ 配置API密钥（可选）

如果已经获得API密钥：

```bash
# 编辑.env文件
nano /home/ubuntu/bedrock-manager/.env

# 添加或修改：
CURSEFORGE_API_KEY=你的API密钥

# 重启服务
pkill -f "python3 run.py"
cd /home/ubuntu/bedrock-manager
. venv/bin/activate
python3 run.py
```

## 📝 注意事项

- ✅ API密钥申请是**免费的**
- ⏰ 审核通常需要24-48小时
- 📝 **所有字段都需要用英文填写**
- 💡 如果只是偶尔使用，直接上传文件更方便
- 🔑 API密钥主要用于批量或自动化下载

## 📄 详细模板

如果需要更详细的填写模板，请查看 `CURSEFORGE_APPLICATION_TEMPLATE.md` 文件，里面提供了所有字段的英文填写示例。

