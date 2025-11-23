# utils-layer Specification

## Purpose
TBD - created by archiving change refactor-competitor-logic-architecture. Update Purpose after archive.
## Requirements
### Requirement: Utils Layer Separation Strategy
系统 SHALL 建立清晰的工具类分层策略，避免全局工具与 Scraper 专用工具的命名冲突和功能重叠。

#### Scenario: Global vs Scraper Utils Separation
- **WHEN** 工具类分层策略实施后
- **THEN** 全局工具必须位于 `utils/` 目录，Scraper专用工具必须位于 `common/utils/` 目录
- **AND** 全局工具必须是无状态的纯函数式工具
- **AND** Scraper工具可以包含与抓取业务相关的状态

#### Scenario: Naming Conflict Prevention
- **WHEN** 新增 Scraper 工具类时
- **THEN** 系统必须自动检测与全局工具的命名冲突
- **AND** 发生冲突时必须提供明确的警告信息
- **AND** 必须提供冲突解决的具体建议

### Requirement: Scraper Utils Directory Creation
系统 SHALL 创建 `common/utils/` 目录，专门用于存放 Scraper 相关的工具类。

#### Scenario: Directory Structure Creation
- **WHEN** 执行工具类重构任务
- **THEN** 必须在 `common/` 目录下创建 `utils/` 子目录
- **AND** 目录必须包含 `__init__.py` 模块初始化文件
- **AND** 建立清晰的工具类导出接口

#### Scenario: Namespace Isolation Setup
- **WHEN** Scraper工具目录创建完成
- **THEN** `common/utils/__init__.py` 必须建立命名空间隔离
- **AND** 支持 `from common.utils import WaitUtils` 导入方式
- **AND** 与全局 `utils/` 包完全隔离，避免命名冲突

### Requirement: Core Utils Classes Implementation
系统 SHALL 实现三个核心的 Scraper 工具类：WaitUtils、ScrapingUtils 和 SelectorUtils。

#### Scenario: WaitUtils Implementation
- **WHEN** 实现时序控制工具类
- **THEN** WaitUtils 必须提供显式等待元素出现的功能
- **AND** 必须支持等待页面加载完成的功能
- **AND** 必须支持自定义超时时间设置
- **AND** 失败时不能影响主流程继续执行

#### Scenario: ScrapingUtils Implementation
- **WHEN** 实现数据抓取工具类
- **THEN** ScrapingUtils 必须提供安全的文本提取功能
- **AND** 必须支持价格字符串解析功能
- **AND** 必须支持从文本中提取数字功能
- **AND** 异常情况下必须返回合理的默认值

#### Scenario: SelectorUtils Implementation
- **WHEN** 实现选择器工具类
- **THEN** SelectorUtils 必须提供 CSS 选择器构建功能
- **AND** 必须支持选择器有效性验证
- **AND** 必须支持多个选择器组合功能
- **AND** 不依赖外部 CSS 选择器库

### Requirement: Cross-Platform Compatibility
系统 SHALL 确保所有工具类在 Windows、Linux、macOS 平台上都能正常工作。

#### Scenario: Path Handling Compatibility
- **WHEN** 在不同操作系统上使用工具类
- **THEN** 路径处理必须在所有平台上正确工作
- **AND** 不能出现平台特定的路径分隔符问题
- **AND** 文件操作必须遵循跨平台最佳实践

#### Scenario: Performance Consistency
- **WHEN** 在不同平台上运行工具类
- **THEN** 性能差异必须控制在 10% 以内
- **AND** 不能出现平台特定的性能瓶颈
- **AND** 内存使用必须保持一致

### Requirement: Legacy Code Migration Support
系统 SHALL 支持现有代码平滑迁移到新的工具类体系。

#### Scenario: Gradual Migration Strategy
- **WHEN** 迁移现有代码到新工具类
- **THEN** 必须支持渐进式迁移，避免一次性大规模修改
- **AND** 旧的临时实现必须能够逐步被新工具类替换
- **AND** 迁移过程中不能影响现有功能正常运行

#### Scenario: Migration Documentation
- **WHEN** 提供代码迁移指导
- **THEN** 必须提供详细的迁移示例和对比
- **AND** 必须说明新旧实现的差异和优势
- **AND** 必须提供自动化迁移脚本或工具建议

