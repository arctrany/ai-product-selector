# Tasks: RPA 浏览器包重构

## 1. 配置层重构（收敛两套配置系统）

### 1.1 确立配置主权
- [ ] 1.1.1 确认 `common/config/browser_config.py::BrowserConfig` 为唯一业务配置源
- [ ] 1.1.2 创建 `rpa/browser/config_adapter.py` 配置适配器
- [ ] 1.1.3 定义 `RPAInternalConfig` 数据类（仅包含 RPA 层特有配置）
- [ ] 1.1.4 实现 `adapt_config(common.BrowserConfig) -> RPAInternalConfig` 转换函数

### 1.2 更新 BrowserService 接口
- [ ] 1.2.1 修改 `BrowserService.__init__` 接受 `Optional[common.BrowserConfig]` 而非 `Dict`
- [ ] 1.2.2 在 `BrowserService` 内部调用 `adapt_config()` 转换配置
- [ ] 1.2.3 更新 `get_global_instance()` 支持传入 `common.BrowserConfig`
- [ ] 1.2.4 保持向后兼容：仍支持 Dict 配置（添加警告）

### 1.3 清理 RPA 层冗余配置
- [ ] 1.3.1 删除 `rpa/browser/core/models/browser_config.py` 中与 common 重复的字段
- [ ] 1.3.2 保留 RPA 特有配置：`ViewportConfig`（内部使用）
- [ ] 1.3.3 删除 `PerformanceConfig` (未使用)
- [ ] 1.3.4 删除 `SecurityConfig` (未使用)
- [ ] 1.3.5 删除 `ExtensionConfig` (未使用)
- [ ] 1.3.6 简化 `BrowserServiceConfig`，移除重复字段
- [ ] 1.3.7 删除 `ConfigManager` 中的冗余加载逻辑

### 1.4 上游适配（8个文件）
- [ ] 1.4.1 更新 `common/scrapers/__init__.py` 导出 `BrowserService`
- [ ] 1.4.2 更新 `common/scrapers/base_scraper.py` 导入
- [ ] 1.4.3 更新 `common/scrapers/seerfar_scraper.py` 导入
- [ ] 1.4.4 更新 `common/scrapers/ozon_scraper.py` 导入
- [ ] 1.4.5 更新 `common/scrapers/competitor_scraper.py` 导入
- [ ] 1.4.6 更新 `common/scrapers/erp_plugin_scraper.py` 导入
- [ ] 1.4.7 更新 `common/services/scraping_orchestrator.py` 导入
- [ ] 1.4.8 更新 `cli/main.py` 使用 `config.browser` 替代 `config.scraping`
- [ ] 1.4.9 添加集成测试验证配置传递链路

### 1.5 单例线程安全
- [ ] 1.5.1 在 `BrowserService` 中添加 `threading.Lock` 保护单例创建
- [ ] 1.5.2 使用双重检查锁定模式 (Double-Checked Locking)
- [ ] 1.5.3 添加线程安全单元测试

## 2. 异常层精简

### 2.1 创建精简异常层次
- [ ] 2.1.1 定义错误码常量模块 `error_codes.py`
- [ ] 2.1.2 创建精简版 `BrowserError` 基类（含错误码）
- [ ] 2.1.3 创建 5 个核心异常类：`InitializationError`, `NavigationError`, `ElementError`, `ResourceError`, `AnalysisError`
- [ ] 2.1.4 添加异常工厂函数 `create_error(code, message)`

### 2.2 迁移异常使用
- [ ] 2.2.1 更新 `browser_service.py` 异常抛出
- [ ] 2.2.2 更新 `playwright_browser_driver.py` 异常抛出
- [ ] 2.2.3 更新 `dom_page_analyzer.py` 异常抛出
- [ ] 2.2.4 更新 `universal_paginator.py` 异常抛出

### 2.3 删除冗余异常类
- [ ] 2.3.1 删除 `BrowserTimeoutError` (合并到 `NavigationError`)
- [ ] 2.3.2 删除 `PageNavigationError` (合并到 `NavigationError`)
- [ ] 2.3.3 删除 `PageLoadError` (合并到 `NavigationError`)
- [ ] 2.3.4 删除 `ElementNotFoundError` (合并到 `ElementError`)
- [ ] 2.3.5 删除 `ElementNotInteractableError` (合并到 `ElementError`)
- [ ] 2.3.6 删除 `ElementInteractionError` (合并到 `ElementError`)
- [ ] 2.3.7 删除 `ResourceManagementError` (合并到 `ResourceError`)
- [ ] 2.3.8 删除 `TimeoutError` (使用标准库)
- [ ] 2.3.9 删除 `ScenarioExecutionError` 别名

## 3. 日志标准化

### 3.1 移除 print 语句
- [ ] 3.1.1 移除 `universal_paginator.py` 中所有 print 语句
- [ ] 3.1.2 移除 `browser_detector.py` 中所有 print 语句
- [ ] 3.1.3 移除 `browser_service.py` 中所有 print 语句（如有）
- [ ] 3.1.4 移除 `playwright_browser_driver.py` 中所有 print 语句（如有）

### 3.2 统一日志格式
- [ ] 3.2.1 确保所有类使用 `StructuredLogger`
- [ ] 3.2.2 移除日志消息中的表情符号
- [ ] 3.2.3 统一日志级别使用规范

## 4. 接口层简化

### 4.0 类重命名
- [ ] 4.0.1 将 `SimplifiedBrowserService` 重命名为 `BrowserService`
- [ ] 4.0.2 将 `SimplifiedPlaywrightBrowserDriver` 重命名为 `PlaywrightBrowserDriver`
- [ ] 4.0.3 将 `SimplifiedDOMPageAnalyzer` 重命名为 `DOMPageAnalyzer`
- [ ] 4.0.4 更新所有导入和引用（common/scrapers/ 等）
- [ ] 4.0.5 更新 `__init__.py` 导出

### 4.1 精简 IBrowserDriver
- [ ] 4.1.1 移除重复的同步方法（保留一个版本）
- [ ] 4.1.2 将 `screenshot_sync` 合并到 `screenshot`
- [ ] 4.1.3 将 `get_page_title_sync` 合并到 `get_page_title`
- [ ] 4.1.4 更新实现类适配新接口

### 4.2 合并分析器接口
- [ ] 4.2.1 创建统一的 `IAnalyzer` 接口
- [ ] 4.2.2 合并 `IPageAnalyzer`, `IContentExtractor`, `IElementMatcher`, `IPageValidator`
- [ ] 4.2.3 更新 `SimplifiedDOMPageAnalyzer` 实现新接口

### 4.3 删除向后兼容别名
- [ ] 4.3.1 删除 `OptimizedDOMPageAnalyzer = SimplifiedDOMPageAnalyzer`
- [ ] 4.3.2 删除 `DOMPageAnalyzer = SimplifiedDOMPageAnalyzer`
- [ ] 4.3.3 删除 `DOMContentExtractor = SimplifiedDOMPageAnalyzer`
- [ ] 4.3.4 删除 `DOMElementMatcher = SimplifiedDOMPageAnalyzer`
- [ ] 4.3.5 删除 `DOMPageValidator = SimplifiedDOMPageAnalyzer`
- [ ] 4.3.6 更新 `__init__.py` 导出

## 5. 目录结构重构

### 5.0 简化目录层次
- [ ] 5.0.1 创建新目录结构：`driver/`、`analyzer/`、`paginator/`
- [ ] 5.0.2 移动 `browser_service.py` → `service.py`
- [ ] 5.0.3 移动 `implementations/playwright_browser_driver.py` → `driver/playwright.py`
- [ ] 5.0.4 移动 `implementations/dom_page_analyzer.py` → `analyzer/dom.py`
- [ ] 5.0.5 移动 `implementations/universal_paginator.py` → `paginator/universal.py`
- [ ] 5.0.6 合并 `core/config/` 和 `core/models/` → `config.py`
- [ ] 5.0.7 合并 `core/interfaces/*.py` → `interfaces.py`
- [ ] 5.0.8 移动 `core/exceptions/` → `exceptions.py`
- [ ] 5.0.9 删除空的 `core/` 目录
- [ ] 5.0.10 删除空的 `implementations/` 目录
- [ ] 5.0.11 更新所有内部导入路径
- [ ] 5.0.12 更新 `__init__.py` 导出

## 6. 代码清理

### 6.1 删除未使用代码
- [ ] 6.1.1 审查并删除 `browser_config.py` 中未使用的工厂函数
- [ ] 6.1.2 审查并删除 `config.py` 中未使用的预设配置
- [ ] 6.1.3 删除 `dom_page_analyzer.py` 中未调用的方法（如 `check_accessibility`）

### 6.2 优化浏览器检测器
- [ ] 6.2.1 将 `subprocess.run()` 改为异步版本（使用 asyncio.subprocess）
- [ ] 6.2.2 添加缓存避免重复检测（TTL 缓存）
- [ ] 6.2.3 扩展支持 Chrome 浏览器检测（除 Edge 外）
- [ ] 6.2.4 添加 `_get_chrome_user_data_dir()` 方法（已存在但未使用，需激活）
- [ ] 6.2.5 创建统一的浏览器类型枚举（EDGE, CHROME）

### 6.3 浏览器插件检测功能
- [ ] 6.3.1 创建 `PluginDetector` 类，用于检测浏览器插件
- [ ] 6.3.2 定义插件配置结构（plugin_id, plugin_name, required）
- [ ] 6.3.3 实现插件安装状态检测（通过检查扩展目录）
- [ ] 6.3.4 支持配置必需插件列表（如 seefar 插件、毛子插件）
- [ ] 6.3.5 在 `common.BrowserConfig` 中添加 `strict_plugin_check: bool = True` 配置
- [ ] 6.3.6 CLI 启动时调用检测，根据 `strict_plugin_check` 决定是否阻断
- [ ] 6.3.7 提供插件安装指引（输出安装链接或说明）

### 6.4 优化分页器
- [ ] 6.4.1 将硬编码选择器移到配置文件
- [ ] 6.4.2 保留所有分页类型（NUMERIC、LOAD_MORE、INFINITE）
- [ ] 6.4.3 简化 `_wait_for_page_update` 逻辑
- [ ] 6.4.4 提取重复的选择器查找逻辑为公共方法

### 6.5 降低 Playwright 耦合
- [ ] 6.5.1 创建抽象接口 `IPage`、`IBrowserContext` 替代直接使用 Playwright 类型
- [ ] 6.5.2 更新 `IBrowserDriver` 使用抽象接口而非 `Optional[Page]`
- [ ] 6.5.3 创建 Playwright 适配器实现抽象接口
- [ ] 6.5.4 更新分析器和分页器使用抽象接口

## 7. 测试重构

### 7.1 重新设计单元测试
- [ ] 7.1.1 创建 `tests/unit/test_config_adapter.py`
- [ ] 7.1.2 创建 `tests/unit/test_browser_errors.py`
- [ ] 7.1.3 更新 `tests/unit/test_browser_service.py`

### 7.2 重新设计集成测试
- [ ] 7.2.1 创建核心功能集成测试
- [ ] 7.2.2 验证配置迁移正确性
- [ ] 7.2.3 验证异常处理正确性

## 8. 代码质量审查

### 8.1 函数长度检查
- [ ] 8.1.1 审查所有函数，确保不超过 30 行（不含注释和空行）
- [ ] 8.1.2 拆分超长函数为多个小函数

### 8.2 异常处理规范
- [ ] 8.2.1 搜索并替换所有裸 `except:` 为具体异常类型
- [ ] 8.2.2 搜索并替换所有 `except Exception:` 为具体异常类型

## 9. 文档和清理

### 9.1 更新文档
- [ ] 9.1.1 更新 `openspec/project.md` 中 RPA 模块描述
- [ ] 9.1.2 添加迁移指南说明 API 变更

### 9.2 最终验证
- [ ] 9.2.1 运行完整测试套件
- [ ] 9.2.2 验证 `common/scrapers/` 功能正常
- [ ] 9.2.3 检查没有未解决的 TODO 或 FIXME
