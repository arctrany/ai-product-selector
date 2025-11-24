## MODIFIED Requirements

### Requirement: 选品业务逻辑协调
GoodStoreSelector SHALL严格通过ScrapingOrchestrator调用所有scraper功能，不允许直接访问任何scraper实例。

#### Scenario: 通过协调器抓取价格
- **WHEN** 需要抓取商品价格信息时
- **THEN** GoodStoreSelector SHALL调用ScrapingOrchestrator.scrape_with_orchestration
- **AND** 使用ScrapingMode.PRODUCT_INFO模式
- **AND** 不允许直接调用OzonScraper

#### Scenario: 通过协调器抓取店铺数据
- **WHEN** 需要获取店铺销售数据时
- **THEN** GoodStoreSelector SHALL调用ScrapingOrchestrator.scrape_with_orchestration
- **AND** 使用ScrapingMode.STORE_ANALYSIS模式
- **AND** 不允许直接调用SeerfarScraper

#### Scenario: 通过协调器检测跟卖
- **WHEN** 需要检测跟卖信息时
- **THEN** GoodStoreSelector SHALL调用ScrapingOrchestrator.scrape_with_orchestration
- **AND** 使用ScrapingMode.COMPETITOR_DETECTION模式
- **AND** 不允许直接调用CompetitorScraper

#### Scenario: 架构合规性验证
- **WHEN** 系统启动时
- **THEN** SHALL验证GoodStoreSelector没有直接引用任何scraper类
- **AND** 所有scraping操作SHALL通过ScrapingOrchestrator进行

### Requirement: 任务控制集成
GoodStoreSelector SHALL完全集成TaskManager的任务控制机制，支持实时的暂停、恢复和停止操作。

#### Scenario: 任务控制点检查
- **WHEN** 在每个关键业务步骤开始前
- **THEN** GoodStoreSelector SHALL检查任务控制点
- **AND** 根据任务状态决定继续、暂停或停止

#### Scenario: 进度实时报告
- **WHEN** 处理店铺或商品时
- **THEN** SHALL通过TaskExecutionContext报告当前进度
- **AND** 进度信息SHALL包括当前处理项、总数、完成百分比

#### Scenario: 任务异常处理
- **WHEN** 任务执行过程中出现异常时
- **THEN** SHALL通过TaskExecutionContext报告异常信息
- **AND** 任务状态SHALL正确更新为FAILED

## REMOVED Requirements

### Requirement: 直接Scraper实例化
**Reason**: 移除GoodStoreSelector中直接创建scraper实例的功能
**Migration**: 所有scraper调用改为通过ScrapingOrchestrator

### Requirement: 独立错误处理
**Reason**: 利用ScrapingOrchestrator的统一错误处理机制
**Migration**: 移除GoodStoreSelector中的重复错误处理代码
