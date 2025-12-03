# 商品数据组装规格说明

## MODIFIED Requirements

### Requirement: ScrapingOrchestrator数据组装职责简化
ScrapingOrchestrator MUST 只负责原始数据的收集和组装，不进行业务逻辑计算。

#### Scenario: 商品数据组装流程
**Given** 一个商品URL需要进行完整分析  
**When** 调用 `_orchestrate_product_full_analysis(url)`  
**Then** 应该返回包含以下结构的 ScrapingResult:
```python
{
    "primary_product": ProductInfo,      # 原商品完整信息
    "competitor_product": ProductInfo,   # 跟卖商品完整信息(可选)  
    "competitors_list": List[Dict]       # 跟卖列表简化版本
}
```

#### Scenario: 数据转换标准化
**Given** OzonScraper返回的原始数据  
**When** 调用 `_convert_to_product_info(raw_data, is_primary)`  
**Then** 应该返回完整的ProductInfo对象，包含所有利润计算必需字段

### Requirement: 移除业务逻辑计算方法
ScrapingOrchestrator MUST 移除以下业务逻辑相关方法：
- `_merge_and_select_best_product()`
- `_evaluate_data_completeness()`
- `_should_fetch_competitor_product()`

#### Scenario: 方法移除验证
**Given** ScrapingOrchestrator类  
**When** 检查类的公有和私有方法  
**Then** 不应该包含任何业务逻辑计算方法

## ADDED Requirements

### Requirement: GoodStoreSelector合并逻辑实现
GoodStoreSelector MUST 实现 `merge_and_compute()` 方法处理商品数据合并和利润计算准备。

#### Scenario: 商品合并决策 - 跟卖商品完整
**Given** primary_product 和 competitor_product 都存在  
**And** competitor_product 的利润计算关键字段完整度为 100%  
**When** 调用 `merge_and_compute(scraping_result)`  
**Then** 应该选择 competitor_product 作为 candidate_product  
**And** 返回的ProductInfo包含所有利润计算必需字段

#### Scenario: 商品合并决策 - 跟卖商品不完整  
**Given** primary_product 和 competitor_product 都存在  
**And** competitor_product 的利润计算关键字段完整度 < 100%  
**When** 调用 `merge_and_compute(scraping_result)`  
**Then** 应该选择 primary_product 作为 candidate_product

#### Scenario: 商品合并决策 - 无跟卖商品
**Given** 只有 primary_product 存在  
**And** competitor_product 为 None  
**When** 调用 `merge_and_compute(scraping_result)`  
**Then** 应该选择 primary_product 作为 candidate_product

### Requirement: 利润计算关键字段完整性评估
GoodStoreSelector MUST 实现基于利润计算器必需字段的完整性评估。

#### Scenario: 关键字段完整性评估
**Given** 一个ProductInfo对象  
**When** 调用 `_evaluate_profit_calculation_completeness(product)`  
**Then** 应该检查以下8个关键字段的完整性:
- green_price, black_price, source_price, commission_rate
- weight, length, width, height  
**And** 返回完整字段数量 / 总字段数量的比例

#### Scenario: 100%完整性判断
**Given** ProductInfo对象包含所有8个关键字段的有效值  
**When** 调用 `_evaluate_profit_calculation_completeness(product)`  
**Then** 应该返回 1.0 (100%)

#### Scenario: 部分完整性判断  
**Given** ProductInfo对象只包含4个关键字段的有效值  
**When** 调用 `_evaluate_profit_calculation_completeness(product)`  
**Then** 应该返回 0.5 (50%)

### Requirement: 利润计算数据准备
GoodStoreSelector MUST 实现 `_prepare_for_profit_calculation()` 方法为利润计算准备完整数据。

#### Scenario: list_price计算 - 基于绿标价格
**Given** ProductInfo对象包含 green_price = 100.0  
**When** 调用 `_prepare_for_profit_calculation(product)`  
**Then** 应该设置 product.list_price = 95.0 (green_price * 0.95)

#### Scenario: list_price计算 - 基于黑标价格
**Given** ProductInfo对象 green_price 为空但 black_price = 120.0  
**When** 调用 `_prepare_for_profit_calculation(product)`  
**Then** 应该设置 product.list_price = 114.0 (black_price * 0.95)

## MODIFIED Requirements

### Requirement: ProductInfo模型字段扩展  
ProductInfo MUST 包含所有利润计算必需的字段。

#### Scenario: 必需字段验证
**Given** 一个ProductInfo实例  
**When** 检查其字段定义  
**Then** 必须包含以下字段:
- 价格字段: green_price, black_price, list_price, source_price, commission_rate
- 物理属性: weight, length, width, height  
- 标识字段: product_id, product_url, image_url
- 业务字段: shelf_days, source_matched

### Requirement: 数据结构标准化
所有商品数据传输 MUST 使用 ProductInfo 对象，移除 Dict 格式的数据传递。

#### Scenario: ScrapingResult数据格式标准化
**Given** ScrapingOrchestrator完成数据组装  
**When** 返回ScrapingResult  
**Then** data字段必须包含ProductInfo对象而非Dict

#### Scenario: 冗余字段移除
**Given** 任何商品数据结构  
**When** 进行数据传输  
**Then** 不应该包含以下冗余字段:
- is_competitor (多处重复)
- analysis_type (调试信息)  
- selection_reason (冗长描述)
- completeness_scores (内部计算结果)

## REMOVED Requirements

### Requirement: 移除嵌套数据结构检查
移除对 `price_data.green_price` 和 `erp_data.purchase_price` 等嵌套路径的依赖。

#### Scenario: 扁平结构验证
**Given** ProductInfo对象使用扁平字段结构  
**When** 进行数据完整性检查  
**Then** 应该直接访问对象属性而非解析嵌套路径

### Requirement: 移除复杂权重计算
移除数据完整度评估中的复杂权重分配机制。

#### Scenario: 简化完整性计算
**Given** 利润计算关键字段列表  
**When** 评估数据完整性  
**Then** 应该使用简单的字段计数方式而非权重加权