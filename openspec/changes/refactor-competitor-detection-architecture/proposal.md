# Change: 重构竞争对手检测架构以消除冗余并优化职责划分

## Why
当前架构中存在CompetitorDetectionService和CompetitorScraper两个组件之间的功能冗余，违反了单一职责原则和DRY原则。这种设计导致了代码重复、维护困难和架构混乱，需要通过重构来优化职责划分，提高代码质量和可维护性。

通过对代码库的分析，我们发现以下问题：
1. **功能冗余**：CompetitorDetectionService和CompetitorScraper都实现了跟卖检测相关的功能
2. **职责不清**：两个组件的职责边界模糊，存在交叉重叠
3. **依赖混乱**：ScrapingOrchestrator协调器需要同时管理两个相似的组件
4. **接口不一致**：两个组件的接口规范和数据模型存在差异

## What Changes
- 重新设计竞争对手检测架构，明确各组件职责边界
- 消除CompetitorDetectionService和CompetitorScraper之间的功能冗余
- 优化依赖关系，确保符合分层架构原则
- 统一数据模型和接口规范
- 简化ScrapingOrchestrator协调器的复杂度

## Impact
- Affected specs: competitor-detection, scraper-layer, ozon-scraper
- Affected code: 
  - common/services/competitor_detection_service.py
  - common/scrapers/competitor_scraper.py
  - common/services/scraping_orchestrator.py
  - 相关的测试文件和配置文件

## Solution Design
### 重构后的架构设计
重构后的架构将采用清晰的分层设计：
1. **CompetitorDetectionService**：专注于跟卖检测的核心逻辑，包括页面元素识别、数量检测和基础价格比较
2. **CompetitorScraper**：专注于跟卖店铺的页面交互和数据抓取，不包含检测逻辑
3. **ScrapingOrchestrator**：协调两个组件的工作，简化依赖关系

### 职责重新划分方案
- **CompetitorDetectionService**：
  - 负责检测页面中是否存在跟卖商品
  - 提供跟卖数量和基础价格信息
  - 返回标准化的检测结果
  
- **CompetitorScraper**：
  - 负责与跟卖相关的页面元素交互
  - 抓取跟卖店铺的详细信息
  - 提供标准化的抓取结果

### 依赖关系优化策略
- 采用依赖注入模式，减少组件间的紧耦合
- 通过ScrapingOrchestrator统一管理组件依赖
- 使用标准接口和数据模型，确保组件间通信的一致性

## Implementation Plan
### 具体的重构步骤
1. 分析现有代码，识别功能重叠点
2. 重新设计接口和数据模型
3. 重构CompetitorDetectionService，移除与抓取相关的功能
4. 重构CompetitorScraper，移除与检测相关的功能
5. 更新ScrapingOrchestrator中的协调逻辑
6. 编写单元测试和集成测试
7. 更新相关文档

### 需要修改的文件列表
- common/services/competitor_detection_service.py
- common/scrapers/competitor_scraper.py
- common/services/scraping_orchestrator.py
- 相关的测试文件
- 配置文件和文档

### 风险评估和缓解措施
- **功能回归风险**：通过全面的测试覆盖来降低风险
- **性能影响风险**：通过性能测试确保重构后性能不下降
- **兼容性风险**：保持向后兼容的接口设计

## Acceptance Criteria
### 重构完成的验收条件
- 所有功能点按新的职责划分正确实现
- 通过所有单元测试和集成测试
- 代码审查通过
- 性能指标符合预期

### 性能和功能验证要求
- 跟卖检测准确率≥95%
- 页面抓取成功率≥95%
- 响应时间与重构前相比变化不超过±10%
- 内存使用量不超过重构前的110%
