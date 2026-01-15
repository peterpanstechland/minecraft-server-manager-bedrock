# CurseForge API 申请模板（英文版）

## 📝 快速复制模板

### 第一部分：基本信息

**Project name*** (最多30字符):
```
Bedrock Server Manager
```

**Your nickname***:
```
YourNickname
```

**Your real name***:
```
Your Real Name
```

**Email***:
```
your.email@example.com
```

**Your full Discord username***:
```
YourUsername#1234
```
(如果没有Discord，填写: `N/A#0000`)

**Describe the project goal and scope***:
```
A web-based management tool for Minecraft Bedrock Edition server addons. 
It allows server administrators to upload, install, enable/disable addons 
from CurseForge, and manage server addons through a web interface.
```

**Why are you building this project?*** (最多2000字符):
```
I'm building this project to simplify addon management for Minecraft Bedrock 
Edition servers. Currently, server administrators need to manually download 
and install addons, which is time-consuming. This tool automates the process 
and provides a user-friendly web interface for managing server addons.

The tool will help me and other server administrators:
- Easily install addons from CurseForge
- Manage addon versions and updates
- Enable/disable addons without manual file operations
- Monitor server addon status

This is a personal project for managing my own server, and I plan to make it 
open-source for the community.
```

### 第二部分：项目详情

**Game Selection**:
- 选择: **Minecraft**

**Website URL***:
```
https://github.com/peterpanstechland/minecraft-server-manager-bedrock
```
(如果没有，填写: `N/A`)

**Git URL***:
```
https://github.com/peterpanstechland/minecraft-server-manager-bedrock
```
(如果没有，填写: `N/A`)

**Mod Author Approval Acknowledgment***:
- ☑️ 勾选: I understand that file distribution through the API is subjected to the mod author's approval

**Are you looking to monetize the project?***:
- 选择: **No**

**If you have a business model please describe it***:
```
This is a free, open-source project for personal use. No monetization planned.
```

**If you're planning to distribute mods, how would you contribute to the mod authors?***:
```
This tool is for personal server management only. All addons will be downloaded 
directly from CurseForge with proper attribution. Users will be directed to 
CurseForge pages for addon information and updates. The tool respects mod authors' 
rights and only facilitates downloading addons that users have already chosen 
to use on their servers.
```

**I understand that above certain volumes I might be required to reduce API calls, or alternatively, pay associated bandwidth costs**:
- ☑️ 勾选 (通常已默认勾选)

**I have read and agree to the API's TOS***:
- ☑️ 勾选
- 先阅读: https://support.curseforge.com/en/support/solutions/articles/9000207405-curse-forge-3rd-party-api-terms-and-conditions

**Additional notes** (可选):
```
This is a personal project for managing my own Minecraft Bedrock server. 
The API will be used only for downloading addons that I personally use on my server. 
I understand and will comply with all API usage guidelines and rate limits.
```

## 💡 填写提示

1. **所有内容都用英文填写**
2. **Project name** 不要超过30个字符
3. **Why are you building this project?** 可以写详细一点，说明用途和好处
4. **Git URL** 如果有GitHub仓库最好，没有可以填 `N/A`
5. **Monetization** 选择 `No` 最简单
6. **Mod Author Contribution** 强调尊重作者权益，只用于个人服务器管理

## ✅ 提交后

- 等待24-48小时审核
- 收到邮件后，复制API密钥
- 添加到 `.env` 文件：`CURSEFORGE_API_KEY=你的密钥`

