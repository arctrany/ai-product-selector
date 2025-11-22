# Change: 添加 PyInstaller 打包支持

## Why

当前 AI 选品自动化系统需要用户安装 Python 环境和依赖包才能运行，这对普通用户来说存在技术门槛。为了提升用户体验，让更多用户能够轻松使用本系统，需要提供独立的可执行文件分发方式。

## What Changes

- 添加 PyInstaller 打包配置和构建脚本
- 创建跨平台（Windows/macOS/Linux）构建流程
- 配置资源文件和配置文件的正确打包处理
- 建立依赖管理文件（requirements.txt）
- 提供自动化构建和分发脚本

## Impact

- 新增功能：packaging 能力规范
- 影响的代码：
  - 新增 `packaging/` 目录及相关构建脚本
  - 新增 `requirements.txt` 依赖管理文件
  - 新增 `build.py` 自动化构建脚本
- 用户体验：用户可直接下载可执行文件运行，无需安装 Python 环境
- 分发方式：支持跨平台独立可执行文件分发
