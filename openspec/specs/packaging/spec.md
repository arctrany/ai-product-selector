# packaging Specification

## Purpose
TBD - created by archiving change add-pyinstaller-packaging. Update Purpose after archive.
## Requirements
### Requirement: 依赖管理
系统 SHALL 提供完整的 Python 依赖管理配置，确保所有必需的包和版本都被正确声明。

#### Scenario: 依赖文件创建
- **WHEN** 开发者需要构建可执行文件
- **THEN** 系统提供 requirements.txt 文件，包含核心依赖：playwright>=1.40.0、openpyxl>=3.1.0、requests>=2.31.0、Pillow>=10.0.0、scikit-image>=0.21.0、opencv-python>=4.8.0、imagehash>=4.3.1、numpy>=1.24.0，以及可选的 AI 依赖：torch>=2.0.0、transformers>=4.30.0

#### Scenario: 依赖完整性验证
- **WHEN** 执行依赖安装命令
- **THEN** 所有依赖成功安装，无缺失或冲突

#### Scenario: Playwright 浏览器安装
- **WHEN** 安装 Playwright 依赖后
- **THEN** 自动执行 playwright install chromium 命令，确保浏览器驱动可用

### Requirement: PyInstaller 打包配置
系统 SHALL 提供 PyInstaller 打包配置，支持将 Python 应用打包为独立可执行文件。

#### Scenario: 单文件打包
- **WHEN** 执行 PyInstaller 构建命令
- **THEN** 生成单个可执行文件，包含所有依赖和资源

#### Scenario: 资源文件包含
- **WHEN** 打包过程中处理配置文件
- **THEN** JSON 配置文件（config.json、example_config.json）和选择器配置（ozon_selectors_default.json）正确包含在可执行文件中

#### Scenario: Playwright 浏览器支持
- **WHEN** 打包包含 Playwright 依赖的应用
- **THEN** Playwright 浏览器驱动和相关文件正确包含，运行时可正常启动 Chrome/Chromium 浏览器

#### Scenario: 第三方依赖打包
- **WHEN** 打包包含 openpyxl、requests、asyncio 等第三方依赖
- **THEN** 所有依赖库及其子依赖正确包含，运行时无导入错误

#### Scenario: 图像处理依赖支持
- **WHEN** 打包包含图像相似度分析功能
- **THEN** PIL/Pillow、opencv-python、scikit-image、imagehash、numpy 等图像处理库正确包含，图像相似度计算功能正常工作

#### Scenario: 入口点配置
- **WHEN** 打包 CLI 应用
- **THEN** 正确配置主入口点为 cli.main:main，支持命令行参数解析和子命令分发

### Requirement: 跨平台构建支持
系统 SHALL 支持在 Windows、macOS 和 Linux 平台上构建对应的可执行文件。

#### Scenario: Windows 平台构建
- **WHEN** 在 Windows 环境执行构建脚本
- **THEN** 生成 .exe 可执行文件，在 Windows 系统上可正常运行

#### Scenario: macOS 平台构建
- **WHEN** 在 macOS 环境执行构建脚本
- **THEN** 生成 macOS 可执行文件，在 macOS 系统上可正常运行

#### Scenario: Linux 平台构建
- **WHEN** 在 Linux 环境执行构建脚本
- **THEN** 生成 Linux 可执行文件，在 Linux 系统上可正常运行

### Requirement: 自动化构建流程
系统 SHALL 提供自动化构建脚本，简化打包过程并确保构建的一致性。

#### Scenario: 一键构建
- **WHEN** 开发者执行构建脚本
- **THEN** 自动完成环境检查、依赖安装、打包和输出整理

#### Scenario: 构建输出管理
- **WHEN** 构建完成后
- **THEN** 可执行文件输出到指定目录，包含版本信息和平台标识

#### Scenario: 构建错误处理
- **WHEN** 构建过程中出现错误
- **THEN** 提供清晰的错误信息和解决建议

### Requirement: 资源文件路径处理
系统 SHALL 正确处理打包后的资源文件路径，确保应用在可执行文件模式下能正常访问配置文件。

#### Scenario: 配置文件访问
- **WHEN** 打包后的应用需要读取配置文件
- **THEN** 能够正确定位和读取内嵌的 config.json、example_config.json、ozon_selectors_default.json 等配置文件

#### Scenario: 动态路径解析
- **WHEN** 应用运行时需要确定资源文件路径
- **THEN** 自动检测运行环境（开发模式 vs 打包模式）并使用正确的路径，支持 sys._MEIPASS 临时目录访问

#### Scenario: 模块化架构支持
- **WHEN** 打包后访问 cli、common、rpa 模块中的资源
- **THEN** 正确处理模块间的相对路径引用，确保所有模块资源可访问

### Requirement: 分发包管理
系统 SHALL 提供分发包的创建和管理功能，便于用户下载和使用。

#### Scenario: 分发包创建
- **WHEN** 构建完成后需要创建分发包
- **THEN** 自动创建包含可执行文件和必要文档的压缩包

#### Scenario: 版本标识
- **WHEN** 创建分发包时
- **THEN** 包名包含版本号和平台信息，便于用户识别

#### Scenario: 文件完整性
- **WHEN** 用户下载分发包
- **THEN** 包含所有必需文件，用户解压后可直接运行

