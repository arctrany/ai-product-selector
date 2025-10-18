# AI选品系统核心问题修复与架构优化

## 项目结构

```
ai-product-selector2/
├── .aone_copilot/          # Aone Copilot 配置文件
├── .cursor/                # Cursor IDE 命令配置
├── .github/                # GitHub 工作流和提示模板
├── .specify/               # Specify 工具配置和模板
├── specs/                  # 项目规格文档
│   ├── AI选品的系统流程.md
│   ├── browser-plugin-compatibility-fix.md
│   ├── code-refactor-remove-redundancy.md
│   ├── playwright/         # Playwright 相关文档
│   ├── upload-directory-configuration-fix.md
│   ├── 用户界面需求.md
│   └── main.md            # 本次修复归档（新增）
├── src/                   # 源代码目录
│   ├── playweight/        # 主要业务逻辑
│   │   ├── scenes/web/    # Web 服务和模板
│   │   ├── utils/         # 工具类（新增 path_config.py）
│   │   ├── config.json    # 系统配置文件
│   │   ├── logger_config.py
│   │   ├── requirements.txt
│   │   └── runner.py
│   └── web/               # Web 控制台
│       └── web_console.py
└── tests/                 # 测试文件目录
    ├── browser_test.py
    ├── playwright_*.py    # Playwright 相关测试
    └── seefar_test.py
```

### 核心模块说明

- **src/playweight/scenes/web/**: Web 服务核心，包含 Flask 应用和 HTML 模板
- **src/playweight/utils/**: 工具类模块，新增跨平台路径配置
- **specs/**: 项目文档和规格说明，记录各种修复和优化
- **tests/**: 自动化测试，主要基于 Playwright 框架

## 修复问题

### 1. 停止按钮无效问题
- **问题**：前端停止按钮无法正常终止任务
- **解决**：修复了 `console.html` 中的任务ID管理和API调用路径
- **文件**：`src/playweight/scenes/web/templates/console.html`

### 2. 店铺ID显示Unknown问题
- **问题**：商品数据中店铺ID字段显示为"Unknown"
- **解决**：改进了Excel字段读取逻辑，支持多种字段名匹配
- **文件**：`src/playweight/scenes/web/seerfar_web.py`

### 3. Checkbox记住选择功能失效
- **问题**：用户选择的配置无法持久化保存
- **解决**：实现了完整的localStorage功能
- **文件**：`src/playweight/scenes/web/templates/seerfar_form.html`

## 架构优化

### 1. 跨平台路径配置
- **新增**：`src/playweight/utils/path_config.py`
- **功能**：实现PathConfig类，支持Windows/macOS/Linux标准目录结构
- **应用**：替换硬编码路径，提升跨平台兼容性

### 2. 配置架构重构
- **优化**：将业务配置从系统级配置分离到用户界面
- **修改**：清理 `config.json` 中不合理的业务配置
- **新增**：用户界面支持"每店铺最大商品数"和"输出格式"配置

## 主要修改文件

1. `src/playweight/scenes/web/seerfar_web.py` - 核心Web服务修复
2. `src/playweight/utils/path_config.py` - 跨平台路径配置工具（新建）
3. `src/playweight/config.json` - 系统配置清理
4. `src/playweight/scenes/web/templates/seerfar_form.html` - 用户界面增强
5. `src/playweight/scenes/web/templates/console.html` - 控制台功能修复

## 验证结果

- ✅ 应用成功启动在 http://127.0.0.1:7788
- ✅ 停止按钮功能正常
- ✅ 商品ID正确显示（不再显示Unknown）
- ✅ 用户配置持久化保存
- ✅ 跨平台路径配置生效
- ✅ 多格式文件输出支持（Excel/CSV/JSON）

## 技术要点

- 实现了RESTful API设计
- 使用localStorage进行前端数据持久化
- 遵循XDG Base Directory标准进行跨平台目录配置
- 异步任务执行和控制机制
- DOM分析和商品数据提取优化