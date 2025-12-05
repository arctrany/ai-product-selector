# cli Specification

## Purpose
TBD - created by archiving change add-cross-platform-xp-command. Update Purpose after archive.
## Requirements
### Requirement: 跨平台 xp 命令支持
系统 SHALL 提供跨平台的 `xp` 命令，在 Windows、Linux、macOS 上都能直接运行，无需用户手动配置 Python 环境或安装依赖。

#### Scenario: Linux/macOS 上运行 xp 命令
- **WHEN** 用户在 Linux 或 macOS 系统上执行 `./xp --help` 或 `xp --help`
- **THEN** 命令成功执行并显示帮助信息
- **AND** 脚本自动检测并使用可用的 Python 解释器（优先使用 `python3`，如果不存在则使用 `python`）

#### Scenario: Windows 上运行 xp 命令
- **WHEN** 用户在 Windows 系统上执行 `xp.bat --help` 或 `xp --help`（如果配置了文件关联）
- **THEN** 命令成功执行并显示帮助信息
- **AND** 脚本自动检测并使用可用的 Python 解释器（优先使用 `python`，如果不存在则尝试 `py`）

#### Scenario: 首次运行时自动安装依赖
- **WHEN** 用户首次运行 `xp` 命令且系统中缺少项目依赖（requirements.txt 中声明的包）
- **THEN** 系统自动检测缺失的依赖包
- **AND** 显示清晰的进度提示："检测到缺失依赖，正在安装..."
- **AND** 自动执行 `pip install -r requirements.txt` 安装缺失的依赖
- **AND** 安装完成后继续执行用户请求的命令

#### Scenario: 依赖已安装时跳过安装
- **WHEN** 用户运行 `xp` 命令且所有依赖都已安装
- **THEN** 系统快速检测依赖状态（< 1秒）
- **AND** 跳过安装步骤，直接执行用户请求的命令
- **AND** 不显示任何依赖相关的提示信息

#### Scenario: 自动安装 Playwright 浏览器驱动
- **WHEN** 用户首次运行 `xp` 命令且 Playwright 浏览器驱动未安装
- **THEN** 系统自动检测 Playwright 浏览器驱动状态
- **AND** 如果驱动缺失，自动执行 `playwright install chromium` 安装浏览器驱动
- **AND** 显示安装进度提示

#### Scenario: Python 版本检测
- **WHEN** 用户运行 `xp` 命令
- **THEN** 系统检测 Python 版本
- **AND** 如果 Python 版本 < 3.8，显示错误消息："错误: 需要 Python 3.8 或更高版本，当前版本: X.X.X"
- **AND** 退出码为 1
- **AND** 提供安装建议："请升级 Python 或使用 pyenv/conda 安装 Python 3.8+"

#### Scenario: pip 不可用时的错误处理
- **WHEN** 用户运行 `xp` 命令但系统中 pip 不可用
- **THEN** 系统检测到 pip 不可用
- **AND** 显示错误消息："错误: 未找到 pip，无法安装依赖"
- **AND** 退出码为 1
- **AND** 提供安装建议："请先安装 pip: python -m ensurepip --upgrade"

#### Scenario: 网络失败时的错误处理
- **WHEN** 用户运行 `xp` 命令需要安装依赖但网络连接失败
- **THEN** 系统检测到网络错误
- **AND** 显示错误消息："错误: 无法连接到 PyPI，请检查网络连接"
- **AND** 退出码为 1
- **AND** 提供解决建议："可以设置环境变量 XP_SKIP_DEP_CHECK=1 跳过依赖检查，或手动运行 pip install -r requirements.txt"

#### Scenario: 权限不足时的错误处理
- **WHEN** 用户运行 `xp` 命令需要安装依赖但权限不足（无法写入系统 Python 目录）
- **THEN** 系统尝试使用 `--user` 标志安装到用户目录
- **AND** 如果仍然失败，显示错误消息："错误: 权限不足，无法安装依赖"
- **AND** 退出码为 1
- **AND** 提供解决建议："建议使用虚拟环境: python -m venv venv && source venv/bin/activate (Linux/macOS) 或 venv\Scripts\activate (Windows)"

#### Scenario: 跳过依赖检查
- **WHEN** 用户设置环境变量 `XP_SKIP_DEP_CHECK=1` 后运行 `xp` 命令
- **THEN** 系统跳过所有依赖检测和安装步骤
- **AND** 直接执行用户请求的命令
- **AND** 如果依赖缺失导致运行时错误，显示相应的导入错误信息

#### Scenario: 虚拟环境检测
- **WHEN** 用户在虚拟环境中运行 `xp` 命令
- **THEN** 系统检测到虚拟环境
- **AND** 依赖安装到虚拟环境中（不使用 `--user` 标志）
- **AND** 提供提示："检测到虚拟环境，依赖将安装到虚拟环境中"

#### Scenario: 依赖冲突检测
- **WHEN** 用户运行 `xp` 命令需要安装依赖但检测到版本冲突
- **THEN** 系统显示警告消息："警告: 检测到依赖版本冲突，可能影响功能"
- **AND** 继续执行安装（使用 requirements.txt 中的版本要求）
- **AND** 提供建议："建议使用虚拟环境隔离依赖"

#### Scenario: 跨平台命令一致性
- **WHEN** 用户在 Windows 上运行 `xp.bat --help`
- **AND** 用户在 Linux 上运行 `./xp --help`
- **AND** 用户在 macOS 上运行 `./xp --help`
- **THEN** 所有平台上的命令行为一致
- **AND** 输出相同的帮助信息
- **AND** 支持相同的命令行参数和选项

