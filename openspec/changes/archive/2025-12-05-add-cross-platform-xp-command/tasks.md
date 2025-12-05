## 1. 依赖检测模块开发
- [x] 1.1 创建 `cli/dependency_checker.py` 模块
- [x] 1.2 实现 `check_python_version()` 函数，检测 Python 版本（需要 3.8+）
- [x] 1.3 实现 `check_pip_available()` 函数，检测 pip 是否可用
- [x] 1.4 实现 `parse_requirements()` 函数，解析 requirements.txt
- [x] 1.5 实现 `check_dependencies()` 函数，检测已安装的依赖包
- [x] 1.6 实现 `install_dependencies()` 函数，安装缺失的依赖
- [x] 1.7 实现 `check_playwright_browser()` 函数，检测 Playwright 浏览器驱动
- [x] 1.8 实现 `install_playwright_browser()` 函数，安装 Playwright 浏览器
- [x] 1.9 添加错误处理和用户友好的提示消息
- [x] 1.10 实现 `check_system_browser()` 函数，检测系统是否安装 Chrome 或 Edge

## 2. Linux/macOS 脚本增强
- [x] 2.1 修改 `xp` 脚本，添加 shebang 行确保可执行
- [x] 2.2 在 `xp` 脚本开头添加依赖检测逻辑
- [x] 2.3 实现自动检测 Python 解释器（python3 或 python）
- [x] 2.4 集成依赖检查器，首次运行时自动安装依赖
- [x] 2.5 添加环境变量支持（XP_SKIP_DEP_CHECK）用于跳过依赖检查
- [x] 2.6 测试脚本在 macOS 上的兼容性

## 3. Windows 脚本增强
- [x] 3.1 修改 `xp.bat` 脚本，添加依赖检测逻辑
- [x] 3.2 实现自动检测 Python 解释器（python、python3 或 py）
- [x] 3.3 集成依赖检查器，首次运行时自动安装依赖
- [x] 3.4 添加环境变量支持（XP_SKIP_DEP_CHECK）用于跳过依赖检查
- [x] 3.5 改进错误处理，提供 Windows 特定的错误提示
- [x] 3.6 添加 UTF-8 代码页设置以支持中文输出

## 4. 文档和测试
- [x] 4.1 创建跨平台使用文档 `docs/cross_platform_usage.md`
- [x] 4.2 文档包含快速开始指南
- [x] 4.3 文档包含环境变量说明
- [x] 4.4 文档包含常见问题解答
- [x] 4.5 文档包含平台特定说明
- [x] 4.6 验证向后兼容性（XP_SKIP_DEP_CHECK=1 可跳过检查）
- [x] 4.7 创建单元测试 `tests/cli/test_dependency_checker.py` (27 个测试用例)
- [x] 4.8 测试 Windows 浏览器检测（使用 mock）
- [x] 4.9 测试 macOS 浏览器检测（使用 mock）
- [x] 4.10 测试 Linux 浏览器检测（使用 mock）

## 5. 验证和清理
- [x] 5.1 在 macOS 上测试 `./xp --help`
- [x] 5.2 测试 dependency_checker.py 独立运行
- [x] 5.3 测试 XP_SKIP_DEP_CHECK 环境变量
- [x] 5.4 运行 `openspec validate add-cross-platform-xp-command --strict`
- [x] 5.5 更新所有任务状态为完成

