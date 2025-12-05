# 图搜抓取器规范

## ADDED Requirements

### Requirement: 图搜抓取器基础功能
ImageSearchScraper SHALL 提供基于代理服务器的图像搜索功能，支持URL搜索和文件上传搜索两种方式。该类不继承 BaseScraper，因为它是纯 API 调用，不涉及浏览器操作。所有方法 MUST 保持同步，符合项目架构约定。

#### Scenario: 根据图片URL搜索商品
- **GIVEN** 一个有效的商品图片URL和搜索参数
- **WHEN** 调用 `search_by_image_url(request: ImageSearchRequest)` 方法
- **THEN** 通过代理服务器调用POST /api/v1/image-search接口
- **AND** 返回标准化的 `ScrapingResult` 对象，包含 `ImageSearchResponse` 数据
- **AND** 结果包含商品ID、标题、价格、图片URL、供应商信息等完整数据

#### Scenario: 上传图片文件并搜索
- **GIVEN** 图片二进制数据和搜索参数
- **WHEN** 调用 `search_by_image_upload(image_data: bytes, params: dict)` 方法
- **THEN** 通过代理服务器调用POST /api/v1/image-upload接口
- **AND** 代理服务器处理图片上传和搜索的完整流程
- **AND** 返回与URL搜索相同格式的搜索结果

#### Scenario: 代理服务器认证
- **GIVEN** 配置的客户端API Key
- **WHEN** 调用任意API方法
- **THEN** 使用Bearer Token方式进行认证
- **AND** 在请求头中添加 Authorization: Bearer {api_key}
- **AND** 认证失败时抛出 `AuthenticationError` 异常

### Requirement: 代理服务器通信和错误处理
ImageSearchScraper SHALL 实现健壮的代理服务器通信和智能错误处理机制，确保API调用的可靠性。

#### Scenario: 网络连接超时处理
- **GIVEN** 代理服务器连接超时或响应超时
- **WHEN** 网络异常被捕获
- **THEN** 使用指数退避策略重试，最多3次
- **AND** 重试间隔为1s, 2s, 4s
- **AND** 最终失败时返回包含详细错误信息的 `ScrapingResult`
- **AND** 错误信息包含网络状态和重试次数

#### Scenario: 代理服务器错误响应处理
- **GIVEN** 代理服务器返回错误响应（4xx, 5xx）
- **WHEN** 检测到错误状态码
- **THEN** 根据错误类型采取相应处理策略
- **AND** 401/403错误立即失败，记录认证问题
- **AND** 429限流错误等待后重试
- **AND** 5xx服务器错误进行重试
- **AND** 记录详细错误日志用于问题排查

#### Scenario: 图片处理错误和降级
- **GIVEN** 图片URL无效、格式不支持或尺寸过大
- **WHEN** 图片验证或处理失败
- **THEN** 返回明确的错误类型和原因
- **AND** 支持的格式：jpg, png, webp, gif（最大8MB）
- **AND** 提供图片处理建议（压缩、格式转换等）
- **AND** 不影响其他商品的处理流程

#### Scenario: 响应数据验证和标准化
- **GIVEN** 代理服务器返回搜索结果
- **WHEN** 处理响应数据
- **THEN** 验证响应格式和必需字段的完整性
- **AND** 将代理服务器数据转换为标准 `ImageSearchProduct` 模型
- **AND** 过滤无效或不完整的商品数据
- **AND** 记录数据质量统计信息

### Requirement: 数据标准化和验证
ImageSearchScraper SHALL 对代理服务器返回数据进行标准化处理和验证，确保数据质量和一致性。

#### Scenario: 响应数据验证
- **GIVEN** 代理服务器返回商品数据
- **WHEN** 解析响应
- **THEN** 验证必需字段存在（product_id, title, price, main_image_url）
- **AND** 数据类型转换和格式标准化
- **AND** 过滤无效或不完整的商品数据

#### Scenario: 价格数据处理
- **GIVEN** 返回的价格信息
- **WHEN** 处理价格数据
- **THEN** 统一价格单位为人民币元
- **AND** 处理价格区间，取最低价格
- **AND** 验证价格合理性（> 0 且 < 999999）

#### Scenario: 图片URL处理
- **GIVEN** 返回的图片URL
- **WHEN** 处理图片链接
- **THEN** 验证URL格式有效性
- **AND** 转换为HTTPS协议
- **AND** 添加必要的URL参数（如尺寸限制）

### Requirement: 配置管理和环境适配
ImageSearchScraper SHALL 支持灵活的配置管理，适配不同环境和用户需求。

#### Scenario: 环境变量配置加载
- **GIVEN** 系统环境变量中的代理服务配置
- **WHEN** 初始化 ImageSearchScraper
- **THEN** 自动加载代理服务器地址和客户端API Key
- **AND** 验证配置完整性和有效性
- **AND** 配置缺失时提供明确的错误提示

#### Scenario: 搜索参数配置
- **GIVEN** 用户配置的搜索参数
- **WHEN** 执行商品搜索
- **THEN** 支持配置最大结果数量（默认20）
- **AND** 支持配置搜索超时时间（默认30秒）
- **AND** 支持配置最小相似度阈值（默认0.5）

#### Scenario: 功能启用控制
- **GIVEN** 图搜功能配置
- **WHEN** 系统初始化
- **THEN** 默认禁用图搜功能（enabled=False）
- **AND** 通过配置显式启用
- **AND** 禁用时不初始化相关组件，节省资源
