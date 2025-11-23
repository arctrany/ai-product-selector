# seerfar-scraper Specification

## Purpose
TBD - created by archiving change add-seerfar-product-fields. Update Purpose after archive.
## Requirements
### Requirement: Extract Product Category
The system SHALL extract category information from Seerfar product list table rows.

#### Scenario: Category extraction success
- **WHEN** a product row contains category information in the third `<td>` element
- **THEN** the system extracts both Chinese and Russian category names
- **AND** stores them in `category_cn` and `category_ru` fields

#### Scenario: Category extraction failure
- **WHEN** category information is not available or cannot be parsed
- **THEN** the system returns `None` for both category fields
- **AND** logs a warning message

### Requirement: Extract Listing Date
The system SHALL extract listing date and shelf days from Seerfar product list table rows.

#### Scenario: Listing date extraction success
- **WHEN** a product row contains listing date in the last `<td>` element
- **THEN** the system extracts the date string (e.g., "2025-06-20")
- **AND** extracts the shelf duration (e.g., "4 个月")
- **AND** stores them in `listing_date` and `shelf_duration` fields

#### Scenario: Listing date extraction failure
- **WHEN** listing date information is not available or cannot be parsed
- **THEN** the system returns `None` for both date fields
- **AND** logs a warning message

### Requirement: Extract Sales Volume
The system SHALL extract sales volume from Seerfar product list table rows.

#### Scenario: Sales volume extraction success
- **WHEN** a product row contains sales volume in the fifth `<td>` element
- **THEN** the system extracts the numeric value
- **AND** stores it in `sales_volume` field as an integer

#### Scenario: Sales volume extraction failure
- **WHEN** sales volume information is not available or cannot be parsed
- **THEN** the system returns `None` for the sales volume field
- **AND** logs a warning message

### Requirement: No Default Values
The system SHALL NOT use hardcoded default values when data extraction fails.

#### Scenario: Failed extraction returns None
- **WHEN** any field extraction fails
- **THEN** the system returns `None` for that field
- **AND** does NOT substitute with default values like 0, "", or placeholder strings

### Requirement: Pre-filter Products Based on Extracted Fields
The system SHALL support pre-filtering products based on category, listing date, and sales volume before processing OZON detail pages.

#### Scenario: Filter function validates product eligibility
- **WHEN** a filter function is provided to `scrape_store_products()`
- **AND** basic fields (category, listing_date, sales_volume) are extracted
- **THEN** the system applies the filter function to the product data
- **AND** skips OZON detail page processing if filter returns `False`
- **AND** logs the reason for skipping

#### Scenario: Category blacklist filtering
- **WHEN** filter function checks category against a blacklist
- **AND** product category matches any blacklist keyword
- **THEN** the filter returns `False`
- **AND** the product is skipped

#### Scenario: Listing date threshold filtering
- **WHEN** filter function checks listing date
- **AND** product shelf duration exceeds the threshold
- **THEN** the filter returns `False`
- **AND** the product is skipped

#### Scenario: Sales volume filtering
- **WHEN** filter function checks sales volume
- **AND** sales volume is `None` or 0
- **THEN** the filter returns `False`
- **AND** the product is skipped

#### Scenario: Combined filter conditions
- **WHEN** filter function applies multiple conditions
- **THEN** product must satisfy ALL conditions to pass
- **AND** failing any condition results in skipping the product

### Requirement: Extract Product Weight
The system SHALL extract product weight from Seerfar product list table rows.

#### Scenario: Weight extraction success
- **WHEN** a product row contains weight in the second-to-last `<td>` element
- **THEN** the system extracts the numeric value and unit (e.g., "161 g")
- **AND** stores it in `weight` field as a float (in grams)

#### Scenario: Weight extraction failure
- **WHEN** weight information is not available or cannot be parsed
- **THEN** the system returns `None` for the weight field
- **AND** logs a warning message

### Requirement: Implement Filter Function with User Data
The system SHALL provide a filter function that validates products against user-defined criteria from `--data` parameter.

#### Scenario: Filter based on category blacklist
- **WHEN** user provides category blacklist keywords
- **AND** product category contains any blacklist keyword
- **THEN** the filter returns `False`

#### Scenario: Filter based on listing date threshold
- **WHEN** user provides `item_shelf_days` threshold
- **AND** product shelf duration exceeds the threshold
- **THEN** the filter returns `False`

#### Scenario: Filter based on sales volume range
- **WHEN** user provides `max_monthly_sold` and `monthly_sold_min` range
- **AND** product sales volume is outside the range
- **THEN** the filter returns `False`

#### Scenario: Filter based on weight range
- **WHEN** user provides `item_min_weight` and `item_max_weight` range
- **AND** product weight is outside the range
- **THEN** the filter returns `False`

#### Scenario: All filter conditions must pass
- **WHEN** multiple filter conditions are defined
- **THEN** product must satisfy ALL conditions
- **AND** failing any single condition results in filtering out the product

### Requirement: 时序控制标准化
SeerfarScraper SHALL 集成统一时序控制机制。

#### Scenario: 硬编码等待移除
- **WHEN** 重构 SeerfarScraper 时序控制
- **THEN** 必须移除所有硬编码的 `time.sleep()` 调用
- **AND** 必须集成 `WaitUtils` 工具类，使用显式等待
- **AND** 必须实现配置化的超时控制
- **AND** 时序控制成功率必须 ≥ 95%

#### Scenario: 跨平台时序兼容
- **WHEN** 在不同平台上运行
- **THEN** 时序控制必须在 Windows、Linux、macOS 上保持一致
- **AND** 必须与 OzonScraper、CompetitorScraper 的时序控制一致

### Requirement: 配置管理统一化
SeerfarScraper SHALL 将配置管理纳入统一架构。

#### Scenario: 配置继承实现
- **WHEN** 重构配置管理
- **THEN** `seerfar_selectors_config.py` 必须继承 `BaseScrapingConfig` 基类
- **AND** 配置格式必须与 OzonSelectors、CompetitorSelectors 保持一致
- **AND** 必须建立配置优先级管理
- **AND** 配置加载性能必须提升 20%+

#### Scenario: 配置热加载支持
- **WHEN** 配置修改时
- **THEN** 必须支持配置热加载
- **AND** 配置修改无需重启应用

### Requirement: 代码复用统一化
SeerfarScraper SHALL 消除与其他 Scraper 的重复逻辑。

#### Scenario: 工具类统一使用
- **WHEN** 重构数据提取逻辑
- **THEN** 必须使用 `ScrapingUtils` 工具类替代重复逻辑
- **AND** 必须统一价格提取、文本清理、数据验证等公共功能
- **AND** 代码重复率必须 < 5%
- **AND** 代码行数必须减少 30%+

#### Scenario: 错误处理统一
- **WHEN** 处理错误时
- **THEN** 必须使用统一的异常类型和处理策略
- **AND** 必须采用统一的日志格式和级别

### Requirement: 接口标准化统一
SeerfarScraper SHALL 统一接口规范和返回格式。

#### Scenario: 方法签名统一
- **WHEN** 调用 SeerfarScraper 方法
- **THEN** 方法签名必须与 OzonScraper、CompetitorScraper 保持一致
- **AND** 所有方法必须返回标准的 `ScrapingResult` 数据格式
- **AND** 必须实现统一的参数验证和类型检查
- **AND** 向后兼容性必须 100% 保持

### Requirement: 测试覆盖补齐
SeerfarScraper SHALL 将测试覆盖率从 0% 提升到 95%+。

#### Scenario: 单元测试创建
- **WHEN** 创建测试套件
- **THEN** 必须创建 `tests/test_seerfar_scraper.py` 完整测试套件
- **AND** 必须为所有核心方法编写单元测试
- **AND** 单元测试覆盖率必须 ≥ 95%
- **AND** 测试执行时间必须 < 30 秒

#### Scenario: 错误场景测试
- **WHEN** 测试错误处理
- **THEN** 必须覆盖错误场景、边界条件、异常处理
- **AND** 必须使用统一的 `BaseScraperTest` 测试基类

### Requirement: 集成测试协同验证
SeerfarScraper SHALL 验证与其他 Scraper 的协同工作。

#### Scenario: 多 Scraper 调用链测试
- **WHEN** 执行集成测试
- **THEN** 必须实现 SeerfarScraper → OzonScraper → CompetitorScraper 调用链测试
- **AND** 调用链测试成功率必须 ≥ 95%
- **AND** 端到端流程测试覆盖率必须 ≥ 90%

#### Scenario: 并发执行验证
- **WHEN** 并发执行多个 Scraper
- **THEN** 必须验证并发执行的稳定性和数据一致性
- **AND** 不能出现数据竞争和资源冲突
- **AND** 响应时间必须提升 20%+

