# 集成选品流程协调器 (integrate-product-selection-orchestration)

## Why

当前系统中各个抓取组件分散独立，缺乏统一的商品分析流程。GoodStoreSelector中存在重复的商品信息获取逻辑，无法充分利用现有的FilterManager和ProfitEvaluator功能，导致代码冗余和维护困难。

## 概述

基于之前成功实现的跟卖商品ID提取功能（competitor-scraper规范），现在需要将整个选品流程进行串联，通过ScrapingOrchestrator统一协调所有抓取器，实现完整的商品分析和选择流程。

## 问题陈述

当前系统存在以下问题：
1. **流程分散**：商品信息抓取、跟卖分析、价格比较分布在不同模块中
2. **重复实现**：GoodStoreSelector中存在独立的商品信息获取逻辑，与抓取器功能重复
3. **缺乏统一协调**：没有统一的入口管理完整的商品分析流程
4. **数据处理割裂**：原商品和跟卖商品数据处理逻辑分散，难以维护

## 解决方案

通过极简化ScrapingOrchestrator并增强OzonScraper，实现完整的商品分析能力：

### 核心功能
1. **OzonScraper增强**：集成FilterManager和ProfitEvaluator，内部处理所有跟卖分析逻辑
2. **协调器极简化**：仅保留降级处理能力，代码量减少80%
3. **统一数据格式**：返回标准化的分析结果，包含原商品、跟卖商品和最终选择
4. **GoodStoreSelector集成**：使用极简协调器进行商品处理

### 技术方案
- 极简化ScrapingOrchestrator，仅保留降级处理（20-30行代码）
- 增强OzonScraper集成FilterManager、ProfitEvaluator和CompetitorScraper
- 使用include_competitor参数替代extract_first_product提升语义清晰度
- 所有业务逻辑下沉到OzonScraper内部，协调器不包含业务判断

## 预期收益

1. **架构极简**：协调器代码量减少80%，维护成本大幅降低
2. **逻辑内聚**：所有业务逻辑集中在OzonScraper，职责清晰
3. **代码复用**：充分复用FilterManager和ProfitEvaluator现有功能
4. **流程完整**：提供端到端的商品分析能力
5. **性能优化**：减少不必要的中间调用和数据传递

## 影响范围

- **核心模块**：ScrapingOrchestrator扩展
- **业务模块**：GoodStoreSelector重构
- **抓取模块**：OzonScraper参数优化
- **测试覆盖**：端到端流程验证

## 风险评估

- **低风险**：基于现有稳定的抓取器实现
- **向后兼容**：不破坏现有接口和功能
- **渐进式**：可以逐步迁移和验证

## 成功标准

1. 完整的5步商品分析流程正常运行
2. GoodStoreSelector成功使用协调器处理商品
3. 所有现有测试通过，新增端到端测试覆盖
4. 性能保持在可接受范围内