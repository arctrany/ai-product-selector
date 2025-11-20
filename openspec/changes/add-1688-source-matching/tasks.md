## 1. 1688 API抓取器开发
- [ ] 1.1 在 `common/scrapers/api_scraper.py` 中实现 `Alibaba1688Scraper` 类
- [ ] 1.2 实现 `_generate_signature()` 方法，按照1688签名规则生成 `_aop_signature`
- [ ] 1.3 实现 `_get_access_token()` 方法，从环境变量 `XP_ATK` 获取访问令牌
- [ ] 1.4 实现 `search_similar_products()` 方法，调用1688相似商品搜索API
- [ ] 1.5 实现请求参数构建（imageUrl、pageSize、currentPage等）
- [ ] 1.6 实现API响应解析，提取商品列表
- [ ] 1.7 实现重试机制（最多重试2次）
- [ ] 1.8 实现超时控制（默认20秒）
- [ ] 1.9 实现错误处理和日志记录
- [ ] 1.10 添加单元测试

## 2. AI相似度评估模块开发
- [ ] 2.1 创建 `common/business/ai_similarity_evaluator.py` 模块
- [ ] 2.2 实现 `AISimilarityEvaluator` 类
- [ ] 2.3 实现环境变量读取（QWEN_API_KEY、QWEN_BASE_URL、QWEN_MODEL）
- [ ] 2.4 实现OpenAI兼容客户端初始化
- [ ] 2.5 实现 `evaluate_product_similarity()` 方法，评估单个商品对相似度
- [ ] 2.6 实现Prompt模板设计（商品鉴定专家角色）
- [ ] 2.7 实现批量评估功能（batch_size=5）
- [ ] 2.8 实现响应解析，提取相似度分数（0-1）
- [ ] 2.9 实现错误处理和降级策略（失败时返回默认值0.5）
- [ ] 2.10 实现AI日志记录（logs/ai_evaluation.log）
- [ ] 2.11 添加单元测试

## 3. 货源匹配器开发
- [ ] 3.1 创建 `common/business/source_matcher.py` 模块
- [ ] 3.2 实现 `SourceMatcher` 类
- [ ] 3.3 集成 `Alibaba1688Scraper` 进行API调用
- [ ] 3.4 集成 `ProductImageSimilarity` 进行图片相似度计算
- [ ] 3.5 集成 `AISimilarityEvaluator` 进行AI评估
- [ ] 3.6 实现 `match_source()` 主方法，完整匹配流程
- [ ] 3.7 实现图片相似度预过滤（阈值：item_similarity × image_weight）
- [ ] 3.8 实现综合相似度计算（图片相似度 × y + AI相似度 × (1-y)）
- [ ] 3.9 实现最终过滤（综合相似度 >= item_similarity）
- [ ] 3.10 实现货源信息提取和转换
- [ ] 3.11 实现DryRun模式支持（跳过AI调用，使用默认值）
- [ ] 3.12 实现性能监控（记录各步骤耗时）
- [ ] 3.13 添加单元测试

## 4. 数据模型扩展
- [ ] 4.1 在 `common/models.py` 中添加 `SourceMatchResult` 数据类
- [ ] 4.2 在 `common/models.py` 中添加 `SourceMatch` 数据类
- [ ] 4.3 在 `common/models.py` 中添加 `Source1688Info` 数据类
- [ ] 4.4 扩展 `ProductInfo` 模型，添加 `source_match_info` 字段（可选）
- [ ] 4.5 验证数据模型序列化和反序列化

## 5. 配置管理扩展
- [ ] 5.1 在 `common/config.py` 中添加 `SourceMatchingConfig` 配置类
- [ ] 5.2 添加配置字段：`image_weight`（默认0.5）、`timeout_seconds`（默认20）、`max_results`（默认10）、`api_retry_count`（默认2）
- [ ] 5.3 在 `GoodStoreSelectorConfig` 中集成 `SourceMatchingConfig`
- [ ] 5.4 支持从 `config.json` 读取配置
- [ ] 5.5 添加配置验证和默认值处理

## 6. 利润评估器集成
- [ ] 6.1 修改 `common/business/profit_evaluator.py`，确保能接收 `source_price` 参数
- [ ] 6.2 验证货源价格正确传递给利润计算
- [ ] 6.3 测试利润评估结果包含货源价格信息

## 7. 主流程集成
- [ ] 7.1 在 `good_store_selector.py` 中集成 `SourceMatcher`
- [ ] 7.2 在 `_process_products()` 方法中添加货源匹配步骤
- [ ] 7.3 确保货源匹配结果正确传递给利润评估器
- [ ] 7.4 处理货源匹配失败的情况（继续后续流程）
- [ ] 7.5 添加日志记录

## 8. 测试和验证
- [ ] 8.1 编写1688 API调用单元测试
- [ ] 8.2 编写AI评估模块单元测试
- [ ] 8.3 编写货源匹配器集成测试
- [ ] 8.4 编写端到端测试（完整匹配流程）
- [ ] 8.5 测试DryRun模式
- [ ] 8.6 测试错误场景（API失败、AI失败、网络超时等）
- [ ] 8.7 测试环境变量缺失时的错误处理
- [ ] 8.8 性能测试（单个商品匹配耗时）

## 9. 文档和清理
- [ ] 9.1 更新README，说明环境变量配置
- [ ] 9.2 添加API使用示例
- [ ] 9.3 添加故障排查指南
- [ ] 9.4 运行 `openspec validate add-1688-source-matching --strict`
- [ ] 9.5 修复所有验证错误
- [ ] 9.6 更新所有任务状态为完成

