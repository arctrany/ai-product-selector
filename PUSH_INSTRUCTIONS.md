# 推送说明文档

## 概述
所有代码更改已成功提交到本地的 `new_framework` 分支。由于 GitHub 安全策略更新，现在必须使用 Personal Access Token 而不是密码进行 Git 操作。

## 本地提交详情
- 提交哈希: 82bfc32
- 提交信息: feat: 集成 Prefect 工作流引擎到 src_new 目录
- 提交时间: 2025-10-21
- 包含内容:
  - Prefect 工作流引擎集成
  - 基础工作流示例 (basic_workflow.py)
  - 暂停/恢复功能演示 (pause_resume_workflow.py)
  - API 控制工具 (control_api.py)
  - 完整的 README 文档
  - 依赖定义文件 (requirements.txt)

## 使用 Personal Access Token 推送的步骤 (推荐方法)

### 步骤1: 创建 Personal Access Token
1. 以 arctrany 用户身份登录 GitHub
2. 访问 https://github.com/settings/tokens
3. 点击 "Generate new token" (经典 token)
4. 设置 token 信息:
   - Note: ai-product-selector-push
   - Expiration: 选择合适的过期时间
   - Select scopes: 勾选 `repo` (完整仓库访问权限)
5. 点击 "Generate token"
6. **重要**: 复制生成的 token 并保存(只显示一次)

### 步骤2: 使用 Token 推送代码
在终端中执行以下命令:
```bash
cd /home/admin/workspace/ai-product-selector
git push https://arctrany:<your-personal-access-token>@github.com/arctrany/ai-product-selector.git new_framework
```

将 `<your-personal-access-token>` 替换为你在步骤1中生成的实际 token。

## 替代方法: 使用 SSH 密钥

### 步骤1: 生成 SSH 密钥
```bash
ssh-keygen -t ed25519 -C "arctrany@example.com"
```

### 步骤2: 添加 SSH 密钥到 GitHub
1. 复制公钥内容:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
2. 在 GitHub 上访问 Settings > SSH and GPG keys
3. 点击 "New SSH key"
4. 粘贴公钥内容并保存

### 步骤3: 更改远程仓库 URL 并推送
```bash
cd /home/admin/workspace/ai-product-selector
git remote set-url origin git@github.com:arctrany/ai-product-selector.git
git push origin new_framework
```

## 验证推送结果
推送成功后，可以通过以下方式验证:
- 访问 https://github.com/arctrany/ai-product-selector/tree/new_framework
- 检查 src_new 目录是否存在且包含所有文件:
  - README.md
  - requirements.txt
  - workflows/basic_workflow.py
  - workflows/pause_resume_workflow.py
  - utils/control_api.py

## 安全注意事项
- Personal Access Token 应该具有最小必要权限
- 不要在代码或配置文件中硬编码 token
- 定期轮换 token
- 推送完成后可以删除临时 token
