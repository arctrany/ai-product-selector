# 商品数据组装合并流程设计方案

## 架构概览

### 当前架构问题
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  OzonScraper    │───▶│ ScrapingOrchestra│───▶│ GoodStoreSelector│
│                 │    │                  │    │                 │
│ 返回扁平结构     │    │ 期望嵌套结构      │    │ 接收混乱数据     │
│ green_price     │    │ price_data.green │    │ 无法准确计算     │
│ source_price    │    │ erp_data.purchase│    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 优化后架构
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  OzonScraper    │───▶│ ScrapingOrchestra│───▶│ GoodStoreSelector│
│                 │    │                  │    │                 │
│ 输出ProductInfo  │    │ 纯数据组装        │    │ merge_and_compute│
│ 标准化结构      │    │ 无业务逻辑        │    │ 利润计算准备     │
│ 完整字段映射    │    │ 职责单一         │    │ 智能合并决策     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 核心设计原则

### 1. 职责分离
- **ScrapingOrchestrator**: 纯数据组装，不进行业务计算
- **GoodStoreSelector**: 业务逻辑处理，包含合并决策和利润计算准备
- **各Scraper**: 只负责数据抓取，输出标准化 `ProductInfo`

### 2. 数据标准化
- 统一使用 `ProductInfo` 作为数据传输对象
- 所有价格、ERP、物理属性字段完整映射
- 移除冗余和调试字段

### 3. 合并策略优化
- 基于利润计算关键字段完整性判断
- 简化决策逻辑，提高可维护性
- 为下游利润计算提供完整数据

## 详细设计

### 1. ScrapingOrchestrator 重构

#### 1.1 简化数据组装逻辑
```python
def _orchestrate_product_full_analysis(self, url: str, **kwargs) -> ScrapingResult:
    """
    简化的商品分析协调 - 只负责数据组装
    """
    # Step 1: 获取原商品数据
    primary_result = self.ozon_scraper.scrape(url, include_competitor=False, **kwargs)
    primary_product = self._convert_to_product_info(primary_result.data, is_primary=True)
    
    # Step 2: 获取跟卖商品数据（如果存在）
    competitor_product = None
    competitors_list = []
    
    competitor_result = self.ozon_scraper.scrape(url, include_competitor=True, **kwargs)
    if competitor_result.success:
        first_competitor_id = competitor_result.data.get('first_competitor_product_id')
        competitors_list = competitor_result.data.get('competitors', [])
        
        if first_competitor_id:
            competitor_url = self._build_competitor_url(first_competitor_id)
            comp_result = self.ozon_scraper.scrape(competitor_url, skip_competitors=True, **kwargs)
            if comp_result.success:
                competitor_product = self._convert_to_product_info(comp_result.data, is_primary=False)
    
    # Step 3: 组装数据，不进行选择决策
    return ScrapingResult(
        success=True,
        data={
            "primary_product": primary_product,
            "competitor_product": competitor_product,
            "competitors_list": competitors_list
        }
    )
```

#### 1.2 数据转换方法
```python
def _convert_to_product_info(self, raw_data: Dict[str, Any], is_primary: bool) -> ProductInfo:
    """
    将原始数据转换为标准 ProductInfo 对象
    """
    return ProductInfo(
        product_id=raw_data.get('product_id'),
        product_url=raw_data.get('product_url'),
        image_url=raw_data.get('product_image'),
        
        # 价格信息
        green_price=raw_data.get('green_price'),
        black_price=raw_data.get('black_price'),
        
        # ERP数据
        source_price=raw_data.get('erp_data', {}).get('purchase_price'),
        commission_rate=raw_data.get('erp_data', {}).get('commission_rate'),
        weight=raw_data.get('erp_data', {}).get('weight'),
        length=raw_data.get('erp_data', {}).get('length'),
        width=raw_data.get('erp_data', {}).get('width'),
        height=raw_data.get('erp_data', {}).get('height'),
        shelf_days=raw_data.get('erp_data', {}).get('shelf_days'),
        
        # 标识字段
        source_matched=bool(raw_data.get('erp_data', {}).get('purchase_price'))
    )
```

### 2. GoodStoreSelector 合并逻辑实现

#### 2.1 核心合并方法

```python
def merge_and_compute(self, scraping_result: ScrapingResult) -> ProductInfo:
    """
    商品数据合并和计算准备
    
    Args:
        scraping_result: 协调器返回的原始数据
        
    Returns:
        ProductInfo: 合并后的候选商品
    """
    primary_product = scraping_result.data.get('primary_product')
    competitor_product = scraping_result.data.get('competitor_product')

    if not primary_product:
        raise ValueError("缺少原商品数据")

    # 如果没有跟卖商品，直接返回原商品
    if not competitor_product:
        return self._prepare_for_profit_calculation(primary_product)

    # 评估关键字段完整性
    primary_completeness = _evaluate_profit_calculation_completeness(primary_product)
    competitor_completeness = _evaluate_profit_calculation_completeness(competitor_product)

    # 合并决策：跟卖商品关键字段完整则选择跟卖，否则选择原商品
    if competitor_completeness >= 1.0:  # 100% 完整
        candidate_product = competitor_product
        self.logger.info(f"选择跟卖商品：关键字段完整度 {competitor_completeness:.1%}")
    else:
        candidate_product = primary_product
        self.logger.info(f"选择原商品：跟卖关键字段不完整 {competitor_completeness:.1%}")

    return self._prepare_for_profit_calculation(candidate_product)
```

#### 2.2 利润计算关键字段评估
```python
def _evaluate_profit_calculation_completeness(self, product: ProductInfo) -> float:
    """
    评估利润计算关键字段完整性
    
    基于 ProfitCalculatorInput 必需字段：
    - green_price, black_price, source_price, commission_rate
    - weight, length, width, height
    """
    required_fields = [
        'green_price', 'black_price', 'source_price', 'commission_rate',
        'weight', 'length', 'width', 'height'
    ]
    
    valid_count = 0
    for field_name in required_fields:
        value = getattr(product, field_name, None)
        if value is not None and value > 0:
            valid_count += 1
    
    return valid_count / len(required_fields)
```

#### 2.3 利润计算准备
```python
def _prepare_for_profit_calculation(self, product: ProductInfo) -> ProductInfo:
    """
    为利润计算准备数据，包括计算 list_price 等衍生字段
    """
    # 计算定价 (绿标价格 * 0.95)
    if product.green_price:
        product.list_price = product.green_price * 0.95
    elif product.black_price:
        product.list_price = product.black_price * 0.95
    
    # 其他必要的数据准备...
    
    return product
```

### 3. 数据流优化

#### 3.1 新的数据流
```
1. OzonScraper.scrape() 
   └─▶ 返回标准化的原始数据

2. ScrapingOrchestrator._orchestrate_product_full_analysis()
   ├─▶ 调用 OzonScraper 获取 primary_product
   ├─▶ 调用 OzonScraper 获取 competitor_product  
   └─▶ 组装数据，返回 ScrapingResult

3. GoodStoreSelector.merge_and_compute()
   ├─▶ 评估关键字段完整性
   ├─▶ 执行合并决策
   └─▶ 返回 candidate_product (ProductInfo)

4. ProfitEvaluator.evaluate_product_profit()
   └─▶ 接收完整的 ProductInfo 进行利润计算
```

#### 3.2 数据结构标准化
```python
# 协调器输出格式
ScrapingResult.data = {
    "primary_product": ProductInfo,      # 原商品完整信息
    "competitor_product": ProductInfo,   # 跟卖商品完整信息 (可选)
    "competitors_list": List[Dict]       # 跟卖列表 (简化版本)
}

# GoodStoreSelector 输出格式  
candidate_product: ProductInfo          # 最终选择的商品，包含所有必要字段
```

## 关键技术决策

### 1. 为什么移除 `_evaluate_data_completeness` 中的嵌套结构检查？
- **问题**: 当前实现期望 `price_data.green_price` 格式，但实际数据是扁平的
- **解决**: 直接在 `ProductInfo` 对象上检查字段，避免路径解析的复杂性
- **优势**: 类型安全、性能更好、更易维护

### 2. 为什么将合并逻辑移到 GoodStoreSelector？
- **原则**: 单一职责原则，协调器只负责数据收集
- **优势**: 业务逻辑集中，便于测试和维护
- **扩展性**: 未来可以轻松添加更复杂的合并策略

### 3. 为什么使用 100% 完整性阈值？
- **需求**: 利润计算需要所有关键字段，缺一不可
- **简化**: 避免复杂的权重计算，决策逻辑更清晰
- **可靠性**: 确保下游利润计算的准确性

## 性能优化考虑

### 1. 内存使用优化
- 移除冗余的 `selected_product` 数据复制
- 使用对象引用而非数据复制
- 及时清理不需要的中间数据

### 2. 计算效率优化
- 简化完整性评估算法
- 避免不必要的数据转换
- 缓存重复计算的结果

### 3. 网络请求优化
- 保持现有的抓取策略，不增加额外请求
- 优化数据传输格式
- 减少序列化/反序列化开销

## 工具函数模块整合优化

### 1. 冗余问题识别
发现三重冗余的工具函数模块：
- `common/models/utils.py` - 包含完整的 `clean_price_string` 实现
- `common/utils/model_utils.py` - 5个函数100%重复
- `common/utils/scraping_utils.py` - 已被广泛使用的工具函数库

### 2. 统一整合方案
**目标架构：**
```
删除冗余文件：
├── common/models/utils.py          ❌ 删除
└── common/utils/model_utils.py     ❌ 删除

统一工具函数库：
└── common/utils/scraping_utils.py  ✅ 增强为完整工具函数库
```

**合并策略：**
- 保留 `scraping_utils.py` 作为统一工具函数库
- 合并所有验证函数：`validate_weight`, `format_currency`, `calculate_profit_rate`
- 通过 `common/models/__init__.py` 维持向后兼容性
- 统一导入路径：`from common.utils.scraping_utils import ...`

### 3. 实施计划
- **阶段1**: 增强 `scraping_utils.py`，添加缺失函数
- **阶段2**: 更新 `models/__init__.py` 导入路径
- **阶段3**: 删除冗余文件，更新所有导入语句
- **阶段4**: 验证向后兼容性和功能完整性

## 向后兼容性处理

### 1. 破坏性变更识别
- `ScrapingResult.data` 结构变更
- `_merge_and_select_best_product` 方法移除
- 数据完整度评估逻辑变更
- **新增**: 工具函数模块合并和导入路径变更

### 2. 迁移策略
- 分阶段实施，确保每个阶段的稳定性
- 更新所有相关的集成测试
- 提供详细的迁移文档
- **新增**: 通过 `__init__.py` 维持工具函数的向后兼容性

### 3. 测试策略
- 创建新的测试套件验证重构结果
- 保留关键的集成测试作为回归验证
- 性能基准测试确保无性能回归
- **新增**: 工具函数合并后的功能验证测试