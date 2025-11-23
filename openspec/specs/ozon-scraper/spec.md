# ozon-scraper Specification

## Purpose
TBD - created by archiving change refactor-ozon-scraper-optimization. Update Purpose after archive.
## Requirements
### Requirement: Code Structure Simplification
The OzonScraper SHALL maintain clean, non-redundant code structure by eliminating unnecessary wrapper methods that do not add functional value.

#### Scenario: Image extraction methods consolidation
- **WHEN** extracting product images from page content
- **THEN** the system SHALL use the core extraction method directly without redundant wrapper methods
- **AND** maintain identical functionality and return values

#### Scenario: Price data extraction methods consolidation  
- **WHEN** extracting price data from page content
- **THEN** the system SHALL use the core extraction method directly without redundant wrapper methods
- **AND** maintain identical functionality and return values

#### Scenario: Method parameter cleanup
- **WHEN** calling core extraction methods
- **THEN** the system SHALL not pass unused parameters
- **AND** maintain method signature compatibility where needed

### Requirement: 时序控制标准化
OzonScraper SHALL 使用统一的时序控制机制，移除所有硬编码等待，确保跨平台兼容性和系统稳定性。

#### Scenario: 显式等待替代硬编码等待
- **WHEN** 需要等待页面元素或状态变化时
- **THEN** 系统应使用 WaitUtils 提供的显式等待方法
- **AND** 不再使用任何 `time.sleep()` 硬编码等待
- **AND** 支持配置化超时控制，适应不同环境需求

#### Scenario: 页面导航等待优化
- **WHEN** 执行页面跳转或导航操作时
- **THEN** 系统应等待 URL 变化或特定元素出现
- **AND** 使用 `wait_for_url_change()` 或 `wait_for_element_visible()` 方法
- **AND** 在等待超时时提供明确的错误信息

#### Scenario: 跨平台兼容性保证
- **WHEN** 在不同操作系统（Windows, Linux, macOS）上运行时
- **THEN** 时序控制行为应保持一致
- **AND** 不依赖平台特定的等待机制
- **AND** 支持环境变量配置超时参数

### Requirement: 职责边界明确化
OzonScraper SHALL 专注于基础商品信息抓取，移除跟卖检测相关逻辑，遵循单一职责原则。

#### Scenario: 跟卖逻辑完全分离
- **WHEN** 执行商品信息抓取时
- **THEN** OzonScraper 只负责商品基础信息的获取
- **AND** 不再包含跟卖区域检测逻辑
- **AND** 不再包含跟卖价格比较逻辑
- **AND** 跟卖相关功能由独立的 CompetitorDetectionService 处理

#### Scenario: 清晰的接口定义
- **WHEN** 调用 OzonScraper 的抓取方法时
- **THEN** 方法签名应明确表示其职责范围
- **AND** 返回的数据结构不包含跟卖检测结果
- **AND** 提供标准的 ScrapingResult 格式返回值

#### Scenario: 服务协调通过外部编排
- **WHEN** 需要同时进行商品抓取和跟卖检测时
- **THEN** 通过 ScrapingOrchestrator 协调多个服务
- **AND** OzonScraper 与 CompetitorDetectionService 通过依赖注入协作
- **AND** 保持各服务间的松耦合关系

### Requirement: 代码复用统一化
OzonScraper SHALL 使用统一的抓取工具类，消除与其他抓取器的重复逻辑，提高代码一致性。

#### Scenario: 价格提取逻辑统一
- **WHEN** 需要从页面元素中提取价格信息时
- **THEN** 使用 ScrapingUtils.extract_price() 统一方法
- **AND** 不再维护独立的价格提取逻辑
- **AND** 确保与其他抓取器的价格提取行为一致

#### Scenario: 数据验证逻辑统一
- **WHEN** 需要验证抓取到的数据有效性时
- **THEN** 使用 ScrapingUtils 提供的验证方法
- **AND** 应用统一的数据清理和格式化规则
- **AND** 错误处理策略与其他抓取器保持一致

#### Scenario: 文本处理逻辑复用
- **WHEN** 需要清理或格式化抓取的文本内容时
- **THEN** 使用 ScrapingUtils.clean_text() 方法
- **AND** 确保文本处理规则的一致性
- **AND** 支持多语言文本的标准化处理

### Requirement: 接口标准化兼容
OzonScraper SHALL 提供标准化的接口，同时保持向后兼容性，支持渐进式迁移。

#### Scenario: 方法签名标准化
- **WHEN** 调用 scrape() 等核心方法时
- **THEN** 方法签名应遵循项目统一规范
- **AND** 参数类型注解完整且正确
- **AND** 返回值使用标准的 ScrapingResult 格式

#### Scenario: 向后兼容性保证
- **WHEN** 现有代码调用重构后的 OzonScraper 时
- **THEN** 所有现有的公共接口应保持可用
- **AND** 现有的调用方式不需要修改即可正常工作
- **AND** 新增的功能通过可选参数提供

#### Scenario: 错误处理标准化
- **WHEN** 抓取过程中发生错误时
- **THEN** 应返回标准化的错误信息
- **AND** 错误码和错误消息格式统一
- **AND** 支持降级处理，部分失败不影响其他功能

### Requirement: 配置管理优化
OzonScraper SHALL 使用重构后的配置管理系统，支持配置继承和优先级控制。

#### Scenario: 选择器配置继承
- **WHEN** 加载页面选择器配置时
- **THEN** 应使用基于继承的配置体系
- **AND** 避免重复定义相同的选择器
- **AND** 支持特定场景的选择器覆盖

#### Scenario: 环境配置适应
- **WHEN** 在不同环境中运行时
- **THEN** 应支持环境特定的配置覆盖
- **AND** 配置加载失败时有明确的错误提示
- **AND** 支持运行时配置更新

