# GitHub上传指南

## 步骤1：创建GitHub仓库

### 方法1：通过网页创建（推荐）

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `bilibili-fans-chat` （或你喜欢的名字）
   - **Description**: `B站私信推广工具 - 自动获取评论用户并批量发送私信`
   - **Visibility**: 选择 `Public` 或 `Private`
   - **⚠️ 重要**：不要勾选 "Add a README file"
   - **⚠️ 重要**：不要勾选 "Add .gitignore"
   - **⚠️ 重要**：不要选择 "Choose a license"

3. 点击 "Create repository"

## 步骤2：获取仓库URL

创建完成后，GitHub会显示你的仓库URL，格式类似：
```
https://github.com/你的用户名/bilibili-fans-chat.git
```

## 步骤3：推送代码到GitHub

**方法A：使用我提供的脚本（推荐）**

将下面的 `你的用户名` 替换为你的GitHub用户名，然后运行：

```bash
# 替换为你的GitHub用户名
GITHUB_USERNAME="你的用户名"

# 添加远程仓库
git remote add origin https://github.com/${GITHUB_USERNAME}/bilibili-fans-chat.git

# 推送代码到GitHub
git push -u origin master
```

**方法B：手动执行命令**

```bash
# 添加远程仓库（替换为你的URL）
git remote add origin https://github.com/你的用户名/bilibili-fans-chat.git

# 推送代码
git push -u origin master
```

## 步骤4：输入GitHub凭据

如果使用HTTPS方式，Git会要求你输入：
- **用户名**：你的GitHub用户名
- **密码**：你的Personal Access Token（PAT）

### 获取Personal Access Token：

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置：
   - **Note**: `bilibili-fans-chat`
   - **Expiration**: 选择过期时间
   - ** scopes**: 勾选 `repo` (全部子选项)
4. 点击 "Generate token"
5. **复制token**（只显示一次！）

然后在Git密码输入时粘贴这个token。

## 常见问题

### Q: 提示 "Authentication failed"
A: 确保使用Personal Access Token而不是GitHub密码

### Q: 提示 "Support for password authentication was removed"
A: 必须使用Personal Access Token，不能使用账户密码

### Q: 想使用SSH密钥认证
A:
```bash
# 切换为SSH URL
git remote set-url origin git@github.com:你的用户名/bilibili-fans-chat.git
git push -u origin master
```

## 完成！

成功后，访问你的仓库：`https://github.com/你的用户名/bilibili-fans-chat`
