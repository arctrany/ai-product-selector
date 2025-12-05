# 设计文档：商品输出功能

## Context
当前系统的 `select-shops` 模式专注于店铺筛选，输出为标记好店的店铺Excel。用户反馈需要 `select-goods` 模式，直接从已知优质店铺中选品，输出为商品清单Excel。

**约束条件**:
- 必须复用现有的商品抓取、利润计算流程（90%代码复用）
- 必须保持 select-shops 模式的向后兼容性
- 商品Excel格式需与业务系统对接，字段标准化

**利益相关方**:
- 用户：需要快速获得可上架的商品清单
- 开发团队：需要最小化代码改动，保持架构清晰

## Goals / Non-Goals

### Goals
- ✅ 实现 select-goods 模式的商品输出功能
- ✅ 复用现有商品抓取和利润计算逻辑（无需重复开发）
- ✅ 提供标准化的商品Excel格式（便于后续处理）
- ✅ 保持 select-shops 模式完全不受影响

### Non-Goals
- ❌ 不修改商品抓取和利润计算的核心逻辑
- ❌ 不输出跟卖店铺列表（仅保存在内存中用于分析）
- ❌ 不支持商品去重和合并（由后续流程处理）
- ❌ 不实现商品Excel的高级格式化（如颜色、图表）

## Decisions

### Decision 1: 商品输出模块位置
**选择**: 在 `common/excel_processor.py` 中新增 `ExcelProductWriter` 类

**理由**:
- 与现有的 `ExcelStoreProcessor` 保持一致的模块组织
- 复用 openpyxl 的依赖和工具函数
- 避免创建新的模块文件，保持代码集中

**替代方案**:
- ❌ 创建独立的 `common/excel_product_writer.py` - 增加文件数量，不必要
- ❌ 放在 `business/` 目录 - Excel处理属于数据层，不是业务逻辑层

### Decision 2: 商品筛选逻辑位置
**选择**: 在 `GoodStoreSelector._evaluate_products()` 中就已经完成了利润计算和筛选，`StoreAnalysisResult.products` 中只包含利润率达标的商品

**理由**:
- 避免重复筛选，保持代码简洁
- 利用现有的 `ProfitEvaluator` 筛选机制
- 店铺评估和商品输出使用同一份筛选后的数据

### Decision 3: 输出逻辑分支位置  
**选择**: 在 `GoodStoreSelector._update_excel_results()` 方法中添加模式判断

**实现伪码**:
```python
def _update_excel_results(self, pending_stores, store_results):
    # 两种模式都需要更新店铺Excel状态
    updates = [(store_data, result.store_info.is_good_store, result.store_info.status) 
               for store_data, result in zip(pending_stores, store_results)]
    self.excel_processor.batch_update_stores(updates)
    
    if self.config.selection_mode == 'select-goods':
        # 收集所有利润达标的商品（已经在 _evaluate_products 中筛选过）
        all_products = []
        for i, (store_data, result) in enumerate(zip(pending_stores, store_results)):
            # 为每个商品添加 store_id
            for product in result.products:
                product.store_id = store_data.store_id
                all_products.append(product)
        
        # 写入商品Excel (每10条写一次)
        self.product_writer.batch_write_products(all_products)
    
    self.excel_processor.save_changes()
```

### Decision 4: 商品Excel字段映射
**选择**: 使用以下标准字段（与商品模板一致）

| Excel列 | 数据源 | 说明 |
|---------|--------|------|
| A: 店铺ID | `product.store_id` | 来源店铺 |
| B: 商品ID | `product.product_id` | OZON商品ID |
| C: 商品名称 | `product.product_name` | 商品标题 |
| D: 商品图片 | `product.image_url` | 主图URL |
| E: 绿标价格 | `product.green_price` | 促销价（卢布） |
| F: 黑标价格 | `product.black_price` | 原价（卢布） |
| G: 佣金率 | `product.commission_rate` | 平台佣金 |
| H: 重量(g) | `product.weight` | 商品重量 |
| I: 长(cm) | `product.length` | 包装长度 |
| J: 宽(cm) | `product.width` | 包装宽度 |
| K: 高(cm) | `product.height` | 包装高度 |
| L: 货源价格 | `product.source_price` | 1688采购价（人民币） |
| M: 利润率 | `price_calculation.profit_rate` | 计算利润率 |
| N: 预计利润 | `price_calculation.profit_amount` | 单件利润（人民币） |

**理由**:
- 包含所有利润计算所需的关键数据
- 便于后续批量上架和价格调整
- 与业务系统的商品导入格式对齐

### Decision 5: 跟卖处理策略  
**选择**: `select-goods` 模式下不执行跟卖数据抓取

**理由**:
- 减少不必要的数据抓取，提高效率
- select-goods 模式专注于商品选择，不关注店铺裂变
- 通过配置或模式判断跳过跟卖逻辑

**实现方式**:
- 在 `_process_single_store()` 中添加模式判断
- `select-goods` 模式时跳过 `_collect_competitor_stores()` 调用

## Risks / Trade-offs

### Risk 1: 商品数据量过大导致Excel文件过大
**影响**: 单个Excel文件可能包含数千个商品（50店铺 × 50商品 = 2500行）

**缓解措施**:
- 使用 openpyxl 的优化写入模式（`write_only=True`）
- 分批写入，避免内存溢出
- 提供配置选项限制单文件商品数量

### Risk 2: 商品字段变更导致Excel格式不兼容
**影响**: 如果 `ProductInfo` 模型字段变更，可能导致写入失败

**缓解措施**:
- 使用字段映射配置（`ExcelConfig.product_columns`）
- 添加字段验证和默认值处理
- 单个商品写入失败记录到错误日志，不影响整批

### Trade-off: ProductInfo 添加 store_id 字段
**优点**: 保持数据完整性，方便追溯商品来源
**缺点**: 需要修改现有数据模型

**决策**: 在 `_evaluate_products()` 中为每个商品添加 store_id，或在输出时动态添加

## Migration Plan

### Phase 1: 实现核心功能（本次变更）
1. 新增 `ExcelProductWriter` 类
2. 修改 `_process_single_store()` 跳过跟卖逻辑
3. 修改 `_evaluate_products()` 添加 store_id
4. 修改 `_update_excel_results()` 添加分支逻辑
5. 修改 CLI 参数验证

### Phase 2: 测试和验证
1. 单元测试覆盖商品写入逻辑
2. 集成测试验证 select-goods 模式端到端流程
3. 性能测试验证大数据量写入性能

### Phase 3: 文档和发布
1. 更新用户文档和配置模板
2. 创建商品Excel模板示例
3. 发布版本说明

### Rollback Plan
如果出现问题，可以：
1. 通过配置禁用 select-goods 模式
2. 回滚代码到上一版本（仅影响新功能）
3. select-shops 模式完全不受影响

## Open Questions

### Q1: 商品Excel是否需要支持多sheet？
**当前决策**: 单sheet，所有商品写入同一表格
**待讨论**: 如果商品数量超过10000，是否需要分sheet或分文件？

### Q2: 是否需要支持商品去重？
**当前决策**: 不去重，保留所有抓取的商品
**未来考虑**: 同一商品在不同店铺出现时，可能需要标记或合并

### Q3: 批量写入优化？  
**当前决策**: 每10条商品写入一次
**原因**: 平衡内存使用和写入效率
