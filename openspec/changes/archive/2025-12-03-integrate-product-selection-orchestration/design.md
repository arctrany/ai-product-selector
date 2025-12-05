# 设计文档 - 集成选品流程协调器

## 架构设计

基于调研FilterManager和现有功能，采用极简化协调器设计：

### 1. 简化协调器职责
- **协调器极简化**: 仅负责降级处理，代码量减少80%
- **逻辑下沉**: 所有业务逻辑集中到OzonScraper内部
- **语义清晰**: 使用`include_competitor=True`替代`extract_first_product=True`

### 2. 职责重新分配
- **OzonScraper**: 集成FilterManager、ProfitEvaluator和CompetitorScraper
- **价格判断**: 复用`ProfitEvaluator.has_better_competitor_price()`
- **过滤逻辑**: 集成`FilterManager.get_product_filter_func()`

## 极简化架构设计

### 总体架构
```
┌─────────────────────────────────────────────────────────────┐
│                    GoodStoreSelector                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              _process_products()                    │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │         ScrapingMode.FULL_CHAIN             │    │    │
│  │  │         (include_competitor=True)           │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                ScrapingOrchestrator                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │        _orchestrate_product_full_analysis()         │    │
│  │                (极简20-30行代码)                     │    │
│  │                                                     │    │
│  │  Step 1: 完整商品分析（含跟卖）                        │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │            OzonScraper.scrape()             │    │    │
│  │  │            (include_competitor=True)        │    │    │
│  │  │                                             │    │    │
│  │  │  内部集成逻辑:                                │    │    │
│  │  │  1. 商品过滤检查 (FilterManager)             │    │    │
│  │  │  2. 价格优势判断 (has_better_competitor_price)│    │    │
│  │  │  3. 如果有优势则调用CompetitorScraper         │    │    │
│  │  │  4. 返回原商品和跟卖数据给协调器              │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  │                                                     │    │
│  │  Step 2: 抓取跟卖商品详情                           │    │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │            OzonScraper.scrape()             │    │    │
│  │  │     (competitor_url, skip_competitors=True) │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  │                                                     │    │
│  │  Step 3: 数据合并和完整度评估（协调器处理）            │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │    _merge_and_select_best_product()         │    │    │
│  │  │    _evaluate_data_completeness()            │    │    │
│  │  │    合并Step1和Step2的商品数据                │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  │                                                     │    │

│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 数据流设计

#### 调整后的数据流
```
商品URL → ScrapingOrchestrator
            ↓
    Step 1: OzonScraper(include_competitor=True)
            ↓
    返回: 原商品数据 + first_competitor_product_id
            ↓
    Step 2: OzonScraper.scrape(competitor_url, skip_competitors=True)
            ↓
    返回: 跟卖商品详情数据
            ↓
    Step 3: 协调器合并Step1和Step2数据
            ↓
    _evaluate_data_completeness() + _merge_and_select_best_product()
            ↓
    返回: 统一分析结果（包含选择的最优商品）
```

## 核心组件重新设计

### 1. OzonScraper增强设计

#### 新增参数和方法
```python
class OzonScraper(BaseScraper):
    def __init__(self, config=None, ...):
        super().__init__()
        # 集成过滤管理器和利润评估器
        self.filter_manager = FilterManager(config)
        self.profit_evaluator = ProfitEvaluator(config)
        
    def scrape(self, target: str, include_competitor: bool = False, **kwargs):
        """
        统一抓取接口，支持跟卖商品分析
        
        Args:
            target: 商品URL
            include_competitor: 是否包含跟卖商品分析
        """
        if include_competitor:
            return self._scrape_with_competitor_analysis(target, **kwargs)
        else:
            return self._scrape_basic_product_info(target, **kwargs)
    
    def _scrape_with_competitor_analysis(self, target: str, **kwargs):
        """完整的跟卖商品分析流程"""
        # 1. 抓取基础商品信息
        basic_data = self._extract_basic_product_info(target)
        
        # 2. 商品过滤检查
        if not self._should_analyze_competitor(basic_data):
            return ScrapingResult(success=True, data={
                "selected_product": basic_data,
                "is_competitor": False,
                "selection_reason": "商品被过滤或无价格优势",
                "analysis_type": "filtered_out"
            })
        
        # 3. 获取跟卖信息
        competitor_result = self.competitor_scraper.scrape(target)
        first_competitor_id = competitor_result.data.get('first_competitor_product_id')
        
        if not first_competitor_id:
            return ScrapingResult(success=True, data={
                "selected_product": basic_data,
                "is_competitor": False,
                "selection_reason": "未找到跟卖商品ID",
                "analysis_type": "no_competitor"
            })
        
        # 4. 抓取跟卖商品详情
        competitor_url = self._build_competitor_url(first_competitor_id)
        competitor_data = self._extract_basic_product_info(competitor_url, skip_competitors=True)
        
        # 5. 数据合并和选择
        return self._merge_and_select_best_product(basic_data, competitor_data, competitor_result.data)
    
    def _should_analyze_competitor(self, product_data: Dict[str, Any]) -> bool:
        """判断是否需要进行跟卖分析"""
        # 1. 商品过滤检查
        product_filter = self.filter_manager.get_product_filter_func()
        if not product_filter(product_data):
            self.logger.info("商品未通过过滤检查，跳过跟卖分析")
            return False
            
        # 2. 价格优势判断（复用现有逻辑）
        has_better_price = self.profit_evaluator.has_better_competitor_price({
            'price_data': product_data
        })
        
        if not has_better_price:
            self.logger.info("跟卖价格无优势，跳过跟卖分析")
            return False
            
        return True
```

### 2. ScrapingOrchestrator职责调整设计

#### 调整后的协调逻辑（负责数据合并和选择）

```python
def _orchestrate_product_full_analysis(self, url: str, **kwargs) -> ScrapingResult:
    """
    调整后的商品分析协调
    1. 获取原商品和跟卖数据
    2. 协调器负责数据合并和完整度评估
    3. 失败时降级使用基础信息
    """
    start_time = time.time()

    try:
        self.logger.info("🔧 开始执行商品分析流程...")

        # Step 1: 获取原商品和跟卖数据
        competitor_result = self.ozon_scraper.scrape(url, include_competitor=True, **kwargs)

        if not competitor_result.success:
            self.logger.error("❌ 原商品和跟卖数据获取失败")
            return ScrapingResult(
                success=False,
                data={},
                error_message=f"原商品和跟卖数据获取失败: {competitor_result.error_message}",
                execution_time=time.time() - start_time
            )

        # Step 2: 根据返回的first_competitor_product_id抓取跟卖详情
        competitor_data = competitor_result.data
        first_competitor_id = competitor_data.get('first_competitor_product_id')

        if first_competitor_id:
            competitor_url = _build_competitor_url(first_competitor_id)
            competitor_product_result = self.ozon_scraper.scrape(
                competitor_url, skip_competitors=True, **kwargs
            )

            if competitor_product_result.success:
                # Step 3: 协调器负责数据合并和完整度评估
                return self._merge_and_select_best_product(
                    competitor_data.get('primary_product', {}),
                    competitor_product_result.data,
                    competitor_data.get('competitors', []),
                    start_time
                )

        # 如果没有跟卖或抓取失败，返回原商品数据
        return ScrapingResult(
            success=True,
            data={
                "primary_product": competitor_data.get('primary_product', {}),
                "selected_product": competitor_data.get('primary_product', {}),
                "is_competitor": False,
                "selection_reason": "无跟卖商品或抓取失败",
                "analysis_type": "primary_only"
            },
            execution_time=time.time() - start_time
        )

    except Exception as e:
        self.logger.error(f"商品分析流程异常: {e}")
        return ScrapingResult(
            success=False,
            data={},
            error_message=f"分析异常: {str(e)}",
            execution_time=time.time() - start_time
        )


def _merge_and_select_best_product(self, primary_data, competitor_data, competitors, start_time):
    """协调器负责的数据合并和选择逻辑"""
    # 评估数据完整度
    primary_completeness = self._evaluate_data_completeness(primary_data)
    competitor_completeness = self._evaluate_data_completeness(competitor_data)

    # 选择最优商品
    if primary_completeness >= 0.7 and competitor_completeness >= 0.7:
        selected_data = competitor_data
        is_competitor = True
        reason = "两商品数据都完整，选择跟卖商品"
    elif competitor_completeness >= 0.7:
        selected_data = competitor_data
        is_competitor = True
        reason = f"跟卖商品数据更完整（{competitor_completeness:.1%} vs {primary_completeness:.1%}）"
    elif primary_completeness >= 0.7:
        selected_data = primary_data
        is_competitor = False
        reason = f"原商品数据更完整（{primary_completeness:.1%} vs {competitor_completeness:.1%}）"
    else:
        return ScrapingResult(
            success=False,
            data={},
            error_message="两商品数据都不完整，无法用于利润计算",
            execution_time=time.time() - start_time
        )

    selected_data_with_flag = selected_data.copy()
    selected_data_with_flag['is_competitor'] = is_competitor

    return ScrapingResult(
        success=True,
        data={
            "primary_product": primary_data,
            "competitor_product": competitor_data,
            "selected_product": selected_data_with_flag,
            "is_competitor": is_competitor,
            "competitors": competitors,
            "selection_reason": reason,
            "analysis_type": "full_analysis",
            "completeness_scores": {
                "primary": primary_completeness,
                "competitor": competitor_completeness
            }
        },
        execution_time=time.time() - start_time
    )


def _evaluate_data_completeness(self, product_data):
    """协调器负责的数据完整度评估"""
    score = 0.0
    weights = {
        'green_price': 0.25, 'black_price': 0.25,
        'erp_data.purchase_price': 0.20, 'erp_data.commission_rate': 0.15,
        'product_id': 0.05, 'title': 0.05, 'brand': 0.05
    }

    for field_path, weight in weights.items():
        value = product_data
        for key in field_path.split('.'):
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                value = None
                break

        if value is not None and value != '' and value != 0:
            score += weight

    return score
```

## 关键优化点

#### 1. 职责清晰化
- **OzonScraper**: 负责所有商品相关的抓取和分析逻辑（集成FilterManager和ProfitEvaluator）
- **ScrapingOrchestrator**: 极简协调，仅提供降级处理能力
- **FilterManager**: 集成到OzonScraper，提供标准化过滤
- **ProfitEvaluator**: 集成到OzonScraper，复用价格比较逻辑

#### 2. 参数语义优化
- `include_competitor=True`: 清晰表达是否包含跟卖分析
- 避免 `extract_first_product=True` 的语义模糊

#### 3. 极简架构
- **协调器极简化**: 仅20-30行代码，只负责降级处理
- **逻辑完全内聚**: 所有业务逻辑集中在OzonScraper内部
- **单一职责**: 每个组件职责明确，便于维护

#### 4. 现有功能复用
- 直接使用 `ProfitEvaluator.has_better_competitor_price()`
- 集成 `FilterManager` 的过滤能力
- 保持与现有代码的兼容性

#### 5. 简化收益
- **代码量**: 协调器从100+行减少到20-30行
- **复杂度**: 移除所有复杂的业务判断逻辑
- **维护成本**: 大幅降低维护复杂度
- **测试友好**: 更容易编写和维护测试

## 实现优先级

### 高优先级调整
1. **OzonScraper增强**: 添加 `include_competitor` 参数支持
2. **集成FilterManager**: 在OzonScraper中集成过滤逻辑
3. **复用价格判断**: 使用现有的 `has_better_competitor_price`
4. **极简化协调器**: 移除所有复杂的业务判断逻辑

### 中优先级调整
1. **数据结构标准化**: 确保返回格式一致
2. **错误处理优化**: 完善降级和容错机制
3. **日志记录**: 详细记录决策过程

### 低优先级调整
1. **性能优化**: 缓存和并发控制
2. **配置化**: 支持更多配置参数
3. **扩展性**: 支持更多分析策略

这种极简化方案更加简洁、职责清晰，同时充分复用了现有的功能模块。