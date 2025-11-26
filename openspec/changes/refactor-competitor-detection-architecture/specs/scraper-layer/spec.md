# scraper-layer Specification Delta

## MODIFIED Requirements
### Requirement: CompetitorScraper职责明确化
CompetitorScraper SHALL 专注于跟卖店铺的页面交互和数据抓取，不包含检测逻辑。

#### Scenario: 跟卖店铺信息抓取
- **WHEN** 需要抓取跟卖店铺详细信息时
- **THEN** CompetitorScraper 应负责页面交互和数据提取
- **AND** 不包含跟卖区域检测逻辑
- **AND** 不包含价格比较分析逻辑

#### Scenario: 页面交互标准化
- **WHEN** 与跟卖相关的页面元素交互时
- **THEN** CompetitorScraper 应使用标准的浏览器交互方法
- **AND** 集成统一的时序控制机制
- **AND** 提供清晰的交互状态反馈

### Requirement: Scraper组件任务控制集成
所有Scraper组件SHALL支持通过TaskControlMixin无侵入地集成任务控制能力。

#### Scenario: CompetitorScraper控制点集成
- **WHEN** CompetitorScraper在跟卖店铺信息抓取中调用_check_task_control("处理跟卖店铺_{i+1}")
- **THEN** 支持在任意跟卖店铺处理步骤暂停/恢复/停止
- **AND** 确保跟卖信息抓取的完整性

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

### Requirement: 接口标准化统一
CompetitorScraper SHALL 统一接口规范和返回格式。

#### Scenario: 方法签名统一
- **WHEN** 调用 CompetitorScraper 方法
- **THEN** 方法签名必须与其他 Scraper 保持一致
- **AND** 所有方法必须返回标准的 ScrapingResult 数据格式
- **AND** 必须实现统一的参数验证和类型检查

#### Scenario: 向后兼容性保证
- **WHEN** 现有代码调用重构后的 CompetitorScraper 时
- **THEN** 所有现有的公共接口应保持可用
- **AND** 现有的调用方式不需要修改即可正常工作
- **AND** 新增的功能通过可选参数提供
