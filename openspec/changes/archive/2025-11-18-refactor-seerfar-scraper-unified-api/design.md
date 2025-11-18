# Design: Seerfar Scraper 统一抓取接口重构

## Context
当前系统中，`good_store_selector.py` 需要分别调用 `seerfar_scraper` 的两个方法来获取店铺的完整信息：
1. `scrape_store_sales_data(store_id)` - 获取销售数据
2. `scrape_store_products(store_id, max_products, product_filter_func)` - 获取商品列表

这种设计导致业务层需要了解 scraper 的内部实现细节，违反了单一职责原则和依赖倒置原则。

## Goals / Non-Goals

### Goals
- 提供统一的 `scrape()` 接口，一次调用完成所有抓取
- 支持过滤函数的依赖注入，解耦业务逻辑
- 简化业务层代码，提高可维护性
- 保持向后兼容，不破坏现有的 `scrape_store_products()` 接口

### Non-Goals
- 不修改 `scrape_store_products()` 的现有实现（保持向后兼容）
- 不改变数据抓取的核心逻辑
- 不引入新的外部依赖

## Decisions

### Decision 1: 增强 `scrape()` 方法而非创建新方法
**选择**: 增强现有的 `scrape()` 方法，添加可选参数

**理由**:
- `scrape()` 方法已经存在，是自然的统一接口
- 通过可选参数保持向后兼容
- 符合 OpenSpec 的 MODIFIED 语义

**替代方案**:
- 创建新方法 `scrape_with_filters()` - 被拒绝，因为会增加接口复杂度
- 使用配置对象传递参数 - 被拒绝，因为过度设计

### Decision 2: 支持店铺级别的过滤
**选择**: 添加 `store_filter_func` 参数，支持在抓取商品前过滤店铺

**理由**:
- 性能优化：店铺不符合条件时，可以跳过商品抓取
- 灵活性：业务层可以根据销售数据决定是否继续
- 一致性：与 `product_filter_func` 的设计保持一致

**实现细节**:
```python
def scrape(
    self, 
    store_id: str, 
    include_products: bool = True,
    max_products: Optional[int] = None,
    product_filter_func: Optional[Callable] = None,
    store_filter_func: Optional[Callable] = None,
    **kwargs
) -> ScrapingResult:
    # 1. 抓取销售数据
    sales_result = self.scrape_store_sales_data(store_id)
    
    # 2. 应用店铺过滤（如果提供）
    if store_filter_func and not store_filter_func(sales_result.data):
        return ScrapingResult(
            success=False,
            data={'store_id': store_id, 'sales_data': sales_result.data},
            error_message="店铺未通过过滤条件"
        )
    
    # 3. 抓取商品（如果需要）
    if include_products:
        products_result = self.scrape_store_products(
            store_id,
            max_products=max_products or self.config.store_filter.max_products_to_check,
            product_filter_func=product_filter_func
        )
        # ... 组合结果
```

### Decision 3: 删除 `scrape_store_products()` 方法
**选择**: 删除 `scrape_store_products()` 方法，将其功能完全整合到 `scrape()` 中

**理由**:
- 避免冗余：两个方法功能重叠，维护成本高
- 统一接口：只保留一个抓取入口，降低使用复杂度
- 强制最佳实践：确保所有调用方使用统一的、功能完整的接口

**权衡**:
- ⚠️ **BREAKING CHANGE**: 现有直接调用 `scrape_store_products()` 的代码需要迁移
- ✅ 简化维护：只需维护一个方法
- ✅ 更清晰的API：避免用户困惑应该使用哪个方法

**迁移路径**:
```python
# 修改前
result = scraper.scrape_store_products(
    store_id, 
    max_products=10,
    product_filter_func=filter_func
)

# 修改后
result = scraper.scrape(
    store_id,
    include_products=True,
    max_products=10,
    product_filter_func=filter_func
)
```

## Risks / Trade-offs

### Risk 1: 参数过多导致接口复杂
**缓解措施**:
- 所有新参数都是可选的，默认行为不变
- 提供清晰的文档说明各参数的用途
- 在 `good_store_selector` 中封装常用的调用模式

### Risk 2: 过滤逻辑的性能影响
**缓解措施**:
- 过滤函数应该是轻量级的，只做简单判断
- 店铺过滤在商品抓取前执行，可以节省时间
- 商品前置过滤避免抓取 OZON 详情页，显著提升性能

### Trade-off: 灵活性 vs 简单性
**选择**: 优先灵活性
- 通过依赖注入支持多种过滤策略
- 业务层可以根据需要组合不同的过滤函数
- 代价是接口参数增多，但通过可选参数和文档可以缓解

## Migration Plan

### Phase 1: 重构 `seerfar_scraper.scrape()` 
1. 将 `scrape_store_products()` 的核心逻辑整合到 `scrape()` 中
2. 添加新参数（`max_products`、`product_filter_func`、`store_filter_func`）
3. 实现店铺过滤逻辑
4. 实现商品抓取逻辑（整合自 `scrape_store_products()`）
5. 更新文档字符串

### Phase 2: 删除冗余方法
1. 搜索所有对 `scrape_store_products()` 的调用
2. 确认只有 `good_store_selector` 在使用
3. 删除 `seerfar_scraper.scrape_store_products()` 方法

### Phase 3: 重构 `good_store_selector`
1. 修改 `_process_single_store()` 使用新的 `scrape()` 接口
2. 删除 `_scrape_store_products()` 方法
3. 更新相关测试

### Phase 4: 验证和清理
1. 运行所有测试确保功能正常
2. 检查 lint 错误
3. 更新相关文档
4. 确认没有遗漏的 `scrape_store_products()` 调用

### Rollback Plan
⚠️ **注意**: 这是一个 BREAKING CHANGE，回滚需要：
1. 恢复 `scrape_store_products()` 方法
2. 恢复 `good_store_selector` 的原有实现
3. 恢复测试代码

## Open Questions
- ❓ 是否需要支持异步的过滤函数？
  - **答案**: 暂不支持，过滤函数应该是同步的轻量级判断
  
- ❓ 是否需要在 `scrape()` 中记录过滤统计信息？
  - **答案**: 是的，应该记录被过滤的店铺和商品数量，便于调试和监控
