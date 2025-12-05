# Spec Delta: RPA 浏览器包重构

## MODIFIED Requirements

### Requirement: RPA-CONFIG-001 统一配置管理

RPA 浏览器模块 **SHALL** 接受 `common.config.BrowserConfig` 作为配置源，内部通过适配器转换为 RPA 层所需格式，消除两套配置系统的冗余。

#### Scenario: 使用业务层配置初始化浏览器服务
- **Given**: 用户通过 `GoodStoreSelectorConfig.browser` 提供配置
- **When**: 调用 `BrowserService(config.browser)` 初始化
- **Then**: 浏览器服务接受 `common.BrowserConfig`，内部适配为 RPA 配置

#### Scenario: 配置适配器转换
- **Given**: `common.BrowserConfig` 包含 `headless=True, window_width=1920`
- **When**: 调用 `adapt_config(common_config)` 转换
- **Then**: 返回 `RPAInternalConfig` 包含 `headless=True, viewport.width=1920`

#### Scenario: 向后兼容 Dict 配置
- **Given**: 旧代码使用 `BrowserService(config_dict)` 传入字典
- **When**: 初始化浏览器服务
- **Then**: 打印警告提示迁移，但仍正常工作

#### Scenario: 单例线程安全
- **Given**: 多个线程同时调用 `BrowserService.get_global_instance()`
- **When**: 并发创建单例
- **Then**: 只创建一个实例，使用 `threading.Lock` 保护

---

### Requirement: RPA-EXCEPTION-001 精简异常层次

RPA 浏览器模块 **MUST** 使用 5 个核心异常类配合错误码机制，替代原有 20+ 个异常类。

#### Scenario: 导航超时抛出统一异常
- **Given**: 页面导航超过配置的超时时间
- **When**: 导航操作超时
- **Then**: 抛出 `NavigationError` 异常，`error_code` 为 `"TIMEOUT"`

#### Scenario: 元素未找到抛出统一异常
- **Given**: 使用选择器查找页面元素
- **When**: 元素不存在或超时
- **Then**: 抛出 `ElementError` 异常，`error_code` 为 `"NOT_FOUND"`

---

### Requirement: RPA-LOGGING-001 统一日志系统

RPA 浏览器模块 **MUST** 全部使用 `StructuredLogger`，移除所有 `print()` 调用。

#### Scenario: 分页操作记录结构化日志
- **Given**: 分页器执行翻页操作
- **When**: 翻页成功或失败
- **Then**: 使用 `logger.info()` 或 `logger.error()` 记录，不使用 `print()`

#### Scenario: 调试模式显示详细日志
- **Given**: 配置 `debug_mode=True`
- **When**: 执行任何浏览器操作
- **Then**: 记录 DEBUG 级别的详细日志，包含操作耗时和参数

---

### Requirement: RPA-INTERFACE-001 同步接口设计

RPA 浏览器模块 **SHALL** 对外提供同步接口，内部实现可使用异步但对上层透明。

#### Scenario: 业务层同步调用浏览器服务
- **Given**: `common/scrapers/` 模块调用浏览器服务
- **When**: 调用 `browser_service.open_page(url)` 等方法
- **Then**: 方法同步返回结果，调用方无需使用 `await`

#### Scenario: 移除重复的同步后缀方法
- **Given**: 原有 `screenshot()` 和 `screenshot_sync()` 两个方法
- **When**: 重构完成后
- **Then**: 只保留 `screenshot()` 方法，行为为同步

---

### Requirement: RPA-QUALITY-001 代码质量标准

RPA 浏览器模块 **MUST** 遵循代码质量标准，包括函数长度、异常处理、代码重复等。

#### Scenario: 函数不超过 30 行
- **Given**: RPA 模块中的任意函数
- **When**: 检查函数行数
- **Then**: 每个函数不超过 30 行（不含注释和空行）

#### Scenario: 异常处理区分类型
- **Given**: try-except 块
- **When**: 捕获异常
- **Then**: 不使用裸 `except:` 或 `except Exception:`，而是捕获具体异常类型

#### Scenario: 提取重复代码为公共方法
- **Given**: 分页器中的选择器查找逻辑
- **When**: 多处使用相同的选择器查找模式
- **Then**: 提取为 `_find_element_by_selectors(selectors)` 公共方法

---

### Requirement: RPA-DETECTOR-001 浏览器和插件检测

RPA 浏览器模块 **SHALL** 提供浏览器检测和插件检测功能，支持 Edge 和 Chrome 浏览器，以及配置化的插件检测。

#### Scenario: 检测 Edge 和 Chrome 浏览器
- **Given**: 用户系统安装了 Edge 或 Chrome 浏览器
- **When**: 调用 `BrowserDetector.detect_browsers()`
- **Then**: 返回检测到的浏览器列表，包含类型和用户数据目录

#### Scenario: 检测必需的浏览器插件
- **Given**: 配置中定义了必需插件列表（如 seefar 插件、毛子插件）
- **When**: CLI 启动时调用 `PluginDetector.check_required_plugins()`
- **Then**: 检测插件安装状态，未安装时输出提示信息和安装指引

#### Scenario: 插件通过 ID 配置
- **Given**: 用户在配置文件中配置插件 ID
- **When**: 系统启动检测
- **Then**: 根据 plugin_id 检查扩展目录中是否存在对应插件

#### Scenario: 严格插件检查模式（默认）
- **Given**: 配置 `strict_plugin_check=True`（默认值）
- **When**: 必需插件未安装
- **Then**: 阻断启动，输出错误信息和安装指引

#### Scenario: 宽松插件检查模式
- **Given**: 配置 `strict_plugin_check=False`
- **When**: 必需插件未安装
- **Then**: 输出警告信息，但继续启动

---

### Requirement: RPA-NAMING-001 类命名规范

RPA 浏览器模块 **MUST** 使用简洁明确的类命名，移除冗余前缀。

#### Scenario: 服务类命名
- **Given**: 浏览器服务类
- **When**: 重构完成后
- **Then**: 类名为 `BrowserService`，而非 `SimplifiedBrowserService`

#### Scenario: 驱动类命名
- **Given**: Playwright 驱动实现类
- **When**: 重构完成后
- **Then**: 类名为 `PlaywrightBrowserDriver`，而非 `SimplifiedPlaywrightBrowserDriver`

---

### Requirement: RPA-STRUCTURE-001 目录结构简化

RPA 浏览器模块 **SHALL** 采用扁平化目录结构，将目录层次从 4 层减少到 2 层。

#### Scenario: 删除 core 层级
- **Given**: 当前存在 `rpa/browser/core/` 目录
- **When**: 重构完成后
- **Then**: `core/` 目录被删除，配置、异常、接口直接放在 `browser/` 下

#### Scenario: 功能模块按职责划分
- **Given**: 当前 `implementations/` 目录包含多个实现
- **When**: 重构完成后
- **Then**: 按职责划分为 `driver/`、`analyzer/`、`paginator/` 子目录

## REMOVED Requirements

### Requirement: 移除未使用的配置类

移除 `PerformanceConfig`、`SecurityConfig`、`ExtensionConfig` 等从未使用的配置类。

#### Scenario: 删除未使用代码后构建成功
- **Given**: 删除 `PerformanceConfig`、`SecurityConfig`、`ExtensionConfig`
- **When**: 运行完整测试套件
- **Then**: 所有测试通过，无导入错误

### Requirement: 移除向后兼容别名

移除 `OptimizedDOMPageAnalyzer`、`DOMPageAnalyzer`、`DOMContentExtractor` 等别名。

#### Scenario: 删除别名后使用正确类名
- **Given**: 代码中使用 `SimplifiedDOMPageAnalyzer` 而非别名
- **When**: 删除所有别名定义
- **Then**: 代码正常运行，无 `NameError`
