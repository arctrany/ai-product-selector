## ADDED Requirements

### Requirement: 1688货源匹配功能
系统 SHALL 提供1688货源匹配功能，通过图片相似度和AI商品信息相似度的综合评分，自动找到最佳匹配货源。

#### Scenario: 成功匹配货源
- **WHEN** 用户提供商品信息（包含图片URL）且配置了1688访问令牌
- **THEN** 系统调用1688 API搜索相似商品
- **AND** 计算图片相似度，过滤明显不匹配的商品
- **AND** 使用AI评估商品信息相似度
- **AND** 计算综合相似度（图片相似度 × image_weight + AI相似度 × (1 - image_weight)）
- **AND** 返回所有综合相似度 >= item_similarity 的货源信息
- **AND** 货源信息包含：offerId、subject、oldPrice、imageUrl、province、city、supplyAmount、categoryId

#### Scenario: 图片相似度预过滤
- **WHEN** 1688 API返回多个相似商品（最多10个）
- **THEN** 系统计算每个商品的图片相似度
- **AND** 过滤掉图片相似度 < (item_similarity × image_weight) 的商品
- **AND** 只对通过图片过滤的商品进行AI评估
- **AND** 记录过滤原因到日志

#### Scenario: AI商品信息相似度评估
- **WHEN** 商品通过图片相似度预过滤
- **THEN** 系统使用大语言模型（Qwen）评估商品信息相似度
- **AND** AI评估角色设定为"商品鉴定专家"
- **AND** 评估依据包括：商品标题、价格、分类、描述
- **AND** 返回0-1之间的相似度分数（1.0=完全相似，0.5=50%相似）
- **AND** 如果AI评估失败，使用默认相似度0.5并记录错误

#### Scenario: 综合相似度计算
- **WHEN** 商品通过图片相似度预过滤且完成AI评估
- **THEN** 系统计算综合相似度：`f(x) = 图片相似度 × y + AI相似度 × (1-y)`
- **AND** `y` 为配置的 `image_weight`（默认0.5）
- **AND** 综合相似度范围在0-1之间

#### Scenario: 最终匹配过滤
- **WHEN** 系统计算完所有候选商品的综合相似度
- **THEN** 过滤掉综合相似度 < item_similarity 的商品
- **AND** 返回所有符合条件的货源信息列表
- **AND** 按综合相似度降序排序

#### Scenario: 无匹配货源处理
- **WHEN** 所有候选商品的综合相似度都 < item_similarity
- **THEN** 系统返回空匹配列表
- **AND** 标记 `source_matched = False`
- **AND** 跳过后续利润验证步骤
- **AND** 记录"无匹配货源"到日志

#### Scenario: 货源价格提取
- **WHEN** 成功匹配到货源
- **THEN** 系统从1688 API响应中提取 `oldPrice` 字段
- **AND** 将价格从"分"转换为"元"（除以100）
- **AND** 将价格赋值给 `ProductInfo.source_price`
- **AND** 标记 `ProductInfo.source_matched = True`

#### Scenario: 利润评估集成
- **WHEN** 货源匹配成功且提取到货源价格
- **THEN** 系统将 `source_price` 传递给 `profit_evaluator.evaluate_product_profit()`
- **AND** 利润评估器使用货源价格进行利润计算
- **AND** 利润评估结果包含货源价格信息

#### Scenario: 环境变量缺失处理
- **WHEN** 系统需要调用1688 API但环境变量 `XP_ATK` 未设置
- **THEN** 系统显示错误消息："错误: 未设置1688访问令牌，请设置环境变量 XP_ATK"
- **AND** 退出码为1
- **AND** 跳过货源匹配步骤，继续后续流程

#### Scenario: API调用失败处理
- **WHEN** 1688 API调用失败（网络错误、超时、认证失败等）
- **THEN** 系统自动重试（最多2次）
- **AND** 如果重试后仍失败，记录错误日志
- **AND** 标记 `source_matched = False`
- **AND** 跳过货源匹配步骤，继续后续流程

#### Scenario: DryRun模式支持
- **WHEN** 系统运行在DryRun模式下
- **THEN** 系统执行所有匹配逻辑（API调用、图片相似度计算）
- **AND** 跳过AI评估调用，使用默认相似度0.5
- **AND** 记录DryRun日志，包含所有处理过程
- **AND** 不产生实际的API调用费用

#### Scenario: 性能监控
- **WHEN** 系统执行货源匹配流程
- **THEN** 系统记录关键性能指标：
  - API调用耗时
  - 图片相似度计算耗时
  - AI评估耗时（如果执行）
  - 总处理耗时
- **AND** 性能指标记录到日志文件

#### Scenario: 配置参数支持
- **WHEN** 系统执行货源匹配
- **THEN** 系统从配置文件中读取以下参数：
  - `item_similarity`: 相似度阈值（0-1），从用户输入数据获取
  - `image_weight`: 图片相似度权重（0-1），默认0.5，从系统配置获取
  - `timeout_seconds`: API超时时间（秒），默认20
  - `max_results`: 最大返回结果数，默认10
  - `api_retry_count`: API重试次数，默认2

#### Scenario: 批量处理支持
- **WHEN** 系统需要处理多个商品的货源匹配
- **THEN** 系统按顺序处理每个商品
- **AND** 每个商品的匹配结果独立记录
- **AND** 单个商品匹配失败不影响其他商品处理
- **AND** 记录每个商品的匹配状态和结果

