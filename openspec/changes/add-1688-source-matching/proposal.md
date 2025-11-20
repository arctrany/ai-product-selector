# Change: 添加1688货源匹配功能

## Why

### 业务痛点
当前系统在选品流程中缺少货源匹配环节，无法自动找到1688平台上的相似货源并获取采购价格。这导致：
- **手动查找效率低**: 用户需要手动在1688平台搜索相似商品，耗时且容易遗漏
- **价格信息缺失**: 无法自动获取货源价格，利润计算不准确
- **匹配准确性差**: 仅凭人工判断，难以准确评估商品相似度

### 业务价值
- **自动化货源匹配**: 通过图片相似度和AI评估，自动找到最佳货源
- **提升选品效率**: 减少50%以上的手动操作时间
- **提高利润计算准确性**: 自动获取货源价格，支持精确的利润评估
- **智能匹配**: 结合图片相似度和商品信息相似度，提供更准确的匹配结果

### 典型场景
商家在OZON平台发现一款有利润潜力的商品，系统需要：
1. 调用1688 API根据商品图片搜索相似货源
2. 计算图片相似度，过滤明显不匹配的商品
3. 使用AI评估商品信息相似度（标题、价格、分类等）
4. 综合评分找到最佳匹配货源
5. 提取货源价格信息，传递给利润评估器进行利润计算

## What Changes

### 功能变更
- ✅ **1688 API集成**: 在 `api_scraper.py` 中实现1688相似商品搜索API调用
- ✅ **图片相似度匹配**: 集成现有的 `image_similarity.py` 进行图片相似度计算
- ✅ **AI商品信息评估**: 创建独立的AI模块，使用大语言模型评估商品信息相似度
- ✅ **综合相似度计算**: 实现图片相似度和AI相似度的加权综合评分
- ✅ **货源信息提取**: 从1688 API响应中提取货源详细信息（价格、起订量、供应商等）
- ✅ **利润评估集成**: 将匹配到的货源价格传递给 `profit_evaluator` 进行利润计算

### 技术实现
- **API抓取器**: `common/scrapers/api_scraper.py` - 实现1688 API调用和签名生成
- **AI评估模块**: `common/business/ai_similarity_evaluator.py` - 独立AI模块，使用Qwen模型
- **货源匹配器**: `common/business/source_matcher.py` - 整合图片相似度、AI评估和综合评分
- **数据模型扩展**: 扩展 `ProductInfo` 模型，添加货源匹配相关字段

### 数据结构变更
```python
# ProductInfo 新增字段
source_price: Optional[float] = None  # 采购价格（已存在）
source_matched: bool = False  # 是否匹配到货源（已存在）
source_match_info: Optional[Dict[str, Any]] = None  # 货源匹配详细信息

# 新增数据模型
@dataclass
class SourceMatchResult:
    success: bool
    matches: List[SourceMatch]
    total_found: int
    filtered_count: int

@dataclass
class SourceMatch:
    offer_id: str
    subject: str
    old_price: float  # 价格（分转元）
    image_url: str
    image_similarity: float
    ai_similarity: float
    comprehensive_score: float
```

**向后兼容**: 新增字段都是可选的，不影响现有代码。

## Impact

### 影响的 Specs
- **source-matching**: 新增能力，货源匹配核心逻辑
- **api-scraper**: 新增能力，1688 API抓取功能

### 影响的代码文件
- `common/scrapers/api_scraper.py` - 实现1688 API调用（新建）
- `common/business/ai_similarity_evaluator.py` - AI评估模块（新建）
- `common/business/source_matcher.py` - 货源匹配器（新建）
- `common/models.py` - 扩展数据模型
- `common/config.py` - 添加货源匹配配置
- `common/business/profit_evaluator.py` - 集成货源价格（可能需要修改）
- `good_store_selector.py` - 集成货源匹配流程（可能需要修改）

### 性能影响
- **API调用**: 每个商品需要调用一次1688 API，预计耗时2-3秒
- **图片相似度计算**: 每个1688商品需要计算相似度，预计耗时0.5-1秒/商品
- **AI评估**: 每个通过图片过滤的商品需要AI评估，预计耗时1-2秒/商品
- **总体影响**: 单个商品的货源匹配预计耗时5-10秒（取决于匹配商品数量）
- **影响评估**: 可接受，因为这是可选的增强功能，可以异步处理

### 风险评估
1. **API依赖**: 依赖1688 API可用性和访问令牌 - **风险等级: 中**，已有重试机制和错误处理
2. **AI服务依赖**: 依赖Qwen API可用性 - **风险等级: 中**，提供降级策略（使用默认相似度）
3. **网络稳定性**: API调用和AI评估需要网络连接 - **风险等级: 低**，已有超时和重试机制
4. **成本控制**: AI API调用可能产生费用 - **风险等级: 低**，支持DryRun模式，可控制调用频率

## Migration Plan

### 向后兼容性
✅ **完全向后兼容** - 所有新功能都是可选的，现有流程不受影响。

### 可选迁移
如果用户希望使用货源匹配功能：
1. 配置环境变量：`XP_ATK`（1688访问令牌）、`QWEN_API_KEY`（Qwen API密钥）
2. 在配置文件中启用货源匹配：`source_matching.enabled = true`
3. 系统会自动在商品处理流程中集成货源匹配

### 配置要求
- **必需环境变量**:
  - `XP_ATK`: 1688访问令牌
  - `QWEN_API_KEY`: Qwen API密钥（如果使用AI评估）
- **可选环境变量**:
  - `QWEN_BASE_URL`: Qwen API基础URL（默认值：https://dashscope.aliyuncs.com/compatible-mode/v1）
  - `QWEN_MODEL`: Qwen模型名称（默认值：qwen-turbo）

## Success Metrics

- ✅ 成功调用1688 API并获取相似商品列表
- ✅ 图片相似度计算准确率 ≥ 85%（基于测试数据）
- ✅ AI商品信息相似度评估准确率 ≥ 80%
- ✅ 综合相似度匹配准确率 ≥ 90%
- ✅ 货源价格成功传递给利润评估器
- ✅ 所有现有测试用例通过，无回归问题
- ✅ DryRun模式正常工作，不产生实际API调用

