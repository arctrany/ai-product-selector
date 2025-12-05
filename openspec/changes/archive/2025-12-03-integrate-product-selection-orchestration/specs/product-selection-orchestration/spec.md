# 选品流程协调器规范

## ADDED Requirements

### Requirement: OzonScraper集成跟卖分析能力
OzonScraper MUST支持include_competitor参数，并在内部集成FilterManager和ProfitEvaluator，实现完整的跟卖商品分析流程。

#### Scenario: 启用跟卖商品分析
给定一个有效的商品URL和include_competitor=True参数
当调用OzonScraper.scrape()时
那么应该执行完整的跟卖分析流程：
1. 抓取基础商品信息
2. 使用FilterManager进行商品过滤检查
3. 使用has_better_competitor_price判断价格优势
4. 如果有优势，调用CompetitorScraper获取跟卖信息
5. 根据first_competitor_product_id抓取跟卖商品详情
6. 合并数据并选择最优商品

#### Scenario: 商品被过滤时的处理
给定商品数据不通过FilterManager过滤检查
当执行跟卖分析时
那么应该直接返回原商品数据
并设置selection_reason为"商品被过滤"
设置analysis_type为"filtered_out"

#### Scenario: 跟卖价格无优势时的处理
给定跟卖价格不优于原商品价格
当执行价格优势判断时
那么应该跳过跟卖商品详情抓取
直接返回原商品数据
并设置selection_reason为"跟卖价格无优势"

#### Scenario: 未找到跟卖商品ID时的处理
给定CompetitorScraper返回的结果中无first_competitor_product_id
当尝试抓取跟卖商品详情时
那么应该返回原商品数据
并设置selection_reason为"未找到跟卖商品ID"
设置analysis_type为"no_competitor"

### Requirement: FilterManager集成到商品抓取流程
OzonScraper MUST在构造函数中初始化FilterManager，并在跟卖分析前进行商品过滤检查。

#### Scenario: 商品过滤检查集成
给定OzonScraper实例包含FilterManager
当执行_should_analyze_competitor方法时
那么应该首先调用FilterManager.get_product_filter_func()
对商品数据进行过滤检查
只有通过过滤的商品才进行后续的跟卖分析

#### Scenario: 类目黑名单过滤
给定商品类目在配置的黑名单中
当进行商品过滤检查时
那么FilterManager应该返回False
跳过该商品的跟卖分析

#### Scenario: 无类目信息的商品处理
给定商品数据中无类目信息
当进行商品过滤检查时
那么FilterManager应该返回True（默认通过）
继续进行跟卖分析

### Requirement: 复用现有价格比较逻辑
OzonScraper MUST集成ProfitEvaluator并复用has_better_competitor_price方法进行价格优势判断。

#### Scenario: 价格优势判断集成
给定OzonScraper实例包含ProfitEvaluator
当执行_should_analyze_competitor方法时
那么应该调用profit_evaluator.has_better_competitor_price()
传入格式为{'price_data': product_data}的参数
根据返回结果决定是否进行跟卖分析

#### Scenario: 跟卖价格更优的判断
给定原商品绿标价格1500₽，跟卖价格1400₽
当调用has_better_competitor_price时
那么应该返回True
继续执行跟卖商品详情抓取

#### Scenario: 跟卖价格不优的判断
给定原商品绿标价格1400₽，跟卖价格1500₽
当调用has_better_competitor_price时
那么应该返回False
跳过跟卖商品详情抓取

### Requirement: 根据first_competitor_product_id抓取跟卖商品详情
OzonScraper MUST能够根据CompetitorScraper返回的first_competitor_product_id构建URL并抓取跟卖商品详情。

#### Scenario: 成功抓取跟卖商品详情
给定CompetitorScraper返回包含first_competitor_product_id的结果
当需要抓取跟卖商品详情时
那么应该使用_build_competitor_url方法构建跟卖商品URL
调用_extract_basic_product_info方法抓取详情（skip_competitors=True）
避免无限递归

#### Scenario: 跟卖商品详情抓取失败
给定跟卖商品URL无效或抓取失败
当尝试抓取跟卖商品详情时
那么应该记录错误日志
返回原商品数据作为最终结果
设置selection_reason说明抓取失败原因

### Requirement: ScrapingOrchestrator负责数据合并和完整度评估
ScrapingOrchestrator MUST负责数据合并和完整度评估，避免OzonScraper过于复杂，保持职责分离。

#### Scenario: 协调器负责数据合并流程
给定商品URL
当调用_orchestrate_product_full_analysis时
那么应该执行以下流程：
1. 调用OzonScraper.scrape(include_competitor=True)获取原商品和跟卖基础数据
2. 根据返回的first_competitor_product_id抓取跟卖商品详情
3. 协调器负责数据合并和完整度评估
4. 选择最优商品并返回标准化结果

#### Scenario: 协调器执行数据完整度评估
给定原商品和跟卖商品数据
当需要选择最优商品时
那么协调器应该调用_evaluate_data_completeness方法
评估两个商品的数据完整度
根据完整度分数选择最优商品

#### Scenario: 协调器执行数据合并和选择
给定完整度评估结果
当进行商品选择时
那么协调器应该：
- 如果都完整(≥70%)，选择跟卖商品
- 如果只有一个完整，选择完整的
- 如果都不完整，返回失败
- 在返回结果中包含选择原因和完整度分数

#### Scenario: 协调器职责边界
给定协调器的实现
当完成职责调整时
那么协调器应该：
- 负责数据合并和完整度评估
- 负责根据first_competitor_product_id抓取跟卖详情
- 不负责商品过滤和价格判断（由OzonScraper处理）
- 保持与OzonScraper的清晰职责分离

### Requirement: 语义清晰的参数命名
系统MUST使用include_competitor参数替代extract_first_product，提供更清晰的语义表达。

#### Scenario: include_competitor参数的使用
给定需要进行跟卖分析的场景
当调用相关方法时
那么应该使用include_competitor=True参数
而不是extract_first_product=True
提供更直观的参数语义

#### Scenario: 向后兼容性保证
给定现有代码可能使用旧参数名
当进行参数升级时
那么应该保持向后兼容性
或提供清晰的迁移指导

### Requirement: 统一的数据结构返回
OzonScraper MUST返回标准化的分析结果数据结构，包含所有必要的商品信息和选择元数据。

#### Scenario: 完整分析结果的数据结构
给定成功的跟卖商品分析
当返回分析结果时
那么数据结构必须包含：
- primary_product: 原商品数据
- competitor_product: 跟卖商品数据（如果抓取成功）
- selected_product: 选中商品数据（包含is_competitor标识）
- is_competitor: 布尔值标识
- selection_reason: 选择原因说明
- analysis_type: 分析类型

#### Scenario: 过滤或降级情况的数据结构
给定商品被过滤或分析失败的情况
当返回结果时
那么应该设置相应的analysis_type
在selection_reason中说明具体原因
确保数据结构的一致性