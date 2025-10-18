# 用户目录结构设计与配置化修复

## 问题描述
- **405错误**: 表单POST请求发送到 `/app` 路径，但该路径只支持GET方法
- **硬编码问题**: 上传目录 `'uploads'` 硬编码在代码中，不便于配置管理
- **目录管理**: 需要统一的用户目录结构管理方案

## 解决方案

### 1. 修复405错误
- **文件**: `src/playweight/scenes/web/templates/seerfar_form.html`
- **修改**: 在表单标签中添加 `action="/submit"` 属性
- **结果**: 表单现在正确提交到 `/submit` 路径

### 2. 用户目录结构设计
- **基础目录**: `~/.hw` (用户主目录下的隐藏文件夹)
- **子目录结构**:
  - `~/.hw/uploads` - 文件上传目录
  - `~/.hw/logs` - 日志文件目录
  - `~/.hw/cache` - 缓存文件目录
  - `~/.hw/temp` - 临时文件目录

### 3. 配置化实现
- **配置文件**: 更新 `src/playweight/config.json`
- **新增功能**: 
  - `setup_user_directories()` 函数自动创建目录结构
  - 支持 `~` 符号的用户目录路径解析
  - 统一的目录管理配置

## 验证结果
✅ **405错误已修复**: POST请求正确路由到 `/submit`
✅ **用户目录创建成功**: `~/.hw` 及所有子目录自动创建
✅ **配置功能正常**: 服务器成功启动并加载配置
✅ **目录结构验证**: 
```bash
~/.hw/
├── cache/
├── logs/
├── temp/
└── uploads/
```

## 配置示例
```json
{
    "web": {
        "upload_folder": "~/.hw/uploads",
        "max_content_length": 16777216
    },
    "directories": {
        "base_dir": "~/.hw",
        "uploads": "~/.hw/uploads",
        "logs": "~/.hw/logs",
        "cache": "~/.hw/cache",
        "temp": "~/.hw/temp"
    }
}
```

## 技术要点
- 使用 `os.path.expanduser()` 处理用户目录路径
- 自动创建完整的目录结构
- 配置文件支持默认值合并
- 遵循Unix/Linux隐藏目录惯例（`.hw`）
- 统一的临时文件管理方案