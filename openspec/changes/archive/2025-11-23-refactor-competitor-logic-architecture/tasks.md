## 1. 基础设施建设

- [x] 1.1 创建统一时序控制工具类 ✅
  - [x] 1.1.1 实现 `common/utils/wait_utils.py` ✅
  - [x] 1.1.2 添加 `wait_for_element_visible()` 方法 ✅
  - [x] 1.1.3 添加 `wait_for_url_change()` 方法 ✅
  - [x] 1.1.4 添加 `wait_for_element_clickable()` 方法 ✅
  - [x] 1.1.5 添加配置化超时控制 ✅

- [x] 1.2 创建统一抓取工具类 ✅
  - [x] 1.2.1 实现 `common/utils/scraping_utils.py` ✅
  - [x] 1.2.2 统一价格提取逻辑 `extract_price()` ✅
  - [x] 1.2.3 统一价格验证逻辑 `validate_price()` ✅
  - [x] 1.2.4 统一文本清理逻辑 `clean_text()` ✅
  - [x] 1.2.5 统一数字提取逻辑 `extract_number()` ✅

- [x] 1.3 建立标准数据格式 ✅
  - [x] 1.3.1 创建 `common/models/scraping_result.py` ✅
  - [x] 1.3.2 定义 `ScrapingResult` 数据类 ✅
  - [x] 1.3.3 定义 `CompetitorDetectionResult` 数据类 ✅
  - [x] 1.3.4 定义 `CompetitorInfo` 数据类 ✅

- [x] 1.4 重构配置管理系统 ✅
  - [x] 1.4.1 创建 `common/config/base_scraping_config.py` ✅
  - [x] 1.4.2 重构 `ozon_selectors_config.py` 使用继承 ✅
  - [x] 1.4.3 **重构 `seerfar_selectors_config.py` 使用继承** ✅
  - [x] 1.4.4 **重构 `erp_selectors_config.py` 使用继承** ✅
  - [x] 1.4.5 合并四个 Scraper 的重复选择器配置 ✅
  - [x] 1.4.6 建立配置优先级管理 ✅

- [x] 1.5 **完善配置层统一管理系统** ✅
  - [x] 1.5.1 **完善 `common/config/selector_base.py` 基类设计** ✅
  - [x] 1.5.2 **确保 `ozon_selectors_config.py` 继承 BaseSelectorConfig** ✅
  - [x] 1.5.3 **确保 `seerfar_selectors.py` 继承 BaseSelectorConfig** ✅
  - [x] 1.5.4 **确保 `erp_selectors_config.py` 继承 BaseSelectorConfig** ✅
  - [x] 1.5.5 **建立统一的配置管理接口规范** ✅
  - [x] 1.5.6 **验证所有 Selectors 配置的一致性** ✅

- [x] 1.6 **统一工具类管理策略** ✅
  - [x] 1.6.1 **分析现有 `utils/` 目录工具类（image_similarity.py, result_factory.py, url_converter.py）** ✅
  - [x] 1.6.2 **设计 ScrapingUtils 与现有工具类的统一管理策略** ✅
  - [x] 1.6.3 **建立统一的工具类命名和组织规范** ✅
  - [x] 1.6.4 **避免功能重复和依赖混乱的重构方案** ✅
  - [x] 1.6.5 **实施工具类合并或重组计划** ✅

- [x] 1.7 建立统一测试基础设施 ✅
  - [x] 1.7.1 创建 `tests/base_scraper_test.py` 统一测试基类 ✅
  - [x] 1.7.2 统一浏览器初始化和Mock框架 ✅
  - [x] 1.7.3 统一测试数据准备和清理逻辑 ✅
  - [x] 1.7.4 建立测试覆盖率检查工具 ✅

## 2. 核心逻辑重构

- [x] 2.1 创建独立跟卖检测服务 ✅
  - [x] 2.1.1 实现 `common/services/competitor_detection_service.py` ✅
  - [x] 2.1.2 实现跟卖区域检测逻辑 ✅
  - [x] 2.1.3 实现跟卖数量识别逻辑 ✅
  - [x] 2.1.4 实现跟卖价格比较逻辑 ✅
  - [x] 2.1.5 集成统一时序控制 ✅

- [x] 2.2 重构 OzonScraper 分离跟卖逻辑 ✅
  - [x] 2.2.1 移除硬编码 `time.sleep()` 调用 ✅
  - [x] 2.2.2 移除跟卖检测相关方法 ✅
  - [x] 2.2.3 重构为纯商品信息抓取器 ✅
  - [x] 2.2.4 集成 WaitUtils 替代硬编码等待 ✅
  - [x] 2.2.5 集成 ScrapingUtils 消除重复逻辑 ✅

- [x] 2.3 **重构 SeerfarScraper 架构统一** ✅
  - [x] 2.3.1 **移除 SeerfarScraper 中的硬编码等待逻辑** ✅
  - [x] 2.3.2 **集成 WaitUtils 替代时序控制代码** ✅
  - [x] 2.3.3 **使用 ScrapingUtils 消除重复的数据提取逻辑** ✅
  - [x] 2.3.4 **重构配置管理使用 BaseScrapingConfig** ✅
  - [x] 2.3.5 **统一 SeerfarScraper 的接口规范和返回格式** ✅

- [x] 2.4 重构 CompetitorScraper 专业化 ✅
  - [x] 2.4.1 移除与 OzonScraper 重复的功能 ✅
  - [x] 2.4.2 专注跟卖店铺信息抓取 ✅
  - [x] 2.4.3 使用统一的抓取工具类 ✅
  - [x] 2.4.4 统一接口规范和返回格式 ✅
  - [x] 2.4.5 集成统一时序控制 ✅

- [x] 2.5 **业务层目录重组** ✅
  - [x] 2.5.1 **创建项目根目录下的 `business/` 目录结构** ✅
  - [x] 2.5.2 **将 `filter_manager.py` 从 `common/scrapers/` 移动到 `business/`** ✅
  - [x] 2.5.3 **更新所有相关导入引用和依赖** ✅
  - [x] 2.5.4 **验证业务逻辑和数据抓取的职责边界** ✅
  - [x] 2.5.5 **确保移动后的功能完整性** ✅

- [x] 2.6 **重构 ErpPluginScraper 架构统一** ✅
  - [x] 2.6.1 **移除 ErpPluginScraper 中的硬编码等待逻辑** ✅
  - [x] 2.6.2 **集成 WaitUtils 替代时序控制代码** ✅
  - [x] 2.6.3 **使用 ScrapingUtils 消除重复的数据提取逻辑** ✅
  - [x] 2.6.4 **重构配置管理使用 BaseScrapingConfig** ✅
  - [x] 2.6.5 **统一 ErpPluginScraper 的接口规范和返回格式** ✅
  - [x] 2.6.6 **优化 ERP 插件加载检测机制** ✅

- [x] 2.7 实现服务协调层 ✅
  - [x] 2.7.1 创建 `ScrapingOrchestrator` 协调类 ✅
  - [x] 2.7.2 实现四个 Scraper 间的依赖注入 ✅
  - [x] 2.7.3 统一错误处理和重试逻辑 ✅
  - [x] 2.7.4 实现统一的日志记录 ✅

## 🚨 2.8 **SeerfarScraper 代码冗余优化（新增紧急任务）** ✅

- [x] 2.8.1 **🔥 分析并消除重复的销售数据提取方法** ✅
  - [x] 2.8.1.1 合并重复的 `_extract_sales_amount()` 方法（第277行和第857行） ✅
  - [x] 2.8.1.2 合并重复的 `_extract_sales_volume()` 方法（第309行和第892行） ✅  
  - [x] 2.8.1.3 合并重复的 `_extract_daily_avg_sales()` 方法（第341行和第927行） ✅
  - [x] 2.8.1.4 验证合并后的功能完整性 ✅

- [x] 2.8.2 **🔥 统一商品数据提取策略** ✅
  - [x] 2.8.2.1 分析 `_extract_all_products_data_js()`, `_extract_products_list()`, `_extract_basic_product_data()` 的功能重叠 ✅
  - [x] 2.8.2.2 设计统一的商品数据提取架构 ✅
  - [x] 2.8.2.3 消除重复的JavaScript模板和选择器逻辑 ✅
  - [x] 2.8.2.4 优化商品行去重和过滤逻辑 ✅

- [x] 2.8.3 **🔥 重构通用工具方法** ✅
  - [x] 2.8.3.1 将 `_extract_data_with_selector()` 和 `_extract_data_with_js()` 迁移到 ScrapingUtils ✅
  - [x] 2.8.3.2 消除 SeerfarScraper 内部的重复工具方法 ✅
  - [x] 2.8.3.3 统一错误处理和日志记录模式 ✅
  - [x] 2.8.3.4 减少代码行数至800-1000行 ✅

- [x] 2.8.4 **🔥 代码质量提升** ✅
  - [x] 2.8.4.1 移除不必要的 try-catch 重复逻辑 ✅
  - [x] 2.8.4.2 优化方法命名和文档字符串 ✅
  - [x] 2.8.4.3 确保零lint错误和代码规范 ✅
  - [x] 2.8.4.4 性能测试验证优化效果 ✅

## 3. 接口标准化 ✅

- [x] 3.1 统一方法签名 ✅
  - [x] 3.1.1 标准化所有 scrape 方法的签名 ✅
  - [x] 3.1.2 统一参数命名和类型定义 ✅
  - [x] 3.1.3 统一可选参数的默认值处理 ✅
  - [x] 3.1.4 添加类型注解和文档字符串 ✅

- [x] 3.2 标准化返回值格式 ✅
  - [x] 3.2.1 所有方法返回 ScrapingResult 格式 ✅
  - [x] 3.2.2 统一成功和失败状态的表示 ✅
  - [x] 3.2.3 标准化错误码和错误信息格式 ✅
  - [x] 3.2.4 确保向后兼容性 ✅

- [x] 3.3 统一异常处理策略 ✅
  - [x] 3.3.1 定义标准异常类型 ✅
  - [x] 3.3.2 实现统一的异常捕获和转换 ✅
  - [x] 3.3.3 添加详细的错误上下文信息 ✅
  - [x] 3.3.4 实现降级处理策略 ✅

## 4. 测试与验证（重点补齐 SeerfarScraper 测试） ✅

- [x] 4.1 **紧急补齐 SeerfarScraper 和 ErpPluginScraper 测试覆盖** ✅
  - [x] 4.1.1 **创建 `tests/test_seerfar_scraper.py`（当前覆盖率几乎为 0%）** ✅
  - [x] 4.1.2 **创建 `tests/test_erp_plugin_scraper.py`（当前覆盖率几乎为 0%）** ✅
  - [x] 4.1.3 **为 SeerfarScraper 核心方法编写单元测试** ✅
  - [x] 4.1.4 **为 ErpPluginScraper 核心方法编写单元测试** ✅
  - [x] 4.1.5 **为 SeerfarScraper 错误处理编写测试** ✅
  - [x] 4.1.6 **为 ErpPluginScraper 错误处理编写测试** ✅
  - [x] 4.1.7 **为 SeerfarScraper 时序控制编写测试** ✅
  - [x] 4.1.8 **为 ErpPluginScraper ERP插件加载检测编写测试** ✅
  - [x] 4.1.9 **确保 SeerfarScraper 测试覆盖率 ≥ 95%** ✅
  - [x] 4.1.10 **确保 ErpPluginScraper 测试覆盖率 ≥ 95%** ✅

- [x] 4.2 统一工具类单元测试 ✅
  - [x] 4.2.1 为 WaitUtils 编写完整单元测试 ✅
  - [x] 4.2.2 为 ScrapingUtils 编写完整单元测试 ✅
  - [x] 4.2.3 为 CompetitorDetectionService 编写单元测试 ✅
  - [x] 4.2.4 为 BaseScrapingConfig 编写单元测试 ✅
  - [x] 4.2.5 确保工具类测试覆盖率 ≥ 95% ✅

- [x] 4.3 重构后的 Scraper 测试更新 ✅
  - [x] 4.3.1 更新 OzonScraper 测试使用统一测试基类 ✅
  - [x] 4.3.2 更新 CompetitorScraper 测试使用统一测试基类 ✅
  - [x] 4.3.3 更新 SeerfarScraper 测试使用统一测试基类 ✅
  - [x] 4.3.4 更新 ErpPluginScraper 测试使用统一测试基类 ✅
  - [x] 4.3.5 为四个 Scraper 编写统一的测试模式 ✅
  - [x] 4.3.6 确保所有 Scraper 测试覆盖率 ≥ 95% ✅

- [x] 4.4 **多 Scraper 集成测试** ✅
  - [x] 4.4.1 **创建 `tests/test_scraping_integration.py`** ✅
  - [x] 4.4.2 **SeerfarScraper → OzonScraper → CompetitorScraper 调用链测试** ✅
  - [x] 4.4.3 **ErpPluginScraper 独立数据抓取和集成测试** ✅
  - [x] 4.4.4 **四个 Scraper 协同工作的端到端测试** ✅
  - [x] 4.4.5 **统一时序控制在多 Scraper 场景下的测试** ✅
  - [x] 4.4.5 **集成测试覆盖率 ≥ 90%** ✅

- [x] 4.5 系统功能验证测试 ✅
  - [x] 4.5.1 端到端跟卖检测流程测试 ✅
  - [x] 4.5.2 时序控制功能测试 ✅
  - [x] 4.5.3 错误处理和降级策略测试 ✅
  - [x] 4.5.4 性能回归测试 ✅
  - [x] 4.5.5 并发场景测试 ✅

- [x] 4.6 向后兼容性测试 ✅
  - [x] 4.6.1 SeerfarScraper API 调用方式兼容性测试 ✅
  - [x] 4.6.2 三个 Scraper 返回值格式兼容性测试 ✅
  - [x] 4.6.3 配置加载兼容性测试 ✅
  - [x] 4.6.4 所有现有测试用例通过验证 ✅

## 5. 性能优化与监控 ✅

- [x] 5.1 性能基准测试 ✅
  - [x] 5.1.1 建立重构前性能基准 ✅
  - [x] 5.1.2 测试重构后性能表现 ✅
  - [x] 5.1.3 对比分析性能改进效果 ✅
  - [x] 5.1.4 识别和解决性能瓶颈 ✅

- [x] 5.2 监控指标实现 ✅
  - [x] 5.2.1 添加时序控制成功率监控 ✅
  - [x] 5.2.2 添加跟卖检测成功率监控 ✅
  - [x] 5.2.3 添加平均响应时间监控 ✅
  - [x] 5.2.4 添加错误率和重试次数监控 ✅

## 6. 文档与部署 ✅

- [x] 6.1 **架构铁律文档化** ✅
  - [x] 6.1.1 **将分层架构原则更新到 `project.md`（协调层、服务层、抓取层、工具层）** ✅
  - [x] 6.1.2 **文档化职责分离和单一职责原则** ✅
  - [x] 6.1.3 **文档化统一接口和数据格式标准** ✅
  - [x] 6.1.4 **文档化测试覆盖率和质量要求** ✅
  - [x] 6.1.5 **文档化跨平台兼容性要求和架构决策** ✅

- [x] 6.2 技术文档更新 ✅
  - [x] 6.2.1 更新架构设计文档 ✅
  - [x] 6.2.2 更新API使用文档 ✅
  - [x] 6.2.3 编写迁移指南 ✅
  - [x] 6.2.4 更新开发者指南 ✅

- [x] 6.3 代码审查与优化 ✅
  - [x] 6.3.1 静态代码分析检查 ✅
  - [x] 6.3.2 代码风格一致性检查 ✅
  - [x] 6.3.3 安全性检查 ✅
  - [x] 6.3.4 最终代码审查 ✅

- [x] 6.4 部署准备 ✅
  - [x] 6.4.1 准备部署脚本和配置 ✅
  - [x] 6.4.2 准备回滚计划 ✅
  - [x] 6.4.3 准备监控和报警配置 ✅
  - [x] 6.4.4 准备发布说明 ✅