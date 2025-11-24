# scraper-layer Specification

## Purpose
TBD - created by archiving change create-independent-task-manager. Update Purpose after archive.
## Requirements
### Requirement: Scraper组件任务控制集成
所有Scraper组件SHALL支持通过TaskControlMixin无侵入地集成任务控制能力，包括SeerfarScraper、OzonScraper、CompetitorScraper、ErpPluginScraper等组件。

#### Scenario: SeerfarScraper控制点集成
- **WHEN** SeerfarScraper继承TaskControlMixin并在商品列表处理循环中调用_check_task_control("处理商品_{i+1}")
- **THEN** 支持在任意商品处理步骤暂停/恢复/停止
- **AND** 不影响现有商品提取逻辑和性能

#### Scenario: OzonScraper控制点集成
- **WHEN** OzonScraper在价格抓取等耗时操作中调用_check_task_control("提取价格_{price_type}")
- **THEN** 支持在任意价格提取步骤暂停/恢复/停止
- **AND** 保持价格提取结果的准确性

#### Scenario: CompetitorScraper控制点集成
- **WHEN** CompetitorScraper在跟卖店铺信息抓取中调用_check_task_control("处理跟卖店铺_{i+1}")
- **THEN** 支持在任意跟卖店铺处理步骤暂停/恢复/停止
- **AND** 确保跟卖信息抓取的完整性

#### Scenario: ErpPluginScraper控制点集成
- **WHEN** ErpPluginScraper在ERP数据抓取中调用_check_task_control("提取ERP字段_{field_key}")
- **THEN** 支持在任意ERP字段提取步骤暂停/恢复/停止
- **AND** 保证ERP数据提取的一致性

### Requirement: Scraper进度回传机制
Scraper组件SHALL提供统一的进度报告机制，支持实时回传处理进度、状态信息和性能数据。

#### Scenario: 商品处理进度回传
- **WHEN** SeerfarScraper处理商品列表时调用_report_task_progress()
- **THEN** 回传当前商品数、总商品数、处理百分比、预估剩余时间
- **AND** 进度信息格式与其他组件保持一致

#### Scenario: 价格抓取进度回传
- **WHEN** OzonScraper进行价格抓取时调用_report_task_progress()
- **THEN** 回传价格类型、提取状态、当前进度
- **AND** 支持多种价格选择器的进度跟踪

#### Scenario: 批量操作进度回传
- **WHEN** CompetitorScraper处理多个跟卖店铺时调用_report_task_progress()
- **THEN** 回传已处理店铺数、成功提取数、失败数量、当前处理速度
- **AND** 提供详细的批量操作统计信息

### Requirement: 无侵入控制点检查
Scraper组件的控制点检查SHALL不影响现有业务逻辑，采用无侵入方式集成，确保向后兼容性。

#### Scenario: 控制点检查性能影响
- **WHEN** Scraper组件调用_check_task_control()进行控制点检查
- **THEN** 控制点检查耗时不超过1毫秒
- **AND** 对整体Scraper性能影响不超过5%

#### Scenario: 异常情况下的控制点处理
- **WHEN** Scraper组件在控制点检查时发生异常
- **THEN** 异常被捕获并记录到日志
- **AND** Scraper继续正常执行，不影响数据抓取流程

#### Scenario: 多线程环境下的控制点行为
- **WHEN** 多个Scraper实例在不同线程中同时进行控制点检查
- **THEN** 控制点检查线程安全，状态同步正确
- **AND** 不出现竞态条件或状态不一致问题

