# 货源匹配规范

## ADDED Requirements

### Requirement: 图像相似度匹配算法
SourceMatcher SHALL 使用多层次图像相似度算法找到最佳货源匹配，确保匹配准确性和效率。所有方法 MUST 保持同步，复用现有 `ProductImageSimilarity` 工具类。

#### Scenario: 多层次匹配策略
- **GIVEN** OZON商品图片和1688候选商品列表
- **WHEN** 执行 `find_best_match()` 方法
- **THEN** 首先使用哈希算法快速筛选相似商品（阈值0.3）
- **AND** 对筛选结果使用SSIM+CLIP算法精确计算相似度
- **AND** 综合图像相似度和价格因素计算最终匹配分数

#### Scenario: 相似度阈值控制
- **GIVEN** 配置的相似度阈值参数
- **WHEN** 计算商品匹配度
- **THEN** 高置信度匹配要求相似度 ≥ 0.85
- **AND** 中等置信度匹配要求相似度 ≥ 0.70
- **AND** 最低可接受匹配要求相似度 ≥ 0.50
- **AND** 低于最低阈值的商品被排除

#### Scenario: 批量同步处理
- **GIVEN** 多个候选商品需要计算相似度
- **WHEN** 处理候选商品列表
- **THEN** 使用同步方式顺序处理，符合项目架构约定
- **AND** 限制单次处理的最大候选数量（默认50个）
- **AND** 实现超时控制避免长时间阻塞
- **AND** 单个图片处理失败不影响其他候选商品的处理

### Requirement: 匹配结果评估和排序
SourceMatcher SHALL 对匹配结果进行综合评估和智能排序，提供最优的货源推荐。

#### Scenario: 综合评分计算
- **GIVEN** 商品的图像相似度和价格信息
- **WHEN** 计算最终匹配分数
- **THEN** 图像相似度权重占80%
- **AND** 价格优势权重占20%（可配置）
- **AND** 价格优势 = (OZON预估售价 - 1688价格) / OZON预估售价

#### Scenario: 匹配置信度分级
- **GIVEN** 计算出的匹配分数
- **WHEN** 评估匹配质量
- **THEN** 分数 ≥ 0.85 标记为HIGH置信度
- **AND** 分数 0.70-0.84 标记为MEDIUM置信度
- **AND** 分数 0.50-0.69 标记为LOW置信度
- **AND** 分数 < 0.50 标记为不匹配

#### Scenario: 结果排序和过滤
- **GIVEN** 所有候选商品的匹配分数
- **WHEN** 生成最终匹配结果
- **THEN** 按匹配分数降序排列
- **AND** 返回最高分商品作为最佳匹配
- **AND** 提供前5个候选商品的详细信息
- **AND** 过滤掉明显不合理的价格（过高或过低）

### Requirement: 图像处理和优化
SourceMatcher SHALL 对输入图像进行预处理和优化，提高匹配算法的准确性和性能。

#### Scenario: 图像预处理标准化
- **GIVEN** 来自不同源的商品图片
- **WHEN** 进行相似度比较前
- **THEN** 统一图片尺寸为800x800像素（保持宽高比）
- **AND** 转换为RGB格式
- **AND** 去除图片水印和边框干扰（如可能）

#### Scenario: 图像质量检测
- **GIVEN** 输入的商品图片
- **WHEN** 开始匹配处理
- **THEN** 检测图片分辨率和清晰度
- **AND** 过滤分辨率过低的图片（< 200x200）
- **AND** 记录图片质量问题用于结果解释

#### Scenario: 图像特征缓存管理
- **GIVEN** 频繁访问的商品图片
- **WHEN** 进行相似度计算
- **THEN** 使用图片URL的MD5哈希作为缓存键
- **AND** 实现LRU缓存策略，最大缓存100个CLIP特征向量
- **AND** 特征缓存持久化到磁盘（pickle格式），支持跨任务复用

### Requirement: 图片本地缓存管理
SourceMatcher SHALL 通过 ImageCacheManager 管理图片下载和本地缓存，支持多次选品任务复用。

#### Scenario: 图片缓存目录结构
- **GIVEN** 图片缓存功能启用
- **WHEN** 初始化缓存管理器
- **THEN** 复用现有工作目录，创建缓存结构：`~/.xp/cache/images/`
- **AND** 按平台分类存储：`ozon/`、`1688/`、`features/`
- **AND** 使用URL的MD5哈希作为文件名，避免路径冲突
- **AND** 目录结构跨平台兼容（Windows/macOS/Linux）

#### Scenario: 缓存优先下载策略
- **GIVEN** 需要获取商品图片
- **WHEN** 调用 `ImageCacheManager.get_image(url, platform)`
- **THEN** 首先检查本地缓存是否存在且未过期（默认7天TTL）
- **AND** 缓存命中时直接返回本地图片，不发起网络请求
- **AND** 缓存未命中时下载图片并保存到缓存

#### Scenario: 多任务缓存复用
- **GIVEN** 多次选品任务处理相似商品
- **WHEN** 不同任务请求相同的1688候选图片
- **THEN** 第二次及以后的任务直接使用缓存，无需重复下载
- **AND** 缓存统计信息记录命中率用于性能分析

#### Scenario: 防盗链处理
- **GIVEN** 1688或OZON图片URL
- **WHEN** 下载图片
- **THEN** 自动添加平台对应的Referer头
- **AND** 使用标准浏览器User-Agent
- **AND** 下载失败时按指数退避重试（最多3次）

#### Scenario: 缓存空间管理
- **GIVEN** 缓存目录可能增长过大
- **WHEN** 系统启动或缓存超过限制（默认5GB）
- **THEN** 自动清理过期缓存文件（超过TTL）
- **AND** 按LRU策略删除最老的文件直到低于限制
- **AND** 记录清理日志便于问题排查

### Requirement: 性能监控和统计
SourceMatcher SHALL 提供详细的性能监控和匹配统计，支持系统优化和问题诊断。

#### Scenario: 匹配性能监控
- **GIVEN** 货源匹配处理过程
- **WHEN** 执行匹配操作
- **THEN** 记录每个阶段的耗时（API调用、图像下载、相似度计算）
- **AND** 监控内存使用情况
- **AND** 统计匹配成功率和失败原因

#### Scenario: 匹配质量统计
- **GIVEN** 一段时间内的匹配结果
- **WHEN** 生成统计报告
- **THEN** 统计各置信度级别的匹配数量
- **AND** 计算平均匹配分数和分布
- **AND** 分析匹配失败的主要原因

#### Scenario: 异常检测和告警
- **GIVEN** 匹配过程中的异常情况
- **WHEN** 检测到性能或质量问题
- **THEN** 匹配成功率低于80%时记录告警
- **AND** 平均处理时间超过15秒时记录告警
- **AND** 连续失败超过5次时暂停处理并告警

### Requirement: 货源匹配数据模型
SourceMatcher SHALL 使用标准化的数据模型表示匹配结果，确保与其他模块的兼容性。

#### Scenario: SourceMatchResult 模型定义
- **GIVEN** 匹配完成后的结果数据
- **WHEN** 构造返回对象
- **THEN** 包含匹配状态（matched: bool）和置信度（match_confidence: str）
- **AND** 包含最佳匹配商品（best_match: Optional[ImageSearchProduct]）
- **AND** 包含所有候选商品列表（all_candidates: List[ImageSearchProduct]）
- **AND** 列表字段使用 `field(default_factory=list)` 避免可变默认值问题

#### Scenario: 匹配结果集成
- **GIVEN** 货源匹配结果
- **WHEN** 集成到利润计算流程
- **THEN** 提供采购价格用于利润计算
- **AND** 提供价格优势百分比
- **AND** 提供预估利润率
